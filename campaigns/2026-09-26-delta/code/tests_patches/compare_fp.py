"""Compare two invariance fingerprints field by field; exit 1 on any difference.
usage: python3 compare_fp.py base.json other.json [--subset]
--subset: compare only the configs present in `other` (a partial run)."""
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
subset = '--subset' in sys.argv
bad = 0
for cfg in sorted(set(b) if subset else set(a) | set(b)):
    if cfg not in a or cfg not in b:
        print('MISSING', cfg); bad += 1; continue
    diffs = [k for k in sorted(set(a[cfg]) | set(b[cfg])) if k != 'seconds' and a[cfg].get(k) != b[cfg].get(k)]
    for k in diffs:
        print('DIFF', cfg, k)
    bad += len(diffs)
    print('SAME' if not diffs else 'DIFFERENT', cfg, 'seconds', a[cfg].get('seconds'), b[cfg].get('seconds'))
print('INVARIANCE_GATE_PASS' if not bad else f'INVARIANCE_GATE_FAIL {bad}')
sys.exit(1 if bad else 0)
