"""bop-optimizer: Bop on the binary latents, Adam on everything else (Delta M020, M071; card B10).

Source: Helwegen, Widdicombe, Geiger, Liu, Cheng, Nusselder, "Latent Weights Do Not Exist:
Rethinking Binarized Neural Network Optimization", NeurIPS 2019, arXiv:1906.02107. Rule
(re-implemented from the paper's algorithm, no code lifted):
    m_t = (1 - gamma) * m_{t-1} + gamma * g_t
    flip w_i  if  |m_t,i| > tau  and  sign(m_t,i) == sign(w_i)

How the rule maps onto this pipeline (the design choices a reviewer should check):
  * The binary weight is q = bipolar_sign(w - alpha), alpha = mean(w), exactly as the forward
    pass computes it (qat.bitnet_binary_ste). "sign(w_i)" in the rule is this q_i.
  * A flip reflects the latent about the centre: w_i <- 2*alpha - w_i. That flips q_i and keeps
    |w_i - alpha|, so the layer scale beta = mean|w - alpha| stays (to first order; alpha moves
    by the mean of the reflected offsets). Bop in the paper has no latent magnitude at all; here
    the magnitude is frozen at its init and only sets beta. Deliberate; it keeps beta and the
    activation ranges downstream comparable with the Adam anchor.
  * g_t is the gradient the bounded STE delivers to the latent (qat.py docstring), after the
    optimizer's clipvalue. Bop variables get no weight decay and ignore the learning rate
    (THEORY: cosine restarts do not act on Bop unless gamma or tau is scheduled).
  * The EMA m lives in Adam's momentum slot for that variable, so optimizer.variables has the
    same length and order as a plain Adam on the same model: the runner's checkpoint
    save/restore by index (ablation.save_checkpoint / restore_checkpoint) works unchanged.

gamma and tau have no defaults: delta.json leaves them null for the wave STUDY. Test values in
tests/ are labelled test-only. Config: train.binary_optimizer = 'bop', train.bop_gamma,
train.bop_tau.
"""
from __future__ import annotations

import keras
from keras import ops


def binary_latents(model):
    """The latent kernels of every binary layer (BitQEinsumDense / BitQDense)."""
    from bnhgq2 import qat
    return [ly._kernel for ly in model.layers if isinstance(ly, (qat.BitQEinsumDense, qat.BitQDense))]


@keras.saving.register_keras_serializable(package='bnhgq2_delta')
class BopAdam(keras.optimizers.Adam):
    """Adam for every variable except `bop_variables`, which follow the Bop flip rule."""

    def __init__(self, *, gamma, tau, bop_variables=(), **adam_kwargs):
        if gamma is None or tau is None:
            raise ValueError('Bop gamma and tau must be set (Delta leaves them to the wave STUDY)')
        if not 0.0 < float(gamma) <= 1.0 or float(tau) < 0.0:
            raise ValueError(f'Bop needs 0 < gamma <= 1 and tau >= 0; got gamma={gamma}, tau={tau}')
        super().__init__(**adam_kwargs)
        self.bop_gamma = float(gamma)
        self.bop_tau = float(tau)
        # Keep only string keys: a Python list of variables on the optimizer would be
        # auto-tracked and leak the model weights into optimizer.variables (and the checkpoint).
        bop_variables = list(bop_variables)
        self._bop_keys = tuple(self._var_key(v) for v in bop_variables)
        self._bop_index = None
        if bop_variables and self.weight_decay is not None:
            self.exclude_from_weight_decay(var_list=bop_variables)

    def build(self, var_list):
        if self.built:
            return
        super().build(var_list)
        missing = [k for k in self._bop_keys if k not in self._trainable_variables_indices]
        if missing:
            raise ValueError(f'{len(missing)} Bop variables are not in the optimizer var_list')
        self._bop_index = frozenset(self._trainable_variables_indices[k] for k in self._bop_keys)

    def is_bop(self, variable):
        return self._bop_index is not None and self._get_variable_index(variable) in self._bop_index

    def update_step(self, gradient, variable, learning_rate):
        if not self.is_bop(variable):
            return super().update_step(gradient, variable, learning_rate)
        gradient = ops.cast(gradient, variable.dtype)
        m = self._momentums[self._get_variable_index(variable)]
        self.assign(m, ops.add(ops.multiply(m, 1.0 - self.bop_gamma), ops.multiply(gradient, self.bop_gamma)))
        alpha = ops.mean(variable)
        q = ops.where(ops.greater_equal(ops.subtract(variable, alpha), 0.0), 1.0, -1.0)
        flip = ops.logical_and(ops.greater(ops.abs(m), self.bop_tau), ops.equal(ops.sign(m), q))
        self.assign(variable, ops.where(flip, ops.subtract(ops.multiply(alpha, 2.0), variable), variable))

    def get_config(self):
        config = super().get_config()
        config.update(gamma=self.bop_gamma, tau=self.bop_tau)
        return config


def bop_optimizer_for(cfg, model):
    """Drop-in for ablation.optimizer_for when cfg['train']['binary_optimizer'] == 'bop'.

    Same Adam hyperparameters as the anchor path (beta_1 0.9, beta_2, weight_decay, clipvalue from
    cfg['train']); Bop on the binary latents. Engram MemoryAdam is not combined with Bop."""
    tr = cfg['train']
    if tr.get('binary_optimizer') != 'bop':
        raise ValueError("bop_optimizer_for needs train.binary_optimizer == 'bop'")
    if cfg.get('engram_study', {}).get('module') is not None:
        raise ValueError('Bop is not combined with the Engram memory optimizer')
    optimizer = BopAdam(gamma=tr.get('bop_gamma'), tau=tr.get('bop_tau'), bop_variables=binary_latents(model),
                        learning_rate=tr['lr'], beta_1=.9, beta_2=tr['beta2'],
                        weight_decay=tr['weight_decay'], clipvalue=tr['clipvalue'])
    optimizer.build(model.trainable_variables)
    model.compile(optimizer=optimizer, loss=keras.losses.CategoricalCrossentropy(from_logits=True),
                  jit_compile=False)
    return optimizer
