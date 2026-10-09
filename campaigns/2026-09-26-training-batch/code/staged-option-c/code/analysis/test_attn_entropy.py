"""[A26] CPU unit tests for attn_entropy.py on tiny synthetic checkpoints built with the staged
code (code/tree). Synthetic inputs only; nothing here is a result.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<campaign>/code/tree CUDA_VISIBLE_DEVICES=-1 \
      uv run --no-project --with pytest --with <pins> python -m pytest -p no:cacheprovider \
      <campaign>/code/analysis/test_attn_entropy.py

Three builds: A (chang softmax, WRAP), C' (fixed softmax, SAT) and an fp32 skeleton
(quant.weight "none"). Each is traced on a synthetic sample (as training traces), saved to
.keras and reloaded through attn_entropy.load_checkpoint, then:
  - uniform logits give H / log 64 = 1 within 1e-6 (pure function, the reloaded softmax layer,
    and the full sub-model path on jets whose 64 constituents are identical);
  - one-hot logits (gap 200) give H / log 64 < 1e-6 (pure function and the reloaded layer);
  - main() end to end on an epoch-500 snapshot layout (the readout Job's call), with
    run_engram.load_cache replaced by a small synthetic split (the real cache is 620,000 jets).
"""
import copy
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
# staged layout: code/analysis beside code/tree; shipped bundle: /work/code/analysis under /work/code
TREE = HERE.parent / 'tree' if (HERE.parent / 'tree' / 'run_study.py').is_file() else HERE.parent
sys.path[:0] = [str(HERE), str(TREE)]
os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')

import attn_entropy as ae  # noqa: E402

CONFIGS = TREE / 'campaigns' / 'chang0926' / 'configs'
TOL_UNIFORM = 1e-6
TOL_ONEHOT = 1e-6


def _cfg(kind):
    if kind == 'a':
        return json.loads((CONFIGS / 'chang0926-a-n64-s1.json').read_text())
    cfg = json.loads((CONFIGS / 'chang0926-cprime-n64-s1.json').read_text())
    cfg['arch']['pos_enc'] = 'none'     # identical constituents -> identical keys (test input only)
    if kind == 'fp32':
        cfg = copy.deepcopy(cfg)
        cfg['quant']['weight'] = 'none'
    return cfg


@pytest.fixture(scope='module', params=['a', 'cprime', 'fp32'])
def checkpoint(request, tmp_path_factory):
    import run_engram
    run_engram.runtime()
    import keras
    from bnhgq2 import qat
    from bnhgq2.ebops_calc import compute_ebops
    keras.backend.clear_session()
    cfg = _cfg(request.param)
    model, _ = qat.build_qat_model(cfg, seed=1)
    sample = np.random.default_rng(0).standard_normal((64, 64, 3)).astype('float32')
    if request.param != 'fp32':
        compute_ebops(model, sample, batch_size=64)       # trace, as the trainer does before a save
    path = tmp_path_factory.mktemp(request.param) / 'model.keras'
    model.save(path)
    loaded = ae.load_checkpoint(path)
    np.testing.assert_allclose(np.asarray(loaded(sample[:4], training=False)),
                               np.asarray(model(sample[:4], training=False)), atol=2e-6, rtol=2e-6)
    return request.param, cfg, loaded


