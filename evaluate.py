"""Evaluate trusted Python/Go candidates and save evidence for human review."""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def evaluate(language, source, output, timeout=60):
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_file():
        raise ValueError(f'Candidate file not found: {source}')
    if timeout <= 0:
        raise ValueError('Timeout must be positive')
    output.mkdir(parents=True, exist_ok=True)
    records = []
    started = time.monotonic()
    status = 'completed'
    with tempfile.TemporaryDirectory(prefix='coding-eval-') as directory:
        work = Path(directory)
        if language == 'python':
            shutil.copy2(source, work / 'solution.py')
            shutil.copy2(ROOT / 'checks.py', work / 'checks.py')
            command = [sys.executable, '-I', str(work / 'checks.py'),
                       str(work / 'solution.py'), str(work / 'results.json')]
        else:
            shutil.copy2(source, work / 'solution.go')
            shutil.copy2(ROOT / 'go-project' / 'solution_test.go', work / 'solution_test.go')
            shutil.copy2(ROOT / 'go-project' / 'go.mod', work / 'go.mod')
            command = ['go', 'test', '-json', '-count=1', '-timeout', f'{timeout}s', '.']
        try:
            process = subprocess.run(command, cwd=work, capture_output=True,
                                     text=True, timeout=timeout)
            log = process.stdout + '\n' + process.stderr
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            log, returncode, status = 'Candidate exceeded evaluation timeout.', None, 'timeout'
        except OSError as exc:
            log, returncode, status = str(exc), None, 'runner_error'
        if status == 'completed':
            if language == 'python' and (work / 'results.json').exists():
                records = json.loads((work / 'results.json').read_text())['tests']
            elif language == 'go':
                evidence = {}
                for line in process.stdout.splitlines():
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    name = event.get('Test')
                    if not name:
                        continue
                    if event['Action'] == 'output':
                        evidence.setdefault(name, []).append(event.get('Output', ''))
                    if event['Action'] in ('pass', 'fail', 'skip'):
                        records.append({'id': name, 'status': event['Action'],
                                        'evidence': ''.join(evidence.get(name, []))})
            if not records or returncode not in (0, 1):
                status = 'runner_error'
    passed = sum(record['status'] == 'pass' for record in records)
    report = {
        'schema_version': 1, 'language': language, 'candidate': source.name,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': status, 'returncode': returncode,
        'duration_seconds': round(time.monotonic() - started, 3),
        'passed': passed, 'total': len(records),
        'pass_rate': round(passed / len(records), 4) if records else 0,
        'tests': records,
        'human_review': {key: {'score': None, 'evidence': ''} for key in
                         ('instruction_following', 'maintainability', 'tool_use', 'explanation_accuracy')},
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (output / 'execution.log').write_text(log, encoding='utf-8')
    lines = ['# Coding evaluation report', '', f'Language: {language}',
             f'Status: {status}', f'Passed: {passed}/{len(records)}', '',
             '| Check | Result |', '| --- | --- |']
    lines.extend(f"| {r['id']} | {r['status']} |" for r in records)
    lines += ['', 'Human review is pending. Test pass rate is not a complete quality rating.',
              'See report.json and execution.log for evidence.']
    (output / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=['python', 'go'], required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    try:
        report = evaluate(args.language, args.candidate, args.output, args.timeout)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"{report['status']}: {report['passed']}/{report['total']} checks passed")
    return 0 if report['status'] == 'completed' and report['returncode'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
