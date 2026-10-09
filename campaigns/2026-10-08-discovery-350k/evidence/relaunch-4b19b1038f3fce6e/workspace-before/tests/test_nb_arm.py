"""[D22]/[A22] arm NB (patch 0036): arm A with every binarized kernel on HGQ2 kbi learned-width
weights, configured as the jsc150 `xfm` weight quantizer.

CPU, synthetic inputs, small. Runs under `python -m unittest` or pytest. Covers: the builder
branch and its jsc150 values; the builder raises on an unknown weight type; the NB gate; one
training step with gradients on the widths; EBOPs bill the real weight bits (equal to binary
pricing at 1 bit, 0 at 0 bits); widths reach 0 under EBOPs pressure; reload round trip; the
init kernels equal arm A's (pairing prerequisite); arm A configs and builds unchanged.
"""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
TREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TREE))
CAMP = TREE / 'campaigns' / 'chang1002c'

import numpy as np  # noqa: E402
import keras  # noqa: E402

from bnhgq2 import ablation, qat  # noqa: E402
from bnhgq2.compat import apply_keras_compat  # noqa: E402
from bnhgq2.ebops_calc import compute_ebops  # noqa: E402

apply_keras_compat()

# The jsc150 xfm weight quantizer as dumped on the pin (hgq2 0.1.9), written out independently
# of qat.JSC150_XFM_WEIGHT so a change to either is caught.
JSC150_DUMP = {'k': 1.0, 'b': 4.0, 'i': 0.0, 'overflow_mode': 'SAT_SYM', 'round_mode': 'RND',
               'bc': (0.0, 23.0), 'br_l1': 1e-8, 'ir_l1': 1e-8}


def a_config(seed=1):
    return json.loads((CAMP / 'configs' / f'chang1002c-a-n64-s{seed}.json').read_text())


def nb_config(seed=1):
    cfg = copy.deepcopy(a_config(seed))
    cfg['quant']['weight'] = 'kbi_learnable'
    cfg['name'] = cfg['name'].replace('-a-', '-nb-')
    return cfg


def sample(n=64, seed=0):
    return np.random.default_rng(seed).standard_normal((n, 64, 3)).astype('float32')


class BuildTests(unittest.TestCase):
    def setUp(self):
        keras.backend.clear_session()

    def test_builds_with_jsc150_weight_quantizer(self):
        cfg = nb_config()
        model, _ = qat.build_qat_model(cfg, seed=1)
        layers = qat.kbi_weight_layers(model)
        self.assertEqual(set(layers), ablation.expected_binary_layers(cfg))
        self.assertEqual(qat.effective_weight_values(model), {})
        for name, layer in layers.items():
            q = layer.kq.quantizer
            self.assertEqual(tuple(q._b.shape), tuple(layer._kernel.shape), name)   # per weight
            self.assertTrue(q._b.trainable and q._i.trainable, name)
            self.assertEqual(np.unique(np.asarray(q._k)).tolist(), [JSC150_DUMP['k']])
            self.assertEqual(np.unique(np.asarray(q._b)).tolist(), [JSC150_DUMP['b']])
            self.assertEqual(np.unique(np.asarray(q._i)).tolist(), [JSC150_DUMP['i']])
            self.assertEqual((q.overflow_mode, q.round_mode),
                             (JSC150_DUMP['overflow_mode'], JSC150_DUMP['round_mode']))
            self.assertEqual((q.b_constraint.min_value, q.b_constraint.max_value), JSC150_DUMP['bc'])
            self.assertIsNone(q.i_constraint)
            self.assertEqual(q.b_regularizer.get_config()['l1'], JSC150_DUMP['br_l1'])
            self.assertEqual(q.i_regularizer.get_config()['l1'], JSC150_DUMP['ir_l1'])
            # biases stay float, as in arm A
            if layer.bq is not None:
                self.assertTrue(getattr(layer.bq.quantizer, '__dummy__', False), name)
        record = ablation.nb_weight_gate(model, cfg)
        self.assertEqual(set(record), set(layers))
        for r in record.values():
            self.assertEqual((r['zero_bits_fraction'], r['mean_bits']), (0.0, 4.0))
            self.assertGreater(r['distinct_values'], 2)        # not binary
        ablation.binary_gate(model, cfg)                        # dispatches to the NB gate

    def test_activation_quantizers_identical_to_a(self):
        from bnhgq2.ebops_target import activation_quantizers

        def describe(model):
            return [(n, type(q).__name__, q.overflow_mode, q.trainable,
                     tuple(np.asarray(q._i).shape), float(np.asarray(q._i).ravel()[0]),
                     float(np.asarray(getattr(q, '_f', getattr(q, '_b', None))).ravel()[0]))
                    for n, q in activation_quantizers(model)]
        a, _ = qat.build_qat_model(a_config(), seed=1)
        keras.backend.clear_session()
        nb, _ = qat.build_qat_model(nb_config(), seed=1)
        self.assertEqual(describe(a), describe(nb))

    def test_unknown_weight_type_raises(self):
        cfg = a_config()
        cfg['quant']['weight'] = 'kbi_learned'
        with self.assertRaises(ValueError):
            qat.build_qat_model(cfg, seed=1)

    def test_not_the_static_int8_quantizer(self):
        """[A22]: NB never falls back to the w8a8 grid. At init (b 4, i 0) the kbi grid 2^-4 is a
        subset of the int8 grid 2^-5 by construction, so the check is structural (kbi, trainable,
        per weight) plus: with 8 fractional bits the NB kernel leaves the int8 grid."""
        model, _ = qat.build_qat_model(nb_config(), seed=1)
        layer = model.get_layer('bit_block_0_ffn_fc1')
        q = layer.kq.quantizer
        self.assertEqual(type(q).__name__, 'FixedPointQuantizerKBI')
        q._b.assign(np.full(q._b.shape, 8.0, 'float32'))
        values = np.asarray(layer.kq(layer._kernel, training=False))
        self.assertFalse(qat.on_static_int8_grid(values))
        self.assertGreater(np.unique(values).size, 2)


