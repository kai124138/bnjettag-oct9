"""Experimental quantized conditional memory for constituent transformers.

An Engram-inspired adaptation, NOT a reproduction of DeepSeek's language model.
Fixed train-only feature bins address learned tables. Values (and optional gate
keys) are trained directly in deployment dimensions, eliminating online dense
projections. The custom bit-operation estimate is separate from native HGQ2
arithmetic. No hls4ml converter or hardware throughput claim is implied.
"""
from __future__ import annotations

import math

import keras
import numpy as np
import tensorflow as tf


def fixed_np(x, bits, integer, signed=True):
    fraction = bits - integer - int(signed)
    scale = float(2.0 ** fraction)
    lo = -2.0 ** integer if signed else 0.0
    hi = 2.0 ** integer - 1.0 / scale
    return np.clip(np.round(np.asarray(x) * scale) / scale, lo, hi).astype('float32')


def fixed_ste(x, bits, integer, signed=True):
    """Round-to-even, saturating fixed point; identity surrogate inside range."""
    fraction = bits - integer - int(signed)
    scale = float(2.0 ** fraction)
    lo = -2.0 ** integer if signed else 0.0
    hi = 2.0 ** integer - 1.0 / scale
    clipped = tf.clip_by_value(x, lo, hi)
    rounded = tf.round(clipped * scale) / scale
    return clipped + tf.stop_gradient(rounded - clipped)


def validate_spec(spec):
    required = {'bins', 'table_size', 'heads', 'orders', 'gate', 'value_bits',
                'key_bits', 'query_bits', 'gate_bits', 'input_bits',
                'input_integer', 'residual_bits', 'insert_after', 'hash_seed'}
    if set(spec) != required:
        raise ValueError(f'Engram spec keys: missing={required-set(spec)}, extra={set(spec)-required}')
    if spec['bins'] not in (4, 8, 16):
        raise ValueError('bins must be 4, 8, or 16')
    if not 16 <= spec['table_size'] <= 65536 or spec['heads'] not in (1, 2, 4):
        raise ValueError('Expected 16..65536 slots per head and 1, 2, or 4 heads')
    if spec['orders'] not in ([1], [2], [2, 3]):
        raise ValueError('orders must be [1], [2], or [2, 3]')
    if spec['gate'] not in ('none', 'hard'):
        raise ValueError('gate must be none or hard')
    for key in ('value_bits', 'key_bits', 'query_bits', 'gate_bits'):
        if not isinstance(spec[key], int) or not 4 <= spec[key] <= 12:
            raise ValueError(f'{key} must be an integer in 4..12')
    if spec['input_bits'] != 16 or spec['input_integer'] != 6:
        raise ValueError('Encoder currently requires signed fixed<16,7>: six magnitude integer bits')
    if spec['residual_bits'] < 24:
        raise ValueError('Residual adder estimate must reserve at least 24 bits')
    if not isinstance(spec['hash_seed'], int) or not 0 <= spec['hash_seed'] <= 1048576:
        raise ValueError('hash_seed must be in 0..1048576 (bounded int64 hashing)')


def fit_tokenizer(x_train, input_std, spec):
    """Fit quantile thresholds on a deterministic TRAIN subset, excluding padding.

    x_train is already standardized using the shared training-only statistics.
    Encoder quantization is part of the forward model (not hidden preprocessing).
    """
    validate_spec(spec)
    if x_train.ndim != 3 or x_train.shape[-1] != 3 or not np.isfinite(x_train).all():
        raise ValueError('Expected finite standardized (jets, constituents, 3) training inputs')
    mu, sigma = (np.asarray(input_std[k], dtype='float32') for k in ('mu', 'sigma'))
    if mu.shape != (3,) or sigma.shape != (3,) or not np.isfinite([mu, sigma]).all() or (sigma <= 0).any():
        raise ValueError('Invalid input standardization')
    raw_padding = float(-mu[0] / sigma[0])
    padding = float(fixed_np(raw_padding, spec['input_bits'], spec['input_integer']))
    xq = fixed_np(x_train, spec['input_bits'], spec['input_integer'])
    valid = xq[..., 0] > padding
    if not valid.any():
        raise ValueError('No valid constituents remain after encoder quantization')
    values = xq[valid]
    fractions = np.arange(1, spec['bins']) / spec['bins']
    edges = fixed_np(np.quantile(values, fractions, axis=0).T,
                     spec['input_bits'], spec['input_integer'])
    return {'edges': edges.tolist(), 'padding_pt': padding,
            'fit_jets': len(x_train), 'fit_valid_constituents': int(valid.sum()),
            'collapsed_thresholds_per_feature': [int(len(e) - len(np.unique(e))) for e in edges],
            'positive_pt_lost_to_encoder': int(((x_train[..., 0] > raw_padding + 1e-6) & ~valid).sum()),
            'fit_split': 'train only'}


