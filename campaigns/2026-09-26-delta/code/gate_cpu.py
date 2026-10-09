#!/usr/bin/env python3
"""CPU build / one-step / save / reload gate for Delta configs. Synthetic inputs; not a result.

    python gate_cpu.py configs/W2/M001-t350000-s1.json [...]     # explicit list
    python gate_cpu.py --index configs/index.json --one-per-entry  # one config per gate-eligible entry
    python gate_cpu.py --index configs/index.json --one-per-arm --results-out gate_results.json
        # one config per (entry, base arm): every architecture a packed cell runs on is built
        # (review C1-v4); --results-out writes the file annotate_index.py and manifest_wave2.py read

Per config, on the runner's own path (apply_anchor.sh tree on PYTHONPATH, run_engram.runtime()):
  1. run_engram.validate_cfg(cfg); build through run_engram.builder_for(info) (what run_study.train
     hands to ablation.run_training; info carries a synthetic input_std mu 0 / sigma 1, which the
     gated-key mask reads) at seed = experiment.seed, calibrated on a synthetic standard-normal sample;
  2. ablation.binary_gate (exactly two symmetric non-zero values per binary layer);
  3. EBOPs trace (ebops_calc.compute_ebops);
  4. ONE optimizer step: ablation.delta_optimizer_for (the runner's dispatch; Bop for
     train.binary_optimizer bop) with LR = ablation.learning_rate(cfg, 0), qat.set_delta_epoch(cfg, 0),
     then ablation.make_epoch_step over exactly one batch (train.batch rows), finite loss, binary gate
     again. delta_optimizer_for and set_delta_epoch are required: a tree without them fails the gate
     (no silent fallback to Adam);
  5. save -> keras.models.load_model -> logits equal within atol 1e-7 (rtol 0), EBOPs re-trace equal.
     The bundle's own preflight uses 2e-6; if 1e-7 fails, the 2e-6 result is printed beside it and
     the config FAILS (the tolerance is not loosened).
Timings per phase are printed. Pass line: `GATE_PASS <name> params <n> ...`; a config the tree's
validator refuses prints `GATE_REFUSED <name> <validator message>` (not a pass); final line
`GATE_ALL_PASS <k>/<k>` only if every config passed. This is not preflight_final.sh and does not
print PREFLIGHT_ALL_PASS.

Synthetic sizes (stated because they differ from production): calibration/build sample 512 rows
(production: xt[:4096]); EBOPs trace on 32 rows (production: 256); one batch of train.batch rows.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
HERE = Path(__file__).resolve().parent

def _drop_own_dir_from_path():
    """This directory holds the UNPATCHED newmods/ (anchor 0023 patches deepsets.py after the copy);
    Python puts a script's own directory first on sys.path, which would shadow the applied tree's
    newmods. Drop it (and '' when cwd is this directory) so PYTHONPATH=<tree>/code wins."""
    here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or os.getcwd()).resolve() != here]


def _assert_tree_modules():
    """Fail if any imported newmods / bnhgq2 module comes from this directory instead of the tree."""
    here = Path(__file__).resolve().parent
    bad = [m.__name__ for m in list(sys.modules.values())
           if getattr(m, '__file__', None) and m.__name__.split('.')[0] in ('newmods', 'bnhgq2')
           and Path(m.__file__).resolve().is_relative_to(here)]
    if bad:
        raise RuntimeError(f'modules imported from {here}, not the applied tree: {bad}')


_drop_own_dir_from_path()
N_SAMPLE, N_TRACE, TOL, BUNDLE_TOL = 512, 32, 1e-7, 2e-6


def synth(n, n_part, n_feat, n_classes, seed):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, n_part, n_feat)).astype('float32')
    y = np.eye(n_classes, dtype='float32')[rng.integers(0, n_classes, n)]
    return x, y


def gate_one(path, workdir):
    import run_engram
    ablation, _ = run_engram.runtime()
    import keras
    import tensorflow as tf
    from bnhgq2.ebops_calc import compute_ebops
    from bnhgq2 import qat as qat_mod
    tf.config.experimental.enable_tensor_float_32_execution(False)
    keras.backend.clear_session()
    cfg = json.loads(Path(path).read_text())
    A, t = cfg['arch'], {}
    try:
        run_engram.validate_cfg(cfg)
    except ValueError as e:
        return {'config': str(path), 'name': cfg['name'], 'pass': False, 'refused': True, 'error': str(e),
                'timing_s': {}}
    teacher = (cfg['experiment'].get('distillation') or {}).get('teacher_artifact') or cfg['experiment'].get('init_checkpoint')
    if teacher:   # the runner loads the teacher artifact; the gate must not pass a KD / warm-start cell without it
        return {'config': str(path), 'name': cfg['name'], 'pass': False, 'needs_teacher': teacher,
                'error': f'needs prerequisite teacher artifact {teacher!r} (P-T1/P-T2 not trained)', 'timing_s': {}}
    seed = int(cfg['experiment']['seed'])
    batch = int(cfg['train']['batch'])
    x, y = synth(max(N_SAMPLE, batch), A['n_part'], A['n_feat'], A['n_classes'], seed)

    s = time.perf_counter()
    info = {'input_std': {'mu': [0.0] * A['n_feat'], 'sigma': [1.0] * A['n_feat']}}
    model, evidence = run_engram.builder_for(info)(cfg, x[:N_SAMPLE], seed)
    ablation.binary_gate(model, cfg)
    _assert_tree_modules()
    t['build_s'] = time.perf_counter() - s
    params = model.count_params()

    s = time.perf_counter()
    cost0 = compute_ebops(model, x[:N_TRACE])['total']
    t['trace_s'] = time.perf_counter() - s

    s = time.perf_counter()
    if not hasattr(ablation, 'delta_optimizer_for') or not hasattr(qat_mod, 'set_delta_epoch'):
        raise RuntimeError('tree lacks ablation.delta_optimizer_for / qat.set_delta_epoch (Delta series not applied)')
    opt = ablation.delta_optimizer_for(cfg, model)   # the runner's own dispatch (Bop, 0024)
    opt.learning_rate.assign(ablation.learning_rate(cfg, 0))
    # mirror ablation.run_training's step call on whatever this tree provides (patched: 0003, 0011, 0012)
    kwargs, extra = {}, ()
    import inspect
    step_params = inspect.signature(ablation.make_epoch_step).parameters
    if 'input_std' in step_params:   # synthetic data are standardized: mu 0, sigma 1
        kwargs['input_std'] = info['input_std']
    if 'latent_ema' in step_params and cfg['experiment'].get('latent_ema_decay') is not None:
        kwargs['latent_ema'] = ablation.LatentEMA(model, cfg['experiment']['latent_ema_decay'], None)
    qat_mod.set_delta_epoch(cfg, 0)
    if hasattr(ablation, 'reflection_columns') and ablation.reflection_columns(cfg):
        extra = (ablation.reflection_signs(cfg, 0, batch),)
    step = ablation.make_epoch_step(model, opt, x[:batch], y[:batch], cfg, **kwargs)
    totals = step(np.arange(batch, dtype='int32'), False, *extra).numpy()
    if not np.isfinite(totals).all():
        raise RuntimeError(f'non-finite step metrics {totals}')
    ablation.binary_gate(model, cfg)
    t['step_s'] = time.perf_counter() - s

    s = time.perf_counter()
    cost1 = compute_ebops(model, x[:N_TRACE])['total']
    logits = np.asarray(model(x[:64], training=False))
    file = Path(workdir) / (cfg['name'] + '.keras')
    model.save(file)
    loaded = keras.models.load_model(file, compile=False)
    relog = np.asarray(loaded(x[:64], training=False))
    recost = compute_ebops(loaded, x[:N_TRACE])['total']
    t['save_reload_s'] = time.perf_counter() - s
    file.unlink()
    max_abs = float(np.max(np.abs(relog - logits)))
    ok_tol = bool(np.all(np.abs(relog - logits) <= TOL))
    ok_bundle = bool(np.all(np.abs(relog - logits) <= BUNDLE_TOL + BUNDLE_TOL * np.abs(logits)))
    return {'config': str(path), 'name': cfg['name'], 'params': int(params), 'seed': seed,
            'n_part': A['n_part'], 'target': cfg['train']['ebops']['pid']['target_ebops'],
            'initial_ebops_synthetic': cost0, 'ebops_after_step_synthetic': cost1, 'reload_ebops_equal': recost == cost1,
            'step_loss_ce_kd_acc': [float(v) for v in totals], 'reload_max_abs_diff': max_abs,
            'reload_within_1e-7': ok_tol, 'reload_within_bundle_2e-6': ok_bundle,
            'matched_projection_count': evidence.get('matched_projection_count'),
            'optimizer': type(opt).__name__, 'pass': ok_tol and recost == cost1, 'timing_s': t}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('configs', nargs='*')
    ap.add_argument('--index', type=Path)
    ap.add_argument('--one-per-entry', action='store_true')
    ap.add_argument('--one-per-arm', action='store_true', help='one config per (entry, base_arm): seed 1 or the lowest')
    ap.add_argument('--json-out', type=Path)
    ap.add_argument('--results-out', type=Path, help='write gate_results.json (entry, base_arm, config, outcome)')
    ap.add_argument('--tree-label', default='apply_anchor.sh: anchor pilot bundle 77f1ca4e + patches-anchor/0001-00NN + newmods/')
    args = ap.parse_args(argv)
    paths = [Path(p) for p in args.configs]
    if args.index:
        ix = json.loads(args.index.read_text())
        seen, meta = set(), {}
        for r in ix['runs']:
            if not r['gate_eligible'] or not r['file']:
                continue
            key = (r['id'], r['base_arm']) if args.one_per_arm else r['id']
            if (args.one_per_entry or args.one_per_arm) and key in seen:
                continue
            seen.add(key)
            paths.append(args.index.parent / r['file'])
            meta[str(args.index.parent / r['file'])] = {'id': r['id'], 'base_arm': r['base_arm'],
                                                         'name': r['name'], 'wave': r['wave']}
    results, n_pass = [], 0
    with tempfile.TemporaryDirectory() as work:
        for p in paths:
            wall = time.perf_counter()
            try:
                r = gate_one(p, work)
            except Exception as e:  # recorded, never swallowed silently
                r = {'config': str(p), 'pass': False, 'error': f'{type(e).__name__}: {e}'}
            r['wall_s'] = time.perf_counter() - wall
            results.append(r)
            if r.get('needs_teacher'):
                print(f"GATE_NEEDS_TEACHER {r['name']} {r['error']}", flush=True)
            elif r.get('refused'):
                print(f"GATE_REFUSED {r['name']} {r['error']}", flush=True)
            elif r['pass']:
                n_pass += 1
                tt = r['timing_s']
                print(f"GATE_PASS {r['name']} params {r['params']} build {tt['build_s']:.2f}s step {tt['step_s']:.2f}s "
                      f"save_reload {tt['save_reload_s']:.2f}s wall {r['wall_s']:.2f}s max_abs {r['reload_max_abs_diff']:.3g} opt {r['optimizer']}",
                      flush=True)
            else:
                print(f"GATE_FAIL {p} {r.get('error') or json.dumps({k: r[k] for k in ('reload_max_abs_diff', 'reload_within_1e-7', 'reload_within_bundle_2e-6', 'reload_ebops_equal')})}",
                      flush=True)
    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=1) + '\n')
    if args.results_out:
        def outcome(r):
            return ('GATE_NEEDS_TEACHER' if r.get('needs_teacher') else 'GATE_REFUSED' if r.get('refused')
                    else 'GATE_PASS' if r['pass'] else 'GATE_FAIL')
        rows = []
        for r in results:
            m = (meta if args.index else {}).get(r['config'], {})
            rows.append({**m, 'config': str(Path(r['config']).relative_to(args.index.parent)) if args.index else r['config'],
                         'outcome': outcome(r), 'needs_teacher': r.get('needs_teacher'), 'error': r.get('error'),
                         'params': r.get('params'), 'optimizer': r.get('optimizer'),
                         'reload_max_abs_diff': r.get('reload_max_abs_diff'), 'timing_s': r.get('timing_s'),
                         'wall_s': r.get('wall_s')})
        args.results_out.write_text(json.dumps({'tree': args.tree_label,
            'harness': 'gate_cpu.py --index configs/index.json ' + ('--one-per-arm' if args.one_per_arm else '--one-per-entry'),
            'results': rows}, indent=1) + '\n')
    if n_pass == len(results) and results:
        print(f'GATE_ALL_PASS {n_pass}/{len(results)}')
        return 0
    print(f'GATE_SOME_FAILED {n_pass}/{len(results)}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
