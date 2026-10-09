import os, sys, json
os.environ['KERAS_BACKEND']='tensorflow'; os.environ['TF_CPP_MIN_LOG_LEVEL']='3'
sys.path.insert(0, os.getcwd())
import numpy as np
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2 import ablation
from bnhgq2.ebops_target import activation_quantizers
from bnhgq2.data import input_std_stats, apply_input_std
rng = np.random.default_rng(0)
n = 8192
x = np.zeros((n, 64, 3), 'float32')
k = rng.integers(10, 64, n)
for j in range(n):
    x[j, :k[j], 0] = np.sort(rng.exponential(8.0, k[j]))[::-1]
    x[j, :k[j], 1:] = rng.normal(0, .3, (k[j], 2))
x *= x[..., :1] >= 2
mu, sd = input_std_stats(x); x = apply_input_std(x, mu, sd)
x = x[rng.permutation(n)]
cfg = json.load(open('campaigns/chang0926/configs/chang0926-a-n64-s1.json'))
m, _ = ablation.matching_initialization(cfg, x[:4096], 1)
e256 = ablation.compute_ebops(m, x[:256])['total']
i256 = {nm: np.asarray(q.i).copy() for nm, q in activation_quantizers(m) if q.overflow_mode == 'WRAP'}
p256 = np.asarray(m.predict(x[4096:], batch_size=1024, verbose=0))
eall = ablation.compute_ebops(m, x[4096:])['total']
iall = {nm: np.asarray(q.i).copy() for nm, q in activation_quantizers(m) if q.overflow_mode == 'WRAP'}
pall = np.asarray(m.predict(x[4096:], batch_size=1024, verbose=0))
d = np.abs(p256 - pall).max(axis=1)
print('ebops trace256', e256, 'trace4096', eall)
print('rows with changed logits', float((d > 1e-6).mean()), 'max_abs', float(d.max()), 'argmax changed', float((p256.argmax(1) != pall.argmax(1)).mean()))
print('quantizers with i raised', sum(bool((iall[k] > i256[k]).any()) for k in i256), 'of', len(i256), 'max di', max(float((iall[k]-i256[k]).max()) for k in i256))
