"""F2 config diff: every b3fb22c8 pilot config vs the F2 tree, flattened; new configs vs their matched base."""
import json, sys
from pathlib import Path
old_d, new_d = Path(sys.argv[1]), Path(sys.argv[2])
def flat(d, p=''):
    out = {}
    for k, v in d.items():
        key = f'{p}.{k}' if p else k
        out.update(flat(v, key) if isinstance(v, dict) and v else {key: v})
    return out
def diff(a, b):
    fa, fb = flat(a), flat(b)
    return {k: (fa.get(k, '<absent>'), fb.get(k, '<absent>')) for k in sorted(set(fa) | set(fb)) if fa.get(k, '<absent>') != fb.get(k, '<absent>')}
olds = {p.name: json.loads(p.read_text()) for p in sorted(old_d.glob('*.json'))}
news = {p.name: json.loads(p.read_text()) for p in sorted(new_d.glob('*.json'))}
for n in sorted(set(olds) | set(news)):
    if n in olds and n in news:
        print('SAME_NAME', n, json.dumps(diff(olds[n], news[n])))
    elif n in olds:
        print('REMOVED', n)
    else:
        print('ADDED', n)
for new, base in (('pilot1005-h3-e-450k-c-qkv1-s1.json', 'pilot1005-h3-e-350k-c-qkv1-s1.json'),
                  ('pilot1005-ctl-e-unc-c-s1.json', 'pilot1005-h1-e-350k-c-s1.json')):
    print('NEW_VS_MATCHED', new, 'vs', base, json.dumps(diff(news[base], news[new])))
