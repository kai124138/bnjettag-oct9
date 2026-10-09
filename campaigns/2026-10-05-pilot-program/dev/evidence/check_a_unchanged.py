#!/usr/bin/env python3
"""Arm A (and any option-(c) config) builds and trains identically in the base tree and a patched
tree. Usage: check_a_unchanged.py <base_tree> <patched_tree> [config names...]

Each tree runs in its own subprocess on CPU (TF deterministic ops, 1 thread) and reports a digest of:
every model variable (bytes) after matching_initialization at seed 1 on a fixed synthetic sample,
the traced init EBOPs (total and per layer), the static floors' zero/one totals, and the loss and
variable digest after one epoch_step on 64 synthetic jets. Exit 0 iff all digests match."""
import hashlib
import json
import subprocess
import sys

CHILD = r'''
import hashlib, json, os, sys
os.environ['KERAS_BACKEND'] = 'tensorflow'; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = ''; os.environ['TF_DETERMINISTIC_OPS'] = '1'
tree, names = sys.argv[1], sys.argv[2:]
sys.path.insert(0, tree); os.chdir(tree)
import numpy as np, tensorflow as tf, keras
tf.config.threading.set_inter_op_parallelism_threads(1); tf.config.threading.set_intra_op_parallelism_threads(1)
from bnhgq2 import ablation
from bnhgq2.compat import apply_keras_compat
from bnhgq2.ebops_calc import compute_ebops
apply_keras_compat()
def vdigest(model):
    h = hashlib.sha256()
    for v in model.weights:
        h.update(v.path.encode()); h.update(np.asarray(v).tobytes())
    return h.hexdigest()
out = {}
x = np.random.default_rng(0).standard_normal((256, 64, 3)).astype('float32')
for name in names:
    cfg = json.load(open(f'campaigns/chang1002c/configs/{name}.json'))
    keras.backend.clear_session()
    model, ev = ablation.matching_initialization(cfg, x, cfg['experiment']['seed'])
    init_vars = vdigest(model)
    cost = compute_ebops(model, x)
    cfg['train']['batch'] = 32
    opt = ablation.optimizer_for(cfg, model)
    y = keras.utils.to_categorical(np.arange(64) % 5, 5).astype('float32')
    step = ablation.make_epoch_step(model, opt, x[:64], y, cfg)
    loss = [float(v) for v in step(np.arange(64, dtype='int32')).numpy()]
    out[name] = {'init_vars': init_vars, 'kernel_hashes': hashlib.sha256(json.dumps(ev['kernel_hashes'], sort_keys=True).encode()).hexdigest(),
                 'init_ebops': cost['total'], 'per_layer': cost['per_layer'], 'step_loss': loss, 'after_step_vars': vdigest(model)}
print('RESULT ' + json.dumps(out, sort_keys=True))
'''


def run(tree, names):
    p = subprocess.run([sys.executable, '-c', CHILD, tree, *names], capture_output=True, text=True)
    line = [l for l in p.stdout.splitlines() if l.startswith('RESULT ')]
    if p.returncode or not line:
        sys.exit(f'child failed in {tree}:\n{p.stderr[-3000:]}')
    return json.loads(line[0][7:])


if __name__ == '__main__':
    base, patched, *names = sys.argv[1:]
    names = names or ['chang1002c-a-n64-s1', 'chang1002c-a-n64-s2']
    a, b = run(base, names), run(patched, names)
    for n in names:
        same = a[n] == b[n]
        print(f"{'SAME' if same else 'DIFF'} {n} init_ebops={a[n]['init_ebops']}/{b[n]['init_ebops']} "
              f"loss={a[n]['step_loss'][0]:.6f}/{b[n]['step_loss'][0]:.6f} vars={a[n]['init_vars'][:12]}/{b[n]['init_vars'][:12]} "
              f"after={a[n]['after_step_vars'][:12]}/{b[n]['after_step_vars'][:12]}")
    sys.exit(0 if all(a[n] == b[n] for n in names) else 1)