class TrainingTests(unittest.TestCase):
    def setUp(self):
        keras.backend.clear_session()

    def test_one_train_step_moves_weights_and_widths(self):
        cfg = nb_config()
        cfg['train']['batch'] = 32
        model, _ = ablation.matching_initialization(cfg, sample(256), 1)
        optimizer = ablation.optimizer_for(cfg, model)
        x = sample(64, seed=3)
        y = keras.utils.to_categorical(np.arange(64) % 5, 5).astype('float32')
        layers = qat.kbi_weight_layers(model)
        b_before = {n: np.asarray(l.kq.quantizer._b).copy() for n, l in layers.items()}
        k_before = {n: np.asarray(l._kernel).copy() for n, l in layers.items()}
        width_vars = [l.kq.quantizer._b for l in layers.values()] + [l.kq.quantizer._i for l in layers.values()]
        trainable_ids = {id(v) for v in model.trainable_variables}
        self.assertTrue(all(id(v) in trainable_ids for v in width_vars))
        step = ablation.make_epoch_step(model, optimizer, x, y, cfg)
        loss, ce, kd, acc = [float(v) for v in step(np.arange(64, dtype='int32')).numpy()]
        self.assertTrue(np.isfinite([loss, ce, kd, acc]).all())
        moved_b = sum(not np.array_equal(b_before[n], np.asarray(l.kq.quantizer._b)) for n, l in layers.items())
        moved_k = sum(not np.array_equal(k_before[n], np.asarray(l._kernel)) for n, l in layers.items())
        self.assertEqual(moved_k, len(layers))
        self.assertGreater(moved_b, 0)

    def test_widths_reach_zero_under_ebops_pressure(self):
        """A layer under EBOPs pressure alone (no task loss): every weight width goes to 0, the
        kernel is exactly 0 and the layer costs 0 EBOPs. Binary weights cannot do this."""
        from hgq.config import LayerConfigScope
        from hgq.layers import QEinsumDense
        keras.utils.set_random_seed(0)
        with LayerConfigScope(enable_ebops=True, beta0=1e-2):
            x = keras.Input((8, 3))
            layer = QEinsumDense('btc,cd->btd', (8, 4), name='probe', kq_conf=qat._kbi_learnable_kq(),
                                 iq_conf=qat._free_act(8, 2, 1e-8, heterogeneous_axis=(-1,), overflow='WRAP'),
                                 bq_conf=None)
            model = keras.Model(x, layer(x))
        data = sample(32, seed=5)[:, :8, :]
        optimizer = keras.optimizers.Adam(0.5)
        import tensorflow as tf
        b = layer.kq.quantizer._b
        for _ in range(60):
            with tf.GradientTape() as tape:
                model(data, training=True)
                loss = tf.add_n(model.losses)
            grads = tape.gradient(loss, [b])
            optimizer.apply_gradients(zip(grads, [b]))
        self.assertTrue(np.all(np.asarray(layer.kq.quantizer.bits) == 0))
        self.assertTrue(np.all(np.asarray(layer.kq(layer._kernel, training=False)) == 0))
        compute_ebops(model, data)
        self.assertEqual(int(layer.ebops), 0)


