"""No-new-keys regression through run_training: 2 epochs on synthetic rows, screen configs
(no [D20]/[ND] keys). Run inside a tree (cwd); compares per-epoch records (minus wall time)
and every variable of the saved checkpoints."""
import sys, os, json, hashlib, tempfile
os.environ['KERAS_BACKEND'] = 'tensorflow'; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, os.getcwd())
import numpy as np, keras, tensorflow as tf
tf.config.experimental.enable_tensor_float_32_execution(False)
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2 import ablation
out = {}
rng = np.random.default_rng(0)
for name in sys.argv[2:]:
    keras.backend.clear_session()
    cfg = json.load(open(f'configs/{name}.json'))
    cfg['train'].update(epochs=2, batch=128, val_batch=256)
    n = cfg['arch']['n_part']
    xt = rng.standard_normal((768, n, 3)).astype('float32'); xv = rng.standard_normal((256, n, 3)).astype('float32')
    yt = np.eye(5, dtype='float32')[rng.integers(0, 5, 768)]; yv = np.eye(5, dtype='float32')[np.arange(256) % 5]
    info = {'unit': True, 'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}}
    d = tempfile.mkdtemp()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, d)
    recs = [json.loads(l) for l in open(os.path.join(d, 'activation_widths.jsonl'))]
    for r in recs:
        r.pop('epoch_seconds')
    ckpt = {}
    for f in sorted(os.listdir(d)):
        if f.endswith('.keras'):
            m = keras.models.load_model(os.path.join(d, f), compile=False)
            ckpt[f] = hashlib.sha256(b''.join(np.asarray(v).tobytes() for v in m.weights)).hexdigest()
    budget = json.load(open(os.path.join(d, 'ebops_budget.json')))
    out[name] = {'records_sha': hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest(),
                 'record_keys': sorted(recs[0]), 'ckpt': ckpt, 'budget_keys': sorted(budget),
                 'ebops': [r['ebops'] for r in recs], 'files': sorted(os.listdir(d))}
json.dump(out, open(sys.argv[1], 'w'), sort_keys=True, indent=1)
print('done', len(out))
