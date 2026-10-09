#!/usr/bin/env python3
"""Classify every written Delta config with the applied tree's own strict validator.

    ANCHOR_BUNDLE=<77f1ca4e tar.gz> code/apply_anchor.sh <build-dir>   # anchor + patches-anchor + newmods
    uv run --with numpy==2.5.0 python code/classify_series.py --tree <build-dir>/code
    (--series patches --tree-label ... for the tarball stand-in set, configs-standin/)

The validator (`run_engram.validate_cfg`, which calls `bnhgq2.delta_keys.validate` and its
`strict_keys` refusal of any key no code path reads) is the ground truth, not a slug list.
Rewrites `status` in the index in place:

  ready_on_base               no method patch, validator accepts
  runnable_on_series          validator accepts, the cell needs Delta patches
  refused_by_key              validator refuses, naming a method key and slug  -> series_refusal
  placeholder_pending_anchor  validator refuses naming an anchor key ([A1]/[A2]/[A3]/[A20] ...);
                              on the anchor tree this should not occur (it would mean a base mismatch)

Only ready_on_base and runnable_on_series rows are gate-eligible; manifest_wave2.py further
drops floor_untraced, cache_not_built and teacher-dependent rows from the launch packs.
Needs numpy (run_engram imports it at module level); no TensorFlow import happens here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANCHOR_RE = re.compile(r'anchor \[A\d+\]|train\.py path only')


def parse_refusal(message):
    """(key, reason) from the validator's three message shapes."""
    for pat in (r': config key (\S+) is refused: (.*)$', r': (\S+)=.* is refused: (.*)$',
                r': (\S+) \(([^)]+)\): (.*)$'):
        m = re.search(pat, message)
        if m:
            return m.group(1), ' '.join(m.groups()[1:])
    return None, message


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', type=Path, required=True, help='<build-dir>/code from apply.sh')
    ap.add_argument('--index', type=Path, default=HERE / 'configs' / 'index.json')
    ap.add_argument('--series', default='patches-anchor', choices=('patches-anchor', 'patches'))
    ap.add_argument('--tree-label', default='apply_anchor.sh: anchor pilot bundle 77f1ca4e + patches-anchor/0001-00NN + newmods/')
    args = ap.parse_args(argv)
    sys.path.insert(0, str(args.tree))
    import run_engram                                   # noqa: E402  (the patched tree's)
    from bnhgq2 import delta_keys                       # noqa: E402
    ix = json.loads(args.index.read_text())
    counts = {}
    for row in ix['runs']:
        if not row.get('file'):
            status, refusal = row['status'], None      # never written (error / refused_unfilled)
        else:
            cfg = json.loads((args.index.parent / row['file']).read_text())
            try:
                run_engram.validate_cfg(cfg)
                accepted, refusal = True, None
            except ValueError as e:
                accepted = False
                key, why = parse_refusal(str(e))
                refusal = {'key': key, 'reason': why, 'message': str(e)}
            if accepted:
                if not row['code_changes']:
                    status = 'ready_on_base'
                else:
                    status = 'runnable_on_series'
            elif ANCHOR_RE.search(refusal['reason']):
                status = 'placeholder_pending_anchor'
            else:
                status = 'refused_by_key'
        row['generator_status'] = row.get('generator_status', row['status'])
        row['status'] = status
        row['series_refusal'] = refusal
        row['gate_eligible'] = status in ('ready_on_base', 'runnable_on_series')
        counts[status] = counts.get(status, 0) + 1
    src = Path(delta_keys.__file__).read_bytes()
    ix['series_classification'] = {
        'tree': args.tree_label, 'delta_keys_sha256': hashlib.sha256(src).hexdigest(),
        'patches': sorted(p.name for p in (HERE / args.series).glob('[0-9][0-9][0-9][0-9]-*.patch')),
        'validator': 'run_engram.validate_cfg -> delta_keys.validate -> strict_keys', 'status_counts': counts}
    ix['status_counts'] = counts
    args.index.write_text(json.dumps(ix, indent=1) + '\n')
    print('series status:', counts)
    by = {}
    for r in ix['runs']:
        if r['status'] == 'refused_by_key':
            by.setdefault((r['series_refusal']['key'], r['series_refusal']['reason'][:90]), set()).add(r['id'])
    for (k, why), ids in sorted(by.items(), key=lambda kv: str(kv[0])):
        print(f'REFUSED {k}: {why} :: {",".join(sorted(ids))}')


if __name__ == '__main__':
    main()
