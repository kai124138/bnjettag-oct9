"""Host-memory growth per epoch of `ablation.run_training` (INCIDENT_stall_20260928 §2, §6).

    python leak_probe.py MODE EPOCHS OUT.json      (cwd = the tree to test)

MODE: A      config as shipped minus `ebops_trace_every` (full-split trace every epoch)
      B      `ebops_trace_every: 10` (regime B)
      A_live A, and the per-epoch validation predicts on the live model instead of a
             reloaded copy (diagnostic only: isolates the reload path)
      A_notrace A, and the per-epoch trace replaced by the stored sum (diagnostic only)
Config: chang0926-a-n64-s1 (epochs overridden), synthetic rows (LEAK_PROBE_NTRAIN / _NVAL,
default 60,000 / 6,000, 64 x 3), CPU. LEAK_PROBE_REMOTE=1 runs the W&B path (remote=True). Memory (VmRSS on Linux, phys_footprint on macOS) is read at the end of every epoch by the epoch observer, after
gc.collect(). Nothing here is a result; it measures the runner, not the model.
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
import psutil
import keras
import tensorflow as tf

tf.config.experimental.enable_tensor_float_32_execution(False)
from bnhgq2.compat import apply_keras_compat
apply_keras_compat()
from bnhgq2 import ablation

mode, epochs, out_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cfg = json.load(open('campaigns/chang0926/configs/chang0926-a-n64-s1.json'))
cfg['train']['epochs'] = epochs
cfg['experiment']['snapshot_every_epochs'] = 10 * epochs      # none in the window
cfg['experiment']['checkpoint_every_epochs'] = 25
cfg['experiment'].pop('recovery_after_epochs', None)
if mode.startswith('A'):
    cfg['train'].pop('ebops_trace_every', None)
elif mode == 'B':
    cfg['train']['ebops_trace_every'] = 10
else:
    raise SystemExit(f'unknown mode {mode}')
rng = np.random.default_rng(0)
NT, NV = int(os.environ.get('LEAK_PROBE_NTRAIN', '60000')), int(os.environ.get('LEAK_PROBE_NVAL', '6000'))
REMOTE = os.environ.get('LEAK_PROBE_REMOTE') == '1'   # W&B path (use WANDB_MODE=offline, BNJ_STAGE=pilot)
xt = rng.standard_normal((NT, 64, 3)).astype('float32')
xv = rng.standard_normal((NV, 64, 3)).astype('float32')
yt = np.eye(5, dtype='float32')[rng.integers(0, 5, NT)]
yv = np.eye(5, dtype='float32')[np.arange(NV) % 5]
info = {'unit': True, 'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]}}

if mode == 'A_live':
    live = {}
    _save = keras.Model.save

    def save(self, path, *a, **k):
        live['m'] = self
        return _save(self, path, *a, **k)
    keras.Model.save = save
    _load = keras.models.load_model

    def load(path, *a, **k):
        if str(path).endswith('validation_candidate.keras') and 'm' in live:
            return live['m']
        return _load(path, *a, **k)
    ablation.keras.models.load_model = load
if mode == 'A_notrace':
    _ce = ablation.compute_ebops

    def fake(model, rows, batch_size=2048):
        if len(rows) == len(xt):
            total = ablation.saved_ebops(model)
            return {'total': total, 'per_layer': {}}
        return _ce(model, rows, batch_size=batch_size)
    ablation.compute_ebops = fake

proc = psutil.Process()
series = []
objects = []


def footprint_mb():
    """Linux: VmRSS. macOS: phys_footprint (proc_pid_rusage), which counts compressed pages;
    plain RSS on macOS drops whenever the compressor takes pages and is useless for a slope."""
    if sys.platform == 'darwin':
        import ctypes
        lib = ctypes.CDLL('/usr/lib/libproc.dylib')
        buf = (ctypes.c_uint64 * 40)()
        assert lib.proc_pid_rusage(os.getpid(), 2, ctypes.byref(buf)) == 0   # RUSAGE_INFO_V2
        return buf[2 + 7] / 2 ** 20      # 16-byte uuid = 2 words, then phys_footprint is word 7
    return proc.memory_info().rss / 2 ** 20


def observer(model, sample, epoch):
    gc.collect()
    rss = footprint_mb()
    series.append(rss)
    objects.append(len(gc.get_objects()))
    print(f'LEAK_PROBE {mode} epoch {epoch + 1} footprint_mb {rss:.1f} py_objects {objects[-1]}', flush=True)
    return {'probe_rss_mb': rss}


d = tempfile.mkdtemp()
try:
    ablation.run_training(cfg, (xt, yt, xv, yv), info, d, epoch_observer=observer, remote=REMOTE)
except AssertionError as e:
    # A_live / A_notrace break the runner's own asserts on purpose late in the epoch; the
    # observer has already recorded that epoch.
    print('LEAK_PROBE_ASSERT', mode, repr(e)[:200], flush=True)
warm = 5
tail = np.array(series[warm:])
slope = float(np.polyfit(np.arange(len(tail)), tail, 1)[0]) if len(tail) > 2 else float('nan')
res = {'mode': mode, 'epochs': len(series), 'rss_mb': series, 'py_objects': objects, 'platform': sys.platform, 'slope_mb_per_epoch_after_warmup': slope,
       'warmup_epochs': warm}
if len(series) >= 105 and hasattr(ablation, 'rss_gate_verdict'):
    # the pilot-b gate's own verdict on this series, projected to 7,000 epochs at the 6 GiB limit
    g = {'limit_mb': 6144.0, 'warm': 5, 'end': 105, 'total_epochs': 7000, 'rss': series}
    gs, gb, gp, gv = ablation.rss_gate_verdict(g)
    res['gate'] = {'slope_mb_per_epoch': gs, 'baseline_mb': gb, 'projection_mb_at_7000': gp, 'limit_mb': 6144.0,
                   'fit_epochs': '5-104', 'verdict': gv}
    print(f'LEAK_PROBE_GATE {mode} {gv} slope_mb_per_epoch {gs:.3f} baseline_mb {gb:.0f} '
          f'projection_mb_at_7000 {gp:.0f} limit_mb 6144', flush=True)
json.dump(res, open(out_path, 'w'), indent=1)
print(f'LEAK_PROBE_SLOPE {mode} epochs {len(series)} slope_mb_per_epoch {slope:.2f} '
      f'first {series[0]:.1f} last {series[-1]:.1f}', flush=True)
