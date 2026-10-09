#!/usr/bin/env python3
"""Traced 0-bit floor per arch/quant signature of the generated Delta configs -> floors_delta.json.

    code/apply_anchor.sh <dir>
    PYTHONPATH=<dir>/code tests_patches/pyenv.sh code/trace_floors_delta.py --index <gen>/index.json

experiment.nondegenerate.zero_floor_ebops is read at run time by the [ND] feasibility rule
(ablation.py: feasible = EBOPs <= target AND EBOPs - zero_floor > 0 AND accuracy > p_maj + 5 SE),
so a cell whose arch or quant section differs from its anchor arm needs its own floor. This runs
the anchor's own tool, static_floor.floors(cfg, with_attn_rule=False)['zero']['total'] (the call
the anchor's cpu_gate.py:106-111 uses to re-trace its arms), once per floor_signature (sha256 of
the arch and quant sections, the anchor's generate.py:135), on the apply_anchor.sh tree (Delta
patches applied). CPU, synthetic standard-normal sample n = 256, seed 0; a structural trace, not
a result.

Self-check first: the anchor arms A and A07-350 (seed 1, unmodified bundle configs) must
re-trace to their stored zero_floor_ebops, else nothing is written.

arch.body other than the transformer (Deep Sets, M006): static_floor.floors builds
qat.build_qat_model only, so these are built through run_engram.builder_for (the runner's path,
patched newmods/deepsets.py) and priced with static_floor.set_floor(model, 'zero', sample); the
self-check runs both paths on arms A and A07-350 and requires equal floors.
Not traced (recorded with the reason, the generator flags the cells floor_untraced and the packer
leaves them out): quant.weight hgq_learnable (learnable weight widths), and any config whose build
the tree refuses. Modules must come from the applied tree (PYTHONPATH), never from this directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

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


def _load_generate_delta():
    import importlib.util
    spec = importlib.util.spec_from_file_location('generate_delta', HERE / 'generate_delta.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def not_traceable(cfg):
    if cfg['quant'].get('weight') == 'hgq_learnable':
        return 'quant.weight hgq_learnable: learnable weight widths; static_floor holds weights fixed'
    return None


def main(argv=None):
    gd = _load_generate_delta()
    floor_signature, AnchorBase = gd.floor_signature, gd.AnchorBase
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', type=Path, required=True, help='index.json of a generate_delta.py run')
    ap.add_argument('--out', type=Path, default=HERE / 'floors_delta.json')
    ap.add_argument('--tree-label', required=True, help='e.g. apply_anchor.sh 77f1ca4e + patches-anchor/0001-0038')
    ap.add_argument('--reuse', type=Path, help='earlier floors_delta.json from the same tree: keep its traced entries')
    args = ap.parse_args(argv)
    import run_engram
    run_engram.runtime()
    from static_floor import floors
    spec = json.loads((HERE / 'anchor_arms.json').read_text())
    base = AnchorBase(spec)

    def trace_builder(cfg):
        """Zero floor through the runner's own builder (run_engram.builder_for -> the Delta body
        dispatch, patch 0023) and static_floor.set_floor(model, 'zero', sample) on the same
        synthetic sample floors() uses. Used for arch.body != transformer, which floors() cannot
        build; validated by the self-check on arms A and A07-350 below."""
        import numpy as np
        import keras
        from static_floor import set_floor
        c = json.loads(json.dumps(cfg))
        c.get('experiment', {}).pop('nondegenerate', None)
        A = c['arch']
        sample = np.random.default_rng(0).standard_normal((256, A['n_part'], A['n_feat'])).astype('float32')
        keras.backend.clear_session()
        info = {'input_std': {'mu': [0.0] * A['n_feat'], 'sigma': [1.0] * A['n_feat']}}
        model, _ = run_engram.builder_for(info)(c, sample, 1)
        _assert_tree_modules()
        cost, check = set_floor(model, 'zero', sample)
        return {'zero': {'total': cost['total'], 'width_check': {'n_quantizers': len(check),
                                                                  'all_ok': all(v['ok'] for v in check.values())}},
                'one': {'total': None}, 'parameters': int(model.count_params()), 'method': 'builder_for + set_floor'}

    def trace(cfg):
        if cfg['arch'].get('body', 'transformer') != 'transformer':
            return trace_builder(cfg)
        c = json.loads(json.dumps(cfg))
        c.get('experiment', {}).pop('nondegenerate', None)
        # arch.mask_gated_keys (patch 0036) builds only through run_engram.builder_for (it needs the
        # cache input_std); its KeyPadMask is unbilled and EBOPs are priced from widths, so the
        # floor is traced on the same config with the mask key removed (recorded as `probe`).
        c['arch'].pop('mask_gated_keys', None)
        return floors(c, with_attn_rule=False)

    checks = {}
    for arm in ('A', 'A07-350'):
        cfg, member, _, _ = base.config(arm, 1)
        stored = cfg['experiment']['nondegenerate']['zero_floor_ebops']
        got = trace(cfg)['zero']['total']
        via_builder = trace_builder(cfg)['zero']['total']
        checks[arm] = {'config': member, 'stored': stored, 'retraced': got, 'retraced_via_builder': via_builder,
                       'ok': got == stored == via_builder}
        print('FLOOR_SELFCHECK', arm, 'stored', stored, 'retraced', got, 'via_builder', via_builder,
              'OK' if checks[arm]['ok'] else 'MISMATCH', flush=True)
    if not all(c['ok'] for c in checks.values()):
        print('FLOOR_SELFCHECK_FAILED: nothing written')
        return 1

    ix = json.loads(args.index.read_text())
    root = args.index.parent
    todo = {}
    for r in ix['runs']:
        if r.get('file') and r.get('floor') and r['floor'].get('signature') and \
                r['floor']['source'].startswith('UNTRACED') and r['floor']['signature'] not in todo:
            todo[r['floor']['signature']] = r
    out = {}
    if args.reuse and args.reuse.exists():
        old = json.loads(args.reuse.read_text())
        assert old['tree'] == args.tree_label, (old['tree'], args.tree_label)
        out = {k: v for k, v in old['signatures'].items() if v.get('zero') is not None}
        print('FLOORS_REUSED', len(out), flush=True)
    t0 = time.perf_counter()
    for sig, r in sorted(todo.items(), key=lambda kv: kv[1]['run_id']):
        if sig in out:
            continue
        cfg = json.loads((root / r['file']).read_text())
        assert floor_signature(cfg) == sig, r['file']
        why = not_traceable(cfg)
        entry = {'config': r['file'], 'entry': r['id'], 'base_arm': r['base_arm'],
                 'base_floor': r['floor']['value']}
        if cfg['arch'].get('mask_gated_keys'):
            entry['probe'] = 'arch.mask_gated_keys removed for the trace (0036 KeyPadMask unbilled)'
        if why:
            entry.update(zero=None, error=why)
            print('FLOOR_NOT_TRACED', r['id'], r['base_arm'], why, flush=True)
        else:
            s = time.perf_counter()
            try:
                res = trace(cfg)
                entry.update(zero=int(res['zero']['total']), one=res['one']['total'] and int(res['one']['total']),
                             method=res.get('method', 'static_floor.floors'),
                             parameters=res['parameters'], width_check=res['zero'].get('width_check'),
                             seconds=round(time.perf_counter() - s, 2))
                print('FLOOR', r['id'], r['base_arm'], 'zero', entry['zero'], 'one', entry['one'],
                      'base', entry['base_floor'], f"{entry['seconds']}s", flush=True)
            except Exception as e:     # recorded, never swallowed silently
                entry.update(zero=None, error=f'{type(e).__name__}: {e}')
                print('FLOOR_ERROR', r['id'], r['base_arm'], entry['error'][:200], flush=True)
        out[sig] = entry
    args.out.write_text(json.dumps({
        'tool': 'static_floor.floors(cfg, with_attn_rule=False) on the apply_anchor.sh tree',
        'tree': args.tree_label, 'sample': 'synthetic standard normal, n=256, seed=0',
        'self_check': checks, 'index_sha256': hashlib.sha256(args.index.read_bytes()).hexdigest(),
        'note': 'structural CPU trace, not a result', 'signatures': out}, indent=1) + '\n')
    n_ok = sum(v['zero'] is not None for v in out.values())
    print(f'FLOORS_WRITTEN {n_ok}/{len(out)} traced in {time.perf_counter() - t0:.0f}s -> {args.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
