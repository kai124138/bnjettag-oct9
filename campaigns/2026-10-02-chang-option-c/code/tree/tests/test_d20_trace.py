"""[D20] trace sample: key semantics, the PID reads the traced EBOPs, logged EBOPs of a
saved candidate reproduce on a reset retrace of the same rows. CPU, tiny model, synthetic."""
import json
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_resume_cadence import tiny_cfg


def arrays(n_train=600, seed=0):
    rng = np.random.default_rng(seed)
    # heavy-tailed first feature so a 256-row prefix under-covers the range
    xt = rng.standard_normal((n_train, 8, 3)).astype('float32')
    xt[..., 0] = rng.standard_t(2, size=(n_train, 8)).astype('float32')
    xv = rng.standard_normal((64, 8, 3)).astype('float32')
    yt = np.eye(5, dtype='float32')[rng.integers(0, 5, n_train)]
    yv = np.eye(5, dtype='float32')[np.arange(64) % 5]
    return (xt, yt, xv, yv), {'unit': True, 'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}}


def test_trace_sample_key():
    from bnhgq2.ablation import ebops_trace_sample, ebops_trace_batch
    xt = np.zeros((1000, 2, 3), 'float32')
    cfg = tiny_cfg()
    assert 'ebops_trace_sample' not in cfg['train']
    assert len(ebops_trace_sample(cfg, xt)) == 256 and ebops_trace_batch(cfg) == 2048
    cfg['train']['ebops_trace_sample'] = 'train_full'
    assert ebops_trace_sample(cfg, xt) is xt
    cfg['train']['ebops_trace_sample'] = 700
    assert len(ebops_trace_sample(cfg, xt)) == 700
    for bad in (0, -1, True, 'all', 1.5):
        cfg['train']['ebops_trace_sample'] = bad
        with pytest.raises(ValueError):
            ebops_trace_sample(cfg, xt)


def records(out):
    return [json.loads(line) for line in (out / 'activation_widths.jsonl').read_text().splitlines()]


def test_full_split_trace_drives_pid_and_reproduces(tmp_path):
    import keras
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    cfg['train'].update(epochs=2, ebops_trace_sample='train_full')
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    recs = records(tmp_path)
    for r in recs:
        assert r['ebops_trace_rows'] == len(xt)
        assert r['pid_ebops'] == pytest.approx(r['ebops'], rel=1e-6)
        assert r['ebops_in_training'] > 0 and r['ebops_in_training_over_traced'] > 0
        assert r['ebops_trace_seconds'] > 0 and r['ebops_reload_check_seconds'] >= 0
        assert 0 < r['ebops_trace_over_epoch'] < 1
    # the last epoch's candidate is model_min_ebops or model_best; retrace it (reset) on the
    # same rows: EBOPs equal to the logged value (the certification rule)
    state = json.loads((tmp_path / 'ebops_budget.json').read_text())
    best = keras.models.load_model(tmp_path / 'model_best.keras', compile=False)
    again = ablation.compute_ebops(best, xt)['total']
    assert again == state['selected']['ebops']


def test_absent_key_logs_nothing_new(tmp_path):
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    cfg['train'].update(epochs=1)
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    r = records(tmp_path)[0]
    assert not {'ebops_in_training', 'pid_ebops', 'ebops_trace_rows', 'ebops_trace_seconds',
                'ebops_reload_check_seconds', 'ebops_trace_over_epoch'} & set(r)


def test_prefix_trace_undercovers_full_split():
    """Why [D20] exists: after a reset trace on 256 rows, the WRAP i of the input quantizer
    can sit below what the full split needs (heavy-tailed synthetic pT)."""
    import keras
    from bnhgq2 import ablation
    from bnhgq2.ebops_target import width_snapshot
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    cfg = tiny_cfg()
    (xt, _, _, _), _ = arrays(n_train=4000)
    keras.backend.clear_session()
    model, _ = ablation.matching_initialization(cfg, xt[:512], 1)
    small = ablation.compute_ebops(model, xt[:256])['total']
    i_small = np.asarray(width_snapshot(model)['input_proj']['i'])
    full = ablation.compute_ebops(model, xt)['total']
    i_full = np.asarray(width_snapshot(model)['input_proj']['i'])
    assert (i_full >= i_small).all() and (i_full > i_small).any() and full > small
