"""[option (c), staged 0032] Absent-key regression: `train.ebops.pid_input` absent must leave the
runner byte-identical to 42abed4b on the regime-B pilot-b config shape (ebops_trace_every 10 kept,
12 epochs so epochs 0, 9 and 11 are traced and the PID reads in-training EBOPs on the others) and on
the regime-A shape (key removed, 3 epochs). Derived from regress_trace_every.py; original docstring:
Absent-key regression for patch 0027 (`train.ebops_trace_every`): run inside a tree (cwd) and
compare with the same script run inside the 77f1ca4e bundle. 3 epochs of run_training on
synthetic rows for screen configs (no [D20] keys) and chang0926 configs with the
`ebops_trace_every` key removed (the regime-A path the running pilot is on). Records every
per-epoch jsonl record minus wall time, every variable of every saved .keras file, the
checkpoint state minus wall time, the file list, and the stdout epoch lines minus wall time.

    python regress_trace_every.py OUT.json   (cwd = the tree to test)
"""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile

os.environ['KERAS_BACKEND'] = 'tensorflow'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, os.getcwd())
import numpy as np
import keras
import tensorflow as tf

tf.config.experimental.enable_tensor_float_32_execution(False)
from bnhgq2.compat import apply_keras_compat
apply_keras_compat()
from bnhgq2 import ablation

TIMING = ('epoch_seconds', 'ebops_trace_seconds', 'ebops_reload_check_seconds', 'ebops_trace_over_epoch')
CONFIGS = [('configs', 'const0922-a07-n64-s1-fast50-fp32'), ('configs', 'const0922-b03-n8-s1-fast50-fp32'),
           ('campaigns/chang0926/configs', 'chang0926-a-n64-s1'),
           ('campaigns/chang0926/configs', 'chang0926-cprime-n64-s1')]


def weights_sha(path):
    m = keras.models.load_model(path, compile=False)
    return hashlib.sha256(b''.join(np.asarray(v).tobytes() for v in m.weights)).hexdigest()


out = {}
RUNS = [(f, n, 'A') for f, n in CONFIGS] + [(f, n, 'B') for f, n in CONFIGS if 'chang0926' in n]
for folder, name, regime in RUNS:
    keras.backend.clear_session()
    cfg = json.load(open(f'{folder}/{name}.json'))
    assert 'pid_input' not in cfg['train']['ebops']
    if regime == 'A':
        had_key = cfg['train'].pop('ebops_trace_every', None)
        cfg['train'].update(epochs=3, batch=128, val_batch=256)
    else:
        had_key = None
        cfg['train'].update(epochs=12, batch=128, val_batch=256)
    n = cfg['arch']['n_part']
    rng = np.random.default_rng(0)
    xt = rng.standard_normal((768, n, 3)).astype('float32')
    xv = rng.standard_normal((256, n, 3)).astype('float32')
    yt = np.eye(5, dtype='float32')[rng.integers(0, 5, 768)]
    yv = np.eye(5, dtype='float32')[np.arange(256) % 5]
    info = {'unit': True, 'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}}
    d = tempfile.mkdtemp()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ablation.run_training(cfg, (xt, yt, xv, yv), info, d)
    recs = [json.loads(line) for line in open(os.path.join(d, 'activation_widths.jsonl'))]
    for r in recs:
        for k in TIMING:
            r.pop(k, None)
    files = {}
    for root, _, names in os.walk(d):
        for f in names:
            rel = os.path.relpath(os.path.join(root, f), d)
            if f.endswith('.keras'):
                files[rel] = weights_sha(os.path.join(root, f))
            elif f == 'state.json':
                s = json.load(open(os.path.join(root, f)))
                s.pop('train_seconds', None)
                files[rel] = hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
            else:
                files[rel] = None
    lines = [re.sub(r' seconds=[0-9.]+', ' seconds=X', ln) for ln in buf.getvalue().splitlines()
             if ln.startswith('[epoch ')]
    out[f'{name}/{regime}'] = {'had_key_removed': had_key, 'records_sha': hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest(),
                 'record_keys': sorted(recs[0]), 'ebops': [r['ebops'] for r in recs], 'files': dict(sorted(files.items())),
                 'epoch_lines': lines}
json.dump(out, open(sys.argv[1], 'w'), sort_keys=True, indent=1)
print('done', len(out))
