"""Small real TensorFlow/HGQ training, checkpoint/resume, and selection regression."""
import copy
import gc
import hashlib
import json
from pathlib import Path
import tempfile

import keras
import numpy as np
import tensorflow as tf
from bnhgq2.ablation import run_training, validation_metrics
from bnhgq2.compat import apply_keras_compat

apply_keras_compat()
tf.config.set_visible_devices([], 'GPU')
tf.config.threading.set_intra_op_parallelism_threads(2)
tf.config.threading.set_inter_op_parallelism_threads(1)
rng = np.random.default_rng(4)
x = rng.normal(size=(60, 8, 3)).astype('float32')
y = np.eye(5, dtype='float32')[np.arange(60) % 5]
arrays = (x[:40], y[:40], x[40:], y[40:])
info = {'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}, 'synthetic': True}
base = json.loads(Path('/eval/config.json').read_text())
reports = []
for name, objective, budget in [
    ('accuracy_feasible', 'val_categorical_accuracy', 2_000_000),
    ('default_auc_feasible', None, 2_000_000),
    ('accuracy_infeasible', 'val_categorical_accuracy', 1),
]:
    cfg = copy.deepcopy(base)
    cfg['name'] = name
    cfg['train'].update(epochs=2, batch=16, val_batch=20)
    cfg['train']['ebops']['pid'].update(warmup=0, target_ebops=budget)
    if objective:
        cfg['experiment']['selection_metric'] = objective
    else:
        cfg['experiment'].pop('selection_metric', None)
    print(f'SMOKE_START {name}', flush=True)
    with tempfile.TemporaryDirectory(dir='/work') as root:
        out = Path(root)
        first = run_training(cfg, arrays, info, out, stop_after=1)
        assert first['completed_epochs'] == 1
        with (out / 'activation_widths.jsonl').open('a') as handle:
            handle.write(json.dumps({'epoch': 999, 'uncommitted': True}) + '\n')
        # Config digest must reject silently changing the objective during resume.
        changed = copy.deepcopy(cfg)
        changed['experiment']['selection_metric'] = 'val_macro_auc' if objective else 'val_categorical_accuracy'
        try:
            run_training(changed, arrays, info, out)
        except AssertionError as error:
            assert 'Resume config mismatch' in str(error), str(error)
        else:
            raise AssertionError('Changing selection objective bypassed resume guard')
        final = run_training(cfg, arrays, info, out)
        assert final['completed_epochs'] == 2
        rows = [json.loads(line) for line in (out / 'activation_widths.jsonl').read_text().splitlines()]
        assert [row['epoch'] for row in rows] == [0, 1], rows
        for row in rows:
            assert row['train_categorical_accuracy'] == row['categorical_accuracy']
            assert 0 <= row['val_categorical_accuracy'] <= 1
            assert np.isfinite(row['val_macro_auc'])
        result = json.loads((out / 'ebops_budget.json').read_text())
        meta = json.loads((out / 'train_meta.json').read_text())
        feasible = [row for row in rows if row['ebops'] <= budget]
        if feasible:
            def expected_key(row):
                secondary = (row['val_macro_auc'], -row['ebops'], -row['epoch'])
                return (row['val_categorical_accuracy'],) + secondary if objective else secondary
            expected = max(feasible, key=expected_key)
            assert result['selection'] == ('max_accuracy_under_final_budget' if objective else 'max_auc_under_final_budget')
            assert result['checkpoint'] == 'model_best.keras'
            assert result['budget_met']
        else:
            assert budget == 1
            expected = min(rows, key=lambda row: row['ebops'])
            assert result['selection'] == 'minimum_ebops_no_feasible_checkpoint'
            assert result['checkpoint'] == 'model_min_ebops.keras'
            assert not result['budget_met']
        assert result['selected']['epoch'] == expected['epoch']
        assert result['selection_metric'] == (objective or 'val_macro_auc')
        model = keras.models.load_model(out / result['checkpoint'], compile=False)
        auc, _, accuracy = validation_metrics(arrays[3], np.asarray(model(arrays[2], training=False)))
        np.testing.assert_allclose(auc, result['selected']['val_macro_auc'], atol=1e-12)
        np.testing.assert_allclose(accuracy, result['selected']['val_categorical_accuracy'], atol=1e-12)
        assert meta['selected_val_categorical_accuracy'] == accuracy
        reports.append({'case': name, 'passed': True, 'selection': result['selection'],
                        'selected': result['selected'], 'epoch_metrics': [
                            {key: row[key] for key in ('epoch', 'train_categorical_accuracy', 'val_categorical_accuracy', 'val_macro_auc', 'ebops')}
                            for row in rows]})
        del model
    keras.backend.clear_session()
    gc.collect()
    print(f'SMOKE_PASS {name}', flush=True)
print('ACCURACY_SELECTION_INTEGRATION_ALL_PASS', flush=True)
print('RESULT_JSON=' + json.dumps({'synthetic_regression_only': True, 'versions': {
    'keras': keras.__version__, 'tensorflow': tf.__version__, 'numpy': np.__version__},
    'ablation_sha256': hashlib.sha256(Path('/work/code/bnhgq2/ablation.py').read_bytes()).hexdigest(),
    'cases': reports}), flush=True)
