#!/bin/bash
# Rebuild the staged tree from the pinned screen bundle plus patches/, and check it equals tree/.
# usage: code/apply.sh [OUT_DIR]   (default: a fresh temp dir; nothing outside OUT_DIR is written)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TARBALL="$HERE/../../2026-09-22-constituent-screen/study-code.tar.gz"
OUT=${1:-$(mktemp -d)}
mkdir -p "$OUT"
echo "26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45  $TARBALL" | shasum -a 256 -c -
tar xzf "$TARBALL" -C "$OUT"
cd "$OUT/code"
for p in "$HERE"/patches/*.patch; do
  git apply --whitespace=nowarn "$p"
  echo "applied $(basename "$p")"
done
diff -r -x __pycache__ -x .pytest_cache "$OUT/code" "$HERE/tree"
echo "APPLY_MATCHES_TREE $OUT/code"
