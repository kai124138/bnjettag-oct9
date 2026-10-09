#!/usr/bin/env bash
# Rebuild the Delta patched tree from the screen tarball (public code/constituent-study-20260922).
#
#   code/apply.sh <build-dir> [last-patch-number]
#
# Extracts campaigns/2026-09-22-constituent-screen/study-code.tar.gz into <build-dir> after
# checking its sha256, commits the pristine tree in a throwaway git repo inside <build-dir>
# (3-way apply needs the blobs), then applies code/patches/NNNN-<slug>.patch in order with
# `git apply --3way`. The new-files engineer's modules (code/newmods/*.py) are copied into
# <build-dir>/code/newmods/ first (their sha256 printed); patches 0023/0024 import them.
# Optional last-patch-number stops early (e.g. 0006). Prints the sha256 of every .py file of
# the result as a manifest. Never touches a project repository.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
TARBALL="$ROOT/campaigns/2026-09-22-constituent-screen/study-code.tar.gz"
EXPECT=26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45
OUT=${1:?usage: apply.sh <build-dir> [last-patch-number]}
LAST=${2:-9999}

GOT=$(shasum -a 256 "$TARBALL" | cut -d' ' -f1)
[ "$GOT" = "$EXPECT" ] || { echo "TARBALL_SHA_MISMATCH $GOT" >&2; exit 1; }
[ ! -e "$OUT" ] || [ -z "$(ls -A "$OUT")" ] || { echo "build dir $OUT is not empty" >&2; exit 1; }
mkdir -p "$OUT"
tar xzf "$TARBALL" -C "$OUT"
cd "$OUT"
git init -q
git -c user.name=apply -c user.email=apply@localhost add -A
git -c user.name=apply -c user.email=apply@localhost commit -qm "pristine 26f3cc40"
mkdir -p code/newmods
cp "$HERE"/newmods/*.py code/newmods/
echo "NEWMODS_COPIED"; (cd code/newmods && shasum -a 256 *.py)
git -c user.name=apply -c user.email=apply@localhost add -A
git -c user.name=apply -c user.email=apply@localhost commit -qm "newmods (new-files engineer)"
for p in "$HERE"/patches/[0-9][0-9][0-9][0-9]-*.patch; do
  n=$(basename "$p" | cut -c1-4)
  [ "$((10#$n))" -le "$((10#$LAST))" ] || break
  git apply --3way "$p"
  git -c user.name=apply -c user.email=apply@localhost add -A
  git -c user.name=apply -c user.email=apply@localhost commit -qm "$(basename "$p" .patch)"
  echo "APPLIED $(basename "$p")"
done
echo "TREE_SHA256_MANIFEST"
find code -name '*.py' -not -path '*/__pycache__/*' | sort | xargs shasum -a 256
echo "APPLY_ALL_PASS $OUT/code"
