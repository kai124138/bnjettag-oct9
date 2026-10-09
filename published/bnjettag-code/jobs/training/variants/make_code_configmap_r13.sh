#!/usr/bin/env bash
# Pack code/hgq2 into ConfigMap kai-bn13-code (key hgq2.tar.gz) — the PVC-FREE code source
# the round-13 training pods untar to /work/code. THE ROUND-13 TRAINING PREREQ.
#
# One ConfigMap per round (kai-bnf-code / kai-bn11-code / kai-bn12-code stay FROZEN so a
# re-run of an old round is reproducible). The r13 jobs hard-fail if this tree lacks the
# r13 configs, `ebops_callbacks` in bnhgq2/train.py, or `_free_act` in bnhgq2/qat.py.
#
# Idempotent (--dry-run=client | apply). Prints the tar md5 — pods echo the same md5.
set -euo pipefail
CTX="nautilus"; NS="cms-ml"
SRC="$(cd "$(dirname "$0")/../../../hgq2" && pwd)"
TAR="/tmp/bnjettag-hgq2-cm-r13.tar.gz"

# local gate: refuse to publish a tree that would fail the pod-side staleness check
grep -q "def ebops_callbacks" "$SRC/bnhgq2/train.py" || { echo "[fatal] $SRC/bnhgq2/train.py has no ebops_callbacks"; exit 1; }
grep -q "_free_act" "$SRC/bnhgq2/qat.py" || { echo "[fatal] $SRC/bnhgq2/qat.py has no _free_act"; exit 1; }
n=$(ls "$SRC"/configs/r13-*.json 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = "9" ] || { echo "[fatal] expected 9 configs/r13-*.json, found $n — run configs/gen_r13.py"; exit 1; }

tar --exclude='__pycache__' --exclude='*.pyc' --exclude='*.tar.gz' --exclude='*.keras' \
    --exclude='.DS_Store' -czf "$TAR" -C "$(dirname "$SRC")" "$(basename "$SRC")"
MD5=$(md5sum "$TAR" 2>/dev/null | awk '{print $1}' || md5 -q "$TAR")
SZ=$(wc -c < "$TAR")
echo "[cm] packed $SRC -> hgq2.tar.gz  md5=$MD5  bytes=$SZ"
[ "$SZ" -lt 1048576 ] || { echo "[fatal] tar $SZ bytes exceeds the 1 MB ConfigMap limit — trim excludes"; exit 1; }
kubectl --context "$CTX" -n "$NS" create configmap kai-bn13-code \
  --from-file=hgq2.tar.gz="$TAR" --dry-run=client -o yaml \
  | kubectl --context "$CTX" -n "$NS" apply -f -
echo "[cm] applied ConfigMap kai-bn13-code (key hgq2.tar.gz, md5 $MD5)"
echo "[cm] training pods echo this md5 as '[code] configmap tar md5: $MD5' for provenance"
