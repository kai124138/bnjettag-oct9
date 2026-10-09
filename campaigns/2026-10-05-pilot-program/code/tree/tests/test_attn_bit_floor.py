"""H3 attention bit floor (patch 0037): quant.attn_bit_floor holds the Q, K, V (and optionally the
softmax input and output) activation quantizers at >= 1 or 2 bits, so EBOPs pressure cannot send
them to 0 bits. Absent key: nothing changes.

CPU, synthetic inputs, small. Runs under `python -m unittest` or pytest.
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
from bnhgq2.ebops_target import activation_quantizers  # noqa: E402

apply_keras_compat()

SITE_NAMES = {'q': 'bit_block_0_attn_scores__in0', 'k': 'bit_block_0_attn_scores__in1',
              'v': 'bit_block_0_attn_ctx__in1', 'softmax_out': 'bit_block_0_attn_ctx__in0',
              'softmax_in': 'bit_block_0_attn_softmax__exp_iq'}


def a_config(seed=1):
    return json.loads((CAMP / 'configs' / f'chang1002c-a-n64-s{seed}.json').read_text())


def floor_config(bits=1, sites=('q', 'k', 'v'), seed=1):
    cfg = copy.deepcopy(a_config(seed))
    cfg['quant']['attn_bit_floor'] = {'bits': bits, 'sites': list(sites)}
    return cfg


def sample(n=64, seed=0):
    return np.random.default_rng(seed).standard_normal((n, 64, 3)).astype('float32')


def zero_all_widths(model):
    """Every learned activation width at its lower bound (static_floor.py's 'zero' state)."""
    for _, q in activation_quantizers(model):
        if not q.trainable:
            continue
        if hasattr(q, '_f'):
            if q.overflow_mode != 'WRAP':
                q._i.assign(np.full(q._i.shape, q.i_constraint.min_value, 'float32'))
            q._f.assign(np.full(q._f.shape, q.f_constraint.min_value, 'float32'))
        else:
            q._b.assign(np.full(q._b.shape, q.b_constraint.min_value, 'float32'))


class AbsentKeyTests(unittest.TestCase):
    def setUp(self):
        keras.backend.clear_session()

    def test_absent_key_builds_no_floor(self):
        model, _ = qat.build_qat_model(a_config(), seed=1)
        self.assertFalse(any(isinstance(q, qat.FlooredKIF) for _, q in activation_quantizers(model)))
        self.assertIsNone(qat.attn_bit_floor(a_config()))

    def test_a_configs_unchanged_and_carry_no_key(self):
        cmap = json.loads((CAMP / 'config_map.json').read_text())
        for row in cmap['rows']:
            path = TREE / row['new']['file']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['new']['sha256'], path.name)
            self.assertNotIn('attn_bit_floor', json.loads(path.read_text())['quant'])

    def test_floor_one_bit_is_inactive_at_init(self):
        """At 1 bit the floor binds nowhere at init: same variables, same traced EBOPs, same
        forward as arm A at the same seed."""
        x = sample(256)
        a, _ = ablation.matching_initialization(a_config(), x, 1)
        ea = compute_ebops(a, x)
        ya = np.asarray(a(x[:16], training=False))
        keras.backend.clear_session()
        f, _ = ablation.matching_initialization(floor_config(1), x, 1)
        ef = compute_ebops(f, x)
        self.assertEqual(ea, ef)
        np.testing.assert_array_equal(ya, np.asarray(f(x[:16], training=False)))
        # same variables in the same order (paths differ only in the quantizer's class name)
        self.assertEqual([np.asarray(v).tobytes() for v in a.weights],
                         [np.asarray(v).tobytes() for v in f.weights])