def address_numpy(x, tokenizer, spec):
    """Independent NumPy address reference, including per-jet boundary masking."""
    xq = fixed_np(x, spec['input_bits'], spec['input_integer'])
    valid = xq[..., 0] > tokenizer['padding_pt']
    bins = (xq[..., None] > np.asarray(tokenizer['edges'], dtype='float32')).sum(-1)
    code = bins[..., 0] * spec['bins'] ** 2 + bins[..., 1] * spec['bins'] + bins[..., 2]
    outputs, masks = [], []
    primes = (73856093, 19349663, 83492791)
    for order in spec['orders']:
        mix = np.zeros_like(code, dtype='int64')
        mask = valid.copy()
        for lag in range(order):
            shifted = np.zeros_like(code)
            present = np.zeros_like(valid)
            if lag == 0:
                shifted, present = code, valid
            else:
                shifted[:, lag:], present[:, lag:] = code[:, :-lag], valid[:, :-lag]
            mask &= present
            mix ^= (shifted + 1) * primes[lag]
        for head in range(spec['heads']):
            if order == 1 and spec['heads'] == 1 and spec['table_size'] >= spec['bins'] ** 3:
                address = code  # exact tuple lookup; no gratuitous collisions
            else:
                salted = mix ^ ((head + 1 + spec['hash_seed']) * 2654435761)
                salted ^= salted >> (11 + head)
                salted ^= salted >> 23
                address = salted % spec['table_size']
            outputs.append(address)
            masks.append(mask)
    return np.stack(outputs, -1), np.stack(masks, -1)


def cost_ledger(spec, n_part, width):
    """Transparent structural ESTIMATE, not a synthesis or native HGQ formula.

    Arithmetic proxy: b1*b2 per product, accumulator width per addition,
    input width per comparison. Shifts/wires/masks are itemized, not charged as
    multipliers. Table bit storage/read traffic are separate budget dimensions.
    """
    validate_spec(spec)
    banks = len(spec['orders']) * spec['heads']
    gated = spec['gate'] == 'hard'
    vb, kb, qb, gb = (spec[k] for k in ('value_bits', 'key_bits', 'query_bits', 'gate_bits'))
    ceil_log = lambda n: int(math.ceil(math.log2(max(1, n))))
    additions = n_part * width * max(0, banks - 1)
    table_reduce = additions * (vb + ceil_log(banks))
    if gated:
        table_reduce += additions * (kb + ceil_log(banks))
    dot = n_part * (width * qb * kb + (width - 1) * (qb + kb + ceil_log(width))) if gated else 0
    value_gate = n_part * width * gb * vb if gated else 0
    gate_affine_clip = n_part * 3 * (qb + kb + ceil_log(width)) if gated else 0
    residual = n_part * width * spec['residual_bits']
    comparisons = n_part * (3 * (spec['bins'] - 1) + 1)
    encoder = comparisons * spec['input_bits']
    # A deliberately simple bitwise implementation budget for hash mixes.
    exact = spec['orders'] == [1] and spec['heads'] == 1 and spec['table_size'] >= spec['bins'] ** 3
    hashed_words = 0 if exact else n_part * sum(spec['orders']) * spec['heads']
    hashing = hashed_words * 64 * 64  # conservative proxy for constant multiply/XOR/modulo chain
    components = dict(encoder_comparisons=encoder, hash_addressing=hashing,
                      table_reduction_adds=table_reduce, query_key_dot=dot,
                      gate_affine_clip=gate_affine_clip, gate_value_products=value_gate,
                      residual_adds=residual)
    table_bits = banks * spec['table_size'] * width * (vb + (kb if gated else 0))
    read_bits = n_part * banks * width * (vb + (kb if gated else 0))
    replicas = math.ceil(n_part / 2)  # illustrative 2-read-port packed key/value ROM
    return {'convention': 'engram_structural_bitops_v1_estimate',
            'estimated_bitops': int(sum(components.values())), 'components': components,
            'logical_table_bits': table_bits, 'logical_table_bytes': math.ceil(table_bits / 8),
            'table_read_bits_per_jet': read_bits, 'vector_reads_per_jet': n_part * banks,
            'independent_addresses_per_bank_per_jet': n_part,
            'two_read_port_replicas_for_whole_jet_ii1': replicas,
            'replicated_table_bytes_estimate': math.ceil(table_bits * replicas / 8),
            'threshold_storage_bits': 3 * (spec['bins'] - 1) * spec['input_bits'],
            'encoder_comparisons_per_jet': comparisons,
            'hash_words_per_jet': hashed_words, 'exact_tuple_addressing': exact,
            'unpriced_operations': ['round/saturate quantizers', 'validity masks and multiplexers',
                                   'control and wiring', 'physical memory block rounding/routing'],
            'hardware_status': 'unimplemented; no timing, resource, or II guarantee'}


