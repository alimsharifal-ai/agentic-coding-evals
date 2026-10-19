# Agentic Coding Evals: Python and Go

A runnable sample project for reviewing coding-agent submissions. It combines
behavioral tests, candidate comparison, execution evidence, and a human rating
rubric. This is a newly created demonstration, not a record of past employment,
client work, or real model performance. The included baseline and reference are
handcrafted fixtures, not outputs attributed to an AI model.

## Requirements

- Python 3.10 or newer for the evaluator and Python tasks.
- Go 1.20 or newer for Go tasks. No third-party packages or API keys are needed.
- Windows, macOS, or Linux. On Windows use `py` instead of `python` if necessary.

## Quick start

Extract the ZIP and open a terminal inside `agentic-coding-evals`.

```sh
python evaluate.py --language python --candidate candidates/reference/solution.py --output reports/python-reference
python evaluate.py --language python --candidate candidates/baseline/solution.py --output reports/python-baseline
python compare.py reports/python-baseline/report.json reports/python-reference/report.json
python evaluate.py --language go --candidate go-project/solution.go --output reports/go-reference
python evaluate.py --language go --candidate candidates/go-baseline/solution.go --output reports/go-baseline
python compare.py reports/go-baseline/report.json reports/go-reference/report.json
```

Reference implementations should pass all checks. Baseline failures are deliberate.
The evaluator exits 1 for failed tests, timeout, compilation failure, or runner errors.
If your first Go compilation is slow, add `--timeout 180`.

The Go project can also run independently:

```sh
cd go-project
go test ./...
go test -race ./...
```

The race detector requires a supported Go platform and a C compiler. Its result
is additional evidence, not proof that every possible race has been excluded.

## What is included

| File or folder | Purpose |
| --- | --- |
| `evaluate.py` | Python CLI that evaluates either language and emits evidence |
| `compare.py` | Side-by-side comparison of equivalent report check sets |
| `checks.py` | 19 Python behavioral checks |
| `go-project/` | Standalone Go module with retry and session-store implementations and 13 tests |
| `candidates/` | Deliberately faulty baselines and a Python reference |
| `tasks/requirements.md` | Coding task contracts and agent instructions |
| `rubric.md` | Evidence-based human evaluation criteria |
| `examples/review_template.json` | Empty human review form |
| `examples/trajectory_example.jsonl` | Explicitly illustrative agent event format |
| `examples/verified-runs/` | Reports generated during validation, when available |
| `tests/` | Tests of report generation, failure handling, and timeout behavior |

## Evaluation workflow

1. Give an agent the task requirements and the baseline for the selected language.
   In a real benchmark, keep references and private checks outside its workspace.
2. Ask it to fix the candidate without changing the required public interface.
   Save the actual conversation, commands, tool outputs, and final explanation.
3. Evaluate the submitted source using `--candidate PATH`. Python submissions
   expose all three task interfaces; Go submissions use package `evaltask` and
   expose the two Go interfaces. This small harness accepts one source file.
4. Read `report.md`, `report.json`, and `execution.log`. Use failure tracebacks
   or named Go test failures as evidence. Keep the submitted source alongside
   its SHA-256 fingerprint in the report.
5. Complete the human review template using `rubric.md`. Leave unavailable
   criteria unrated. Do not infer tool-use quality from a code diff alone.
6. Compare two reports from the same language. The comparison identifies changed
   checks but does not automatically declare an overall winner.

## Scope and limitations

This is an evaluator for submitted code. It does not call an LLM, generate
genuine agent trajectories, or integrate a hosted model provider. Python has
an additional profile-merge task; Go and Python aggregate scores therefore
must not be compared directly.

The session tests exercise 1,000 distinct sessions in one process. They do not
demonstrate a deployment supporting 1,000 network clients, distributed session
consistency, throughput, or production capacity. Expired sessions are removed
lazily on access; this example has no capacity limit or background cleanup.

The runner uses a temporary directory and a subprocess timeout for convenience.
These are NOT a security sandbox: candidate code inherits host permissions and
can read files, access the network, create processes, or tamper with results.
Use only trusted code locally. For untrusted agent submissions, run the entire
evaluation in a disposable restricted VM/container with no credentials, no
network, and CPU/memory/process limits. The included harness does not enforce
those controls or kill all descendant processes.

All checks are public and finite. Passing them does not prove full correctness
or replace human review. Human ratings are intentionally separate from the
automated pass rate. Reruns can have different timings and timestamps.

## Harness validation

```sh
python -m unittest discover -s tests -v
```

See `VALIDATION.md` for the checks actually executed when this sample was created.
