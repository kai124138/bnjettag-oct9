"""β-convention diagnostic: BNJetTag (centered absmean) vs BitNet b1 reference (uncentered).

Our binarizer scales by the absmean of the *centered* latents
(`bnhgq2/qat.py:59-61`, mirrored in `bnhgq2/binarize.py:41`):

    alpha = mean(w);  beta = mean(|w - alpha|) + 1e-6;  q = sign(w - alpha)

The BitNet b1 reference ("The Era of 1-bit LLMs: Training Tips, Code and FAQ",
microsoft/unilm/bitnet, Figure 5) scales by the absmean of the *uncentered* latents:

    scale = w.abs().mean();  e = w.mean();  u = (w - e).sign() * scale

Same sign pattern, different scale. This script quantifies the disagreement on a
trained checkpoint and — the question that actually matters for hardware — asks
whether it survives the fx8 encoding (`bnhgq2/gold.py:74`, γ = round(β·256)/256)
that produces the constants the β-restore affines synthesize with.

Note on interpretation: β sits inside the training gradient path (`ws = wc /
stop_gradient(beta)`, qat.py:62), so training under the uncentered convention would
have produced a *different checkpoint*, not these weights with a different scale.
What this measures is how far the two formulas disagree on these latents — not what
the convention choice cost.

Usage:  python beta_convention_check.py [path/to/model_best.keras]
"""
from __future__ import annotations

import io
import re
import sys
import zipfile

import h5py
import numpy as np

DEFAULT_CKPT = "results/predictions/pre_conference/n8/_ckpt_dl/w1a8-s3/model_best.keras"
EPS_BETA = 1e-6          # bnhgq2/qat.py EPS_BETA == bnhgq2/binarize.py
FX8_STEP = 2.0 ** -8     # bnhgq2/gold.py:74


def fx8(beta: float) -> float:
    return float(np.round(beta * 256.0) / 256.0)


def _walk(group, prefix: str = "") -> dict:
    out = {}
    for key, val in group.items():
        path = f"{prefix}/{key}" if prefix else key
        if isinstance(val, h5py.Dataset):
            out[path] = np.asarray(val)
        else:
            out.update(_walk(val, path))
    return out


def latent_kernels(ckpt_path: str) -> dict:
    """{layer_name: latent kernel} for every binary layer in an HGQ2-native checkpoint."""
    with zipfile.ZipFile(ckpt_path) as z:
        blob = z.read("model.weights.h5")
    with h5py.File(io.BytesIO(blob), "r") as f:
        weights = _walk(f)
    kernels = {}
    for path, arr in weights.items():
        m = re.fullmatch(r"layers/(bit_q_(?:einsum_)?dense[_0-9]*)/vars/0", path)
        if m and arr.ndim >= 2:
            kernels[m.group(1)] = np.asarray(arr, np.float64)
    return kernels


def main(ckpt_path: str = DEFAULT_CKPT) -> None:
    kernels = latent_kernels(ckpt_path)
    rows = []
    for name, w in kernels.items():
        alpha = w.mean()
        beta_ours = np.abs(w - alpha).mean() + EPS_BETA
        beta_ref = np.abs(w).mean()
        rows.append({
            "name": name, "shape": w.shape, "alpha": alpha,
            "beta_ours": beta_ours, "beta_ref": beta_ref,
            "abs_diff": abs(beta_ours - beta_ref),
            "rel_diff": abs(beta_ours - beta_ref) / beta_ours,
            "fx8_ours": fx8(beta_ours), "fx8_ref": fx8(beta_ref),
            "sign_zeros": int((np.sign(w - alpha) == 0).sum()),
        })
    rows.sort(key=lambda r: (len(r["name"]), r["name"]))

    print(f"checkpoint: {ckpt_path}")
    print(f"{len(rows)} binary (BitLinear) kernels\n")
    hdr = (f"{'layer':<26}{'shape':>12}{'alpha':>11}{'beta_ours':>11}{'beta_ref':>11}"
           f"{'|diff|':>11}{'rel':>9}{'fx8_ours':>10}{'fx8_ref':>10}  fx8 same")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        same = r["fx8_ours"] == r["fx8_ref"]
        print(f"{r['name']:<26}{str(r['shape']):>12}{r['alpha']:>11.2e}"
              f"{r['beta_ours']:>11.6f}{r['beta_ref']:>11.6f}{r['abs_diff']:>11.6f}"
              f"{r['rel_diff']:>9.2e}{r['fx8_ours']:>10.6f}{r['fx8_ref']:>10.6f}"
              f"  {'YES' if same else 'NO'}")

    rel = [r["rel_diff"] for r in rows]
    over = [r for r in rows if r["abs_diff"] > FX8_STEP]
    same_n = sum(r["fx8_ours"] == r["fx8_ref"] for r in rows)
    print(f"\nrelative disagreement: max {max(rel):.3e}  median {np.median(rel):.3e}"
          f"  mean {np.mean(rel):.3e}")
    print(f"fx8 grid step 2^-8 = {FX8_STEP:.6f}")
    print(f"layers with |diff| > one fx8 step (a different grid point is then guaranteed): "
          f"{len(over)}  {[r['name'] for r in over]}")
    print(f"fx8-encoded gamma identical under both conventions: {same_n}/{len(rows)}")
    print(f"sign(w - alpha) == 0 occurrences (would void the binary claim): "
          f"{sum(r['sign_zeros'] for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CKPT)
