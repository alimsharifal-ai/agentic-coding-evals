"""Compare two reports from the same language and test suite."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left', type=Path)
    parser.add_argument('right', type=Path)
    args = parser.parse_args()
    left, right = (json.loads(path.read_text(encoding='utf-8')) for path in (args.left, args.right))
    if left['language'] != right['language']:
        parser.error('Compare candidates in the same language only.')
    if any(report['status'] != 'completed' for report in (left, right)):
        parser.error('A run did not complete; inspect its execution log.')
    a = {test['id']: test['status'] for test in left['tests']}
    b = {test['id']: test['status'] for test in right['tests']}
    if not a or a.keys() != b.keys():
        parser.error('Reports must contain the same nonempty set of checks.')
    print(f"Left: {left['passed']}/{left['total']}; right: {right['passed']}/{right['total']}")
    for check in sorted(a):
        if a[check] != b[check]:
            print(f'{check}: {a[check]} -> {b[check]}')
    print('Human review is required before selecting an overall winner.')


if __name__ == '__main__':
    main()
