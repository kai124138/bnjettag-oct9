#!/usr/bin/env python3
"""Re-derive code/tree from the immutable historical Chang payload and the two patches.

python3 campaigns/2026-10-02-chang-option-c/build_tree.py [--out DIR]

1. Decode `hgq2.tar.gz` from ../2026-09-26-training-batch/manifests/configmap-42abed4b.json and
   require SHA-256 42abed4b… (patches 0001-0031 included). Read only; nothing there is written.
2. `git apply` patches/0032 (byte copy of the staged patch, SHA-256 f475c69e…), then patches/0033
   (this amendment).
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
PATCHES = [('0032-option-c-pid-traced-only.patch', 'f475c69e487ff20f66d8d39e45b89f6775b11354d419b81746b01cd7a25508be'),
           ('0033-option-c-amendment.patch', '23536dfec1e700a8831ab13e436881ee1e7142db83e2cdf9b610a9726e05736b')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    payload = base64.b64decode(json.loads(SOURCE.read_bytes())['binaryData']['hgq2.tar.gz'])
    assert hashlib.sha256(payload).hexdigest() == BUNDLE
    out = args.out or Path(tempfile.mkdtemp(prefix='chang1002c-tree-'))
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        archive.extractall(out, filter='data')
    code = out / 'code'
    for name, expected in PATCHES:
        data = (HERE / 'patches' / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        assert expected is None or digest == expected, (name, digest)
        subprocess.run(['git', 'apply', '--whitespace=nowarn', str(HERE / 'patches' / name)], cwd=code, check=True)
        print('APPLIED', name, digest)
    diff = subprocess.run(['diff', '-r', '-x', '__pycache__', '-x', '.pytest_cache', str(code), str(HERE / 'code' / 'tree')])
    if diff.returncode:
        sys.exit('TREE_MISMATCH')
    print('TREE_MATCHES', code)


if __name__ == '__main__':
    main()
