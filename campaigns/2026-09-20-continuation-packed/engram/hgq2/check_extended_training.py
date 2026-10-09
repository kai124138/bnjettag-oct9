#!/usr/bin/env python3
"""Cluster synthetic check: long-budget training continues after budget attainment."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
if '--gpu' not in sys.argv:
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
import numpy as np
import tensorflow as tf
from bnhgq2 import train as trainer, wandb_util
from bnhgq2.config import load_config
from bnhgq2.ebops_target import resolve_budget


def main():
    if '--gpu' in sys.argv:
        assert tf.config.list_physical_devices('GPU'), 'GPU required'
    cfg = load_config(Path(__file__).parent / 'configs/post_conference_extended_budget350k-w1a8.json')
    tr = cfg['train']
    assert tr['epochs'] == 1000 and tr['decay_epochs'] == 999 and tr['es_patience'] == 0
    assert tr['jit_compile'] is False
    assert tr['ebops']['selection'] == 'max_auc' and not tr['ebops']['stop_on_target']
    assert resolve_budget(cfg, 1700000)['train']['ebops']['threshold'] == 350000
    rng = np.random.default_rng(10)
    x = rng.normal(size=(400, 8, 3)).astype('float32')
    y = np.eye(5, dtype='float32')[np.arange(400) % 5]
    trainer.load_train_data = lambda *a, **kw: (x.copy(), y.copy(), 1)
    wandb_util.wandb_enabled = lambda *a, **kw: False
    for feasible in (True, False):
        c = copy.deepcopy(cfg)
        c['train']['epochs'] = 2
        c['train']['ebops']['pid']['target_ebops'] = 1e9 if feasible else 1.
        with tempfile.TemporaryDirectory() as out:
            meta = trainer.train(c, seed=1, out_dir=out)
            result = meta['ebops_budget']
            assert meta['epochs_run'] == 2, 'Must keep training after attaining the budget'
            assert result['budget_met'] is feasible
            assert result['checkpoint'] == ('model_best.keras' if feasible else 'model_unconstrained.keras')
            history = [json.loads(s) for s in (Path(out) / 'activation_widths.jsonl').read_text().splitlines()]
            assert len(history) == 2
            if feasible:
                assert result['best_feasible']['val_macro_auc'] == meta['best_val_macro_auc']
            else:
                assert not (Path(out) / 'model_best.keras').exists()
    print('EBOPS_LONG_ALL_PASS', flush=True)


if __name__ == '__main__':
    main()
