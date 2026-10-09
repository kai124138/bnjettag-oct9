"""Tiny dependency-optional numerical crosscheck; never loads model or data."""
import datetime
import json
import math
import platform
import sys
import time

started = time.perf_counter()
bias = [0., 2., 4., 6., 8.]
truth = [i % 5 for i in range(500)]
logits = [[bias[c] + float(c == y) for c in range(5)] for y in truth]

def argmax(x):
    return max(range(len(x)), key=x.__getitem__)

def accuracy(scores):
    return sum(argmax(row) == y for row, y in zip(scores, truth)) / len(truth)

def auc_column(scores, col):
    pos = [row[col] for row, y in zip(scores, truth) if y == col]
    neg = [row[col] for row, y in zip(scores, truth) if y != col]
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

corrected = [[v - b for v, b in zip(row, bias)] for row in logits]
aucs = [auc_column(logits, c) for c in range(5)]
corrected_aucs = [auc_column(corrected, c) for c in range(5)]
assert accuracy(logits) == 0.2
assert accuracy(corrected) == 1.0
assert aucs == corrected_aucs == [1.] * 5
predictions = [argmax(row) for row in logits]
for temperature in (0.1, 0.5, 1., 2., 10.):
    scaled = [[v / temperature for v in row] for row in logits]
    assert [argmax(row) for row in scaled] == predictions
    probabilities = []
    for row in scaled:
        vals = [math.exp(v - max(row)) for v in row]
        probabilities.append([v / sum(vals) for v in vals])
    assert [argmax(row) for row in probabilities] == predictions

result = {
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "host": platform.node(),
    "python": sys.version,
    "experiment": "synthetic only, not a measurement of trained jet models",
    "n_rows": len(truth),
    "raw_logit_ovr_auc": aucs,
    "original_accuracy": accuracy(logits),
    "bias_corrected_accuracy": accuracy(corrected),
    "bias_corrected_raw_logit_ovr_auc": corrected_aucs,
    "scalar_temperature_argmax_invariance": "PASS for temperatures 0.1,0.5,1,2,10 and corresponding softmax",
}
try:
    import numpy as np
    result["numpy"] = np.__version__
    rng = np.random.default_rng(17)
    x = rng.normal(size=(4096, 5)).astype(np.float32)
    b = np.asarray(bias, dtype=np.float32)
    scales = np.linspace(.8, 1.2, 5, dtype=np.float32)
    out = np.empty_like(x)
    repeats = 2000
    for _ in range(50):
        np.add(x, b, out=out)
    timer = time.perf_counter()
    for _ in range(repeats):
        np.add(x, b, out=out)
    bias_time = time.perf_counter() - timer
    timer = time.perf_counter()
    for _ in range(repeats):
        np.multiply(x, scales, out=out)
        np.add(out, b, out=out)
    affine_time = time.perf_counter() - timer
    result["numpy_cpu_benchmark"] = {
        "batch": 4096,
        "repeats": repeats,
        "bias_add_us_per_jet": bias_time * 1e6 / repeats / len(x),
        "scale_and_bias_us_per_jet": affine_time * 1e6 / repeats / len(x),
        "scope": "warm vectorized CPU throughput including Python dispatch; excludes model/argmax; not single-event latency or FPGA resource/latency",
    }
except ImportError:
    result["numpy"] = "unavailable; used dependency-free exact pairwise AUC verification"
result["wall_seconds"] = time.perf_counter() - started
print(json.dumps(result, indent=2))