class FloorTests(unittest.TestCase):
    def setUp(self):
        keras.backend.clear_session()

    def _floored(self, model):
        return {n: q for n, q in activation_quantizers(model) if isinstance(q, qat.FlooredKIF)}

    def test_sites_and_validation(self):
        model, _ = qat.build_qat_model(floor_config(1, ('q', 'k', 'v', 'softmax_in', 'softmax_out')), seed=1)
        self.assertEqual(set(self._floored(model)), set(SITE_NAMES.values()))
        keras.backend.clear_session()
        model, _ = qat.build_qat_model(floor_config(2, ('v',)), seed=1)
        self.assertEqual(set(self._floored(model)), {SITE_NAMES['v']})
        for bad in ({'bits': 0, 'sites': ['q']}, {'bits': 3, 'sites': ['q']}, {'bits': True, 'sites': ['q']},
                    {'bits': 1, 'sites': []}, {'bits': 1, 'sites': ['q', 'q']}, {'bits': 1, 'sites': ['Wq']},
                    {'bits': 1}, {'bits': 1, 'sites': ['q'], 'extra': 1}, [1, ['q']]):
            cfg = a_config()
            cfg['quant']['attn_bit_floor'] = bad
            with self.assertRaises(ValueError, msg=repr(bad)):
                qat.build_qat_model(cfg, seed=1)
        cfg = a_config()
        cfg['quant'].update(softmax_quant='fixed', act_overflow='SAT', attn_bit_floor={'bits': 1, 'sites': ['softmax_out']})
        cfg['quant'].pop('i_decay_speed')
        with self.assertRaises(ValueError):
            qat.build_qat_model(cfg, seed=1)

    def test_zero_state_holds_floor_and_prices_it(self):
        """At the lower bound of every width, the floored Q/K/V read exactly `bits`, every other
        WRAP width reads 0, and the attention einsums are billed for the floor."""
        x = sample(64)
        for bits in (1, 2):
            keras.backend.clear_session()
            model, _ = qat.build_qat_model(floor_config(bits), seed=1)
            zero_all_widths(model)
            cost = compute_ebops(model, x)
            floored = self._floored(model)
            self.assertEqual(set(floored), {SITE_NAMES[s] for s in ('q', 'k', 'v')})
            for name, q in activation_quantizers(model):
                if not (q.trainable and hasattr(q, '_f') and q.overflow_mode == 'WRAP'):
                    continue
                expect = bits if name in floored else 0
                self.assertTrue(np.all(np.asarray(q.bits) == expect), (name, np.unique(np.asarray(q.bits))))
            self.assertGreater(cost['per_layer']['bit_block_0_attn_scores'], 0)
            keras.backend.clear_session()
            base, _ = qat.build_qat_model(a_config(), seed=1)
            zero_all_widths(base)
            self.assertEqual(compute_ebops(base, x)['per_layer']['bit_block_0_attn_scores'], 0)

    def test_training_cannot_push_below_floor(self):
        """EBOPs pressure alone on a floored quantizer: the raw f is clamped every training forward,
        so it stays at the floor and never drifts below it; bits stay at the floor."""
        from hgq.config import LayerConfigScope
        from hgq.layers.ops.einsum import QEinsum
        import tensorflow as tf
        keras.utils.set_random_seed(0)
        conf = qat._with_bit_floor(qat._free_act(8, 2, 1e-8, heterogeneous_axis=(-2, -1), overflow='WRAP'), 1)
        with LayerConfigScope(enable_ebops=True, beta0=1e-2):
            a = keras.Input((8, 2, 4))
            b = keras.Input((8, 2, 4))
            layer = QEinsum('bthe,bshe->bhts', iq_confs=[conf, conf], name='probe')
            model = keras.Model([a, b], layer([a, b]))
        data = [sample(16, 1)[:, :8, :].repeat(3, -1)[..., :8].reshape(16, 8, 2, 4),
                sample(16, 2)[:, :8, :].repeat(3, -1)[..., :8].reshape(16, 8, 2, 4)]
        fvars = [q.quantizer._f for q in layer.iq]
        opt = keras.optimizers.Adam(0.5)
        for _ in range(60):
            with tf.GradientTape() as tape:
                model(data, training=True)
                loss = tf.add_n(model.losses)
            opt.apply_gradients(zip(tape.gradient(loss, fvars), fvars))
        for q in layer.iq:
            qz = q.quantizer
            self.assertTrue(np.all(np.asarray(qz.bits) == 1), np.unique(np.asarray(qz.bits)))
            model(data, training=True)    # one more forward applies the clamp to the last step
            self.assertTrue(np.all(np.asarray(qz._f) >= 1 - np.asarray(qz.i) - 1e-6))
        self.assertGreater(int(layer.ebops), 0)      # stored by the last training forward

    def test_reload_keeps_floor(self):
        cfg = floor_config(2, ('q', 'k', 'v', 'softmax_out'))
        model, _ = qat.build_qat_model(cfg, seed=1)
        zero_all_widths(model)
        x = sample(32)
        compute_ebops(model, x)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'm.keras'
            model.save(path)
            loaded = keras.models.load_model(path, compile=False)
        floored = {n: q.min_bits for n, q in activation_quantizers(loaded) if isinstance(q, qat.FlooredKIF)}
        self.assertEqual(floored, {SITE_NAMES[s]: 2.0 for s in ('q', 'k', 'v', 'softmax_out')})
        self.assertEqual(ablation.stored_state_ebops(model, loaded)['total'], ablation.saved_ebops(model))
        self.assertEqual(compute_ebops(loaded, x)['total'], compute_ebops(model, x)['total'])
        np.testing.assert_array_equal(np.asarray(model(x, training=False)), np.asarray(loaded(x, training=False)))

    def test_one_train_step(self):
        cfg = floor_config(1)
        cfg['train']['batch'] = 32
        x = sample(256)
        model, _ = ablation.matching_initialization(cfg, x, 1)
        opt = ablation.optimizer_for(cfg, model)
        y = keras.utils.to_categorical(np.arange(64) % 5, 5).astype('float32')
        step = ablation.make_epoch_step(model, opt, x[:64], y, cfg)
        loss = [float(v) for v in step(np.arange(64, dtype='int32')).numpy()]
        self.assertTrue(np.isfinite(loss).all())
        for q in self._floored(model).values():
            self.assertTrue(np.all(np.asarray(q.bits) >= 1))


if __name__ == '__main__':
    unittest.main()