@keras.saving.register_keras_serializable(package='bnhgq2')
class JetEngram(keras.layers.Layer):
    """Quantized table residual with an optional bounded context-dependent gate."""

    def __init__(self, spec, tokenizer, **kwargs):
        super().__init__(**kwargs)
        validate_spec(spec)
        self.spec = dict(spec)
        self.tokenizer = dict(tokenizer)
        self.enable_ebops = True

    def build(self, input_shape):
        hidden_shape, raw_shape = input_shape
        self.width, self.n_part = int(hidden_shape[-1]), int(hidden_shape[1])
        if raw_shape[-1] != 3 or raw_shape[1] != self.n_part:
            raise ValueError('Engram needs matching constituent dimensions and exactly pt/etarel/phirel')
        if self.width & (self.width - 1):
            raise ValueError('Power-of-two width required for shift-only gate scaling')
        banks = len(self.spec['orders']) * self.spec['heads']
        self.values = self.add_weight(name='values', shape=(banks, self.spec['table_size'], self.width),
                                      initializer='zeros')
        if self.spec['gate'] == 'hard':
            self.keys = self.add_weight(name='keys', shape=self.values.shape,
                                        initializer=keras.initializers.RandomUniform(-.5, .5,
                                                                                     seed=self.spec['hash_seed']))
        self.ledger = cost_ledger(self.spec, self.n_part, self.width)
        self._ebops = self.add_weight(name='estimated_bitops', shape=(), trainable=False,
                                      initializer=keras.initializers.Constant(self.ledger['estimated_bitops']))
        super().build(input_shape)

    @property
    def ebops(self):
        return self._ebops

    def addresses(self, x):
        s = self.spec
        xq = fixed_ste(x, s['input_bits'], s['input_integer'])
        valid = xq[..., 0] > self.tokenizer['padding_pt']
        edges = tf.constant(self.tokenizer['edges'], dtype=x.dtype)
        bins = tf.reduce_sum(tf.cast(xq[..., None] > edges, tf.int64), axis=-1)
        code = bins[..., 0] * s['bins'] ** 2 + bins[..., 1] * s['bins'] + bins[..., 2]
        ids, masks = [], []
        for order in s['orders']:
            mix, mask = tf.zeros_like(code), valid
            for lag, prime in enumerate((73856093, 19349663, 83492791)[:order]):
                shifted = code if lag == 0 else tf.pad(code[:, :-lag], [[0, 0], [lag, 0]])
                present = valid if lag == 0 else tf.pad(valid[:, :-lag], [[0, 0], [lag, 0]])
                mask = mask & present
                mix = tf.bitwise.bitwise_xor(mix, (shifted + 1) * prime)
            for head in range(s['heads']):
                if order == 1 and s['heads'] == 1 and s['table_size'] >= s['bins'] ** 3:
                    index = code
                else:
                    salted = tf.bitwise.bitwise_xor(mix, tf.constant((head + 1 + s['hash_seed']) * 2654435761, tf.int64))
                    salted = tf.bitwise.bitwise_xor(salted, tf.bitwise.right_shift(salted, 11 + head))
                    salted = tf.bitwise.bitwise_xor(salted, tf.bitwise.right_shift(salted, 23))
                    index = tf.math.floormod(salted, s['table_size'])
                ids.append(index)
                masks.append(mask)
        return tf.stack(ids, -1), tf.stack(masks, -1)

    def components(self, inputs):
        """Expose the actual quantized gate/residual for bounded audit diagnostics."""
        h, x = inputs
        s = self.spec
        ids, masks = self.addresses(x)
        banks = len(s['orders']) * s['heads']

        def retrieve(table, bits, integer):
            # Gather first: no dense full-table fake quantization in the forward pass.
            rows = [fixed_ste(tf.gather(table[i], ids[..., i]), bits, integer)
                    * tf.cast(masks[..., i, None], h.dtype) for i in range(banks)]
            return fixed_ste(tf.add_n(rows) / float(banks), bits, integer)

        value = retrieve(self.values, s['value_bits'], 1)
        query, gate = None, None
        if s['gate'] == 'hard':
            key = retrieve(self.keys, s['key_bits'], 0)
            query = fixed_ste(h, s['query_bits'], 3)
            gate = tf.clip_by_value(.5 + tf.reduce_sum(query * key, -1, keepdims=True)
                                    / float(4 * self.width), 0., 1.)
            gate = fixed_ste(gate, s['gate_bits'], 1, signed=False)
            value = fixed_ste(gate * value, s['value_bits'], 1)
        return {'residual': value, 'query': query, 'gate': gate, 'masks': masks}

    def call(self, inputs, training=None):
        return inputs[0] + self.components(inputs)['residual']

    def compute_output_shape(self, input_shape):
        return input_shape[0]

    def get_config(self):
        return {**super().get_config(), 'spec': self.spec, 'tokenizer': self.tokenizer}