def _softmax(z):
    z = z - z.max(-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(-1, keepdims=True)


def test_uniform_logits_give_one(checkpoint):
    kind, cfg, model = checkpoint
    heads = cfg['arch']['n_heads']
    h, _, _, neg = ae.row_entropies(_softmax(np.zeros((3, heads, 64, 64))))
    assert neg == 0 and np.all(np.abs(h - 1.0) < TOL_UNIFORM)

    names = ae.softmax_layer_names(model)
    assert names == ['bit_block_0_attn_softmax']
    q = np.asarray(model.get_layer(names[0])(np.zeros((1, heads, 64, 64), 'float32')))
    h, h_raw, row_sum, neg = ae.row_entropies(q)
    assert neg == 0 and np.all(np.abs(h - 1.0) < TOL_UNIFORM), (kind, h.min(), h.max())
    print(f'A26_TEST uniform layer {kind} H_over_logN min {h.min():.9f} max {h.max():.9f} '
          f'row_sum {row_sum.min():.6f}..{row_sum.max():.6f} unrenormalized {h_raw.mean():.6f}')

    x = np.repeat(np.random.default_rng(1).standard_normal((32, 1, 3)), 64, axis=1).astype('float32')
    report = ae.analyze(model, x, batch=16)
    heads_out = report['bit_block_0']['heads']
    assert len(heads_out) == heads and report['bit_block_0']['n_jets'] == 32
    for entry in heads_out:
        assert abs(entry['entropy_over_log_n'] - 1.0) < TOL_UNIFORM, (kind, entry)
        assert entry['query_rows'] == 32 * 64
    print(f'A26_TEST uniform submodel {kind}',
          [round(e['entropy_over_log_n'], 9) for e in heads_out])

    zb = ae.zero_bit_fractions(model, heads)['bit_block_0']
    if kind == 'fp32':
        assert zb['status'].startswith('undefined')
    else:
        e = cfg['arch']['d_model'] // heads
        for role in ('Q', 'K', 'V'):
            assert zb[role]['channels'] == heads * e and zb[role]['granularity'] == 'channel'
        assert zb['Q']['overflow_mode'] == ('WRAP' if kind == 'a' else 'SAT')
        assert 0.0 <= zb['QK_zero_bit_fraction'] <= 1.0 and 0.0 <= zb['V_zero_bit_fraction'] <= 1.0
        assert len(zb['QK_live_pairs_per_head']) == heads


def test_one_hot_logits_give_zero(checkpoint):
    kind, cfg, model = checkpoint
    heads = cfg['arch']['n_heads']
    p = np.zeros((2, heads, 64, 64))
    p[..., 7] = 1.0
    h, _, _, _ = ae.row_entropies(p)
    assert np.all(h < TOL_ONEHOT)

    logits = np.zeros((1, heads, 64, 64), 'float32')
    logits[..., 7] = 200.0
    q = np.asarray(model.get_layer('bit_block_0_attn_softmax')(logits))
    h, _, row_sum, neg = ae.row_entropies(q)
    assert neg == 0 and np.all(h < TOL_ONEHOT), (kind, h.max())
    print(f'A26_TEST one-hot layer {kind} H_over_logN max {h.max():.3e} '
          f'row_sum {row_sum.min():.6f}..{row_sum.max():.6f}')


def test_main_on_snapshot_layout(checkpoint, tmp_path, monkeypatch, capsys):
    """The readout Job's call: --indices I --epoch 500 reads runs/<name>/snapshots/epoch-0500,
    picks model_best.keras when best_feasible is set (else model_min_ebops.keras), feeds only
    x_val, writes the JSON once and refuses to overwrite it."""
    import shutil
    import run_engram
    kind, cfg, model = checkpoint
    rows = json.loads((CONFIGS.parent / 'index.json').read_text())['runs']
    index = next(i for i, r in enumerate(rows) if r['file'] == ('chang0926-a-n64-s1.json' if kind == 'a'
                                                                  else 'chang0926-cprime-n64-s1.json'))
    if kind != 'a':
        pytest.skip('main() is exercised on the A build (C-prime test cfg differs from its file: pos_enc)')
    campaign = tmp_path / 'campaign'
    (campaign / 'configs').mkdir(parents=True)
    shutil.copy(CONFIGS.parent / 'index.json', campaign / 'index.json')
    shutil.copy(CONFIGS / rows[index]['file'], campaign / 'configs' / rows[index]['file'])
    snap = tmp_path / 'runs' / 'runs' / rows[index]['name'] / 'snapshots' / 'epoch-0500'
    snap.mkdir(parents=True)
    model.save(snap / 'model_min_ebops.keras')
    (snap / 'state.json').write_text(json.dumps({'best_feasible': None, 'completed_epochs': 500}))
    x_val = np.random.default_rng(2).standard_normal((40, 64, 3)).astype('float32')
    touched = []

    def fake_cache(path, cfg_arg):
        touched.append(str(path))
        info = {'engram_array_sha256': {'x_val': 'synthetic-x', 'y_val': 'synthetic-y'}}
        return (None, None, x_val, None), info
    monkeypatch.setattr(run_engram, 'load_cache', fake_cache)
    monkeypatch.setenv('BNJ_CAMPAIGN_DIR', str(campaign))
    monkeypatch.setenv('BNJ_DATA_ROOT', str(tmp_path / 'data'))
    monkeypatch.setenv('BNJ_RUN_ROOT', str(tmp_path / 'runs'))
    out = tmp_path / 'a26.json'
    assert ae.main(['--indices', str(index), '--epoch', '500', '--n-val', '32', '--batch', '16',
                    '--out', str(out)]) == 0
    text = capsys.readouterr().out
    assert 'A26_DONE' in text and 'A26_ENTROPY' in text and 'A26_ZEROBIT' in text
    record = json.loads(out.read_text())
    assert record['split'] == 'validation' and record['test_set_used'] is False
    run = record['runs'][0]
    assert run['status'] == 'ok' and run['n_val_rows'] == 32
    assert run['checkpoint'].endswith('model_min_ebops.keras')
    assert touched == [str(tmp_path / 'data' / 'n64' / 'data')]
    for head in run['entropy']['bit_block_0']['heads']:
        assert 0.0 <= head['entropy_over_log_n'] <= 1.0 + 1e-9
    with pytest.raises(SystemExit):
        ae.main(['--indices', str(index), '--epoch', '500', '--out', str(out)])
