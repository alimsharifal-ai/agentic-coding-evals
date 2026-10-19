"""Public behavioral checks, run in a separate interpreter by evaluate.py."""
import copy
import importlib.util
import json
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

candidate = None


class MergeChecks(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(candidate.merge_updates([]), {})

    def test_order_and_users(self):
        updates = [
            {'user_id': 'a', 'revision': 2, 'changes': {'name': 'new'}},
            {'user_id': 'b', 'revision': 1, 'changes': {'name': 'other'}},
            {'user_id': 'a', 'revision': 1, 'changes': {'name': 'old', 'age': 20}},
        ]
        self.assertEqual(candidate.merge_updates(updates), {
            'a': {'name': 'new', 'age': 20}, 'b': {'name': 'other'}})

    def test_last_duplicate_replaces_entire_update(self):
        rows = [
            {'user_id': 'a', 'revision': 1, 'changes': {'stale': True}},
            {'user_id': 'a', 'revision': 1, 'changes': {'name': 'last'}},
        ]
        self.assertEqual(candidate.merge_updates(rows), {'a': {'name': 'last'}})

    def test_none_deletes_and_keeps_empty_user(self):
        rows = [
            {'user_id': 'a', 'revision': 1, 'changes': {'name': 'old'}},
            {'user_id': 'a', 'revision': 2, 'changes': {'name': None, 'missing': None}},
        ]
        self.assertEqual(candidate.merge_updates(rows), {'a': {}})

    def test_no_input_mutation_or_alias(self):
        rows = [{'user_id': 'a', 'revision': 1, 'changes': {'tags': ['x']}}]
        original = copy.deepcopy(rows)
        result = candidate.merge_updates(rows)
        self.assertEqual(rows, original)
        result['a']['tags'].append('y')
        self.assertEqual(rows, original)

    def test_nested_values_replace_not_merge(self):
        rows = [
            {'user_id': 'a', 'revision': 1, 'changes': {'prefs': {'x': 1}}},
            {'user_id': 'a', 'revision': 2, 'changes': {'prefs': {'y': 2}}},
        ]
        self.assertEqual(candidate.merge_updates(rows), {'a': {'prefs': {'y': 2}}})


class RetryChecks(unittest.TestCase):
    def test_sequence(self):
        self.assertEqual([candidate.retry_delay(n) for n in range(1, 6)], [0, 1, 2, 4, 8])

    def test_cap(self):
        self.assertEqual(candidate.retry_delay(9, base=3, cap=10), 10)

    def test_custom_base(self):
        self.assertEqual(candidate.retry_delay(3, base=5, cap=100), 10)

    def test_zero(self):
        self.assertEqual(candidate.retry_delay(3, base=0), 0)
        self.assertEqual(candidate.retry_delay(3, cap=0), 0)

    def test_invalid(self):
        for n in (0, -1, 1.5, True, '2'):
            with self.assertRaises(ValueError):
                candidate.retry_delay(n)
        for options in ({'base': -1}, {'cap': -2}, {'base': True}, {'cap': 0.5}):
            with self.assertRaises(ValueError):
                candidate.retry_delay(1, **options)

    def test_large_attempt(self):
        self.assertEqual(candidate.retry_delay(10000), 60)


class SessionChecks(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.store = candidate.SessionStore(lambda: self.now)

    def test_missing_and_delete(self):
        self.assertIsNone(self.store.get('missing'))
        self.assertFalse(self.store.delete('missing'))
        self.store.put('a', {'v': 1}, 10)
        self.assertTrue(self.store.delete('a'))
        self.assertIsNone(self.store.get('a'))

    def test_expiry_boundary(self):
        self.store.put('a', {'v': 1}, 10)
        self.now = 109.999
        self.assertEqual(self.store.get('a'), {'v': 1})
        self.now = 110
        self.assertIsNone(self.store.get('a'))

    def test_write_copy(self):
        data = {'items': [1]}
        self.store.put('a', data, 10)
        data['items'].append(2)
        self.assertEqual(self.store.get('a'), {'items': [1]})

    def test_read_copy(self):
        self.store.put('a', {'items': [1]}, 10)
        self.store.get('a')['items'].append(2)
        self.assertEqual(self.store.get('a'), {'items': [1]})

    def test_refresh(self):
        self.store.put('a', {'v': 1}, 10)
        self.now = 105
        self.store.put('a', {'v': 2}, 20)
        self.now = 111
        self.assertEqual(self.store.get('a'), {'v': 2})

    def test_invalid(self):
        for ttl in (0, -1, float('inf'), float('nan'), True):
            with self.assertRaises(ValueError):
                self.store.put('a', {}, ttl)
        for key in ('', None, 1):
            with self.assertRaises(ValueError):
                self.store.put(key, {}, 10)

    def test_threaded_distinct_sessions(self):
        def work(index):
            key = str(index)
            self.store.put(key, {'owner': index}, 10)
            return self.store.get(key)
        with ThreadPoolExecutor(max_workers=16) as pool:
            values = list(pool.map(work, range(1000)))
        self.assertEqual(values, [{'owner': i} for i in range(1000)])


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'id': test.id(), 'status': 'pass'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({'id': test.id(), 'status': 'fail',
                             'evidence': self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({'id': test.id(), 'status': 'error',
                             'evidence': self._exc_info_to_string(err, test)})


if __name__ == '__main__':
    spec = importlib.util.spec_from_file_location('candidate', sys.argv[1])
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (MergeChecks, RetryChecks, SessionChecks))
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    with open(sys.argv[2], 'w', encoding='utf-8') as out:
        json.dump({'tests': result.records, 'total': result.testsRun}, out, indent=2)
    sys.exit(0 if result.wasSuccessful() else 1)
