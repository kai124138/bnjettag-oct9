"""Pilot readout (patch 0039): readout_pilot.py on synthetic run directories (no model, no data).

Each fixture writes what the runner writes (activation_widths.jsonl, snapshots/epoch-0500/state.json,
latest.json + checkpoints/<leaf>/state.json, nondegenerate_rule.json, DIVERGED.json) plus the a26,
certification and controller JSON the readout Job produces, then checks every field and status.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

TREE = Path(__file__).resolve().parents[1]
CAMP = TREE / 'campaigns' / 'pilot1005'
spec = importlib.util.spec_from_file_location('readout_pilot', CAMP / 'readout_pilot.py')
readout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readout)

THR = readout.THRESHOLD_C
LABELS = readout.LABELS_SHA256
E_FLOOR = 171526


def traced(epoch):
    return epoch == 0 or (epoch + 1) % 10 == 0


def row(name, arm, *, option_c=True, budget=350000, warmup=1, seed=1, hyp='H1', arch='E', floor=E_FLOOR):
    return {'name': name, 'program_arm': arm, 'hypothesis': hyp, 'arch_name': arch, 'budget': budget,
            'option_c': option_c, 'warmup': warmup, 'seed': seed, 'zero_floor_ebops': floor, 'round': 'R1'}


class Fixture:
    def __init__(self, tmp):
        self.tmp = Path(tmp)
        self.runs = self.tmp / 'root' / 'runs'
        self.ctrl = self.tmp / 'ctrl'
        self.ctrl.mkdir(parents=True)
        self.rows, self.a26, self.cert = [], [], []

    def add(self, r, curve, *, epochs=500, snapshot=True, diverged=False, runner='auto', threshold=THR,
            labels=LABELS, a26_heads=(0.7, 0.8), cert='CERTIFIED', audit=True, extra_rows=0):
        """curve(epoch) -> (ebops, val_acc, val_auc)."""
        self.rows.append(r)
        run = self.runs / r['name']
        run.mkdir(parents=True)
        best = None
        with (run / 'activation_widths.jsonl').open('w') as f:
            for e in range(epochs + extra_rows):
                ebops, acc, auc = curve(e)
                t = traced(e)
                rec = {'epoch': e, 'ebops': ebops if t else None, 'ebops_traced': int(t),
                       'val_categorical_accuracy': acc, 'val_macro_auc': auc,
                       'val_accuracy_threshold': threshold, 'widths': {}, 'per_layer': None}
                f.write(json.dumps(rec) + '\n')
                if e < epochs and t and ebops <= r['budget'] and ebops > r['zero_floor_ebops'] and acc > THR:
                    point = {'epoch': e, 'ebops': ebops, 'val_categorical_accuracy': acc, 'val_macro_auc': auc}
                    if best is None or readout.key(point) > readout.key(best):
                        best = point
        chosen = best if runner == 'auto' else runner
        state = {'completed_epochs': epochs, 'best_feasible': chosen}
        (run / 'nondegenerate_rule.json').write_text(json.dumps({
            'val_accuracy_threshold': threshold, 'labels_sha256': labels, 'zero_floor_ebops': r['zero_floor_ebops']}))
        leaf = f'epoch-{epochs:04d}'
        (run / 'checkpoints' / leaf).mkdir(parents=True)
        (run / 'checkpoints' / leaf / 'state.json').write_text(json.dumps(state))
        (run / 'latest.json').write_text(json.dumps({'checkpoint': leaf}))
        if snapshot:
            (run / 'snapshots' / 'epoch-0500').mkdir(parents=True)
            (run / 'snapshots' / 'epoch-0500' / 'state.json').write_text(json.dumps(state))
        if diverged:
            (run / 'DIVERGED.json').write_text('{}')
            self.a26.append({'name': r['name'], 'status': 'DIVERGED.json present'})
        elif snapshot and a26_heads is not None:
            ck = 'model_best.keras' if chosen else 'model_min_ebops.keras'
            self.a26.append({'name': r['name'], 'status': 'ok',
                             'checkpoint': str(run / 'snapshots' / 'epoch-0500' / ck),
                             'entropy': {'blk0': {'heads': [{'head': i, 'entropy_over_log_n': h}
                                                            for i, h in enumerate(a26_heads)]}}})
        if chosen and cert is not None:
            self.cert.append({'name': r['name'], 'status': 'checked',
                              'checkpoints': [{'which': 'snapshot500_primary', 'status': cert}]})
        elif cert is not None:
            self.cert.append({'name': r['name'], 'status': 'no feasible checkpoint', 'checkpoints': []})
        if r['option_c'] and audit is not None:
            (self.ctrl / f"controller-{r['name']}.json").write_text(json.dumps(
                {'audit_problems': [] if audit else ['epoch 12: held epoch moved controller state']}))

    def run(self, rows_only=None):
        index = self.tmp / 'index.json'
        index.write_text(json.dumps({'runs': rows_only if rows_only is not None else self.rows}))
        a26 = self.tmp / 'a26.json'
        a26.write_text(json.dumps({'epoch': 500, 'runs': self.a26}))
        cert = self.tmp / 'cert.json'
        cert.write_text(json.dumps({'runs': self.cert}))
        out = self.tmp / 'out' / 'readout.json'
        code = readout.main(['--run-root', str(self.runs), '--round', 'R1', '--bundle-sha256', 'ab' * 32,
                             '--a26', str(a26), '--cert', str(cert), '--controller-dir', str(self.ctrl),
                             '--index', str(index), '--out', str(out)])
        self.assertion_out = out
        assert code == 0
        return json.loads(out.read_text()), json.loads(out.with_name('readout_detail.json').read_text())


def healthy(e):
    """Falls to 300k by epoch ~300, accuracy rising to 0.6."""
    return int(max(300000, 2_000_000 - 6000 * e)), 0.2 + 0.4 * min(e, 400) / 400, 0.6 + 0.3 * min(e, 400) / 400


def degenerate(e):
    return int(max(200000, 2_000_000 - 8000 * e)), 0.2029, 0.5


def never_feasible(e):
    return int(max(400000, 2_000_000 - 6000 * e)), 0.5, 0.8


class ReadoutTests(unittest.TestCase):
    def test_healthy_degenerate_infeasible(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('h', 'A350-C'), healthy)
            fx.add(row('d', 'A350-noC', option_c=False), degenerate, a26_heads=(1.0, 1.0))
            fx.add(row('n', 'E250k-C', budget=250000, hyp='H2'), never_feasible, a26_heads=(1.0, 1.0))
            top, detail = fx.run()
        self.assertEqual(list(top), ['round', 'bundle_sha256', 'n_arms', 'complete', 'threshold_c', 'labels_sha256', 'arms'])
        self.assertEqual((top['round'], top['n_arms'], top['complete']), ('R1', 3, True))
        self.assertEqual((top['threshold_c'], top['labels_sha256']), (THR, LABELS))
        h, d, n = top['arms']
        for a in top['arms']:
            self.assertEqual(tuple(a), readout.FIELDS)
            self.assertEqual((a['epochs_done'], a['status']), (500, 'complete'))
        self.assertTrue(h['feasible_any'] and h['nondegenerate_best'])
        self.assertAlmostEqual(h['best_feasible_val_acc'], 0.6, places=12)          # max accuracy at a feasible traced epoch
        self.assertAlmostEqual(h['attn_entropy_norm_mean'], 0.75)
        self.assertEqual(h['min_traced_ebops'], 300000)
        self.assertEqual((h['arm'], h['hypothesis'], h['arch'], h['budget'], h['option_c'], h['warmup'], h['seed']),
                         ('A350-C', 'H1', 'E', 350000, True, 1, 1))
        self.assertTrue(d['feasible_any'])
        self.assertFalse(d['nondegenerate_best'])
        self.assertIsNone(d['best_feasible_val_acc'])
        self.assertIsNone(d['best_feasible_val_auc'])
        self.assertEqual(d['attn_entropy_norm_mean'], 1.0)
        self.assertFalse(n['feasible_any'] or n['nondegenerate_best'])
        self.assertEqual(n['min_traced_ebops'], 400000)
        self.assertEqual(detail['arms'][0]['problems'], [])

    def test_only_traced_epochs_before_the_pause_count(self):
        def curve(e):
            if not traced(e):
                return 200000, 0.9, 0.95       # untraced epochs carry no cost and are never candidates
            return healthy(e)
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('h', 'A350-C'), curve, extra_rows=30)   # records past epoch 500 are ignored
            top, _ = fx.run()
        a = top['arms'][0]
        self.assertEqual(a['status'], 'complete')
        self.assertAlmostEqual(a['best_feasible_val_acc'], 0.6, places=12)
        self.assertEqual(a['min_traced_ebops'], 300000)

    def test_floor_condition_b(self):
        def at_floor(e):
            return E_FLOOR, 0.5, 0.8                         # budget met but not above the 0-bit floor
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('f', 'A350-C'), at_floor, a26_heads=(1.0, 1.0))
            top, _ = fx.run()
        self.assertFalse(top['arms'][0]['feasible_any'])
        self.assertFalse(top['arms'][0]['nondegenerate_best'])

    def test_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('inc', 'A350-C'), healthy, epochs=300, snapshot=False)
            fx.add(row('div', 'A350-C', seed=2), healthy, epochs=125, snapshot=False, diverged=True)
            fx.add(row('cert', 'E500k-C', budget=500000, hyp='H2'), healthy, cert='MISMATCH')
            fx.add(row('aud', 'E750k-C', budget=750000, hyp='H2'), healthy, audit=False)
            fx.add(row('noaud', 'E1000k-C', budget=1000000, hyp='H2'), healthy, audit=None)
            fx.add(row('mis', 'E2000k-C', budget=2000000, hyp='H2'), healthy,
                   runner={'epoch': 9, 'ebops': 1946000, 'val_categorical_accuracy': 0.209, 'val_macro_auc': 0.6})
            fx.add(row('noa26', 'E5000k-C', budget=5000000, hyp='H2'), healthy, a26_heads=None)
            fx.rows.append(row('gone', 'A07-350k-C', arch='A07', floor=343053, hyp='H2'))
            top, detail = fx.run()
        status = {d['name']: a['status'] for a, d in zip(top['arms'], detail['arms'])}
        self.assertEqual(status, {'inc': 'failed', 'div': 'diverged', 'cert': 'cert_fail', 'aud': 'audit_fail',
                                  'noaud': 'audit_fail', 'mis': 'failed', 'noa26': 'failed', 'gone': 'failed'})
        self.assertFalse(top['complete'])
        self.assertEqual(top['n_arms'], 8)
        inc = top['arms'][0]
        self.assertEqual(inc['epochs_done'], 300)
        self.assertTrue(inc['feasible_any'])                   # reported from what exists
        self.assertEqual(top['arms'][1]['epochs_done'], 125)

    def test_no_option_c_needs_no_controller_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('noc', 'A350-noC', option_c=False), healthy, audit=None)
            top, _ = fx.run()
        self.assertEqual(top['arms'][0]['status'], 'complete')

    def test_integrity_threshold_and_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('a', 'A350-C'), healthy)
            fx.add(row('b', 'A350-C', seed=2), healthy, threshold=0.25, labels='0' * 64)
            top, detail = fx.run()
        self.assertEqual([a['status'] for a in top['arms']], ['complete', 'failed'])
        self.assertIsNone(top['threshold_c'])
        self.assertIsNone(top['labels_sha256'])
        self.assertTrue(any('threshold' in p for p in detail['arms'][1]['problems']))

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            fx.add(row('a', 'A350-C'), healthy)
            fx.run()
            with self.assertRaises(SystemExit):
                fx.run()

    def test_real_index_rows_and_program_ids(self):
        index = json.loads((CAMP / 'index.json').read_text())['runs']
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(tmp)
            top, _ = fx.run(rows_only=index)
        self.assertEqual(top['n_arms'], 24)
        self.assertFalse(top['complete'])
        self.assertTrue(all(a['status'] == 'failed' and a['epochs_done'] == 0 for a in top['arms']))
        ids = sorted({a['arm'] for a in top['arms']})
        self.assertEqual(ids, sorted(['A350-noC', 'A350-C', 'A350-C-w50', 'A350-C-w100', 'E250k-C', 'E500k-C',
                                      'E750k-C', 'E1000k-C', 'E2000k-C', 'E5000k-C', 'A07-500k-C',
                                      'A07-1000k-C', 'A07-2000k-C', 'A07-5000k-C', 'NB350-C', 'A350-C-qkv1',
                                      'A350-C-qkv1-450k', 'E-unc-C']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
