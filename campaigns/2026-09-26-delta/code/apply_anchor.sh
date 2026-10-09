#!/usr/bin/env bash
# Rebuild the Delta tree on the anchor regime-B freeze (chang0926 bundle 42abed4b, commit 3dabcd2, ConfigMap
# kai-chang0926-code-42abed4b5d) for launch. Superseded bases: 77f1ca4e, e90327d4, f2107a04, ceb174db.
#
#   code/apply_anchor.sh <build-dir> [last-patch-number]
#
# Extracts campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz into <build-dir>
# after checking its sha256 (42abed4b..., the ConfigMap payload; = training-batch code/tree +
# code/analysis), commits it in a throwaway git repo inside <build-dir>, copies the new-files
# engineer's modules (code/newmods/*.py) into <build-dir>/code/newmods/ and commits them, then
# applies code/patches-anchor/NNNN-<slug>.patch in order with `git apply --3way`. 0001-0024 are
# the tarball series (code/patches/) rebased onto the anchor; 0025+ exist only here (they need
# anchor code). Optional last-patch-number stops early. Prints the sha256 of every .py file of
# the result. Never touches a project repository and never edits the training-batch campaign.
#
# Next anchor sha (production bundle): set ANCHOR_BUNDLE / ANCHOR_SHA256 below (or in the
# environment) and follow PLAN_rebase.md "Next rebase".
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
BUNDLE=${ANCHOR_BUNDLE:-"$ROOT/campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz"}
EXPECT=${ANCHOR_SHA256:-42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0}
OUT=${1:?usage: apply_anchor.sh <build-dir> [last-patch-number]}
LAST=${2:-9999}
G="git -c user.name=apply -c user.email=apply@localhost"

GOT=$(shasum -a 256 "$BUNDLE" | cut -d' ' -f1)
[ "$GOT" = "$EXPECT" ] || { echo "ANCHOR_BUNDLE_SHA_MISMATCH $GOT (expected $EXPECT)" >&2; exit 1; }
echo "ANCHOR_BUNDLE_SHA_OK $GOT"
[ ! -e "$OUT" ] || [ -z "$(ls -A "$OUT")" ] || { echo "build dir $OUT is not empty" >&2; exit 1; }
mkdir -p "$OUT"
tar xzf "$BUNDLE" -C "$OUT"
cd "$OUT"
git init -q
$G add -A
$G commit -qm "anchor bundle ${EXPECT:0:8}"
mkdir -p code/newmods
cp "$HERE"/newmods/*.py code/newmods/
echo "NEWMODS_COPIED"; (cd code/newmods && shasum -a 256 *.py)
$G add -A
$G commit -qm "newmods (new-files engineer)"
for p in "$HERE"/patches-anchor/[0-9][0-9][0-9][0-9]-*.patch; do
  n=$(basename "$p" | cut -c1-4)
  [ "$((10#$n))" -le "$((10#$LAST))" ] || break
  git apply --3way "$p"
  $G add -A
  $G commit -qm "$(basename "$p" .patch)"
  echo "APPLIED $(basename "$p")"
done
echo "TREE_SHA256_MANIFEST"
find code -name '*.py' -not -path '*/__pycache__/*' | sort | xargs shasum -a 256
echo "APPLY_ANCHOR_ALL_PASS $OUT/code"
