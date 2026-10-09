#!/usr/bin/env bash
# Pack code/hgq2 into ConfigMap kai-bn14-code (key hgq2.tar.gz) — the PVC-FREE code source
# the round-14 training pods untar to /work/code. THE ROUND-14 TRAINING PREREQ.
#
# One ConfigMap per round (kai-bnf/bn11/bn12/bn13-code stay FROZEN so a re-run of an old
# round is reproducible). The r14 jobs hard-fail if this tree lacks the r14 configs,
# `feature_indices` in bnhgq2/data.py (the L1 feature subset), or the 2026-08-01
# wandb_util layout in bnhgq2/train.py.
#
# Idempotent (--dry-run=client | apply). Prints the tar md5 — pods echo the same md5.
set -euo pipefail
CTX="nautilus"; NS="cms-ml"
SRC="$(cd "$(dirname "$0")/../../../hgq2" && pwd)"
TAR="/tmp/bnjettag-hgq2-cm-r14.tar.gz"

# local gate: refuse to publish a tree that would fail the pod-side staleness check
grep -q "def feature_indices" "$SRC/bnhgq2/data.py" || { echo "[fatal] $SRC/bnhgq2/data.py has no feature_indices"; exit 1; }
grep -q "wandb_util" "$SRC/bnhgq2/train.py" || { echo "[fatal] $SRC/bnhgq2/train.py predates the wandb_util layout"; exit 1; }
n=$(ls "$SRC"/configs/r14-*.json 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = "20" ] || { echo "[fatal] expected 20 configs/r14-*.json, found $n — run configs/gen_r14.py"; exit 1; }

tar --exclude='__pycache__' --exclude='*.pyc' --exclude='*.tar.gz' --exclude='*.keras' \
    --exclude='.DS_Store' -czf "$TAR" -C "$(dirname "$SRC")" "$(basename "$SRC")"
MD5=$(md5sum "$TAR" 2>/dev/null | awk '{print $1}' || md5 -q "$TAR")
SZ=$(wc -c < "$TAR")
echo "[cm] packed $SRC -> hgq2.tar.gz  md5=$MD5  bytes=$SZ"
[ "$SZ" -lt 1048576 ] || { echo "[fatal] tar $SZ bytes exceeds the 1 MB ConfigMap limit — trim excludes"; exit 1; }
# --server-side: the r14 tree (~240 KB tar) overflows client-side apply's
# last-applied-configuration annotation (262144-byte cap) — hit 2026-08-01.
kubectl --context "$CTX" -n "$NS" create configmap kai-bn14-code \
  --from-file=hgq2.tar.gz="$TAR" --dry-run=client -o yaml \
  | kubectl --context "$CTX" -n "$NS" apply --server-side -f -
echo "[cm] applied ConfigMap kai-bn14-code (key hgq2.tar.gz, md5 $MD5)"
echo "[cm] training pods echo this md5 as '[code] configmap tar md5: $MD5' for provenance"
