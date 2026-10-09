#!/usr/bin/env bash
# NRP GPU notebook session: bring it up, put our code on it, reach it, take it down.
# Every kubectl call is echoed before it runs - nothing happens off-screen.
set -euo pipefail

NS=cms-ml
JOB=kai-lab
SEL=app=kai-lab
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABREPO="$(cd "$HERE/.." && pwd)"

# Where the BNJetTag research tree lives. This repo holds the environment, not the
# pipeline code - `sync` pushes code/hgq2 from the research tree onto the pod so there
# is exactly one source of truth. Resolution order:
#   1. $BNJETTAG_REPO   2. ./research symlink (made by setup.sh)   3. the usual place
resolve_repo() {
  if [ -n "${BNJETTAG_REPO:-}" ]; then echo "$BNJETTAG_REPO"; return; fi
  # Unified workspace (2026-09-26): nrp-lab/ sits inside the science tree itself.
  if [ -d "$LABREPO/bnjettag/code/hgq2" ]; then
    (cd "$LABREPO" && pwd -P); return
  fi
  if [ -d "$LABREPO/research/bnjettag/code/hgq2" ]; then
    (cd "$LABREPO/research" && pwd -P); return
  fi
  echo "$HOME/Downloads/bnjettag-training-results"
}

require_repo() {
  REPO="$(resolve_repo)"
  if [ ! -d "$REPO/bnjettag/code/hgq2" ]; then
    cat >&2 <<EOM
Cannot find the BNJetTag research tree.

  looked for : \$REPO/bnjettag/code/hgq2
  resolved to: $REPO

Fix it with either:
  ./setup.sh /path/to/bnjettag-training-results     (makes a ./research symlink)
  export BNJETTAG_REPO=/path/to/bnjettag-training-results
EOM
    return 1
  fi
}

run() { printf '\033[2m$ %s\033[0m\n' "$*" >&2; "$@"; }

pod() {
  local p
  p=$(kubectl get pods -n "$NS" -l "$SEL" \
        -o jsonpath='{range .items[?(@.status.phase=="Running")]}{.metadata.name}{"\n"}{end}' \
      | head -1)
  [ -n "$p" ] || { echo "no Running kai-lab pod. Try: $0 status" >&2; return 1; }
  echo "$p"
}

case "${1:-help}" in

up)
  run kubectl apply -f "$HERE/kai-lab.yaml" -n "$NS"
  echo
  echo "Waiting for the pod to reach Running..."
  for _ in $(seq 1 60); do
    ph=$(kubectl get pods -n "$NS" -l "$SEL" -o jsonpath='{.items[-1:].status.phase}' 2>/dev/null || true)
    printf '  %s\r' "${ph:-Pending}"
    [ "$ph" = "Running" ] && break
    sleep 5
  done
  echo
  run kubectl get pods -n "$NS" -l "$SEL" -o wide
  echo
  echo "The container is up. A FIRST start now builds the venv on the PVC (41 min, measured);"
  echo "follow it with:  $0 logs -f      (wait for the [jupyter] line, then: $0 sync)"
  ;;

status)
  run kubectl get job "$JOB" -n "$NS" 2>/dev/null || echo "(no job $JOB)"
  echo
  run kubectl get pods -n "$NS" -l "$SEL" -o wide
  ;;

logs)
  shift
  p=$(pod)
  run kubectl logs "$p" -n "$NS" "$@"
  ;;

url)
  p=$(pod)
  echo "Asking the pod for its Jupyter URL + token:"
  run kubectl exec "$p" -n "$NS" -- /data/lab/venv/bin/jupyter server list \
    | sed 's|http://[^:]*:8888|http://localhost:8888|'
  echo
  echo "Open that URL after starting: $0 forward"
  ;;

forward)
  p=$(pod)
  echo "Forwarding localhost:8888 -> $p:8888. Ctrl-C to stop (the pod keeps running)."
  run kubectl port-forward "$p" -n "$NS" 8888:8888
  ;;

sync)
  # The research tree is the source of truth for code. This overwrites /data/lab/repo.
  require_repo
  p=$(pod)
  echo "Research tree: $REPO"
  echo "Pushing $REPO/bnjettag/code/hgq2 -> $p:/data/lab/repo/bnjettag/code/"
  run kubectl exec "$p" -n "$NS" -- mkdir -p /data/lab/repo/bnjettag/code
  COPYFILE_DISABLE=1 tar --no-xattrs -czf - -C "$REPO/bnjettag/code" \
      --exclude '__pycache__' --exclude '*.pyc' --exclude 'wandb' hgq2 \
    | kubectl exec -i "$p" -n "$NS" -- tar xzf - -C /data/lab/repo/bnjettag/code
  run kubectl exec "$p" -n "$NS" -- ls /data/lab/repo/bnjettag/code/hgq2
  # Notebooks: by default only seed the ones that are not there yet, so your edits on
  # the PVC are never clobbered. `sync --replace-notebooks` overwrites them instead —
  # use it when the starters here have been fixed and the PVC still has the old ones.
  if [ -d "$HERE/notebooks" ] && [ -n "$(ls -A "$HERE/notebooks" 2>/dev/null)" ]; then
    echo
    if [ "${2:-}" = "--replace-notebooks" ]; then
      echo "Replacing notebooks on the PVC with the copies in this repo:"
      COPYFILE_DISABLE=1 tar --no-xattrs -czf - -C "$HERE" notebooks \
        | kubectl exec -i "$p" -n "$NS" -- tar xzf - -C /data/lab
    else
      echo "Seeding notebooks (skips any that already exist on the PVC;"
      echo "pass --replace-notebooks to overwrite them):"
      COPYFILE_DISABLE=1 tar --no-xattrs -czf - -C "$HERE" notebooks \
        | kubectl exec -i "$p" -n "$NS" -- tar xzf - -C /data/lab --skip-old-files
    fi
    run kubectl exec "$p" -n "$NS" -- ls /data/lab/notebooks
  fi
  ;;

pull)
  # Bring notebooks back off the PVC into the repo so edits are committable.
  p=$(pod)
  echo "Pulling $p:/data/lab/notebooks -> $HERE/notebooks"
  kubectl exec "$p" -n "$NS" -- tar czf - -C /data/lab --exclude '.ipynb_checkpoints' notebooks \
    | tar xzf - -C "$HERE"
  run ls "$HERE/notebooks"
  ;;

shell)
  p=$(pod)
  run kubectl exec -it "$p" -n "$NS" -- bash
  ;;

down)
  run kubectl delete job "$JOB" -n "$NS"
  echo "Gone. /data/lab on the kai-data PVC (venv, notebooks, outputs) is untouched."
  ;;

*)
  cat <<EOF
usage: lab.sh <command>

  up        launch the GPU notebook Job on Nautilus and watch it start
  status    job + pod state, which node, which GPU
  logs      pod logs (pass -f to follow)
  sync      push code/hgq2 from the research tree onto the pod, seed notebooks
            (sync --replace-notebooks overwrites the PVC copies instead of skipping)
  url       print the Jupyter URL with its token
  forward   port-forward localhost:8888 to the pod
  shell     interactive bash inside the pod
  pull      copy notebooks off the PVC back into this folder
  down      delete the Job (the PVC keeps the venv, notebooks and outputs)

  sync needs the BNJetTag research tree; point at it with ./setup.sh or \$BNJETTAG_REPO.

typical session:  ./lab.sh up   ->  ./lab.sh sync  ->  ./lab.sh forward  (new terminal: ./lab.sh url)
EOF
  ;;
esac
