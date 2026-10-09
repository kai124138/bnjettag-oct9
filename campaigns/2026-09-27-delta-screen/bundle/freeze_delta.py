#!/usr/bin/env python3
"""Freeze the Delta wave-2 code bundle (ConfigMap payload) for campaigns/2026-09-27-delta-screen.

    python3 campaigns/2026-09-27-delta-screen/bundle/freeze_delta.py [--tree <apply_anchor build>/code]
        [--packs-dir <product-specific manifest directory>] [--out-dir <new bundle directory>]

Without --tree it runs `campaigns/2026-09-26-delta/code/apply_anchor.sh` into a fresh temporary
directory (anchor bundle 42abed4b, sha-checked by the script; patches-anchor/0001-0038; newmods).
Never submits anything, never edits the Delta code directory or the Job manifests.

Payload (tarball members under code/):
    code/**                          the apply_anchor.sh tree, unchanged (anchor 42abed4b + Delta series)
    code/campaigns/delta0926/        BNJ_CAMPAIGN_DIR of every Delta Job (WIRING.md "Launch path")
        index.json                   byte-identical to code/configs/index.json (582 rows; the packs pin its
                                     sha256 and run_pack launches by row position)
        configs/W2/*.json            the 312 wave-2 configs only (W3 and prereq rows point at files that are
                                     NOT shipped: never run `run_study.py preflight`, which iterates all rows)
        delta_canary_packs.json, delta_w2_t0_packs.json, delta_w2_cells_packs.json   (PLANNING packs)
        canary_k.py                  the canary's K readout
        fingerprint_check.py         PREFLIGHT gate 15 (2026-09-28): every Delta pod, before any arm

Deterministic in the same way as the anchor's manifests/freeze.py (PAX, mtime/uid/gid 0, sorted
members, gzip mtime 0 level 9, __pycache__/.pytest_cache/.DS_Store skipped).

Writes beside this file: delta-code.tar.gz, configmap.json (kai-delta0926-code-<sha10>),
bundle-manifest.json (bundle sha, manifest sha re-derived, per-file sha256, sizes).
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DELTA = ROOT / 'campaigns' / '2026-09-26-delta' / 'code'
ANCHOR_SHA = '42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0'
ANCHOR_CONFIGMAP = 'kai-chang0926-code-42abed4b5d'
CAMPAIGN_REL = 'campaigns/delta0926'
PACKS = ('delta_canary_packs.json', 'delta_w2_t0_packs.json', 'delta_w2_cells_packs.json')
KEY = 'hgq2.tar.gz'
SKIP = ('__pycache__', '.pytest_cache', '.DS_Store', '.git')
CM_LIMIT = 1024 * 1024
RSS_BASE, RSS_SLOPE = 2100, 5


def sha(data):
    return hashlib.sha256(data).hexdigest()


def keep(path, root):
    return not any(part in SKIP for part in path.relative_to(root).parts)


def members(tree, packs_dir):
    out = [(p.relative_to(tree).as_posix(), p) for p in tree.rglob('*') if keep(p, tree)]
    assert not (tree / CAMPAIGN_REL).exists(), 'the anchor tree already has ' + CAMPAIGN_REL
    camp = {CAMPAIGN_REL: None, CAMPAIGN_REL + '/configs': None, CAMPAIGN_REL + '/configs/W2': None}
    camp[CAMPAIGN_REL + '/index.json'] = DELTA / 'configs' / 'index.json'
    for p in sorted((DELTA / 'configs' / 'W2').glob('*.json')):
        camp[f'{CAMPAIGN_REL}/configs/W2/{p.name}'] = p
    for name in PACKS:
        camp[f'{CAMPAIGN_REL}/{name}'] = packs_dir / name
    camp[f'{CAMPAIGN_REL}/canary_k.py'] = DELTA / 'canary_k.py'
    camp[f'{CAMPAIGN_REL}/fingerprint_check.py'] = DELTA / 'fingerprint_check.py'   # PREFLIGHT gate 15
    out += list(camp.items())
    return sorted(out, key=lambda t: t[0])


def build_tarball(entries):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for rel, path in entries:
            info = tarfile.TarInfo('code/' + rel)
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, '', ''
            if path is None or path.is_dir():
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                archive.addfile(info)
            else:
                data = path.read_bytes()
                info.size, info.mode = len(data), 0o755 if path.stat().st_mode & 0o111 else 0o644
                archive.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0, compresslevel=9) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def pinned_versions(tree):
    pins = {}
    for line in (tree / 'requirements-training.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split('==')
            pins[name.split('[')[0].strip()] = version.strip()
    return {k: pins[k] for k in ('tensorflow', 'keras', 'hgq2', 'quantizers', 'numpy', 'scikit-learn')}


def manifest_sha(tree):
    # Same construction as the Delta tree's run_study.manifest(): top level, bnhgq2/ AND newmods/.
    paths = sorted(tree.glob('*.py')) + sorted((tree / 'bnhgq2').glob('*.py')) + sorted((tree / 'newmods').glob('*.py'))
    result = {'files': {str(p.relative_to(tree)): sha(p.read_bytes()) for p in paths},
              'versions': pinned_versions(tree)}
    return sha(json.dumps(result, sort_keys=True).encode()), sorted(result['files'])


def check_campaign(packs_dir):
    index_bytes = (DELTA / 'configs' / 'index.json').read_bytes()
    index_sha = sha(index_bytes)
    rows = json.loads(index_bytes)['runs']
    by_name = {r['name']: r for r in rows}
    assert len(by_name) == len(rows) == 582, len(rows)
    w2 = [r for r in rows if r['file'].startswith('W2/')]
    for r in w2:
        got = sha((DELTA / 'configs' / r['file']).read_bytes())
        assert got == r['config_sha256'], (r['file'], got)
    assert len(list((DELTA / 'configs' / 'W2').glob('*.json'))) == len(w2) == 312, len(w2)
    summary = {}
    for name in PACKS:
        p = json.loads((packs_dir / name).read_text())
        assert p['index_sha256'] == index_sha, (name, p['index_sha256'])
        arms = 0
        for i, pack in enumerate(p['packs']):
            meta = p['pack_meta'][i]
            horizons = set()
            for run in pack:
                row = by_name[run]
                assert row['file'].startswith('W2/'), (name, run, row['file'])
                cfg = json.loads((DELTA / 'configs' / row['file']).read_text())
                horizons.add(cfg['train']['epochs'])
                arms += 1
            assert len(horizons) == 1, (name, i, horizons)            # a pack never mixes horizons
            h = horizons.pop()
            assert meta['rss_gate_limit_mb'] == RSS_BASE + RSS_SLOPE * h, (name, i, meta['rss_gate_limit_mb'], h)
        summary[name] = {'packs': len(p['packs']), 'arms': arms, 'planning': p.get('planning'),
                         'sha256': sha((packs_dir / name).read_bytes())}
    return index_sha, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', type=Path, help='an apply_anchor.sh build dir/code (default: build one now)')
    ap.add_argument('--packs-dir', type=Path, default=DELTA / 'manifests',
                    help='product-specific packs from manifest_wave2.py --out; default is the historical directory')
    ap.add_argument('--out-dir', type=Path, default=HERE,
                    help='write the ConfigMap and bundle here; use a separate directory for each candidate')
    args = ap.parse_args()
    packs_dir = args.packs_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = None
    if args.tree is None:
        tmp = tempfile.TemporaryDirectory()
        build = Path(tmp.name) / 'build'
        log = subprocess.run(['bash', str(DELTA / 'apply_anchor.sh'), str(build)], check=True,
                             capture_output=True, text=True).stdout
        assert f'ANCHOR_BUNDLE_SHA_OK {ANCHOR_SHA}' in log and 'APPLY_ANCHOR_ALL_PASS' in log
        assert log.count('APPLIED ') == 38, log.count('APPLIED ')
        tree = build / 'code'
    else:
        tree = args.tree.resolve()
    index_sha, packs = check_campaign(packs_dir)
    entries = members(tree, packs_dir)
    data = build_tarball(entries)
    bundle = sha(data)
    b64 = base64.b64encode(data).decode()
    assert len(b64) < CM_LIMIT, f'base64 payload {len(b64)} bytes >= 1 MiB: split the payload'
    msha, mfiles = manifest_sha(tree)
    name = 'kai-delta0926-code-' + bundle[:10]
    files = {rel: {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}
             for rel, p in entries if p is not None and p.is_file()}
    (out_dir / 'delta-code.tar.gz').write_bytes(data)
    cm = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
          'metadata': {'name': name, 'namespace': 'cms-ml',
                       'labels': {'user': 'kai', 'campaign': 'delta-20260927'},
                       'annotations': {'bnjettag.io/bundle-sha256': bundle, 'bnjettag.io/manifest-sha256': msha,
                                       'bnjettag.io/anchor-bundle-sha256': ANCHOR_SHA}},
          'binaryData': {KEY: b64}}
    (out_dir / 'configmap.json').write_text(json.dumps(cm, indent=1) + '\n')
    man = {'bundle_sha256': bundle, 'manifest_sha256': msha, 'configmap': name, 'key': KEY,
           'bytes': len(data), 'base64_bytes': len(b64), 'configmap_limit_bytes': CM_LIMIT,
           'n_files': len(files), 'anchor_bundle_sha256': ANCHOR_SHA, 'anchor_configmap': ANCHOR_CONFIGMAP,
           'series': 'campaigns/2026-09-26-delta/code/patches-anchor/0001-0038 + newmods/ (apply_anchor.sh)',
           'campaign_dir': '/work/code/' + CAMPAIGN_REL, 'index_sha256': index_sha, 'packs': packs,
           'shipped_configs': 'configs/W2 only (312); index rows for W3 (268) and prereq (2) name files not shipped',
           'manifest_files': mfiles, 'files': files}
    (out_dir / 'bundle-manifest.json').write_text(json.dumps(man, indent=1, sort_keys=True) + '\n')
    print('BUNDLE_SHA256', bundle)
    print('BUNDLE_BYTES', len(data), 'BASE64_BYTES', len(b64), 'LIMIT', CM_LIMIT, 'FILES', len(files))
    print('MANIFEST_SHA256_REDERIVED', msha)
    print('CONFIGMAP', name)
    print('INDEX_SHA256', index_sha, 'PACKS', json.dumps({k: (v['packs'], v['arms']) for k, v in packs.items()}))
    print('FREEZE_DELTA_DONE')


if __name__ == '__main__':
    main()
