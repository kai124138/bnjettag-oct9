#!/usr/bin/env python3
"""Bounded synthetic preflight for the fifteen 20260918 configurations (5 arms x 3 seeds).

Reuses the 20260917 per-config checks (build, one gradient step, save/reload, resume
guards) and adds one check per arm that its single change actually reached the model.
Mechanics only: no physics accuracy, no real-data budget attainment.
"""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import time

from check_training_batch_preflight import build_gradient_reload, resume_check  # sets CPU/W&B env first
import keras
import numpy as np
import tensorflow as tf
from bnhgq2.ablation import matching_initialization, training_target
from bnhgq2.compat import apply_keras_compat


def arm_check(cfg, reference):
    """Confirm the one knob each arm changes is what the built model actually differs in."""
    arm = cfg['name'].split('-')[1]
    x = np.random.default_rng(1729).normal(size=(64, cfg['arch']['n_part'], cfg['arch']['n_feat'])).astype('float32')
    model, _ = matching_initialization(cfg, x, cfg['experiment']['seed'])
    layers = {layer.name for layer in model.layers}
    params = int(model.count_params())
    record = {'name': cfg['name'], 'arm': arm, 'parameters': params}
    if arm == 'b02':
        assert 'pos_enc' not in layers and not any(v.name == 'pos_table' for v in model.weights)
        assert params == reference['parameters'] - cfg['arch']['n_part'] * cfg['arch']['d_model']
        record['positional_table_absent'] = True
    else:
        assert 'pos_enc' in layers
    if arm == 'b01':
        assert cfg['arch']['n_heads'] == 1
        record['head_dim'] = cfg['arch']['d_model'] // cfg['arch']['n_heads']
    if arm == 'b03':
        assert cfg['quant']['softmax_out_bits'] == 8
    if arm == 'b04':
        expected = {0: 525000, 99: 525000, 100: 420000, 199: 420000, 200: 350000, 399: 350000, 999: 350000}
        assert {e: training_target(cfg, e) for e in expected} == expected
        assert cfg['train']['ebops']['pid']['target_ebops'] == 350000, 'selection must use the final budget'
        record['target_schedule_checked'] = expected
    else:
        assert 'target_schedule' not in cfg['experiment']
        assert training_target(cfg, 0) == 350000
    del model
    keras.backend.clear_session()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--configs', type=Path, default=Path(__file__).parent / 'configs/batch20260918')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    apply_keras_compat()
    tf.config.set_visible_devices([], 'GPU')
    index = json.loads((args.configs / 'index.json').read_text())['runs']
    assert len(index) == 15 and [run['index'] for run in index] == list(range(15))
    configs = [json.loads((args.configs / (run['name'] + '.json')).read_text()) for run in index]
    assert len({cfg['name'] for cfg in configs}) == 15
    assert all(cfg['experiment']['selection_metric'] == 'val_categorical_accuracy' for cfg in configs)
    assert all(cfg['train']['split_seed'] == 1 and cfg['train']['order_seed'] == 20260912 for cfg in configs)
    assert sorted({cfg['experiment']['seed'] for cfg in configs}) == [4, 5, 6]
    start = time.monotonic()
    report = {'synthetic_regression_only': True, 'versions': {'tensorflow': tf.__version__, 'keras': keras.__version__},
              'build_gradient_reload': [], 'arm_checks': [], 'resume': []}
    with tempfile.TemporaryDirectory(prefix='batch0918-preflight-') as temporary:
        directory = Path(temporary)
        records = {}
        for cfg in configs:
            record, _, _ = build_gradient_reload(cfg, directory)
            records[cfg['name']] = record
            report['build_gradient_reload'].append(record)
            print('CONFIG_PASS ' + json.dumps(record), flush=True)
        for cfg in configs:
            reference = records[cfg['name'].rsplit('-', 2)[0] + '-b00-' + cfg['name'].rsplit('-', 1)[1]]
            report['arm_checks'].append(arm_check(cfg, reference))
        print('ARM_CHECKS_PASS', flush=True)
        by_arm = {cfg['name'].split('-')[1]: cfg for cfg in configs if cfg['experiment']['seed'] == 4}
        report['resume'].append(resume_check(by_arm['b02'], directory, seed=4, compare_uninterrupted=True))
        print('RESUME_NO_POS_PASS', flush=True)
        report['resume'].append(resume_check(by_arm['b04'], directory, seed=4, compare_uninterrupted=False))
        print('RESUME_GRADUAL_PASS', flush=True)
    report['seconds'] = time.monotonic() - start
    report['passed'] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('PREFLIGHT_ALL_PASS', flush=True)


if __name__ == '__main__':
    main()
