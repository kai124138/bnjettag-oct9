#!/usr/bin/env python3
"""Compare repro-chang Pareto checkpoints against arXiv 2510.24784 Table 1 / Fig. 2.

Training checkpoints (from the NRP jobs in code/jobs/training/repro-chang/) encode their
metrics in filenames: epoch=E-val_acc=A-train_acc=T-ebops=B-val_loss=L.keras. The paper's
Table 1 is iso-EBOPs at a shared 350k training target, so the comparable point on each of
our fronts is the max-val_acc checkpoint with ebops <= 350k (reported alongside the
unconstrained best). Accuracy here is VALIDATION accuracy from training; the paper's
Table 1 accuracy is on the 260k test set — final numbers must come from run_test.py on
the test split before anything is reported (verify-roc discipline).

Targets transcribed in docs/literature/jet-tagging-transformers/
2510.24784_replication-targets_hgq2-examples.md. Deltas repo-vs-paper (attach to every
comparison): xfm h=2 vs "single head"; xfmt = post-paper LUT/QDenseT Linformer k=4;
open-loop beta schedule vs claimed PID.
"""

import argparse
import json
import re
from pathlib import Path

EBOPS_TARGET = 350_000  # shared training target, 2510.24784 section 3

# Table 1 (accuracy %, test set) + Fig. 2 macro-OvR AUC (our arithmetic mean of the
# five per-class values; the paper states no macro AUC).
PAPER = {
    ('xfm', 8): {'acc': 66.3, 'macro_auc': 0.8970},
    ('xfm', 16): {'acc': 72.3, 'macro_auc': 0.9230},
    ('xfm', 32): {'acc': 77.0, 'macro_auc': 0.9430},
    ('xfm', 64): {'acc': 77.9, 'macro_auc': 0.9428},  # disqualified: attention collapses (section 3)
    ('xfmt', 8): {'acc': 66.3, 'macro_auc': 0.8970},
    ('xfmt', 16): {'acc': 72.8, 'macro_auc': 0.9256},
    ('xfmt', 32): {'acc': 78.4, 'macro_auc': 0.9484},
    ('xfmt', 64): {'acc': 79.8, 'macro_auc': 0.9532},
}

CKPT_RE = re.compile(
    r'epoch=(?P<epoch>\d+)-val_acc=(?P<val_acc>[\d.]+)-train_acc=(?P<train_acc>[\d.]+)'
    r'-ebops=(?P<ebops>[\d.]+)-val_loss=(?P<val_loss>[\d.]+)\.keras$'
)


def front(ckpt_dir: Path):
    pts = []
    for f in ckpt_dir.glob('*.keras'):
        m = CKPT_RE.search(f.name)
        if m:
            pts.append({'file': f.name, 'epoch': int(m['epoch']), 'val_acc': float(m['val_acc']),
                        'ebops': float(m['ebops']), 'val_loss': float(m['val_loss'])})
    return sorted(pts, key=lambda p: p['ebops'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input', required=True,
                    help='root dir holding one subdir per run, named <model>-n<N> (e.g. xfm-n32)')
    ap.add_argument('-o', '--output', default=None, help='write the table as .md and .json here')
    args = ap.parse_args()

    rows = []
    for d in sorted(Path(args.input).iterdir()):
        m = re.fullmatch(r'(xfm|xfmt)-n(\d+)', d.name)
        if not (m and d.is_dir()):
            continue
        model, n = m[1], int(m[2])
        pts = front(d)
        if not pts:
            continue
        best = max(pts, key=lambda p: p['val_acc'])
        admitted = [p for p in pts if p['ebops'] <= EBOPS_TARGET]
        iso = max(admitted, key=lambda p: p['val_acc']) if admitted else None
        paper = PAPER.get((model, n), {})
        rows.append({
            'model': model, 'n': n, 'n_ckpts': len(pts),
            'iso350k_val_acc': round(iso['val_acc'] * 100, 2) if iso else None,
            'iso350k_ebops': iso['ebops'] if iso else None,
            'iso350k_file': iso['file'] if iso else None,
            'best_val_acc': round(best['val_acc'] * 100, 2), 'best_ebops': best['ebops'],
            'paper_test_acc': paper.get('acc'), 'paper_macro_auc': paper.get('macro_auc'),
            'gap_iso_vs_paper': round(iso['val_acc'] * 100 - paper['acc'], 2) if iso and paper else None,
        })

    hdr = ('| model | N | ckpts | ours val_acc@<=350k EBOPs | EBOPs | ours best val_acc | paper test acc | gap (val-test!) |\n'
           '|---|---|---|---|---|---|---|---|\n')
    lines = ''.join(
        f"| {r['model']} | {r['n']} | {r['n_ckpts']} | {r['iso350k_val_acc']} | {r['iso350k_ebops']} "
        f"| {r['best_val_acc']} | {r['paper_test_acc']} | {r['gap_iso_vs_paper']} |\n"
        for r in rows)
    caveat = ('\nCaveats: ours = VALIDATION acc (10% split), paper = TEST acc (260k); repo!=paper '
              'deltas apply (see module docstring). Final comparison requires run_test.py on the test set.\n')
    print(hdr + lines + caveat)
    if args.output:
        out = Path(args.output)
        out.with_suffix('.md').write_text('# repro-chang vs arXiv 2510.24784\n\n' + hdr + lines + caveat)
        out.with_suffix('.json').write_text(json.dumps(rows, indent=2))
        print('wrote', out.with_suffix('.md'), out.with_suffix('.json'))


if __name__ == '__main__':
    main()
