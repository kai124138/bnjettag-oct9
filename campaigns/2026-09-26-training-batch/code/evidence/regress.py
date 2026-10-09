"""Byte-level regression: the patched tree must reproduce the base tree on screen configs."""
import sys, os, json, hashlib
os.environ['KERAS_BACKEND']='tensorflow'; os.environ['TF_CPP_MIN_LOG_LEVEL']='3'
sys.path.insert(0, os.getcwd())
import numpy as np, keras
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2 import ablation
from bnhgq2.ebops_target import width_snapshot
out = {}
x = np.random.default_rng(0).standard_normal((4096, 64, 3)).astype('float32')
for name in sys.argv[2:]:
    keras.backend.clear_session()
    cfg = json.load(open(f'configs/{name}.json'))
    n = cfg['arch']['n_part']; xs = x[:, :n]
    m, ev = ablation.matching_initialization(cfg, xs, 1)
    e = ablation.compute_ebops(m, xs[:256])
    p = np.asarray(m(xs[:64], training=False))
    out[name] = {'ebops': e, 'kernel_hashes': ev['kernel_hashes'], 'pred_sha': hashlib.sha256(p.tobytes()).hexdigest(),
                 'widths': width_snapshot(m), 'lr': [ablation.learning_rate(cfg, k) for k in (0, 1, 10, 49)],
                 'digest': ablation.digest_json(cfg), 'params': m.count_params()}
json.dump(out, open(sys.argv[1], 'w'), sort_keys=True, default=str)
print('done', len(out))
