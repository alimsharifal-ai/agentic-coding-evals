import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('evaluate', ROOT / 'evaluate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HarnessTests(unittest.TestCase):
    def test_reference_and_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = module.evaluate('python', ROOT / 'candidates/reference/solution.py', Path(directory) / 'ref')
            baseline = module.evaluate('python', ROOT / 'candidates/baseline/solution.py', Path(directory) / 'base')
            self.assertEqual(reference['status'], 'completed')
            self.assertEqual(reference['passed'], 19)
            self.assertEqual(reference['total'], 19)
            self.assertEqual(baseline['status'], 'completed')
            self.assertEqual(baseline['total'], 19)
            self.assertLess(baseline['passed'], baseline['total'])
            self.assertTrue((Path(directory) / 'ref/report.md').exists())

    def test_import_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'broken.py'
            source.write_text('raise RuntimeError("broken import")')
            report = module.evaluate('python', source, Path(directory) / 'out')
            self.assertEqual(report['status'], 'runner_error')
            self.assertEqual(report['total'], 0)

    def test_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'slow.py'
            source.write_text('import time\ntime.sleep(10)')
            report = module.evaluate('python', source, Path(directory) / 'out', timeout=1)
            self.assertEqual(report['status'], 'timeout')
            self.assertEqual(report['total'], 0)


if __name__ == '__main__':
    unittest.main()
