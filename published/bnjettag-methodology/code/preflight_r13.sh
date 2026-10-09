#!/usr/bin/env bash
# ROUND-13 preflight — PVC-FREE, CPU-only (no GPU burned). Mirrors preflight_r7.sh and adds
# the checks round 13 specifically needs: that the EBOPs-pressure plumbing is really wired
# (beta0 knob, learnable-bitwidth activations, the three HGQ2 sugar callbacks in the right
# ORDER) and — the important one — that turning that plumbing on did NOT change any
# pre-r13 config. Run in a CPU pod on image python:3.12 with the round-13 code ConfigMap
# kai-bn13-code mounted at /cmcode (apply it first with ./make_code_configmap_r13.sh):
#   kubectl -n cms-ml run kai-r13-preflight --restart=Never -it --image=python:3.12 \
#     --overrides='{"spec":{"containers":[{"name":"p","image":"python:3.12","command":["bash","-lc",
#       "tar xzf /cmcode/hgq2.tar.gz -C /tmp && bash /tmp/hgq2/preflight_r13.sh"],
#       "volumeMounts":[{"name":"cm","mountPath":"/cmcode"}]}],
#       "volumes":[{"name":"cm","configMap":{"name":"kai-bn13-code"}}]}}'
# Require the literal PREFLIGHT_ALL_PASS in the output before launching any GPU job.
set -uo pipefail
export KERAS_BACKEND=tensorflow CUDA_VISIBLE_DEVICES=-1
CODE=${BNF_CODE:-/work/code}
mkdir -p "$CODE"
if [ -f /cmcode/hgq2.tar.gz ]; then tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1; fi
fail=0
echo "=== BNJetTag ROUND-13 preflight (PVC-free) $(date) ==="

echo "[deps] pinned install (mirror .venv-hgq2)"
pip install -q --no-cache-dir "tensorflow[and-cuda]==2.21.0" "keras==3.15.0" "hgq2==0.1.9" "quantizers==1.2.2" "scikit-learn==1.9.0" "h5py==3.14.0" "wandb==0.28.0" "hls4ml==1.3.0" "numpy==2.5.0" || { echo "  FAIL deps"; fail=1; }

echo "--- data source reachability: Zenodo train tarball (HEAD, no download) ---"
if python - <<'PYEOF'
import urllib.request
req = urllib.request.Request("https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_train.tar.gz?download=1", method="HEAD")
r = urllib.request.urlopen(req, timeout=90)
cl = int(r.headers.get("Content-Length", "0"))
assert r.status == 200 and cl > 2_500_000_000, f"status={r.status} content-length={cl}"  # real tarball = 2,725,115,104 B
print(f"  OK Zenodo train tarball reachable: {cl} bytes")
PYEOF
then echo "  PASS data-source"; else echo "  FAIL data-source"; fail=1; fi

echo "--- build all 9 r13 configs (CPU) + param count + binary {-1,+1} gate + arm matching ---"
if python - <<PYEOF
import sys, glob, json, numpy as np
sys.path.insert(0, "$CODE")
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2.subln import register_subln; register_subln()
from bnhgq2.config import load_config, cfg_hash
from bnhgq2 import qat

PARAMS = 19201                      # the deployable 'small' QAT-stack count (r7/r8/r11)
ok = True
configs = sorted(glob.glob("$CODE/configs/r13-*.json"))
if len(configs) != 9:
    print(f"  FAIL expected 9 r13 configs, found {len(configs)}"); ok = False
for p in configs:
    c = load_config(p)
    m, taps = qat.build_qat_model(c, seed=1, enable_ebops=True)
    got = int(m.count_params())
    pmatch = got == PARAMS
    ok = ok and pmatch
    tag = ""
    if c["quant"]["weight"] == "binary_absmean":
        effs = qat.effective_weight_values(m)
        binok = all(len(v) == 2 and not (v == 0).any()
                    and abs(abs(v[0]) - abs(v[1])) < 1e-9 for v in effs.values())
        tag = f" binary_gate={'OK' if binok else 'FAIL'}({len(effs)} layers)"
        ok = ok and binok
    # every r13 arm is norm-free (the 2026-07-25 confound must not recur)
    if c["arch"]["norm"] != "none":
        print(f"  FAIL {c['name']}: norm={c['arch']['norm']} (all r13 arms must be 'none')")
        ok = False
    print(f"  {c['name']:34s} [{cfg_hash(c)}] params={got:>6,} "
          f"{'OK' if pmatch else 'MISMATCH!'} w={c['quant']['weight']:15s} "
          f"act={c['quant']['act_calib']}{tag}")
sys.exit(0 if ok else 1)
PYEOF
then echo "  PASS build"; else echo "  FAIL build"; fail=1; fi

echo "--- GUARDED-KNOB REGRESSION: the r13 plumbing must not touch any pre-r13 config ---"
if python - <<PYEOF
import sys, glob, numpy as np
sys.path.insert(0, "$CODE")
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2.subln import register_subln; register_subln()
import keras
from bnhgq2.config import load_config
from bnhgq2 import qat
from bnhgq2.train import ebops_callbacks

