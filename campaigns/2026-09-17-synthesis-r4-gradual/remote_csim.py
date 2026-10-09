"""Replay the gated sample against a freshly compiled Linux HLS C emulator."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--project", type=Path, required=True)
ap.add_argument("--inputs", type=Path, required=True)
ap.add_argument("--reference", type=Path, required=True)
args = ap.parse_args()
project = args.project.resolve()
stamp = re.search(r"^LIB_STAMP=(\w+)$", (project / "build_lib.sh").read_text(), re.M).group(1)
lib = ctypes.CDLL(str(project / "firmware" / ("myproject-" + stamp + ".so")))
fn = lib.myproject_float
ptr = ctypes.POINTER(ctypes.c_float)
fn.argtypes = [ptr, ptr]
fn.restype = None
x = np.ascontiguousarray(np.load(args.inputs), dtype=np.float32)
ref = np.ascontiguousarray(np.load(args.reference), dtype=np.float32)
assert x.shape == (4096, 8, 3) and ref.shape == (4096, 5)
y = np.empty_like(ref)
for a, b in zip(x, y):
    fn(a.ctypes.data_as(ptr), b.ctypes.data_as(ptr))
delta = np.abs(y-ref)
result = {"stage": "Linux C simulation on Mulder", "n": len(x),
          "max_abs_diff": float(delta.max()), "mean_abs_diff": float(delta.mean()),
          "argmax_agreement": float(np.mean(y.argmax(1) == ref.argmax(1))),
          "bit_exact": bool(np.array_equal(y, ref)),
          "input_sha256": hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
          "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
          "numpy_version": np.__version__}
(project.parent / "linux_csim_verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result), flush=True)
if not result["bit_exact"]:
    raise SystemExit("Linux C simulation differs: vendor synthesis prohibited")
