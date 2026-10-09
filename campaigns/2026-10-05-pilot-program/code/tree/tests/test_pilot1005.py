"""Pilot program R1 (patch 0035): the pilot1005 generator, its 19 configs and the warmup-aware monitor.

Synthetic only (no model, no training): the generator's byte checks against chang0926/chang1002c,
the arm table, the option-(c) schedule for warmup 1/50/100 through the runner's own functions, and
monitor_p.py on telemetry from hgq2's real BetaPID driven by a scalar plant
(test_option_c_amendment.simulate).
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
TREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TREE))
CAMP = TREE / 'campaigns' / 'pilot1005'

from bnhgq2 import ablation  # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = load_module(CAMP / 'generate.py', 'pilot1005_generate')
monitor = load_module(CAMP / 'monitor_p.py', 'monitor_p')
amendment = load_module(TREE / 'tests' / 'test_option_c_amendment.py', 'option_c_amendment_helpers')
INDEX = json.loads((CAMP / 'index.json').read_text())['runs']


def cfg_of(name):
    return json.loads((CAMP / 'configs' / f'{name}.json').read_text())


class Generator(unittest.TestCase):
    def test_idempotent_and_byte_checked(self):
        built = generate.build_all()          # asserts chang0926 / chang1002c bases byte-exact
        cmap = json.loads((CAMP / 'config_map.json').read_text())['rows']
        self.assertEqual(len(built), 24)
        self.assertEqual(len(INDEX), 24)
        for i, (b, row, m) in enumerate(zip(built, INDEX, cmap)):
            data = (CAMP / 'configs' / row['file']).read_bytes()
            self.assertEqual(data, generate.encode(b['cfg']))
            self.assertEqual(generate.sha(data), row['config_sha256'])
            self.assertEqual(m['sha256'], row['config_sha256'])
            self.assertEqual(row['index'], i)
            self.assertEqual(json.loads((CAMP / row['pack']).read_text()), [[i]])
        self.assertEqual(json.loads((CAMP / 'r1_packs.json').read_text()), [[i] for i in range(24)])

    def test_arm_table(self):
        got = sorted((r['hypothesis'], r['arch_name'], r['budget'], r['option_c'], r['warmup'], r['seed'], str(r['variant']))
                     for r in INDEX)
        want = sorted([('H1', 'E', 350000, c, 1, s, 'None') for c in (True, False) for s in (1, 2)]
                      + [('H2', 'E', t, True, 1, 1, 'None') for t in (250000, 500000, 750000, 1000000, 2000000, 5000000)]
                      + [('H2', 'A07', t, True, 1, 1, 'None') for t in (500000, 1000000, 2000000, 5000000)]
                      + [('H4', 'E', 350000, True, w, s, 'None') for w in (50, 100) for s in (1, 2)]
                      + [('H5', 'E', 350000, True, 1, s, 'nb') for s in (1, 2)]
                      + [('H3', 'E', 350000, True, 1, s, 'qkv1') for s in (1, 2)]
                      + [('H3', 'E', 450000, True, 1, 1, 'qkv1'), ('control', 'E', 100000000, True, 1, 1, 'unc')])
        self.assertEqual(got, want)
        for r in INDEX:
            cfg = cfg_of(r['name'])
            self.assertEqual(cfg['train']['ebops']['pid']['target_ebops'], r['budget'])
            self.assertEqual(cfg['train']['ebops_trace_every'], 10)
            self.assertEqual(cfg['train']['optimizer'], 'adam_default')
            self.assertEqual(cfg['experiment']['group'], 'chang-n64-20261005')
            floor = {'qkv1': 269830}.get(r['variant']) or {'E': 171526, 'A07': 343053}[r['arch_name']]
            self.assertEqual(cfg['quant']['weight'], 'kbi_learnable' if r['variant'] == 'nb' else 'binary_absmean')
            self.assertEqual(cfg['quant'].get('attn_bit_floor'),
                             {'bits': 1, 'sites': ['q', 'k', 'v']} if r['variant'] == 'qkv1' else None)
            self.assertEqual(cfg['experiment']['nondegenerate']['zero_floor_ebops'], floor)
            self.assertGreater(r['budget'], floor)
            self.assertFalse(r['headroom_flag'])
            self.assertIs(cfg['campaign']['production'], False)              # [A3] F2 iv

    def test_h1_pair_differs_only_in_pid_input(self):
        for s in (1, 2):
            a, b = cfg_of(f'pilot1005-h1-e-350k-c-s{s}'), cfg_of(f'pilot1005-h1-e-350k-noc-s{s}')
            d = generate.load(TREE / 'campaigns/chang0926/generate.py', 'g').diff(a, b)
            self.assertEqual(set(d['removed']), {'train.ebops.pid_input', 'train.ebops.pid_traced_integral',
                                                 'campaign.amendment'})
            self.assertEqual(set(d['changed']), {'name', 'experiment.arm', 'campaign.revision_of',
                                                 'campaign.pilot.option_c', 'campaign.pilot.arm'})
            self.assertEqual((a['campaign']['pilot']['arm'], b['campaign']['pilot']['arm']), ('A350-C', 'A350-noC'))
            self.assertEqual(ablation.pid_traced_only(a), 'per_epoch')
            self.assertIsNone(ablation.pid_traced_only(b))

    def test_warmup_schedule_is_legal(self):
        for r in INDEX:
            cfg = cfg_of(r['name'])
            if not r['option_c']:
                continue
            w = r['warmup']
            self.assertEqual(ablation.pid_traced_only(cfg), 'per_epoch')    # raises if warmup - 1 untraced
            self.assertEqual(ablation.pid_step_epochs(cfg, w), (True, 1))
            first = {1: 10, 50: 60, 100: 110}[w]
            self.assertEqual(ablation.pid_step_epochs(cfg, first), (True, first - w))
            self.assertTrue(all(not ablation.pid_step_epochs(cfg, e)[0] for e in range(w + 1, first)))

    def test_illegal_warmup_rejected(self):
        self.assertFalse(generate.warmup_ok(45))
        self.assertTrue(generate.warmup_ok(50) and generate.warmup_ok(100) and generate.warmup_ok(1))


class MonitorWarmup(unittest.TestCase):
    def run_monitor(self, name, epochs):
        cfg = cfg_of(name)
        rows, _ = amendment.simulate(cfg, epochs)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pid_telemetry.jsonl'
            for row in rows:
                ablation.append_jsonl(path, row)
            return rows, monitor.main(['--config', str(CAMP / 'configs' / f'{name}.json'), '--telemetry', str(path)])

    def test_canary_follows_warmup(self):
        for name, first in (('pilot1005-h1-e-350k-c-s1', 10), ('pilot1005-h4-e-350k-c-w50-s1', 60),
                            ('pilot1005-h4-e-350k-c-w100-s2', 110)):
            rows, report = self.run_monitor(name, first + 15)
            self.assertEqual(report['canary']['first_feedback_epoch'], first)
            self.assertTrue(report['canary']['CANARY_PID_FIRST'], (name, report['canary']))
            self.assertEqual(report['audit_problems'], [], name)
            self.assertEqual(rows[first]['pid_step_span'], first - cfg_of(name)['train']['ebops']['pid']['warmup'])

    def test_canary_fails_when_feedback_step_is_wrong(self):
        name = 'pilot1005-h4-e-350k-c-w50-s1'
        rows, _ = amendment.simulate(cfg_of(name), 70)
        rows[60]['pid_step_span'] = 9
        self.assertFalse(monitor.canary(cfg_of(name), rows)['CANARY_PID_FIRST'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
