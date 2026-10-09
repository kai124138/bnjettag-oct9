#!/usr/bin/env python3
"""Re-derive code/tree for the pilot program (round 1) from the immutable historical Chang payload.

python3 campaigns/2026-10-05-pilot-program/build_tree.py [--out DIR]

1. Decode `hgq2.tar.gz` from ../2026-09-26-training-batch/manifests/configmap-42abed4b.json and
   require SHA-256 42abed4b… (patches 0001-0031). Read only.
2. `git apply`, in the order of patches/PATCHES.json, each patch with its SHA-256 asserted: 0032 and
   0033 (byte copies of the option-(c) patches, bundle 6919462c), 0034 (test env), 0036 and 0037 (byte
   copies of dev/patches: NB arm, attention bit floor), then 0035 (pilot configs), 0038 (W&B stages),
   0039 (readout), 0040 (gate checks, NB pairing), 0041 (validate_cfg accepts NB).
3. `diff -r` the result against code/tree; prints TREE_MATCHES on success.
"""
import argparse
import base64
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '2026-09-26-training-batch' / 'manifests' / 'configmap-42abed4b.json'
BUNDLE = '42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0'
PATCHES_JSON = HERE / 'patches' / 'PATCHES.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    patches = json.loads(PATCHES_JSON.read_text())['order']
    payload = base64.b64decode(json.loads(SOURCE.read_bytes())['binaryData']['hgq2.tar.gz'])
    assert hashlib.sha256(payload).hexdigest() == BUNDLE
    out = args.out or Path(tempfile.mkdtemp(prefix='pilot1005-tree-'))
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        archive.extractall(out, filter='data')
    code = out / 'code'
    for entry in patches:
        path = HERE / 'patches' / entry['file']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry['sha256'], (entry['file'], digest)
        subprocess.run(['git', 'apply', '--whitespace=nowarn', str(path)], cwd=code, check=True)
        print('APPLIED', entry['file'], digest)
    diff = subprocess.run(['diff', '-r', '-x', '__pycache__', '-x', '.pytest_cache', str(code), str(HERE / 'code' / 'tree')])
    if diff.returncode:
        sys.exit('TREE_MISMATCH')
    print('TREE_MATCHES', code)


if __name__ == '__main__':
    main()
