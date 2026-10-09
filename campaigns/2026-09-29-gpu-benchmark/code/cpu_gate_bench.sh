#!/usr/bin/env bash
# CPU gate for bench_driver.py (PREFLIGHT, build half). Synthetic data; nothing here is a result.
#
#   bash cpu_gate_bench.sh TREE CACHE_ROOT WORK
#
# TREE        an extraction of manifests/chang0926-code.tar.gz (sha256 42abed4b...), read only
# CACHE_ROOT  a directory holding n64/data from make_synthetic_cache.py (full size, 620,000 rows)
# WORK        scratch directory for the run roots (outside the repo)
#
# Pinned CPU environment = the bundle's requirements-cpu.txt (tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9,
# quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0, h5py 3.14.0, hls4ml 1.3.0, wandb 0.28.0) via `uv run --with`;
# wandb is installed on purpose, so "not imported" means something. Pod env copied from the manifests:
# thread counts, TF32 off, RSS-gate env (host_rss_mb on the epoch line), WANDB_MODE=disabled.
set -uo pipefail
TREE=$(cd "$1" && pwd); CACHE=$(cd "$2" && pwd); WORK=$3
HERE=$(cd "$(dirname "$0")" && pwd)
EV="$HERE/evidence"
mkdir -p "$EV" "$WORK"
DRIVER="$HERE/bench_driver.py"
export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2 CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONPATH="$TREE" BNJ_DATA_ROOT="$CACHE" BNJ_CAMPAIGN_DIR="$TREE/campaigns/chang0926"
export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0 BNJ_RSS_GATE_LIMIT_MB=8192 BNJ_RSS_GATE_WINDOW=5:105
unset BNJ_STAGE WANDB_PROJECT WANDB_ENTITY WANDB_API_KEY KUBERNETES_SERVICE_HOST
export WANDB_MODE=disabled
PY=(uv run --quiet --no-project --python 3.12 --with tensorflow==2.21.0 --with keras==3.15.0 --with hgq2==0.1.9
    --with quantizers==1.2.2 --with numpy==2.5.0 --with scikit-learn==1.9.0 --with h5py==3.14.0 --with hls4ml==1.3.0
    --with wandb==0.28.0 python)
ROWS=11160,1240          # 4 training steps of batch 2,790; 1,240 validation rows; sliced after load_cache
header() {
  echo "# cwd $(pwd); tree $TREE (extraction of chang0926-code.tar.gz sha256 $(shasum -a 256 "$HERE/../../2026-09-26-training-batch/manifests/chang0926-code.tar.gz" | cut -d' ' -f1))"
  echo "# driver sha256 $(shasum -a 256 "$DRIVER" | cut -d' ' -f1); cache $CACHE ($(python3 -c "import json;print(json.load(open('$CACHE/n64/data/data_info.json'))['synthetic'])") synthetic); $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# platform $(uname -s) $(uname -m); CPU affinity API: $(python3 -c "import os; print('os.sched_setaffinity' if hasattr(os, 'sched_setaffinity') else 'none (arms cannot pin here; the kernel check is test_bench.py test_pinning_k2_phase_arms_see_4_cpus on Linux)')")"
}

# 1. One arm, E class (A s1), stop_after 2: epoch lines, the post-pause check, no W&B.
LOG1="$EV/cpu_gate_arm_a-s1.log"
{ header; echo "# 1. arm mode: chang0926-a-n64-s1 --stop-after 2 --test-cpu --test-rows $ROWS"
  "${PY[@]}" -u "$DRIVER" arm --name chang0926-a-n64-s1 --run-root "$WORK/arm1" --stop-after 2 --test-cpu --test-rows "$ROWS"
  echo "EXIT $?"
  echo "# run root after the arm (files under $WORK/arm1):"
  (cd "$WORK/arm1" && find . -type f | sort)
  echo "# any wandb file or directory under the run root:"; find "$WORK/arm1" -iname '*wandb*' | wc -l
} > "$LOG1" 2>&1

