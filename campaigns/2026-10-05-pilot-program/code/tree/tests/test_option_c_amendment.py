"""Option-(c) amendment (2026-10-01), patch 0033: explicit integral key, routing guard, input
guard, durable controller telemetry, pilot-c stage, the chang1002c configs and the monitor.

Synthetic only: hgq2 0.1.9's real BetaPID with its model hooks replaced by a scalar plant, so no
model is built and nothing is trained. Runs under pytest or `python -m unittest`. The
run_training integration tests (test_pid_traced_only.py) need the CPU suite job, not a laptop.
"""
import copy
import importlib.util
import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
TREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TREE))
CAMP = TREE / 'campaigns' / 'chang1002c'

from hgq.utils.sugar import BetaPID  # noqa: E402
from bnhgq2 import ablation  # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


monitor = load_module(CAMP / 'monitor_c.py', 'monitor_c')


def config(name='chang1002c-a-n64-s1'):
    return json.loads((CAMP / 'configs' / f'{name}.json').read_text())


class ScalarPID(BetaPID):
    """hgq2's BetaPID with get_ebops/set_beta on a scalar instead of a Keras model."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.stored = 0.0
        self.applied = []

    def get_ebops(self):
        return float(self.stored)

    def set_beta(self, beta):
        self.applied.append(float(beta))

    def get_avg_beta(self):
        return self.applied[-1] if self.applied else 0.0


def plant(epoch, beta):
    """Deterministic synthetic costs: traced falls with epoch and with beta; in-training is 3 % above."""
    traced = 9.4e6 * math.exp(-epoch / 15.0) + 3.0e5 * (1.0 + 0.1 * math.sin(epoch)) / (1.0 + 1e5 * beta)
    return traced, 1.03 * traced


def simulate(cfg, epochs, start=None):
    """The run_training controller sequence for option (c), epoch by epoch, with the same calls
    and guards. `start`: (completed_epochs, state['pid']) to resume, as restore_checkpoint does."""
    mode = ablation.pid_traced_only(cfg)
    pid = ScalarPID(**cfg['train']['ebops']['pid'])
    pid.stored = plant(0, 1e-7)[0]
    pid.on_train_begin({})
    first, state_pid = (0, None) if start is None else start
    if state_pid:
        pid.beta, pid._ebops = state_pid['beta'], state_pid['ebops']
        pid.pid.integral, pid.pid.prev_error = state_pid['integral'], state_pid['prev_error']
        pid.set_beta(pid.beta)
    last_trace = state_pid['ebops'] if state_pid else None
    warmup = int(cfg['train']['ebops']['pid'].get('warmup', 10))
    rows = []
    for epoch in range(first, epochs):
        pid.target_ebops = ablation.training_target(cfg, epoch)
        reads = ablation.pid_step_epochs(cfg, epoch)[0] and epoch >= warmup
        pid_input = float(pid._ebops) if reads else None
        if reads:
            ablation.pid_input_check(pid_input, last_trace)
        err = ablation.pid_error(pid) if reads else None
        stepped, span = ablation.pid_begin_traced_only(pid, cfg, epoch, mode)
        beta_after = float(pid.beta)
        traced_cost, in_training = plant(epoch, beta_after)
        pid.stored = in_training                      # last training step's stored layer cost
        traced = ablation.is_traced_epoch(cfg, epoch)
        if traced:
            pid.stored = traced_cost                  # the trace overwrites the stored cost
            last_trace = traced_cost
            pid.on_epoch_end(epoch, {})
        else:
            assert pid._ebops == state_pid['ebops']
        state_pid = {'beta': pid.beta, 'ebops': pid._ebops, 'integral': pid.pid.integral,
                     'prev_error': pid.pid.prev_error}
        rows.append(ablation.pid_telemetry_row(
            epoch, stepped=stepped, span=span, pid_input=pid_input, pid_error_value=err,
            integral=pid.pid.integral, prev_error=pid.pid.prev_error, beta_after_step=beta_after,
            beta_end=pid.beta, target=pid.target_ebops, ebops_in_training=in_training, traced=traced,
            ebops_traced=traced_cost if traced else None, pid_ebops_end=pid._ebops, learning_rate=1e-3,
            monitor={'loss': 2.0 - 0.01 * epoch, 'val_categorical_accuracy': 0.5, 'val_macro_auc': 0.8,
                     'budget_met': None if not traced else int(traced_cost <= pid.target_ebops),
                     'nondegenerate': None if not traced else 1}))
    return rows, state_pid


class KeyGuards(unittest.TestCase):
    def test_explicit_integral_required(self):
        cfg = config()
        self.assertEqual(ablation.pid_traced_only(cfg), 'per_epoch')
        bad = copy.deepcopy(cfg)
        del bad['train']['ebops']['pid_traced_integral']
        with self.assertRaises(ValueError):
            ablation.pid_traced_only(bad)
        bad = copy.deepcopy(cfg)
        bad['train']['ebops']['pid_traced_integral'] = 'per_time'
        with self.assertRaises(ValueError):
            ablation.pid_traced_only(bad)

    def test_historical_config_is_slot_p(self):
        old = json.loads((TREE / 'campaigns/chang0926/configs/chang0926-a-n64-s1.json').read_text())
        self.assertIsNone(ablation.pid_traced_only(old))


class Controller(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.rows, self.state = simulate(self.cfg, 60)
        self.pid = self.cfg['train']['ebops']['pid']

    def test_schedule_and_spans(self):
        stepped = [(r['epoch'], r['pid_step_span']) for r in self.rows if r['pid_stepped']]
        self.assertEqual(stepped, [(0, 1), (1, 1), (10, 9), (20, 10), (30, 10), (40, 10), (50, 10)])

    def test_seed_keeps_beta_and_held_epochs_freeze_state(self):
        r1 = self.rows[1]
        self.assertAlmostEqual(math.log10(r1['beta_after_step']), math.log10(self.pid['init_beta']), places=6)
        for prev, row in zip(self.rows, self.rows[1:]):
            if not row['pid_stepped']:
                self.assertEqual((row['beta_after_step'], row['pid_integral'], row['pid_prev_error']),
                                 (prev['beta_end'], prev['pid_integral'], prev['pid_prev_error']))

    def test_inputs_are_traces_and_per_epoch_integral(self):
        last = None
        for prev, row in zip(self.rows, self.rows[1:]):
            if prev['ebops_traced_flag']:
                last = prev['ebops_traced']
            if row['pid_stepped'] and row['epoch'] > 1:
                self.assertEqual(row['pid_input'], last)
                self.assertNotEqual(row['pid_input'], prev['ebops_in_training'])
                err = math.log10(last / row['pid_target_ebops'])
                self.assertAlmostEqual(row['pid_error'], err, places=12)
                self.assertTrue(math.isclose(row['pid_integral'], prev['pid_integral'] + row['pid_step_span'] * err,
                                             rel_tol=1e-12))
                beta = 10 ** (self.pid['p'] * err + self.pid['i'] * row['pid_integral'])
                beta = min(max(beta, self.pid['min_beta']), self.pid['max_beta'])
                self.assertTrue(math.isclose(row['beta_after_step'], beta, rel_tol=1e-12))

    def test_monitor_canary_and_audit_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pid_telemetry.jsonl'
            for row in self.rows:
                ablation.append_jsonl(path, row)
            report = monitor.main(['--config', str(CAMP / 'configs' / 'chang1002c-a-n64-s1.json'),
                                   '--telemetry', str(path)])
        self.assertTrue(report['canary']['CANARY_PID_E11'], report['canary'])
        self.assertTrue(report['canary']['CANARY_LOSS'] and report['canary']['CANARY_TRACE'])
        self.assertEqual(report['audit_problems'], [])

    def test_monitor_detects_in_training_input_and_moving_hold(self):
        rows = copy.deepcopy(self.rows)
        rows[20]['pid_input'] = rows[19]['ebops_in_training']
        rows[15]['beta_after_step'] *= 1.5
        problems = monitor.audit(self.cfg, rows)
        self.assertTrue(any('epoch 20' in p for p in problems) and any('epoch 15' in p for p in problems))
        rows = copy.deepcopy(self.rows)
        rows[10]['pid_step_span'] = 10
        self.assertFalse(monitor.canary(self.cfg, rows)['CANARY_PID_E11'])

    def test_resume_at_untraced_checkpoint_replays(self):
        first, state = simulate(self.cfg, 25)            # checkpoint_every 25: pause at an untraced end
        rest, _ = simulate(self.cfg, 60, start=(25, state))
        self.assertEqual(first + rest, self.rows)

    def test_input_guard(self):
        ablation.pid_input_check(350000.0, 350000.0 * (1 + 5e-7))
        with self.assertRaises(AssertionError):
            ablation.pid_input_check(350000.0 * 1.03, 350000.0)
        with self.assertRaises(AssertionError):
            ablation.pid_input_check(350000.0, None)


class TelemetryFiles(unittest.TestCase):
    def test_truncate_on_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pid_telemetry.jsonl'
            for e in range(30):
                ablation.append_jsonl(path, {'epoch': e})
            self.assertEqual(ablation.truncate_jsonl(path, 25), 25)
            self.assertEqual([json.loads(x)['epoch'] for x in path.read_text().splitlines()], list(range(25)))
            with self.assertRaises(AssertionError):
                ablation.truncate_jsonl(path, 26)

    def test_attention_summary(self):
        widths = {'bit_block_0_attn_scores__in0': {'bits': [[0.0, 0.0], [0.0, 0.0]]},
                  'bit_block_0_attn_scores__in1': {'bits': [0.0, 0.0, 0.0, 0.0]},
                  'bit_block_0_attn_ctx__in1': {'bits': [0.0, 3.0, 2.0, 0.0]},
                  'input_proj__in0': {'bits': [4.0]}}
        per_layer = {'bit_block_0_attn_softmax': 171526.0, 'bit_block_0_attn_Wq': 10.0, 'head_fc1': 5.0}
        s = ablation.attention_summary(widths, per_layer)
        self.assertEqual(s['attn_zero_bits'], {'0': {'q': [4, 4], 'k': [4, 4], 'v': [2, 4]}})
        self.assertEqual(s['attn_qk_all_zero'], 1)
        self.assertEqual((s['attn_softmax_ebops'], s['attn_nonsoftmax_ebops']), (171526.0, 10.0))
        widths['bit_block_0_attn_scores__in0']['bits'][0][0] = 2.0
        self.assertEqual(ablation.attention_summary(widths)['attn_qk_all_zero'], 0)


class Routing(unittest.TestCase):
    def test_callback_route_refuses_option_c(self):
        from bnhgq2 import train
        cfg = config()
        with self.assertRaises(ValueError):
            train.reject_traced_only_pid(cfg)
        with self.assertRaises(ValueError):
            train.ebops_callbacks(cfg, tempfile.gettempdir())
        with self.assertRaises(ValueError):
            train.train(cfg, 1, tempfile.gettempdir())
        old = json.loads((TREE / 'campaigns/chang0926/configs/chang0926-a-n64-s1.json').read_text())
        train.reject_traced_only_pid(old)

    def test_pilot_c_stage(self):
        from bnhgq2.wandb_util import stage_group, stage_run_id
        self.assertEqual(stage_group('chang-n64-20261002-c', 'pilot-c'), 'chang-n64-20261002-c-pilot-c')
        self.assertNotEqual(stage_run_id('chang1002c-a-n64-s1', 'pilot-c'),
                            stage_run_id('chang1002c-a-n64-s1', 'production'))


class GeneratedConfigs(unittest.TestCase):
    def test_index_map_and_idempotence(self):
        generate = load_module(CAMP / 'generate.py', 'chang1002c_generate')
        gen, built = generate.build_all()        # asserts every chang0926 config is rebuilt byte-exact
        index = json.loads((CAMP / 'index.json').read_text())['runs']
        cmap = json.loads((CAMP / 'config_map.json').read_text())
        old_index = json.loads((TREE / 'campaigns/chang0926/index.json').read_text())['runs']
        self.assertEqual(len(index), 58)
        self.assertEqual(sum(r['production'] for r in index), 56)
        for (arm, seed, old_row, old_cfg, new_cfg, delta), row, m, o in zip(built, index, cmap['rows'], old_index):
            data = (CAMP / 'configs' / row['file']).read_bytes()
            self.assertEqual(data, generate.encode(new_cfg))
            self.assertEqual(generate.sha(data), row['config_sha256'])
            self.assertEqual((m['old']['sha256'], m['new']['sha256']), (o['config_sha256'], row['config_sha256']))
            self.assertEqual({k: v for k, v in row.items() if k not in ('name', 'file', 'config_sha256')},
                             {k: v for k, v in o.items() if k not in ('name', 'file', 'config_sha256')})
            cfg = json.loads(data)
            self.assertEqual(ablation.pid_traced_only(cfg), 'per_epoch')
            self.assertEqual(cfg['train']['ebops']['pid'], old_cfg['train']['ebops']['pid'])
            self.assertEqual(ablation.pid_step_epochs(cfg, 10), (True, 9))
        epochs = sorted({json.loads((CAMP / 'configs' / r['file']).read_text())['train']['epochs'] for r in index})
        self.assertEqual(epochs, [1000, 7000])

    def test_pilot_c_packs(self):
        packs = json.loads((CAMP / 'pilot_c_packs.json').read_text())
        index = json.loads((CAMP / 'index.json').read_text())['runs']
        names = [[index[i]['name'] for i in pod] for pod in packs]
        self.assertEqual(names, [['chang1002c-a-n64-s1', 'chang1002c-a-n64-s2', 'chang1002c-d-n64-s1',
                                  'chang1002c-e1-n64-s1'],
                                 ['chang1002c-a07-350-n64-s1', 'chang1002c-c-n64-s1'],
                                 ['chang1002c-f-n64-s1', 'chang1002c-cprime-n64-s1']])


if __name__ == '__main__':
    unittest.main(verbosity=2)
