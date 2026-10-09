#!/usr/bin/env bash
# Register a Jupyter kernel that runs the BNJetTag pipeline on THIS machine.
#
# The notebooks read everything from the environment (PYTHONPATH, BNHGQ2_*), which is
# why they need no editing to move off the pod: the kernelspec carries the same
# variables kai-lab.yaml used to export, pointed at local paths instead of the PVC.
#
# Re-run this whenever the research tree moves or you switch data splits.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABREPO="$(cd "$HERE/.." && pwd)"
SPLIT=train

while [ $# -gt 0 ]; do
  case "$1" in
    --data) SPLIT="${2:?--data needs train|val}"; shift 2 ;;
    -h|--help) sed -n '2,9p' "$0"; echo; echo "usage: $0 [--data train|val]"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# Same resolution order as nrp-lab/lab.sh - one source of truth for the pipeline code.
resolve_repo() {
  if [ -n "${BNJETTAG_REPO:-}" ]; then echo "$BNJETTAG_REPO"; return; fi
  if [ -d "$LABREPO/research/bnjettag/code/hgq2" ]; then (cd "$LABREPO/research" && pwd -P); return; fi
  echo "$HOME/Downloads/bnjettag-training-results"
}
REPO="$(resolve_repo)"
VENV="$REPO/.venv-hgq2"
CODE="$REPO/bnjettag/code/hgq2"

[ -d "$CODE" ] || { echo "no pipeline code at $CODE - run ../setup.sh" >&2; exit 1; }
[ -x "$VENV/bin/python" ] || { echo "no venv at $VENV" >&2; exit 1; }

case "$SPLIT" in
  train) DATA="$REPO/data/train";        NAME=bnjettag-local;     DISPLAY="BNJetTag (local)" ;;
  val)   DATA="$REPO/data/val";          NAME=bnjettag-local-val; DISPLAY="BNJetTag (local, VAL-as-train)" ;;
  *) echo "--data must be train or val" >&2; exit 2 ;;
esac

if [ ! -d "$DATA" ] || [ -z "$(ls "$DATA"/*.h5 2>/dev/null)" ]; then
  echo "!! No .h5 files in $DATA" >&2
  if [ "$SPLIT" = train ]; then
    cat >&2 <<'EOM'
!! The train split is not on this machine yet (Zenodo record 3602260,
!! hls4ml_LHCjet_150p_train.tar.gz, ~2.7 GB).
!! To work against the val split in the meantime - deliberately, and with the
!! substitution visible in the kernel picker - run:  ./setup-local.sh --data val
EOM
  fi
  exit 1
fi
NFILES=$(ls "$DATA"/*.h5 | wc -l | tr -d ' ')

"$VENV/bin/python" -c "import ipykernel" 2>/dev/null || "$VENV/bin/pip" install -q ipykernel

mkdir -p "$HERE"/{outputs,store,wandb}

# W&B: the pod was safe because no key was mounted. This laptop HAS a credential in
# ~/.netrc, so wandb_enabled() is True here and an unguarded run would resolve to
# entity kayamaguchi-uc-san-diego / project bnjettag-final - the real record. Both
# layers below are load-bearing: offline mode, and a project that is never the real one.
"$VENV/bin/python" -m ipykernel install --user \
  --name "$NAME" --display-name "$DISPLAY" \
  --env KERAS_BACKEND tensorflow \
  --env PYTHONPATH "$CODE" \
  --env BNHGQ2_TRAIN_DATA "$DATA" \
  --env BNHGQ2_OUT_ROOT "$HERE/outputs" \
  --env BNHGQ2_STORE "$HERE/store" \
  --env WANDB_MODE offline \
  --env WANDB_PROJECT bnjettag-lab \
  --env WANDB_DIR "$HERE/wandb"

# ipykernel 7 writes two keys the older kernelspec format never had -
# `kernel_protocol_version` and metadata.supported_encryption. Jupyter itself is fine with
# them, but VS Code's Jupyter extension silently DROPS such a kernel from its "Jupyter
# Kernel..." picker, so it looks like this script never ran (seen 2026-09-09, ipykernel
# 7.3.0). Strip them: the kernel launches and receives its env identically without them.
SPECDIR="$("$VENV/bin/python" -c 'import jupyter_core.paths as p; print(p.jupyter_data_dir())')/kernels/$NAME"
"$VENV/bin/python" - "$SPECDIR/kernel.json" <<'PYEOF'
import json, sys
spec = json.load(open(sys.argv[1]))
spec.pop("kernel_protocol_version", None)
spec.get("metadata", {}).pop("supported_encryption", None)
json.dump(spec, open(sys.argv[1], "w"), indent=1)
PYEOF

echo
echo "Registered kernel '$DISPLAY'  (name: $NAME)"
echo "  python  : $VENV/bin/python"
echo "  code    : $CODE"
echo "  data    : $DATA  ($NFILES .h5 files)"
echo "  outputs : $HERE/outputs"
echo "  wandb   : offline, project bnjettag-lab (never bnjettag-final / BNJetTagAug)"
echo
echo "In VS Code: Select Kernel -> Jupyter Kernel... -> $DISPLAY"
echo "(if it is not listed, reload the window so VS Code rescans kernelspecs)"