# 2. Pod mode: three phases, an injected OOM in phase 2; the next phase must still run. The allowed CPU set is
#    injected (0-9) so the pod computes each phase's first 2K CPUs and passes them to every arm (--cpus); where the
#    platform cannot pin, each arm prints ARM_CPUS unavailable and runs on under --test-cpu (STUDY Amendment 1, A2).
PLAN=$(python3 - <<'EOF'
import json
E = [f'chang0926-a-n64-s{s}' for s in (1, 2)]
A = [f'chang0926-c-n64-s{s}' for s in (1, 2)]
print(json.dumps({'product': 'CPU-gate', 'slug': 'cpu-gate', 'stop_after': 2, 'phases': [
    {'phase': 'p1-E-k2', 'class': 'E', 'k': 2, 'names': E},
    {'phase': 'p2-A07-k2', 'class': 'A07', 'k': 2, 'names': A},
    {'phase': 'p3-E-k1', 'class': 'E', 'k': 1, 'names': E[:1]}]}))
EOF
)
LOG2="$EV/cpu_gate_pod.log"
{ header; echo "# 2. pod mode, plan: $PLAN"; echo "# injected: p2-A07-k2:chang0926-c-n64-s2 (test flag)"
  BENCH_SAMPLE_SECONDS=10 BENCH_STAGGER_SECONDS=2 "${PY[@]}" -u "$DRIVER" pod --bench-root "$WORK/pod/cpu-gate" \
      --plan-json "$PLAN" --test-cpu --test-rows "$ROWS" --test-inject-oom p2-A07-k2:chang0926-c-n64-s2 --test-allowed-cpus 0-9
  echo "EXIT $?"
  echo "# bench root after the pod:"; (cd "$WORK/pod/cpu-gate" && find . -type f -not -path '*/checkpoints/*' | sort)
  echo "# any wandb file or directory under the bench root:"; find "$WORK/pod" -iname '*wandb*' | wc -l
} > "$LOG2" 2>&1
mkdir -p "$EV/cpu_gate_pod"
cp "$WORK/pod/cpu-gate/samples.csv" "$WORK/pod/cpu-gate/bench_result.json" "$WORK/pod/cpu-gate/plan.json" "$EV/cpu_gate_pod/" 2>/dev/null
for d in "$WORK"/pod/cpu-gate/p[0-9]*; do
  mkdir -p "$EV/cpu_gate_pod/$(basename "$d")"
  cp "$d"/phase_result.json "$d"/logs/*.log "$EV/cpu_gate_pod/$(basename "$d")/" 2>/dev/null
done

# 3. Negative paths: nothing may start on a used root, a bad plan, or test flags inside a pod.
LOG3="$EV/cpu_gate_negative.log"
{ header
  echo "# 3a. pod mode again on the same bench root (expect BENCH_ROOT_NOT_EMPTY, exit 11)"
  "${PY[@]}" -u "$DRIVER" pod --bench-root "$WORK/pod/cpu-gate" --plan-json "$PLAN" --test-cpu --test-rows "$ROWS"; echo "EXIT $?"
  echo "# 3b. arm mode on a used run directory (expect ARM_ROOT_NOT_EMPTY, exit 11)"
  "${PY[@]}" -u "$DRIVER" arm --name chang0926-a-n64-s1 --run-root "$WORK/arm1" --stop-after 2 --test-cpu --test-rows "$ROWS"; echo "EXIT $?"
  echo "# 3c. a plan whose names are not the first K of the class (expect BENCH_PLAN_ERROR, exit 2)"
  BAD='{"product":"x","slug":"x","stop_after":21,"phases":[{"phase":"p1-E-k2","class":"E","k":2,"names":["chang0926-a-n64-s2","chang0926-b-n64-s1"]}]}'
  "${PY[@]}" -u "$DRIVER" pod --bench-root "$WORK/bad" --plan-json "$BAD"; echo "EXIT $?"
  echo "# 3d. test flags inside a Kubernetes pod (KUBERNETES_SERVICE_HOST set; expect BENCH_TEST_FLAGS_REFUSED, exit 2)"
  KUBERNETES_SERVICE_HOST=10.0.0.1 "${PY[@]}" -u "$DRIVER" arm --name chang0926-a-n64-s1 --run-root "$WORK/k8s" --test-cpu; echo "EXIT $?"
  echo "# 3e. no --test-cpu on a machine without a GPU (expect AssertionError 'Training requires GPU', exit 1)"
  "${PY[@]}" -u "$DRIVER" arm --name chang0926-a-n64-s1 --run-root "$WORK/nogpu" --stop-after 2 2>&1 | grep -E "AssertionError|BENCH_ARM|Training requires GPU"; echo "EXIT ${PIPESTATUS[0]}"
  echo "# 3f. directories 3c-3e would have created (expect "No such file or directory" for all three):"
  ls -A "$WORK/bad" "$WORK/k8s" "$WORK/nogpu" 2>&1
  echo "# 3g. an arm asked to pin (--cpus 0-3) without --test-cpu where it cannot (no sched_setaffinity on this platform; expect ARM_CPUS unavailable, exit 14, before any import)"
  "${PY[@]}" -u "$DRIVER" arm --name chang0926-a-n64-s1 --run-root "$WORK/nopin" --stop-after 2 --cpus 0-3; echo "EXIT $?"
  ls -A "$WORK/nopin" 2>&1
} > "$LOG3" 2>&1
echo "CPU_GATE_LOGS $LOG1 $LOG2 $LOG3"
