#!/usr/bin/env python3
"""PREFLIGHT gate 15: pre-arm GPU integer fingerprint (REGRESSION_TICKET 2026-09-28, Kai's decision 2026-09-28).

    python -u fingerprint_check.py [--run NAME] [--expect N] [--data-root DIR] [--campaign-dir DIR]
                                   [--env-report] [--allow-cpu]

Builds the named run's model and data exactly as the runner does (run_study.train -> ablation.run_training:
TF32 off, validate_cfg, load_cache(<data-root>/n<n_part>/data), apply_keras_compat, set_random_seed(seed),
run_engram.builder_for(info)(cfg, xt[:4096], seed), delta_optimizer_for, then the initial trace
compute_ebops(model, ebops_trace_sample(cfg, xt), batch_size=ebops_trace_batch(cfg))) and compares
initial_ebops with the reference. On a healthy stack this integer is deterministic: CPU and the anchor's
GPU pod on c5825 both give 11,559,681 (arm A s1) and 11,295,521 (arm A s2) on the anchor cache
/data/chang-n64-20260926 (REGRESSION_TICKET.md §1). Node c6017 gave 1.4M-8.3M, different per process.

Prints `FINGERPRINT <value> expected <ref> <run>`, then `FINGERPRINT_OK` or
`GPU_FINGERPRINT_MISMATCH <value>` and exits 9. Exit 8: no GPU visible (without --allow-cpu).
--env-report prints the driver, GPU, TF/CUDA/cuDNN build, python and `pip freeze` first
(package list only; no environment variable is printed). The integer is a check, never a result.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Import the tree on PYTHONPATH, never this script's own directory (the Delta code dir holds an
# unpatched newmods/; the gate_cpu.py shadowing finding, decisions.md 2026-09-28).
HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != HERE]

REFERENCE = {   # initial_ebops on the anchor cache; CPU = anchor GPU c5825 (REGRESSION_TICKET.md §1)
    'delta0926-w2-rep-a-t350000-s1': 11559681,
    'delta0926-w2-rep-a-t350000-s2': 11295521,
    'chang0926-a-n64-s1': 11559681,
    'chang0926-a-n64-s2': 11295521,
}
DEFAULT_RUN = 'delta0926-w2-rep-a-t350000-s1'
ANCHOR_DATA_ROOT = '/data/chang-n64-20260926'
EXIT_NO_GPU, EXIT_MISMATCH = 8, 9


def sh(cmd):
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return (out.stdout + out.stderr).rstrip()
    except Exception as exc:   # report and continue: the report is diagnostic only
        return f'<{cmd!r} failed: {exc}>'


def env_report():
    print('ENV_REPORT_BEGIN', flush=True)
    print('HOSTNAME_NODE', os.environ.get('NODE_NAME', '<NODE_NAME unset>'), flush=True)
    print(sh('nvidia-smi --query-gpu=name,uuid,serial,driver_version,memory.total,ecc.mode.current '
             '--format=csv,noheader'), flush=True)
    print(sh('nvidia-smi -q | grep -E "Driver Version|CUDA Version|Volatile|Retired|Remapped|Pending|'
             'Single Bit|Double Bit|Uncorr|Corr"'), flush=True)
    print(sh('cat /proc/driver/nvidia/version'), flush=True)
    print('PYTHON', sys.version.replace('\n', ' '), flush=True)
    import tensorflow as tf
    import keras
    print('TF', tf.__version__, 'KERAS', keras.__version__, flush=True)
    print('TF_BUILD_INFO', json.dumps(dict(tf.sysconfig.get_build_info()), sort_keys=True, default=str), flush=True)
    print('PIP_FREEZE_BEGIN', flush=True)
    print(sh(f'{sys.executable} -m pip freeze --all'), flush=True)
    print('PIP_FREEZE_END', flush=True)
    print('ENV_REPORT_END', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', default=DEFAULT_RUN, help='index.json row name (default rep-A s1)')
    ap.add_argument('--expect', type=int, help='reference initial_ebops (default: the table above)')
    ap.add_argument('--data-root', type=Path, default=Path(ANCHOR_DATA_ROOT),
                    help='the anchor cache the reference was taken on (never a pack data_root)')
    ap.add_argument('--campaign-dir', type=Path, default=Path(os.environ.get('BNJ_CAMPAIGN_DIR', '.')))
    ap.add_argument('--env-report', action='store_true')
    ap.add_argument('--allow-cpu', action='store_true', help='CPU test only; a pod never passes this')
    args = ap.parse_args()
    expect = args.expect if args.expect is not None else REFERENCE[args.run]

    if args.env_report:
        env_report()
    import run_engram
    ablation, _ = run_engram.runtime()
    print('FINGERPRINT_TREE', Path(run_engram.__file__).resolve().parent, flush=True)
    import keras
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)   # as run_study.train
    assert not tf.config.experimental.tensor_float_32_execution_enabled()
    gpus = tf.config.list_physical_devices('GPU')
    print('FINGERPRINT_DEVICES', [g.name for g in gpus] or 'CPU-only', flush=True)
    if not gpus and not args.allow_cpu:
        print('GPU_FINGERPRINT_NO_GPU', flush=True)
        return EXIT_NO_GPU

    rows = json.loads((args.campaign_dir / 'index.json').read_text())['runs']
    row = [r for r in rows if r['name'] == args.run]
    assert len(row) == 1, f'{args.run}: {len(row)} rows in {args.campaign_dir}/index.json'
    cfg = json.loads((args.campaign_dir / 'configs' / row[0]['file']).read_text())
    run_engram.validate_cfg(cfg)
    arrays, info = run_engram.load_cache(args.data_root / f"n{cfg['arch']['n_part']}" / 'data', cfg)
    xt = arrays[0]
    # ablation.run_training, fresh start (no checkpoint): same calls, same order
    ablation.apply_keras_compat()
    seed = cfg['experiment']['seed']
    keras.utils.set_random_seed(seed)
    model, _ = run_engram.builder_for(info)(cfg, xt[:4096], seed)
    if hasattr(ablation, 'delta_optimizer_for'):
        ablation.delta_optimizer_for(cfg, model)
    else:   # pre-Delta anchor tree
        ablation.optimizer_for(cfg, model)
    initial = ablation.compute_ebops(model, ablation.ebops_trace_sample(cfg, xt),
                                     batch_size=ablation.ebops_trace_batch(cfg))
    value = int(initial['total'])
    print(f'FINGERPRINT {value} expected {expect} {args.run}', flush=True)
    if value != expect:
        print(f'GPU_FINGERPRINT_MISMATCH {value}', flush=True)
        return EXIT_MISMATCH
    print('FINGERPRINT_OK', args.run, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
