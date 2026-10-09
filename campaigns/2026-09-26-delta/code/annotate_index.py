#!/usr/bin/env python3
"""Annotate configs/index.json with the CPU gate outcome and the teacher dependency (review B1-v4).

Pipeline (WIRING.md): generate_delta.py -> apply_anchor.sh -> trace_floors_delta.py -> generate_delta.py ->
classify_series.py -> gate_cpu.py --one-per-arm --results-out gate_results.json -> annotate_index.py ->
manifest_wave2.py.

Per row it writes:
  gate        the outcome of the gated config of the same (entry, base_arm) from gate_results.json
              (GATE_PASS / GATE_FAIL / GATE_REFUSED / GATE_NEEDS_TEACHER), or null if that pair
              was not gated (the row is not gate-eligible)
  depends_on  the teacher artifact every KD / warm-start row needs (read from the config itself,
              so rows of non-gated entries are covered too), else absent
and refreshes patch_status from the ledger (code/README.md), so the index never carries a status the
ledger has since changed. Deterministic: same inputs, same bytes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', type=Path, default=HERE / 'configs' / 'index.json')
    ap.add_argument('--gate', type=Path, default=HERE / 'gate_results.json')
    args = ap.parse_args(argv)
    import generate_delta
    ledger = generate_delta.ledger_status()
    ix = json.loads(args.index.read_text())
    gate = json.loads(args.gate.read_text())
    by_pair = {(r['id'], r['base_arm']): r['outcome'] for r in gate['results']}
    n_dep = 0
    for row in ix['runs']:
        row['patch_status'] = {s: ledger.get(s, 'not started') for s in row['code_changes']}
        row['gate'] = by_pair.get((row['id'], row['base_arm']))
        row.pop('gate_v5', None)
        row.pop('depends_on', None)
        if row.get('file'):
            exp = json.loads((args.index.parent / row['file']).read_text())['experiment']
            teacher = (exp.get('distillation') or {}).get('teacher_artifact') or exp.get('init_checkpoint')
            if teacher:
                row['depends_on'] = teacher
                n_dep += 1
    ix.pop('gate_v5', None)
    ix['gate'] = {'source': 'gate_results.json', 'harness': gate['harness'], 'tree': gate['tree'],
                  'pairs_gated': len(by_pair)}
    args.index.write_text(json.dumps(ix, indent=1) + '\n')
    print(f'annotated {len(ix["runs"])} rows; gate pairs {len(by_pair)}; depends_on {n_dep}')


if __name__ == '__main__':
    main()
