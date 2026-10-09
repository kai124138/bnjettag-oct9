#!/usr/bin/env python3
"""Read-back audit of an emitted hls4ml firmware weight array's REALIZED grid.

Written 2026-09-03 for the weight-width-matched PTQ control (design memo CORRECTION
C1.3). It reads ONLY the emitted `firmware/weights/w*.txt` -- i.e. the values actually
compiled into the netlist -- and never a driver flag or a Keras object.

Validated against the numbers already on record in CORRECTION C1.3: over all 15 weight
arrays (17,664 elements) it reproduces distinct-value counts 35 (w8a8-s3), 227
(fp32-s3-w8) and 14,321 (fp32-s3-w16) exactly. Its "<=2 set bits" fraction excludes
exact zeros from the denominator, which is why it reads 87.9% where C1.3 records 83.1%
for w8a8 (414 zeros of 17,664); the two other C1.3 entries agree to 0.3 pp.

Usage:
  python3 weight_grid_audit.py <path-to-hls_prj/firmware> [label]

For each named weight array: total distinct values, min/max, the realized fractional
bits (the smallest f such that every value is an exact multiple of 2^-f), the realized
integer/total bits under a signed two's-complement ap_fixed<1+i+f, 1+i> that contains the
range, and the set-bit distribution of the odd mantissa (the strength-reduction predictor
used in CORRECTION C1.3).
"""
import sys, os, re, json
import numpy as np


def load_txt(p):
    s = open(p).read().strip().rstrip(',')
    return np.array([float(v) for v in s.split(',') if v.strip()], dtype=np.float64)


def frac_bits(v, fmax=40):
    """smallest f with v * 2^f integral for all v."""
    for f in range(0, fmax + 1):
        s = v * (2.0 ** f)
        if np.all(np.abs(s - np.round(s)) < 1e-9):
            return f
    return None


def int_bits(v, f):
    """smallest i >= -f such that signed range [-2^i, 2^i - 2^-f] contains all v."""
    step = 2.0 ** -f
    for i in range(-f, 33):
        if v.min() >= -(2.0 ** i) - 1e-12 and v.max() <= (2.0 ** i) - step + 1e-12:
            return i
    return None


def setbits(v, f):
    """odd-mantissa popcount for each nonzero value: strip trailing zeros of |v|*2^f."""
    m = np.abs(np.round(v * (2.0 ** f))).astype(np.int64)
    m = m[m != 0]
    out = []
    for x in m:
        while x % 2 == 0:
            x //= 2
        out.append(bin(x).count('1'))
    return np.array(out, dtype=int)


def audit_array(path):
    v = load_txt(path)
    f = frac_bits(v)
    i = int_bits(v, f)
    sb = setbits(v, f)
    n = v.size
    hist = {int(k): int(c) for k, c in zip(*np.unique(sb, return_counts=True))}
    return {
        "n": int(n),
        "n_zero": int((v == 0).sum()),
        "distinct": int(np.unique(v).size),
        "min": float(v.min()), "max": float(v.max()),
        "absmax": float(np.abs(v).max()),
        "frac_bits": int(f), "int_bits": int(i), "total_bits": int(1 + i + f),
        "ap_fixed": f"ap_fixed<{1+i+f},{1+i}>",
        "lsb": 2.0 ** -f,
        "setbit_hist": hist,
        "frac_le2_setbits": float((sb <= 2).mean()) if sb.size else float('nan'),
        "frac_ge4_setbits": float((sb >= 4).mean()) if sb.size else float('nan'),
        "mean_setbits": float(sb.mean()) if sb.size else float('nan'),
    }


def audit_group(fwdir, names, label):
    per = {}
    allv = []
    for nm in names:
        p = os.path.join(fwdir, "weights", nm + ".txt")
        per[nm] = audit_array(p)
        allv.append(load_txt(p))
    v = np.concatenate(allv)
    f = frac_bits(v); i = int_bits(v, f); sb = setbits(v, f)
    hist = {int(k): int(c) for k, c in zip(*np.unique(sb, return_counts=True))}
    pooled = {
        "arrays": names, "n": int(v.size), "n_zero": int((v == 0).sum()),
        "distinct": int(np.unique(v).size),
        "min": float(v.min()), "max": float(v.max()), "absmax": float(np.abs(v).max()),
        "frac_bits": int(f), "int_bits": int(i), "total_bits": int(1 + i + f),
        "ap_fixed": f"ap_fixed<{1+i+f},{1+i}>",
        "setbit_hist": hist,
        "frac_le2_setbits": float((sb <= 2).mean()),
        "frac_ge4_setbits": float((sb >= 4).mean()),
        "mean_setbits": float(sb.mean()),
    }
    return {"label": label, "firmware": fwdir, "pooled": pooled, "per_array": per}


# the eight EinsumDense attention projection arrays (2 blocks x Wq/Wk/Wv/Wo). These get
# NO per-layer weight typedef from hls4ml 1.3.0 and load as `model_default_t`, so they
# are the only DSP-eligible weight arrays in this graph (C1.3).
ATTN = ["w5", "w7", "w13", "w18", "w27", "w29", "w35", "w40"]

if __name__ == "__main__":
    fw = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else fw
    r = audit_group(fw, ATTN, label)
    print(json.dumps(r, indent=2))
