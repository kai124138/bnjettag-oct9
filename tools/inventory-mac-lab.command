#!/bin/bash
# User-run only. Inventories one lab directory; never uploads, deletes or installs.
# The helpers are pinned to the independently reviewed run-handoff v1 implementation.
set -euo pipefail
umask 077

if [ "$(uname -s)" != "Darwin" ]; then
  printf '%s\n' 'Stopped: run this script yourself on your Mac, not on the home PC.' >&2
  exit 2
fi
for bnj_tool in python3 scp shasum; do
  if ! command -v "$bnj_tool" >/dev/null 2>&1; then
    printf 'Stopped: %s is not available. Nothing will be installed.\n' "$bnj_tool" >&2
    exit 2
  fi
done

bnj_root='/Users/kaiyamaguchi/Desktop/bnjettag'
python3 - "$bnj_root" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
if not root.is_dir() or root.is_symlink() or root.resolve() != root:
    raise SystemExit('Stopped: the exact lab directory is missing or redirected by a symlink.')
PY

bnj_work="$(mktemp -d "$HOME/bnjettag-inventory.XXXXXX")"
printf 'Local inventory folder: %s\n' "$bnj_work"
printf '%s\n' 'Downloading two checksum-pinned helpers from your home PC. No Mac files are uploaded.'
scp -o StrictHostKeyChecking=yes -P 2222 \
  kaimoe@100.93.120.69:/home/kaimoe/lab/bnjettag/tools/run_handoff.py \
  kaimoe@100.93.120.69:/home/kaimoe/lab/bnjettag/tools/lab_transfer.py \
  "$bnj_work/"

cat > "$bnj_work/SHA256SUMS" <<'CHECKSUMS'
0c34dcb56f8902c8fba92353d105099b5b83bfeef601e4bab600ed235b7fdc2c  run_handoff.py
f694e79bb515df75b67c17a88e856cab52141c3b90af854f54edb17d84a8300d  lab_transfer.py
CHECKSUMS
(cd "$bnj_work" && shasum -a 256 -c SHA256SUMS)

python3 - "$bnj_root" "$bnj_work" <<'PY'
from pathlib import Path
import os
import sys

root, work = map(Path, sys.argv[1:])
if root.resolve() != root or root.is_symlink():
    raise SystemExit('Stopped: lab path changed during helper download.')
sys.path.insert(0, str(work))
import lab_transfer

# Select regular, nonhidden paths before invoking the unchanged reviewed helper.
# This also prunes nested hidden directories without inspecting their contents.
includes = []
for current, dirs, files in os.walk(root, followlinks=False):
    for name in list(dirs):
        path = Path(current) / name
        try:
            if name.startswith('.') or path.is_symlink():
                raise ValueError('excluded directory')
            lab_transfer.safety.safe_name(path.relative_to(root).as_posix())
        except ValueError:
            dirs.remove(name)
    for name in files:
        path = Path(current) / name
        if not name.startswith('.') and not path.is_symlink():
            relative = path.relative_to(root).as_posix()
            try:
                lab_transfer.safety.safe_name(relative)
            except ValueError:
                continue
            includes.append(relative)
if not includes:
    raise SystemExit('Stopped: no eligible top-level lab paths found.')
lab_transfer.inventory(root, sorted(includes), work / 'lab-inventory.json')
print('\nInventory complete. Mac output:', work / 'lab-inventory.json')
print('Helpers and SHA256SUMS are preserved in the same private local folder.')
print('Next: review the inventory locally. Only share it if you choose; select files for a later transfer.')
print('No source files were changed or deleted. No lab contents or inventory were uploaded.')
print('Git history, hidden top-level paths, credentials and excluded/opaque files remain separate review items.')
PY