def augment_model(base, spec, tokenizer):
    """Insert after a named layer, preserving every backbone layer and parameter."""
    memory = JetEngram(spec, tokenizer, name='jet_engram')
    raw = keras.Input(base.input_shape[1:], name='engram_input')
    hits = []

    def call(layer, *args, **kwargs):
        result = layer(*args, **kwargs)
        if layer.name == spec['insert_after']:
            result = memory([result, raw])
            hits.append(layer.name)
        return result

    model = keras.models.clone_model(base, input_tensors=raw,
                                     clone_function=lambda layer: layer, call_function=call)
    if hits != [spec['insert_after']]:
        raise ValueError(f'Expected exactly one insertion at {spec["insert_after"]}; got {hits}')
    return model


def accounting(model, native_trace):
    ledgers = {layer.name: layer.ledger for layer in model.layers if isinstance(layer, JetEngram)}
    estimated = sum(v['estimated_bitops'] for v in ledgers.values())
    return {'selection_cost': native_trace['total'],
            'selection_cost_convention': 'native_hgq2_plus_custom_estimate' if ledgers else 'native_hgq2',
            'native_hgq2_backbone_ebops': native_trace['total'] - estimated,
            'custom_estimated_bitops': estimated, 'modules': ledgers,
            'warning': 'Augmented total is not directly interchangeable with historical native HGQ2 totals.'}


