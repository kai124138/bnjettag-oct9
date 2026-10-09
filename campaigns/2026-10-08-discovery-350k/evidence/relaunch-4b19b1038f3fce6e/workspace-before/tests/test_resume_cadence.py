"""[A15] checkpoint cadence, [A5] rollback to the resume point, [A6] snapshots, [A19] copy.
Runs ablation.run_training on CPU with a tiny model and synthetic data (seconds)."""
import copy
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
BASE = json.loads((HERE / 'configs' / 'const0922-a07-n64-s1-fast50-fp32.json').read_text())


def tiny_cfg():
    cfg = copy.deepcopy(BASE)
    cfg['name'] = 'unit-resume'
    cfg['arch'].update(n_part=8, d_model=8, n_heads=2, ffn_dim=8)
    cfg['quant'].update(act_overflow='WRAP', softmax_quant='chang')
    cfg['train'].update(epochs=5, batch=32, lr=3e-3, optimizer='adam_default',
                        lr_schedule='chang_cosine_restarts', lr_cycle_epochs=4, lr_alpha=1e-6,
                        lr_alpha_epochs=1, val_batch=64)
    cfg['train']['ebops']['pid']['target_ebops'] = 10 ** 9
    cfg['experiment'].update(checkpoint_every_epochs=2, snapshot_every_epochs=2,
                             cost_before_auc=False, keep_auc_selected_feasible=True)
    return cfg


def data(seed=0):
    rng = np.random.default_rng(seed)
    xt = rng.standard_normal((128, 8, 3)).astype('float32')
    xv = rng.standard_normal((64, 8, 3)).astype('float32')
    yt = np.eye(5, dtype='float32')[rng.integers(0, 5, 128)]
    yv = np.eye(5, dtype='float32')[np.arange(64) % 5]
    return (xt, yt, xv, yv), {'unit': True, 'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Crash(RuntimeError):
    pass


def test_cadence_rollback_resume(tmp_path):
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    arrays, info = data()

    def crash_at_3(model, sample, epoch):
        if epoch == 2:                       # third epoch, after selection, before its record
            raise Crash()
        return {}
    with pytest.raises(Crash):
        ablation.run_training(cfg, arrays, info, tmp_path, epoch_observer=crash_at_3)
    assert json.loads((tmp_path / 'latest.json').read_text())['checkpoint'] == 'epoch-0002'
    assert sorted(p.name for p in (tmp_path / 'checkpoints').glob('epoch-*')) == ['epoch-0002']
    assert (tmp_path / 'snapshots' / 'epoch-0002' / 'state.json').exists()
    ckpt = tmp_path / 'checkpoints' / 'epoch-0002'
    # ghost trajectory: selected files and a later snapshot from abandoned epochs
    (tmp_path / 'model_best.keras').write_bytes(b'ghost')
    (tmp_path / 'snapshots' / 'epoch-0004').mkdir()
    model, optimizer, state = ablation.restore_checkpoint(tmp_path, cfg, info)
    assert state['completed_epochs'] == 2
    assert sha(tmp_path / 'model_best.keras') == sha(ckpt / 'model_best.keras')
    assert sha(tmp_path / 'model_best_auc_feasible.keras') == sha(ckpt / 'model_best_auc_feasible.keras')
    assert not (tmp_path / 'snapshots' / 'epoch-0004').exists()
    assert len((tmp_path / 'activation_widths.jsonl').read_text().splitlines()) == 2
    del model, optimizer
    final = ablation.run_training(cfg, arrays, info, tmp_path)
    assert final['completed_epochs'] == 5
    assert sorted(p.name for p in (tmp_path / 'checkpoints').glob('epoch-*')) == ['epoch-0004', 'epoch-0005']
    assert sorted(p.name for p in (tmp_path / 'snapshots').glob('epoch-*')) == ['epoch-0002', 'epoch-0004']
    budget = json.loads((tmp_path / 'ebops_budget.json').read_text())
    assert budget['checkpoint'] == 'model_best.keras' and budget['auc_selected_checkpoint'] == 'model_best_auc_feasible.keras'
    lines = [json.loads(l) for l in (tmp_path / 'activation_widths.jsonl').read_text().splitlines()]
    assert [l['epoch'] for l in lines] == [0, 1, 2, 3, 4]
    assert lines[0]['learning_rate'] == pytest.approx(3e-3) and lines[3]['learning_rate'] == pytest.approx(1e-6)
    assert 'bit_block_0_attn_softmax__exp_oq' in lines[-1]['widths']


def test_divergence_is_recorded(tmp_path):
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    (xt, yt, xv, yv), info = data(1)
    calls = {'n': 0}

    def poison(model, sample, epoch):       # after epoch 0 completes, corrupt a kernel
        if epoch == 0:
            k = next(v for v in model.trainable_variables if v.name == 'kernel')
            k.assign(np.full(k.shape, np.nan, 'float32'))
        return {}
    with pytest.raises(ablation.Diverged):
        ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path, epoch_observer=poison)
    record = json.loads((tmp_path / 'DIVERGED.json').read_text())
    assert record['divergence_epoch_zero_based'] == 1 and record['completed_epochs_before'] == 1
    assert record['best_feasible_before']['epoch'] == 0
