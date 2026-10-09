"""CPU-gate pass/fail checks (patch 0040): gate_check.py on synthetic junit XML, logs and threshold files."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

TREE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gate_check', TREE / 'campaigns' / 'pilot1005' / 'gate_check.py')
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

SKIP = ('<skipped type="pytest.skip" message="main() is exercised on the A build">'
        'analysis/test_attn_entropy.py:142: main() is exercised on the A build</skipped>')


def junit(extra_pass=0, fail=None, skips=2, stray_skip=False, missing_required=None):
    cases = []
    for name in gc.REQUIRED:
        if name == missing_required:
            continue
        mod = name[:-3].replace('/', '.')
        cases.append(f'<testcase classname="{mod}" name="test_one" time="0.1"/>')
    for i in range(extra_pass):
        cases.append(f'<testcase classname="tests.test_other" name="test_{i}" time="0.1"/>')
    for i in range(skips):
        cases.append(f'<testcase classname="analysis.test_attn_entropy" name="test_main[{i}]" time="0">{SKIP}</testcase>')
    if stray_skip:
        cases.append('<testcase classname="tests.test_other" name="test_skipme" time="0">'
                     '<skipped message="no gpu">tests/test_other.py:9: no gpu</skipped></testcase>')
    if fail:
        cases.append(f'<testcase classname="{fail}" name="test_bad" time="0"><failure message="x">boom</failure></testcase>')
    return ('<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" errors="0" '
            f'failures="0" skipped="{skips}" tests="{len(cases)}">' + ''.join(cases) + '</testsuite></testsuites>')


class PytestCheck(unittest.TestCase):
    def check(self, xml, exit_code=0, total=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p.xml'
            path.write_text(xml)
            n = total if total is not None else len(gc.REQUIRED) + 10 + 2
            return gc.check_pytest(path, exit_code, n)

    def test_pass(self):
        self.assertIsNone(self.check(junit(extra_pass=10)))

    def test_failure_exit_and_count(self):
        self.assertIn('failed', self.check(junit(extra_pass=9, fail='tests.test_other'), exit_code=1))
        self.assertIn('pytest exit 1', self.check(junit(extra_pass=10), exit_code=1))
        self.assertIn('collected', self.check(junit(extra_pass=11)))

    def test_skips_exact(self):
        self.assertIn('skipped', self.check(junit(extra_pass=11, skips=1)))
        self.assertIn('skipped', self.check(junit(extra_pass=9, skips=2, stray_skip=True)))

    def test_required_file_missing(self):
        problem = self.check(junit(extra_pass=11, missing_required='tests/test_run_pack.py'))
        self.assertIn('tests/test_run_pack.py', problem)


class OtherChecks(unittest.TestCase):
    def test_cpu_gate_log(self):
        lines = []
        for i in range(gc.N_CONFIGS):
            lines += [f'PID_TRACED_ONLY_OK n{i} warmup 1', f'CONFIG_PREFLIGHT_PASS n{i} params 1']
        lines += ['PAIRED_INIT_OK E seed 1 arms 9', 'PAIRED_INIT_OK A07 seed 1 arms 5',
                  f'PREFLIGHT_ALL_PASS {gc.N_CONFIGS} production 0 pilot_only {gc.N_CONFIGS}']
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'g.log'
            log.write_text('\n'.join(lines) + '\n')
            self.assertIsNone(gc.check_cpu_gate(log, 0))
            self.assertIn('exit', gc.check_cpu_gate(log, 1))
            log.write_text('\n'.join(lines[2:]) + '\n')
            self.assertIsNotNone(gc.check_cpu_gate(log, 0))

    def test_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 't.json'
            path.write_text(json.dumps({'val_accuracy_threshold': gc.THRESHOLD_C, 'labels_sha256': gc.LABELS_SHA256}))
            self.assertIsNone(gc.check_threshold(path))
            path.write_text(json.dumps({'val_accuracy_threshold': 0.21, 'labels_sha256': gc.LABELS_SHA256}))
            self.assertIn('threshold', gc.check_threshold(path))

    def test_nb_pairing(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'n.log'
            log.write_text('\n'.join([f'NB_PAIRED_OK {s} kernels 15' for s in range(1, 9)] + ['NB_PAIRING_ALL_OK 8']) + '\n')
            self.assertIsNone(gc.check_nb_pairing(log, 0))
            self.assertIn('exit', gc.check_nb_pairing(log, 1))
            log.write_text('\n'.join([f'NB_PAIRED_OK {s} kernels 15' for s in range(1, 8)] + ['NB_PAIRING_ALL_OK 7']) + '\n')
            self.assertIn('seeds', gc.check_nb_pairing(log, 0))

    def test_main_prints_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gc.main(['threshold', '--json', str(Path(tmp) / 'missing.json')]), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
