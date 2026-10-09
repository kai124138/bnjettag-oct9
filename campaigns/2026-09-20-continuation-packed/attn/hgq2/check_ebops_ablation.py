#!/usr/bin/env python3
'Check matched initialization, quantization variants, budget schedules, and optional training resumption.'
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import gc
os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
if '--gpu' not in sys.argv:
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
import keras
import numpy as np
import tensorflow as tf
from bnhgq2.compat import apply_keras_compat
apply_keras_compat()
from bnhgq2 import qat
from bnhgq2.ablation import matching_initialization, run_training, raw_widths, training_target, binary_gate
from bnhgq2.ebops_calc import compute_ebops
from bnhgq2.ebops_target import activation_quantizers, width_snapshot
sys.path.insert(0, str(Path(__file__).parent / 'configs'))
from gen_ebops_ablation import ARMS, make_ablation


def main():
    if '--gpu' in sys.argv:
        assert tf.config.list_physical_devices('GPU')
    rng = np.random.default_rng(4)
    x = rng.normal(size=(40, 8, 3)).astype('float32')
    y = np.eye(5, dtype='float32')[np.arange(len(x)) % 5]
    arrays = (x, y, x[:20], y[:20])
    info = {'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}, 'synthetic': True}
    costs, hashes, penalties = {}, {}, {}
    for arm in ARMS:
        cfg = make_ablation(arm)
        model, init = matching_initialization(cfg, x, 1)
        binary_gate(model)
        cost = compute_ebops(model, x)['total']
        costs[arm], hashes[arm] = cost, init['kernel_hashes']
        model(x[:8], training=True)
        penalties[arm] = float(tf.add_n(model.losses))
        if arm == 'channel_quantization':
            assert any(np.asarray(w['bits']).size > 1 for w in width_snapshot(model).values())
            variables = [v for _, q in activation_quantizers(model) if q.trainable and hasattr(q, '_f') for v in (q._i, q._f)]
            with tf.GradientTape() as tape:
                model(x[:8], training=True)
                penalty = tf.add_n(model.losses)
            gradients = tape.gradient(penalty, variables)
            assert all(g is not None and np.isfinite(g.numpy()).all() for g in gradients)
        if arm == 'attention_probability_8bit':
            assert width_snapshot(model)['bit_block_0_attn_ctx__in0']['bits'] == 8
        print(f'[build] {arm} params={model.count_params()} initial_ebops={cost}', flush=True)
        del model
        keras.backend.clear_session()
        gc.collect()
    np.testing.assert_allclose(penalties['tensor_quantization'], penalties['channel_quantization'], atol=1e-8, rtol=1e-7)
    assert costs['tensor_quantization'] == costs['channel_quantization'] == 1739182
    assert costs['reduced_feedforward'] < costs['tensor_quantization'] and costs['attention_probability_8bit'] < costs['tensor_quantization']
    for arm in ARMS:
        for name in hashes[arm].keys() & hashes['tensor_quantization'].keys():
            if arm == 'reduced_feedforward' and ('ffn_fc1/kernel' in name or 'ffn_fc2/kernel' in name or 'ffn_fc1/bias' in name):
                continue
            assert hashes[arm][name] == hashes['tensor_quantization'][name], (arm, name)
    assert [training_target(make_ablation('gradual_budget'), i) for i in (0, 249, 250, 499, 500, 749, 750, 999)] == [1e6,1e6,750000,750000,500000,500000,350000,350000]
    if '--integration' in sys.argv:
        # All variants go through the same real epoch function, checkpoint and reload path.
        for arm in ARMS:
            cfg = make_ablation(arm)
            cfg['train'].update(epochs=2, batch=16, val_batch=20)
            cfg['train']['ebops']['pid']['warmup'] = 0
            # Synthetic budget tests do not claim real-data budget attainment.
            cfg['train']['ebops']['pid']['target_ebops'] = 2e6 if arm in ('tensor_quantization','fixed_width_recovery') else 1.
            if arm == 'fixed_width_recovery':
                cfg['experiment']['recovery_after_epochs'] = 1
            if arm == 'gradual_budget':
                cfg['experiment']['target_schedule'] = [[0, 2e6], [1, 1.5e6]]
            teacher = rng.normal(size=y.shape).astype('float32') if arm == 'knowledge_distillation' else None
            with tempfile.TemporaryDirectory() as out:
                first = run_training(cfg, arrays, info, out, teacher_logits=teacher, stop_after=1)
                assert first['completed_epochs'] == 1
                # Deliberately add an uncommitted epoch; resume must trim it.
                with (Path(out)/'activation_widths.jsonl').open('a') as f:
                    f.write(json.dumps({'epoch': 99})+'\n')
                final = run_training(cfg, arrays, info, out, teacher_logits=teacher)
                assert final['completed_epochs'] == 2
                rows = [json.loads(s) for s in (Path(out)/'activation_widths.jsonl').read_text().splitlines()]
                assert len(rows) == 2
                if arm == 'fixed_width_recovery':
                    assert final['freeze_epoch'] == 1
                    assert rows[0]['widths'] == rows[1]['widths'], 'Recovery quantizer drift'
                if arm == 'gradual_budget':
                    assert final['best_feasible'] is None, 'Intermediate target admitted over-final-budget checkpoint'
                if arm == 'knowledge_distillation':
                    assert rows[-1]['distillation_loss'] > 0
                if arm == 'tensor_quantization':
                    with tempfile.TemporaryDirectory() as uninterrupted:
                        normal = run_training(cfg, arrays, info, uninterrupted)
                        assert normal['pid'] == final['pid']
                        a = keras.models.load_model(Path(out)/'checkpoints/epoch-0002/model.keras',compile=False)
                        b = keras.models.load_model(Path(uninterrupted)/'checkpoints/epoch-0002/model.keras',compile=False)
                        for av,bv in zip(a.weights,b.weights):
                            np.testing.assert_allclose(av.numpy(),bv.numpy(),atol=1e-7,rtol=1e-6)
                        with np.load(Path(out)/'checkpoints/epoch-0002/optimizer.npz') as ao, np.load(Path(uninterrupted)/'checkpoints/epoch-0002/optimizer.npz') as bo:
                            for k in ao.files: np.testing.assert_allclose(ao[k],bo[k],atol=1e-7,rtol=1e-6)
            keras.backend.clear_session()
            gc.collect()
            print(f'[integration] {arm} PASS', flush=True)
    print('EBOPS_ABLATION_ALL_PASS', flush=True)


if __name__ == '__main__':
    main()
