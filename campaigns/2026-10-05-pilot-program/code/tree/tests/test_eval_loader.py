"""[A11]/[A3] the held-out loader gates exactly as the training cache path does, labels and
row order unchanged; sort statistics counted. Synthetic h5 files in the dataset layout."""
import numpy as np


def write_h5(path, seed):
    import h5py
    from bnhgq2.qat import PART_FEATURE_NAMES_CANONICAL
    rng = np.random.default_rng(seed)
    const = np.zeros((40, 100, 16), 'float32')
    for j in range(40):
        k = rng.integers(10, 100)
        const[j, :k, 5] = rng.exponential(6.0, k)          # raw pt, unsorted
        const[j, :k, 6] = const[j, :k, 5] / 500.0          # ptrel
        const[j, :k, 8] = rng.normal(0, .3, k)             # etarel
        const[j, :k, 11] = rng.normal(0, .3, k)            # phirel
    jets = np.zeros((40, 5), 'float32'); jets[np.arange(40), rng.integers(0, 5, 40)] = 1
    with h5py.File(path, 'w') as f:
        f['jetConstituentList'] = const
        f['jets'] = jets
        f['jetFeatureNames'] = np.array([b'j_g', b'j_q', b'j_w', b'j_z', b'j_t'])
        f['particleFeatureNames'] = np.array([n.encode() for n in PART_FEATURE_NAMES_CANONICAL])


def test_eval_gate_equals_train_gate(tmp_path):
    from bnhgq2.data import load_eval_set, apply_pt_gate
    from bnhgq2.train import load_train_data
    for i in range(2):
        write_h5(tmp_path / f'f{i}.h5', i)
    feats = ['pt', 'etarel', 'phirel']
    stats = {}
    xt, yt, _ = load_train_data(str(tmp_path), 64, features=feats, sort_stats=stats)
    x0, y0 = load_eval_set(str(tmp_path), 64, features=feats)
    xg, yg = load_eval_set(str(tmp_path), 64, features=feats, pt_gate_gev=2.0)
    np.testing.assert_array_equal(x0, xt)
    np.testing.assert_array_equal(yg, y0)
    np.testing.assert_array_equal(xg, apply_pt_gate(xt, feats, 2.0))
    assert np.all(np.diff(x0[..., 0], axis=1) <= 0)          # sorted by descending raw pt
    assert x0[..., 0].max() > 2 and (xg[..., 0][xg[..., 0] > 0] >= 2).all()
    assert stats['n_jets'] == 80 and 0 < stats['n_jets_top_n_reordered'] <= 80
