"""CPU timing: one reset trace (compute_ebops, batch 2048) vs one training pass (make_epoch_step
at the config batch) on the same synthetic rows; ratio and linear scale to 558,000 rows.
CPU only, synthetic; not a result and not the GPU cost."""
import sys, os, json, time
os.environ['KERAS_BACKEND'] = 'tensorflow'; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, os.getcwd())
import numpy as np, keras, tensorflow as tf
tf.config.experimental.enable_tensor_float_32_execution(False)
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2 import ablation
N = int(sys.argv[1]); out = {}
rng = np.random.default_rng(0)
x = rng.standard_normal((N, 64, 3)).astype('float32'); y = np.eye(5, dtype='float32')[rng.integers(0, 5, N)]
for arm in sys.argv[2:]:
    keras.backend.clear_session()
    cfg = json.load(open(f'campaigns/chang0926/configs/chang0926-{arm}-n64-s1.json'))
    m, _ = ablation.matching_initialization(cfg, x[:4096], 1)
    opt = ablation.optimizer_for(cfg, m)
    step = ablation.make_epoch_step(m, opt, x, y, cfg)
    opt.learning_rate.assign(1e-4)
    order = np.arange(N, dtype='int32')
    ablation.compute_ebops(m, x[:4096], batch_size=2048); step(order[:cfg['train']['batch'] * 2])   # warm-up/compile
    t = time.monotonic(); step(order); t_train = time.monotonic() - t
    t = time.monotonic(); ablation.compute_ebops(m, x, batch_size=2048); t_trace = time.monotonic() - t
    out[arm] = {'rows': N, 'train_s': t_train, 'trace_s': t_trace, 'trace_over_train': t_trace / t_train,
                'trace_s_at_558000': t_trace * 558000 / N, 'train_s_at_558000': t_train * 558000 / N}
    print(arm, json.dumps(out[arm]), flush=True)
json.dump(out, open(os.environ.get('OUT', '/dev/null'), 'w'), indent=1)
