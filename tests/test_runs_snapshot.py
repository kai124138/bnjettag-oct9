"""tools/runs_snapshot.py: config description, campaign differences, login detection. No cluster."""
import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('runs_snapshot', ROOT / 'tools' / 'runs_snapshot.py')
snap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snap)

BASE = {'name': 'a', 'arch': {'n_part': 64, 'features': ['pt', 'etarel', 'phirel'], 'd_model': 24, 'n_heads': 2},
        'quant': {'weight': 'binary_absmean'}, 'experiment': {'arm': 'a', 'seed': 1},
        'train': {'ebops': {'controller': 'pid', 'pid': {'target_ebops': 350000}}}}


def variant(name, target):
    cfg = {**BASE, 'name': name, 'experiment': {'arm': name, 'seed': 1},
           'train': {'ebops': {'controller': 'pid', 'pid': {'target_ebops': target}}}}
    return cfg


class Describe(unittest.TestCase):
    def test_inputs_and_model_come_from_config(self):
        d = snap.describe(BASE)
        self.assertEqual(d['inputs']['constituents'], 64)
        self.assertEqual(d['inputs']['features'], ['pt', 'etarel', 'phirel'])
        self.assertEqual(d['quant']['target_ebops'], 350000)

    def test_differences_ignore_names_and_keep_scientific_settings(self):
        diff = snap.differences({'a': variant('a', 350000), 'b': variant('b', 5000000)})
        self.assertEqual(diff['a'], {'train.ebops.pid.target_ebops': 350000})
        self.assertEqual(diff['b'], {'train.ebops.pid.target_ebops': 5000000})

    def test_identical_configs_have_no_difference(self):
        self.assertEqual(snap.differences({'a': variant('a', 1), 'b': variant('b', 1)}), {'a': {}, 'b': {}})


class Login(unittest.TestCase):
    def run_kubectl(self, **kw):
        with mock.patch.object(snap.subprocess, 'run', **kw):
            return snap.kubectl(['get', 'pods'])

    def test_unauthorized_reads_as_login_needed(self):
        done = subprocess.CompletedProcess([], 1, '', 'error: You must be logged in to the server (Unauthorized)')
        self.assertEqual(self.run_kubectl(return_value=done)[1], 'login_needed')

    def test_device_code_wait_is_cut_by_the_timeout(self):
        stuck = subprocess.TimeoutExpired(['kubectl'], 25, stderr=b'Please visit the following URL ... device code')
        self.assertEqual(self.run_kubectl(side_effect=stuck)[1], 'login_needed')

    def test_other_errors_are_errors(self):
        done = subprocess.CompletedProcess([], 1, '', 'Unable to connect to the server: dial tcp: i/o timeout')
        self.assertEqual(self.run_kubectl(return_value=done)[1], 'error')


if __name__ == '__main__':
    unittest.main()