ok = True
for p in sorted(glob.glob("$CODE/configs/r8-*.json") + glob.glob("$CODE/configs/r11-d32-*.json")):
    c = load_config(p)
    # (a) beta0 defaults to 0.0 -> the EBOPs term stays OFF for every legacy config
    b0 = float(c["quant"].get("beta0", 0.0))
    # (b) no ebops block -> zero extra callbacks
    cbs, front = ebops_callbacks(c, "/tmp/_pf")
    m, _ = qat.build_qat_model(c, seed=1, enable_ebops=True)
    betas = set()
    for ly in m._flatten_layers():
        b = getattr(ly, "_beta", None)
        if b is not None:
            betas.add(float(np.asarray(keras.ops.convert_to_numpy(b)).ravel()[0]))
    good = (b0 == 0.0) and not cbs and front is None and betas <= {0.0}
    ok = ok and good
    print(f"  {c['name']:34s} beta0={b0} extra_cbs={len(cbs)} layer_betas={sorted(betas)[:2]} "
          f"{'OK' if good else 'REGRESSION!'}")
sys.exit(0 if ok else 1)
PYEOF
then echo "  PASS legacy-unchanged"; else echo "  FAIL legacy-unchanged"; fail=1; fi

echo "--- EBOPs callbacks: presence, ORDER, and a 2-epoch end-to-end front on random data ---"
if python - <<PYEOF
import sys, numpy as np
sys.path.insert(0, "$CODE")
from bnhgq2.compat import apply_keras_compat; apply_keras_compat()
from bnhgq2.subln import register_subln; register_subln()
import keras
from bnhgq2.config import load_config
from bnhgq2 import qat, train as T

ok = True
c = load_config("$CODE/configs/r13-small-w1-freeact-beta.json")
cbs, front_dir = T.ebops_callbacks(c, "/tmp/_r13pf")
names = [type(x).__name__ for x in cbs]
order_ok = names == ["BetaScheduler", "FreeEBOPs", "ParetoFront"]
print(f"  callbacks={names} order={'OK' if order_ok else 'WRONG'}")
ok = ok and order_ok

# ParetoFront must read logs['ebops'] AFTER FreeEBOPs wrote it -> exercise the whole chain
# with the admission threshold lifted, on random data (2 epochs, CPU, seconds).
c["train"]["ebops"]["threshold"] = 1e12
m, taps = qat.build_qat_model(c, seed=1, enable_ebops=True)
X = np.random.randn(256, 10, 16).astype("float32")
Y = np.eye(5, dtype="float32")[np.random.randint(0, 5, 256)]
qat.calibrate_activations(m, taps, X, 8)
m.compile(loss=keras.losses.CategoricalCrossentropy(from_logits=True),
          optimizer=keras.optimizers.Adam(1e-3))
state = {"best_auc": -1.0, "best_epoch": -1}
tr = c["train"]
cb = T.make_callbacks(X, Y, "/tmp/_r13pf_best.keras", int(tr["es_patience"]), float(tr["lr"]),
                      1, 0, 1.0, False, state, val_batch=int(tr["val_batch"]),
                      lr_schedule=tr["lr_schedule"], lr_cycle_epochs=int(tr["lr_cycle_epochs"]),
                      lr_min_frac=float(tr["lr_min_frac"]))
eb, fd = T.ebops_callbacks(c, "/tmp/_r13pf_run")
m.fit(X, Y, epochs=2, batch_size=64, verbose=0, callbacks=cb + eb)
f = T.summarize_front(fd)
sel = T.select_front_point(f)
print(f"  front points={len(f)} selected={sel}")
ok = ok and len(f) > 0 and sel is not None and sel["ebops"] > 0
# es_patience == 0 must mean NO EarlyStopping (the front would otherwise be truncated)
es = [n for n in [type(x).__name__ for x in cb] if n == "EarlyStopping"]
print(f"  early_stopping_callbacks={len(es)} (must be 0 at es_patience=0)")
ok = ok and not es
# learnable activation bitwidths must actually be trainable variables
free = [v.path for v in m.trainable_variables
        if "quantizer_kif" in v.path and v.path.rsplit("/", 1)[-1] in ("i", "f")]
print(f"  trainable act-bitwidth vars (KIF i/f): {len(free)} (must be > 0)")
ok = ok and len(free) > 0
sys.exit(0 if ok else 1)
PYEOF
then echo "  PASS ebops-callbacks"; else echo "  FAIL ebops-callbacks"; fail=1; fi

echo "--- production LR must no longer be the placeholder when stage1/2 are launched ---"
python - <<PYEOF
import json, glob
for p in sorted(glob.glob("$CODE/configs/r13-small-*.json")):
    c = json.load(open(p))
    lr = c["train"]["lr"]
    flag = "  <-- STILL THE r8 PLACEHOLDER: pin the Stage-0 winner (gen_r13.py --lr) before stage1" if lr == 2e-05 else ""
    print(f"  {c['name']:34s} lr={lr:g}{flag}")
PYEOF
echo "  NOTE advisory only — Stage 0 legitimately runs before the LR is pinned."

if [ "$fail" = 0 ]; then echo "PREFLIGHT_ALL_PASS"; else echo "PREFLIGHT_HAD_FAILURES"; fi
