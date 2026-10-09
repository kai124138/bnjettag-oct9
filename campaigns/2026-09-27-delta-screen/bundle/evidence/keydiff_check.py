"""Independent cell-vs-replica key diff for every packed W2 non-replica run (STUDY Arms 'Cell configs':
classes (1) delta.json config_delta/extra_delta, (2) train.epochs, (3) name/experiment.arm/delta_study/
engram_study.question, (4) experiment.nondegenerate.zero_floor_ebops; (5) needs no admission vs a replica).
Run from campaigns/2026-09-26-delta."""
import json, collections
from pathlib import Path
C = Path('code/configs')
delta = json.load(open('delta.json'))
ent = {e['id']: e for e in delta['entries']}
def flat(d, pre=''):
    o = {}
    for k, v in d.items():
        if isinstance(v, dict) and v: o.update(flat(v, pre + k + '.'))
        else: o[pre + k] = v
    return o
rows = json.load(open(C / 'index.json'))['runs']
packed = set()
for f in ('delta_canary_packs.json', 'delta_w2_t0_packs.json', 'delta_w2_cells_packs.json'):
    for pk in json.load(open('code/manifests/' + f))['packs']: packed.update(pk)
reps = {(r['base_arm'], r['seed']): r for r in rows if r['wave'] == 'W2' and r['kind'] == 'drift_replica'}
ident = ('name', 'experiment.arm', 'delta_study', 'engram_study.question', 'train.epochs', 'experiment.nondegenerate.zero_floor_ebops')
extra = collections.Counter(); ex_rows = collections.defaultdict(list); n = 0; kinds = collections.Counter()
for r in rows:
    if r['wave'] != 'W2' or r['kind'] == 'drift_replica' or r['name'] not in packed: continue
    rep = reps[(r['base_arm'], r['seed'])]
    cfg = flat(json.load(open(C / r['file']))); rc = flat(json.load(open(C / rep['file'])))
    e = ent.get(r['id'], {})
    dk = set(flat(e.get('config_delta') or {})) | set(flat(e.get('extra_delta') or {}))
    n += 1; kinds[r['kind']] += 1
    for k in sorted(set(cfg) | set(rc)):
        if cfg.get(k, '<a>') == rc.get(k, '<a>'): continue
        if any(k == x or k.startswith(x + '.') for x in ident): continue
        if any(k == x or k.startswith(x + '.') or x.startswith(k + '.') for x in dk): continue
        extra[k] += 1; ex_rows[k].append(r['name'])
print('KEYDIFF_PACKED_NON_REPLICA_RUNS', n, dict(kinds))
for k, c in extra.items(): print('KEYDIFF_OUTSIDE_STUDY_CLASSES', k, c, ex_rows[k][:3])
print('KEYDIFF_DONE outside_classes', sum(extra.values()))