def diagnostic_observer():
    """Training-only fixed-sample diagnostics; no validation-dependent tuning.

    The returned closure caches a hidden-state probe, and works again after a
    model reload. It does not change any parameter or quantizer state.
    """
    cached = {}

    def observe(model, sample, epoch):
        layers = [layer for layer in model.layers if isinstance(layer, JetEngram)]
        if not layers:
            return {'cost/native_hgq2_backbone_ebops': float(sum(
                float(layer.ebops) for layer in model.layers if getattr(layer, 'enable_ebops', False))),
                    'cost/custom_estimated_bitops': 0.}
        if len(layers) != 1:
            raise ValueError('Diagnostics expect one memory module')
        layer = layers[0]
        if cached.get('model') is not model:
            cached.update(model=model, probe=keras.Model(model.inputs, layer.input[0]))
        h = cached['probe'](sample, training=False)
        parts = layer.components([h, tf.convert_to_tensor(sample, dtype=h.dtype)])
        valid = np.any(np.asarray(parts['masks']), axis=-1)
        if not valid.any():
            raise ValueError('Diagnostic sample has no valid memory lookups')
        residual, hidden = np.asarray(parts['residual'])[valid], np.asarray(h)[valid]
        total = sum(float(l.ebops) for l in model.layers if getattr(l, 'enable_ebops', False))
        ledger = layer.ledger
        value_table = fixed_np(layer.values.numpy(), layer.spec['value_bits'], 1)
        result = {'cost/native_hgq2_backbone_ebops': total - ledger['estimated_bitops'],
                  'cost/custom_estimated_bitops': float(ledger['estimated_bitops']),
                  'memory/logical_table_bytes': float(ledger['logical_table_bytes']),
                  'memory/table_read_bits_per_jet': float(ledger['table_read_bits_per_jet']),
                  'memory/valid_lookup_fraction': float(valid.mean()),
                  'memory/effective_value_nonzero_fraction': float(np.mean(value_table != 0)),
                  'memory/residual_nonzero_fraction': float(np.mean(residual != 0)),
                  'memory/residual_rms': float(np.sqrt(np.mean(residual.astype('float64') ** 2))),
                  'memory/hidden_rms': float(np.sqrt(np.mean(hidden.astype('float64') ** 2)))}
        result['memory/residual_to_hidden_rms'] = result['memory/residual_rms'] / max(result['memory/hidden_rms'], 1e-12)
        if parts['gate'] is not None:
            gate = np.asarray(parts['gate'])[valid].reshape(-1)
            qhi = 8. - 2. ** -(layer.spec['query_bits'] - 4)
            result.update({'memory/gate_mean': float(gate.mean()),
                           'memory/gate_std': float(gate.std()),
                           'memory/gate_half_fraction': float(np.mean(gate == .5)),
                           'memory/gate_saturation_fraction': float(np.mean((gate == 0) | (gate == 1))),
                           'memory/query_clipped_fraction': float(np.mean((hidden < -8) | (hidden > qhi)))})
            # Nine interpretable gate histogram bins for the pilot's 4-bit gate.
            counts, _ = np.histogram(gate, bins=np.linspace(-.0625, 1.0625, 10))
            result.update({f'memory/gate_hist_{i}': float(count / len(gate)) for i, count in enumerate(counts)})
        if not np.isfinite(list(result.values())).all():
            raise ValueError('Nonfinite memory diagnostics')
        return result
    return observe


@keras.saving.register_keras_serializable(package='bnhgq2')
class MemoryAdam(keras.optimizers.Adam):
    """Adam with a true table LR multiplier, unchanged backbone updates/slots.

    Scaling gradients alone does not implement an Adam learning-rate multiplier.
    The multiplier is applied to the LR passed to the actual Adam update instead.
    Table variables are excluded from decoupled weight decay before optimizer build.
    """

    def __init__(self, memory_lr_multiplier=5., **kwargs):
        super().__init__(**kwargs)
        if not 0 < memory_lr_multiplier <= 100:
            raise ValueError('memory_lr_multiplier must be in (0,100]')
        self.memory_lr_multiplier = float(memory_lr_multiplier)

    def build(self, var_list):
        if self.built:
            return
        self.memory_indices = frozenset(i for i, v in enumerate(var_list)
                                       if 'jet_engram/' in v.path and v.name in ('values', 'keys'))
        if not self.memory_indices:
            raise ValueError('MemoryAdam requires identified jet_engram table variables')
        self.exclude_from_weight_decay(var_list=[var_list[i] for i in self.memory_indices])
        super().build(var_list)

    def update_step(self, gradient, variable, learning_rate):
        if self._get_variable_index(variable) in self.memory_indices:
            learning_rate = learning_rate * self.memory_lr_multiplier
        super().update_step(gradient, variable, learning_rate)

    def get_config(self):
        return {**super().get_config(), 'memory_lr_multiplier': self.memory_lr_multiplier}
