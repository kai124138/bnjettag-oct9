"""CPU-only regression checks; AST-load pure helpers to avoid importing TensorFlow/HGQ."""
import ast
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / 'publication/code/hgq2/bnhgq2'
sys.path.insert(0, str(CODE.parent))
from bnhgq2.train import macro_ovr_auc, _softmax

tree = ast.parse((CODE / 'ablation.py').read_text())
names = {'checkpoint_selection_metric', 'checkpoint_selection_key', 'validation_metrics',
         'expected_binary_layers', 'seeded_run_name', 'training_status_summary'}
module = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
ns = {'np': np, 'macro_ovr_auc': macro_ovr_auc, '_softmax': _softmax}
exec(compile(module, str(CODE / 'ablation.py'), 'exec'), ns)
metric = ns['checkpoint_selection_metric']
key = ns['checkpoint_selection_key']
metrics = ns['validation_metrics']


class SelectionTests(unittest.TestCase):
    def test_registered_default_and_historical_resume_points(self):
        self.assertEqual(metric({'experiment': {}}), 'val_macro_auc')
        old = {'epoch': 2, 'ebops': 100, 'val_macro_auc': .9}
        new = {'epoch': 3, 'ebops': 100, 'val_macro_auc': .9, 'val_categorical_accuracy': .7}
        self.assertGreater(key(old, 'val_macro_auc'), key(new, 'val_macro_auc'))

    def test_accuracy_selection_disagrees_with_auc_as_intended(self):
        auc_winner = dict(epoch=2, ebops=100, val_macro_auc=.9, val_categorical_accuracy=.6)
        acc_winner = dict(epoch=3, ebops=100, val_macro_auc=.89, val_categorical_accuracy=.7)
        self.assertGreater(key(auc_winner, 'val_macro_auc'), key(acc_winner, 'val_macro_auc'))
        self.assertGreater(key(acc_winner, 'val_categorical_accuracy'), key(auc_winner, 'val_categorical_accuracy'))

    def test_accuracy_ties_use_auc_then_cost_then_epoch(self):
        base = dict(epoch=2, ebops=100, val_macro_auc=.9, val_categorical_accuracy=.6)
        for improved in [dict(base, val_macro_auc=.91), dict(base, ebops=99), dict(base, epoch=1)]:
            self.assertGreater(key(improved, 'val_categorical_accuracy'), key(base, 'val_categorical_accuracy'))

    def test_invalid_objective_fails(self):
        with self.assertRaises(ValueError):
            metric({'experiment': {'selection_metric': 'test_accuracy'}})
        with self.assertRaises(KeyError):
            key(dict(epoch=1, ebops=1, val_macro_auc=.8), 'val_categorical_accuracy')

    def test_perfect_auc_does_not_imply_perfect_accuracy(self):
        probs = np.full((5, 5), .05)
        probs[:, 0] = .55
        np.fill_diagonal(probs, .3)
        probs[0, 0] = .8
        labels = np.eye(5)
        logits = np.log(probs)
        auc, per, acc = metrics(labels, logits)
        self.assertAlmostEqual(auc, 1.)
        self.assertEqual(per, [1.] * 5)
        self.assertAlmostEqual(acc, .2)
        for temperature in (.1, .5, 2., 10.):
            self.assertAlmostEqual(metrics(labels, logits / temperature)[2], acc)
        (Path(__file__).parent / 'synthetic_metrics.json').write_text(json.dumps({
            'description': 'Synthetic illustration only; not model evaluation',
            'macro_ovr_auc': auc, 'top1_accuracy': acc,
            'probabilities': probs.tolist(), 'temperature_accuracy_unchanged': True,
        }, indent=2) + '\n')

    def test_nonfinite_or_mismatched_validation_logits_rejected(self):
        with self.assertRaises(ValueError):
            metrics(np.eye(5), np.full((5, 5), np.nan))
        with self.assertRaises(ValueError):
            metrics(np.eye(5), np.ones((4, 5)))

    def test_binary_projection_count_tracks_architecture(self):
        expected = ns['expected_binary_layers']
        self.assertEqual(len(expected({'arch': {'n_layers': 1}})), 9)
        self.assertEqual(len(expected({'arch': {'n_layers': 2}})), 15)
        self.assertEqual(len(expected({'arch': {'n_layers': 3}})), 21)
        self.assertIn('bit_block_0_ffn_fc2', expected({'arch': {'n_layers': 1}}))
        self.assertNotIn('bit_block_1_attn_Wq', expected({'arch': {'n_layers': 1}}))

    def test_seed_names_preserve_legacy_without_duplicate_new_suffix(self):
        seeded = ns['seeded_run_name']
        self.assertEqual(seeded('old-arm', 1), 'old-arm-s1')
        self.assertEqual(seeded('batch20260917-a07-s2', 2), 'batch20260917-a07-s2')
        self.assertEqual(seeded('old-arm', 3), 'old-arm-s3')

    def test_screening_summary_explicit_epoch_and_missing_feasible_point(self):
        summary = ns['training_status_summary']
        point = {'epoch': 17, 'ebops': 345000, 'val_macro_auc': .85, 'val_categorical_accuracy': .60}
        result = summary({'completed_epochs': 100, 'best_feasible': point}, 'val_categorical_accuracy', 100, paused=True)
        self.assertEqual(result['phase'], 'paused_for_promotion')
        self.assertEqual(result['completed_epochs'], 100)
        self.assertEqual(result['screening_target_epochs'], 100)
        self.assertEqual(result['best_feasible_epoch'], 18)
        self.assertEqual(result['best_feasible_epoch_zero_based'], 17)
        self.assertEqual(result['best_feasible_val_accuracy'], .60)
        missing = summary({'completed_epochs': 3, 'best_feasible': None}, 'val_categorical_accuracy', 100)
        self.assertEqual(missing['phase'], 'screening')
        self.assertNotIn('best_feasible_val_accuracy', missing)


if __name__ == '__main__':
    unittest.main(verbosity=2)
