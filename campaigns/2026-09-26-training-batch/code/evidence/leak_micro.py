"""Which per-epoch operation of `ablation.run_training` keeps host memory (INCIDENT_stall_20260928).

    python leak_micro.py OP N OUT.json     (cwd = the tree to test)

OP: reload  model.save(candidate) -> keras.models.load_model -> predict(val) -> del, as the
            runner does every epoch (ablation.py, validation candidate)
    reload_persist  as reload, but one validation model is loaded once and later epochs
            load_weights(candidate) into it (the fix under test)
    predict_np  model.predict(numpy validation rows) on one model (no save/reload)
    predict_batches  one tf.function forward over numpy slices of the validation rows
    trace   ablation.compute_ebops(model, train rows) (the [D20] full-split trace)
    stored  ablation.stored_state_ebops(model, loaded) on a fresh reload (the reload check)
Model: chang0926-a-n64-s1 production initializer; synthetic 60,000 x 64 x 3 train rows,
6,000 validation rows (LEAK_MICRO_NVAL; production 62,000); CPU. Memory after gc.collect() per iteration: VmRSS on Linux,
phys_footprint on macOS; plus the Python object count. Not a result.
"""
import gc
import json
import os
import sys
import tempfile

os.environ['KERAS_BACKEND'] = 'tensorflow'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
sys.path.insert(0, os.getcwd())
import numpy as np
import keras
import tensorflow as tf

tf.config.experimental.enable_tensor_float_32_execution(False)
from bnhgq2.compat import apply_keras_compat
apply_keras_compat()
from bnhgq2 import ablation


def footprint_mb():
    if sys.platform == 'darwin':
        import ctypes
        buf = (ctypes.c_uint64 * 40)()
        assert ctypes.CDLL('/usr/lib/libproc.dylib').proc_pid_rusage(os.getpid(), 2, ctypes.byref(buf)) == 0
        return buf[9] / 2 ** 20
    for line in open('/proc/self/status'):
        if line.startswith('VmRSS:'):
            return int(line.split()[1]) / 1024


op, n, out_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cfg = json.load(open('campaigns/chang0926/configs/chang0926-a-n64-s1.json'))
rng = np.random.default_rng(0)
xt = rng.standard_normal((60000, 64, 3)).astype('float32')
xv = rng.standard_normal((int(os.environ.get('LEAK_MICRO_NVAL', '6000')), 64, 3)).astype('float32')
model, _ = ablation.matching_initialization(cfg, xt[:4096], 1)
ablation.compute_ebops(model, xt[:4096])
d = tempfile.mkdtemp()
path = os.path.join(d, 'validation_candidate.keras')
series, objects = [], []
for i in range(n):
    if op == 'reload':
        model.save(path)
        loaded = keras.models.load_model(path, compile=False)
        np.asarray(loaded.predict(xv, batch_size=cfg['train']['val_batch'], verbose=0))
        del loaded
    elif op == 'reload_persist':
        model.save(path)
        if i == 0:
            persistent = keras.models.load_model(path, compile=False)
        else:
            persistent.load_weights(path)
        np.asarray(persistent.predict(xv, batch_size=cfg['train']['val_batch'], verbose=0))
    elif op == 'predict_np':
        np.asarray(model.predict(xv, batch_size=cfg['train']['val_batch'], verbose=0))
    elif op == 'predict_batches':
        b = cfg['train']['val_batch']
        if i == 0:
            infer = tf.function(lambda x: model(x, training=False), reduce_retracing=True)
        np.concatenate([np.asarray(infer(xv[j:j + b])) for j in range(0, len(xv), b)])
    elif op == 'trace':
        ablation.compute_ebops(model, xt, batch_size=2048)
    elif op == 'stored':
        model.save(path)
        loaded = keras.models.load_model(path, compile=False)
        ablation.stored_state_ebops(model, loaded)
        del loaded
    else:
        raise SystemExit(op)
    gc.collect()
    series.append(footprint_mb())
    objects.append(len(gc.get_objects()))
    print(f'LEAK_MICRO {op} iter {i + 1} footprint_mb {series[-1]:.1f} py_objects {objects[-1]}', flush=True)
tail = np.array(series[3:])
slope = float(np.polyfit(np.arange(len(tail)), tail, 1)[0])
oslope = float(np.polyfit(np.arange(len(tail)), np.array(objects[3:]), 1)[0])
json.dump({'op': op, 'n': n, 'footprint_mb': series, 'py_objects': objects, 'slope_mb_per_iter': slope,
           'py_objects_per_iter': oslope, 'platform': sys.platform}, open(out_path, 'w'), indent=1)
print(f'LEAK_MICRO_SLOPE {op} n {n} mb_per_iter {slope:.2f} py_objects_per_iter {oslope:.0f}', flush=True)
