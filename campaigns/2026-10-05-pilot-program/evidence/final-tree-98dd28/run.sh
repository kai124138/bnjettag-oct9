set -u
cd /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/tree
export PYTHONPATH=/tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/tree:/tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/pytestlib PYTHONDONTWRITEBYTECODE=1
export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2
export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1
export BNJ_DATA_ROOT=/data/chang-n64-20260926 BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot-program-20261005/r1 BNJ_CAMPAIGN_DIR=/tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/tree/campaigns/pilot1005 BNJ_STAGE=pilot-r1
export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled
PY=~/venv-hgq2/bin/python
C="$PY -u campaigns/pilot1005/gate_check.py"
echo "START $(date '+%F %T %Z') tree=/tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/tree"
$PY -c "import tensorflow as tf, hgq; print('TF', tf.__version__)" 2>/dev/null || $PY -c "import tensorflow as tf; print('TF', tf.__version__)"
GATE=0; $PY -u campaigns/pilot1005/cpu_gate.py --out /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/cpu_gate.json > /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/cpu_gate.log 2>&1 || GATE=$?
grep -E "PAIRED_INIT_OK|PREFLIGHT_ALL_PASS|FLOOR|Error" /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/cpu_gate.log | tail -20
$C cpu-gate --log /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/cpu_gate.log --exit-code $GATE; echo "cpu_gate_exit=$GATE $(date '+%T')"
NBP=0; $PY -u campaigns/pilot1005/pair_nb.py --out /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/nb_pairing.json > /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/nb_pairing.log 2>&1 || NBP=$?
grep -E "^NB_" /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/nb_pairing.log
$C nb-pairing --log /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/nb_pairing.log --exit-code $NBP; echo "nb_pairing_exit=$NBP $(date '+%T')"
$PY -m pytest --collect-only -q -p no:cacheprovider tests analysis 2>&1 | tail -2
PT=0; $PY -m pytest -q -p no:cacheprovider -rs --junitxml /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/pytest.xml tests analysis > /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/pytest.log 2>&1 || PT=$?
tail -n 8 /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/pytest.log
$C pytest --junit /tmp/claude-1000/-home-kaimoe-lab-bnjettag/e92600b4-dce3-4d77-b804-05a4a62d92c5/scratchpad/f2/out/pytest.xml --exit-code $PT; echo "pytest_exit=$PT $(date '+%T')"
echo "END $(date '+%F %T %Z')"