class EbopsTests(unittest.TestCase):
    def setUp(self):
        keras.backend.clear_session()

    def _pair(self):
        x = sample(256)
        a, _ = ablation.matching_initialization(a_config(), x, 1)
        keras.backend.clear_session()
        nb, _ = ablation.matching_initialization(nb_config(), x, 1)
        return a, nb, x

    def test_kernel_hashes_equal_a_at_init(self):
        """[A22] pairing prerequisite: equal latent kernels/biases after matching_initialization."""
        x = sample(256)
        _, ea = ablation.matching_initialization(a_config(), x, 1)
        keras.backend.clear_session()
        _, en = ablation.matching_initialization(nb_config(), x, 1)
        self.assertEqual(ea['kernel_hashes'], en['kernel_hashes'])
        self.assertEqual(ea['matched_projection_count'], en['matched_projection_count'])

    def test_weight_bits_billed(self):
        a, nb, x = self._pair()
        ea, en = compute_ebops(a, x)['total'], compute_ebops(nb, x)['total']
        self.assertGreater(en, ea)                     # 4-bit weights cost more than 1-bit ones
        # input_proj sees the raw input in both models, so its traced input widths are equal and
        # its cost isolates the weight term: binary pricing at 1 bit, twice that at 2 bits.
        # (Downstream layers see different activations, so their traced ranges differ.)
        def set_bits(bits):
            for layer in qat.kbi_weight_layers(nb).values():
                q = layer.kq.quantizer
                q._b.assign(np.full(q._b.shape, bits, 'float32'))
        set_bits(1)
        a_in = compute_ebops(a, x)['per_layer']['input_proj']
        self.assertEqual(compute_ebops(nb, x)['per_layer']['input_proj'], a_in)
        set_bits(2)
        self.assertEqual(compute_ebops(nb, x)['per_layer']['input_proj'], 2 * a_in)
        layer = nb.get_layer('bit_block_0_ffn_fc1')    # a pruned kernel costs nothing
        before = compute_ebops(nb, x)['per_layer']['bit_block_0_ffn_fc1']
        layer.kq.quantizer._b.assign(np.zeros(layer.kq.quantizer._b.shape, 'float32'))
        after = compute_ebops(nb, x)['per_layer']['bit_block_0_ffn_fc1']
        self.assertGreater(before, 0)
        self.assertEqual(after, 0)
        self.assertTrue(np.all(np.asarray(layer.kq(layer._kernel, training=False)) == 0))

    def test_reload_round_trip(self):
        cfg = nb_config()
        model, _ = qat.build_qat_model(cfg, seed=1)
        x = sample(32)
        compute_ebops(model, x)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'm.keras'
            model.save(path)
            loaded = keras.models.load_model(path, compile=False)
        self.assertEqual(ablation.stored_state_ebops(model, loaded)['total'], ablation.saved_ebops(model))
        ablation.binary_gate(loaded, cfg)
        np.testing.assert_array_equal(np.asarray(model(x, training=False)), np.asarray(loaded(x, training=False)))


class ArmAUnchangedTests(unittest.TestCase):
    def test_a_config_files_unchanged(self):
        """Every chang1002c config is byte-identical to the hash its config map records."""
        cmap = json.loads((CAMP / 'config_map.json').read_text())
        for row in cmap['rows']:
            path = TREE / row['new']['file']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['new']['sha256'], path.name)
            self.assertNotEqual(json.loads(path.read_text())['quant']['weight'], 'kbi_learnable')
        self.assertEqual(len(cmap['rows']), 58)

    def test_a_model_has_no_learned_weight_widths(self):
        keras.backend.clear_session()
        cfg = a_config()
        model, _ = qat.build_qat_model(cfg, seed=1)
        self.assertEqual(qat.kbi_weight_layers(model), {})
        self.assertFalse(ablation.is_nb(cfg))
        ablation.binary_gate(model, cfg)


if __name__ == '__main__':
    unittest.main()
