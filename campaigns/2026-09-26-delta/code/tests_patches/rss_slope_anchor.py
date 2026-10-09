"""CPU host-memory slope check on the anchor tree (42abed4b + patches-anchor): does any Delta key
add per-epoch host growth on top of the anchor runner? Brief 2026-09-28 (RSS gate, incident
2026-09-28).

usage: pyenv.sh rss_slope_anchor.py --tree <apply_anchor.sh build>/code --out rss.json
           [--epochs 40] [--only case ...]

Each case is one fresh process-level run of ablation.run_training (the runner's own epoch loop:
[D20] regime-B trace every 10 incl. epoch 0, ValidationReloader, checkpoint cadence 25) on the
anchor arm config (seed 1), synthetic data (512 train / 256 val jets, batch 256, mu 0 sigma 1),
for --epochs epochs. Host RSS (`ablation.host_rss_mb`, phys_footprint on macOS) is read at the
end of every epoch through the runner's epoch_observer hook (which returns nothing, so the logs
are unchanged); slope = least-squares MB/epoch over epochs 5..N-1, as the anchor's gate fits.
The number of live Python objects (gc.get_objects after gc.collect) is recorded too: on macOS
phys_footprint moves in allocator steps of tens of MB, so the object count is the sharper,
allocator-independent signal of per-epoch accumulation. Cases run in separate subprocesses so one case's allocations cannot bleed into the next.

Cases: E and A07-350 without Delta keys (the anchor reference), E and A07-350 with the Delta
always-on keys (experiment.collapse_stop, experiment.accumulator_metric), and on E the
latent-EMA, KD (stub float teacher, per-batch teacher forward) and diag-sign-flips keys.
Deviation (stated): collapse_stop's after_epoch is set past the run (1000 instead of 20) so the
rule is evaluated every epoch but cannot stop a run on random synthetic labels.
CPU and macOS allocator: the numbers are a relative check (Delta case minus its reference), not
a GPU-pod RSS forecast. Nothing here is a result.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ALWAYS_ON = {'experiment__collapse_stop': {'threshold': 0.25, 'patience': 10, 'after_epoch': 1000},
             'experiment__accumulator_metric': True}
CASES = {
    'E-anchor': ('chang0926-a-n64-s1.json', {}),
    'E-always-on': ('chang0926-a-n64-s1.json', ALWAYS_ON),
    'A07-350-anchor': ('chang0926-a07-350-n64-s1.json', {}),
    'A07-350-always-on': ('chang0926-a07-350-n64-s1.json', ALWAYS_ON),
    'E-latent-ema': ('chang0926-a-n64-s1.json', {**ALWAYS_ON, 'experiment__latent_ema_decay': 0.9}),
    'E-kd-stub-teacher': ('chang0926-a-n64-s1.json', {**ALWAYS_ON, 'experiment__distillation': 'STUB'}),
    'E-diag-sign-flips': ('chang0926-a-n64-s1.json', {**ALWAYS_ON, 'experiment__diagnostics': ['sign_flips']}),
}
REFERENCE = {'E-always-on': 'E-anchor', 'A07-350-always-on': 'A07-350-anchor', 'E-latent-ema': 'E-anchor',
             'E-kd-stub-teacher': 'E-anchor', 'E-diag-sign-flips': 'E-anchor'}


def one_case(tree, name, epochs):
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(tree))
    import slug_tests as T
    import run_engram
    ablation, _ = run_engram.runtime()
    import keras
    import tensorflow as tf
    from bnhgq2 import qat
    tf.config.experimental.enable_tensor_float_32_execution(False)
    T.CTX.update(tree=tree, ablation=ablation, keras=keras, qat=qat)
    file, keys = CASES[name]
    cfg = json.loads((tree / 'campaigns' / 'chang0926' / 'configs' / file).read_text())
    cfg['train']['batch'] = 256
    keys = dict(keys)
    if keys.get('experiment__distillation') == 'STUB':
        tag, _ = T.make_teacher('teacher-rss-stub')
        keys['experiment__distillation'] = {'teacher_artifact': tag, 'temperature': 2, 'coefficient': 0.5}
    cfg = T.with_keys(cfg, **keys)
    rss, objs = [], []
    import gc

    def observer(model, sample, epoch):
        gc.collect()
        rss.append(ablation.host_rss_mb())
        objs.append(len(gc.get_objects()))      # deterministic leak signal (allocator-independent)
        return {}
    t0 = time.monotonic()
    state, out, _, _ = T.mini_train(cfg, epochs=epochs, epoch_observer=observer)
    assert state['completed_epochs'] == epochs, state['completed_epochs']
    y = np.asarray(rss[5:], float)
    slope = float(np.polyfit(np.arange(len(y)), y, 1)[0])
    o = np.asarray(objs[5:], float)
    # objects: slope over epochs 5..end, and the net change between the same point of two
    # regime-B trace cycles (end of epoch 20 vs end of epoch N-? with the same phase)
    last = len(objs) - 1 - ((len(objs) - 1 - 20) % 10)
    return {'epochs': epochs, 'rss_mb': rss, 'slope_mb_per_epoch_5_to_end': slope,
            'gc_objects': objs, 'gc_objects_slope_per_epoch_5_to_end': float(np.polyfit(np.arange(len(o)), o, 1)[0]),
            'gc_objects_change_epoch20_to_same_phase': [20, last, objs[last] - objs[20]] if last > 20 else None,
            'rss_first_mb': rss[0], 'rss_last_mb': rss[-1], 'seconds': round(time.monotonic() - t0, 1)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tree', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--epochs', type=int, default=40)
    p.add_argument('--only', nargs='*')
    p.add_argument('--case')           # internal: run one case in this process
    args = p.parse_args()
    if args.case:
        print('RSS_CASE_JSON', json.dumps(one_case(args.tree, args.case, args.epochs)), flush=True)
        return
    results = json.loads(args.out.read_text()) if args.out.exists() else {}
    for name in args.only or list(CASES):
        r = subprocess.run([sys.executable, __file__, '--tree', str(args.tree), '--out', str(args.out),
                            '--epochs', str(args.epochs), '--case', name], capture_output=True, text=True)
        line = next((l for l in r.stdout.splitlines() if l.startswith('RSS_CASE_JSON ')), None)
        if r.returncode or line is None:
            results[name] = {'status': 'FAIL', 'error': (r.stdout + r.stderr)[-2000:]}
            print('RSS_CASE_FAIL', name, flush=True)
        else:
            results[name] = {'status': 'PASS', **json.loads(line.split(' ', 1)[1])}
            print('RSS_CASE', name, 'epochs', results[name]['epochs'], 'slope_mb_per_epoch',
                  f"{results[name]['slope_mb_per_epoch_5_to_end']:.3f}", 'rss_first_last_mb',
                  f"{results[name]['rss_first_mb']:.0f} {results[name]['rss_last_mb']:.0f}",
                  'gc_objects_per_epoch', f"{results[name]['gc_objects_slope_per_epoch_5_to_end']:.1f}",
                  'gc_objects_change', results[name]['gc_objects_change_epoch20_to_same_phase'], flush=True)
        args.out.write_text(json.dumps(results, indent=1, sort_keys=True) + '\n')
    for name, ref in REFERENCE.items():
        if results.get(name, {}).get('status') == 'PASS' and results.get(ref, {}).get('status') == 'PASS':
            d = results[name]['slope_mb_per_epoch_5_to_end'] - results[ref]['slope_mb_per_epoch_5_to_end']
            print('RSS_DELTA_MINUS_REFERENCE', name, 'vs', ref, f'{d:+.3f} MB/epoch', flush=True)
    bad = [k for k in (args.only or CASES) if results[k]['status'] != 'PASS']
    print('RSS_SLOPE_ALL_RAN' if not bad else f'RSS_SLOPE_FAIL {bad}', flush=True)


if __name__ == '__main__':
    main()
