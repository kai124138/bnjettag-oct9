#!/usr/bin/env python3
"""User-run, lab-only inventory/selected export and verified import. No network or deletion."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import io
import sys
import run_handoff as safety

BINARY = {'.h5', '.hdf5', '.npy', '.npz', '.keras', '.onnx', '.safetensors',
          '.pt', '.pth', '.png', '.jpg', '.jpeg', '.svg', '.pdf'}
TEXT = safety.TEXT_EXT | {'.log', '.tex', '.bib', '.ipynb'}
RESERVED = 'LAB_TRANSFER_MANIFEST.json'


def content_path(relative):
    safety.safe_name(relative)
    safety.need(relative.casefold() != RESERVED.casefold(), 'reserved transfer metadata path')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def eligible(root, relative):
    content_path(relative)
    path = root / relative
    safety.need(path.resolve().is_relative_to(root.resolve()), 'path escapes selected lab root')
    for part in [path, *path.parents]:
        if part == root:
            break
        safety.need(not part.is_symlink(), 'symlinks are excluded')
    safety.need(path.is_file(), 'not a regular file')
    ext = path.suffix.lower()
    safety.need(ext in BINARY | TEXT, 'opaque archive/unsupported type; review separately')
    if ext in TEXT:
        safety.need(path.stat().st_size <= 16 * 1024 * 1024, 'large text needs separate review')
        content = path.read_bytes()
        safety.scan_text(content)
        if ext in ('.json', '.ipynb'):
            safety.no_inline_secrets(json.loads(content))
    return path


def inventory(root, includes, destination):
    root = Path(root).resolve()
    safety.need(root.is_dir(), 'lab root missing')
    rows, excluded, visited = [], [], set()
    for include in includes:
        safety.safe_name(include)
        start = root / include
        safety.need(start.exists(), 'selected lab path missing: ' + include)
        safety.need(not start.is_symlink(), 'selected symlink directory is excluded')
        candidates = [start] if start.is_file() else []
        if start.is_dir():
            for current, dirs, files in os.walk(start, followlinks=False):
                for name in list(dirs):
                    path = Path(current) / name
                    try:
                        safety.safe_name(path.relative_to(root).as_posix())
                        safety.need(not path.is_symlink(), 'symlink directory excluded')
                    except ValueError:
                        dirs.remove(name)
                candidates.extend(Path(current) / name for name in files)
        for path in candidates:
            if path.is_dir() and not path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            if relative in visited:
                continue
            visited.add(relative)
            try:
                path = eligible(root, relative)
                rows.append({'path':relative, 'bytes':path.stat().st_size, 'sha256':digest(path)})
            except (ValueError, OSError) as exc:
                excluded.append({'path':relative, 'reason':str(exc)})
    result = {'schema':1, 'files':sorted(rows,key=lambda x:x['path']),
              'excluded':sorted(excluded,key=lambda x:x['path'])}
    with Path(destination).open('xb') as f:
        f.write(safety.encoded(result))
    print(json.dumps({'eligible_files':len(rows),'eligible_bytes':sum(x['bytes'] for x in rows),
                      'excluded_files':len(excluded),'inventory':str(destination)}))
    return result


def pack(root, inventory_path, selection_path, destination):
    root = Path(root).resolve()
    manifest = safety.read_json(inventory_path)
    choice = safety.read_json(selection_path)
    safety.need(isinstance(choice,list) and choice and len(choice)==len(set(choice)), 'selection must be unique path list')
    by_name = {x['path']:x for x in manifest['files']}
    selected=[]
    for name in choice:
        safety.need(name in by_name, 'selection not in eligible inventory')
        path=eligible(root,name);entry=by_name[name]
        safety.need(path.stat().st_size==entry['bytes'] and digest(path)==entry['sha256'], 'changed file; inventory again')
        selected.append(entry)
    # Creation is exclusive, no replacing any existing archive. Source is never changed/deleted.
    with Path(destination).open('xb') as output:
        with tarfile.open(fileobj=output,mode='w|gz') as archive:
            data=safety.encoded({'schema':1,'files':selected})
            item=tarfile.TarInfo('LAB_TRANSFER_MANIFEST.json');item.size=len(data)
            archive.addfile(item,io.BytesIO(data))
            for entry in selected:
                path=eligible(root,entry['path'])
                item=tarfile.TarInfo('files/'+entry['path']);item.size=entry['bytes'];item.mode=0o600
                with path.open('rb') as f: archive.addfile(item,f)
    # Catch source races while archiving before advising any transfer.
    verify(destination, None)
    print(json.dumps({'archive':str(destination),'bytes':Path(destination).stat().st_size,
                      'sha256':digest(destination),'files':len(selected)}))


def verify(archive_path, destination, expected_sha=None):
    if expected_sha:
        safety.need(digest(archive_path)==expected_sha, 'archive SHA-256 mismatch')
    dest=Path(destination) if destination else None
    safety.need(dest is None or not dest.exists(), 'destination exists; never overwrite lab files')
    temp=None
    if dest:
        dest.parent.mkdir(parents=True,exist_ok=True)
        temp=Path(tempfile.mkdtemp(prefix='.lab-import-',dir=dest.parent))
    try:
        with tarfile.open(archive_path,'r:gz') as archive:
            members=archive.getmembers()
            names=[m.name for m in members]
            safety.need(len(names)==len(set(names)), 'duplicate archive member')
            for m in members:
                safety.safe_name(m.name)
                safety.need(m.isfile(), 'non-regular archive member')
            info=archive.getmember('LAB_TRANSFER_MANIFEST.json')
            safety.need(info.size<=8*1024*1024, 'oversized transfer manifest')
            manifest=json.load(archive.extractfile(info))
            safety.need(manifest.get('schema')==1, 'unknown transfer schema')
            entries=manifest['files']
            paths=[e['path'] for e in entries]
            safety.need(len(paths)==len(set(paths)), 'duplicate manifest path')
            safety.need(set(names)=={'LAB_TRANSFER_MANIFEST.json'}|{'files/'+p for p in paths},'manifest/archive membership mismatch')
            for e in entries:
                content_path(e['path'])
                member=archive.getmember('files/'+e['path'])
                safety.need(member.size==e['bytes'], 'archive size mismatch')
                h=hashlib.sha256();target=None
                if temp:
                    path=temp/e['path'];path.parent.mkdir(parents=True,exist_ok=True);target=path.open('xb')
                try:
                    stream=archive.extractfile(member)
                    for block in iter(lambda:stream.read(1024*1024),b''):
                        h.update(block)
                        if target:target.write(block)
                finally:
                    if target:target.close()
                safety.need(h.hexdigest()==e['sha256'], 'file checksum mismatch')
                if temp:eligible(temp,e['path'])
        if temp:
            (temp/'LAB_TRANSFER_MANIFEST.json').write_bytes(safety.encoded(manifest))
            temp.rename(dest);temp=None
        return manifest
    finally:
        if temp and temp.exists():shutil.rmtree(temp)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    inv=sub.add_parser('inventory');inv.add_argument('--root',required=True);inv.add_argument('--include',action='append',required=True);inv.add_argument('--out',required=True)
    arc=sub.add_parser('pack');arc.add_argument('--root',required=True);arc.add_argument('--inventory',required=True);arc.add_argument('--selection',required=True);arc.add_argument('--out',required=True)
    check=sub.add_parser('verify');check.add_argument('--archive',required=True);check.add_argument('--out');check.add_argument('--sha256')
    args=parser.parse_args()
    try:
        if args.command=='inventory':inventory(args.root,args.include,args.out)
        elif args.command=='pack':pack(args.root,args.inventory,args.selection,args.out)
        else:
            value=verify(args.archive,args.out,args.sha256);print('VERIFIED',len(value['files']),'files')
    except (ValueError,OSError,KeyError,TypeError,tarfile.TarError) as exc:
        print('TRANSFER_BLOCKED:',str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':sys.exit(main())
