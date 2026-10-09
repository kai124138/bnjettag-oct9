"""[A3] pT gate equals jsc150 `X *= X[..., :1] >= 2` on raw GeV (CPU, synthetic arrays)."""
import numpy as np


def raw(seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros((50, 64, 3), 'float32')
    n = rng.integers(5, 64, size=50)
    for j, k in enumerate(n):
        pt = np.sort(rng.exponential(8.0, size=k))[::-1]
        x[j, :k, 0] = pt
        x[j, :k, 1:] = rng.normal(0, 0.4, size=(k, 2))
    return x


def test_gate_matches_chang():
    from bnhgq2.data import apply_pt_gate
    x = raw()
    chang = x.copy(); chang *= chang[..., :1] >= 2
    ours = apply_pt_gate(x.copy(), ['pt', 'etarel', 'phirel'], 2.0)
    np.testing.assert_array_equal(ours, chang)
    assert ours.dtype == np.float32


def test_gate_zeroes_all_features_and_keeps_rows():
    from bnhgq2.data import apply_pt_gate
    x = raw(1)
    stats = {}
    g = apply_pt_gate(x, ['pt', 'etarel', 'phirel'], 2.0, stats)
    low = (x[..., 0] > 0) & (x[..., 0] < 2)
    assert np.all(g[low] == 0) and np.array_equal(g[x[..., 0] >= 2], x[x[..., 0] >= 2])
    assert g.shape == x.shape
    assert stats['n_newly_gated_slots'] == int(low.sum())
    assert stats['n_padded_slots'] == int((x[..., 0] == 0).sum())


def test_gate_off_is_identity():
    from bnhgq2.data import apply_pt_gate
    x = raw(2)
    assert apply_pt_gate(x, ['pt', 'etarel', 'phirel'], None) is x


def test_gate_then_standardize_matches_chang_order():
    """Gate before standardization: a gated constituent becomes -mu/sigma, not 0."""
    from bnhgq2.data import apply_pt_gate, input_std_stats, apply_input_std
    x = raw(3)
    g = apply_pt_gate(x, ['pt', 'etarel', 'phirel'], 2.0)
    mu, sigma = input_std_stats(g)
    s = apply_input_std(g, mu, sigma)
    low = (x[..., 0] > 0) & (x[..., 0] < 2)
    np.testing.assert_allclose(s[low], np.broadcast_to(-mu / sigma, s[low].shape), rtol=1e-6)


def test_split_sizes():
    import prepare_cache
    assert prepare_cache.split_sizes(0.2) == (496000, 124000)
    assert prepare_cache.split_sizes(0.1) == (558000, 62000)
    assert prepare_cache.cache_order_seed({'train': {'order_seed': 5}}) == 5
    assert prepare_cache.cache_order_seed({'train': {'order_seed': 5}, 'cache': {'order_seed_in_cache': False}}) is None
