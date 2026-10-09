#!/usr/bin/env python
"""
W1.4 -- Shrink exchange-rate table: local pricing of architecture cuts.

Counting-level only: no training, no synthesis, no promote/kill bands. Prices
three architecture cuts on the r8 stdnn flagship (d_model=32, H=4 heads,
2 blocks, FFN=64, T=10 tokens, 16 feats, 19,201 params) in modeled LUT, in two
regimes:

  UNFOLDED -- the as-synthesized RF=8 census frame (whole_model_rf8_stdnn.xml,
              tree-exact 3,910,515 LUT; COMPILER.md section 1).
  FOLDED   -- the token-fold projection frame (one physical per-token datapath,
              II = T; baseline projection 1,414,413 LUT, COMPILER.md section 3 /
              counting_results.json ["fold"]).

Anchors (measured, with sources):
  - LUT census categories: counting_results.json ["fold"]["census_categories"]
    (parsed from whole_model_rf8_stdnn.xml; rows sum to 3,910,515).
  - Measured fold ratios: dense 9.31x (e1 arm P 270,382 -> arm A v2 29,029,
    results/adder-graph/e1/RESULTS.md); attention core 6.46x (e1attn s12+s18
    219,748 -> f12+f18 33,994, results/adder-graph/e1attn/RESULTS.md); fold+FR
    composed 18.0x (arm C v2 15,042, e1/RESULTS.md). These establish that the
    fold projection frame is real, and that folded II=T is trigger-legal at
    layer scale (II=10 rewind, 16.5 ns / 17.5 ns < 25 ns).
  - FFN bit-adds from the real deployed sign matrices:
    counting_results.json ["small"] naive bits (fc1/fc2, both blocks).
  - alpha calibration LUT = 0.923 x bit-adds + 3,412 (R2 = 0.987):
    RANKING-GRADE ONLY -- its pre-registered 15% residual gate FAILED at 24.1%
    (COMPILER.md section 3). Every alpha-derived number printed here is
    "modeled, ranking-grade". FFN deltas use the slope only: the intercept is
    per-layer fixed overhead and cancels exactly (layers shrink, none deleted).

Scaling models (all "modeled" -- geometric scaling of measured census lines):
  - FFN 64->F : dense bit-adds linear in F (fc1 m=F, fc2 n=F). alpha slope.
  - T (n_part) 10->T : attention act x act ~ T^2 (score grid T x T); softmax,
    pooling, per-token glue ~ T; per-token dense stack ~ T in the UNFOLDED
    regime, T-INDEPENDENT in the FOLDED regime (one instance, II=T).
  - H 4->2 : task-directed model = attention core and softmax ~ linear in H,
    dense QKV/Wo unchanged at fixed d_model. A counting check (printed below)
    brackets this: at fixed d_model the act x act MAC count is H-INVARIANT
    (H * T^2 * d_k = T^2 * d_model; the measured DSP census 1,600 = 12,800/RF
    is per-MAC and thus H-independent), so the defensible savings are only the
    softmax rows (~H) plus part of the QK^T score-grid output overhead.

Accuracy is UNKNOWN for every cut: no trained arm exists at H=2, FFN<64, or
n_part<10 in the current campaigns. Every accuracy cell is a placeholder:
"requires training arm".

Runnable with .venv-hgq2 python; stdlib only; writes nothing.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CJ = REPO / "bnjettag" / "results" / "adder-graph" / "counting_results.json"

j = json.loads(CJ.read_text())
cats = j["fold"]["census_categories"]
ALPHA = j["calibration"]["alpha"]            # 0.9234 LUT/bit-add (ranking-grade)
DEVICE = j["constants"]["device_lut"]        # 1,728,000 (VU13P)
II_BUDGET = j["constants"]["ii_budget"]      # 11 (25 ns / 2.157 ns)
BX_NS = 25.0                                 # L1 bunch-crossing budget

T0, F0, H0, DMODEL = 10, 64, 4, 32           # flagship architecture

CENSUS_TOTAL = sum(cats.values())            # 3,910,515 tree-exact
SLICE = cats["dense_per_token"] / T0         # census-frame per-token dense slice
MUX = j["fold"]["mux_overhead_lut"]          # 15,456 (10:1 muxes @ 3 LUT/bit, modeled)
CTRL = j["fold"]["dense_folded"] - j["fold"]["per_token_slice_lut"] - MUX
GLUE_FOLDED = j["fold"]["glue_folded"]       # 40,539 (modeled)
FOLD_PROJ = j["fold"]["total"]               # 1,414,413

# FFN naive bit-adds and measured LUT (both blocks, fc1+fc2), real sign matrices
FFN_BITS = sum(l["naive"]["bits"] for l in j["small"] if "ffn" in l["name"])
FFN_MEAS = sum(l["measured_lut"]["per_instance"] for l in j["small"] if "ffn" in l["name"])

# RF=8 census split of the attention act x act einsums (COMPILER.md section 5)
QKT_RF8 = 272_938        # QK^T, config12+config38
AV_RF8 = 516_138         # attn.V, config18+config44
ATTN_DSP_RF8 = 1_600     # attention einsum DSPs at RF=8 (12,800 at RF=1)

WEIGHTS0 = sum(l["m"] * l["n"] for l in j["small"])   # 18,080 deployed sign weights


def d_ffn_slice(F):
    """Per-slice LUT saved by FFN 64->F. Modeled, ranking-grade (alpha slope)."""
    return ALPHA * FFN_BITS * (1.0 - F / F0)


def parts(T, F, H, regime, h_model="linear"):
    """Whole-model LUT decomposition under the scaling models above."""
    hfac = (H / H0) if h_model == "linear" else 1.0
    slice_lut = SLICE - d_ffn_slice(F)
    p = {}
    if regime == "unfolded":
        p["dense per-token (x T)"] = slice_lut * T
        p["glue per-token (~T)"] = cats["glue_other"] * T / T0
    elif regime == "folded":
        p["dense folded (1 slice+mux+ctrl)"] = slice_lut + MUX + CTRL
        p["glue folded"] = GLUE_FOLDED
    else:
        raise ValueError(regime)
    p["attention act x act (~T^2)"] = cats["einsum_actxact"] * (T / T0) ** 2 * hfac
    p["softmax (~T)"] = cats["softmax"] * (T / T0) * hfac
    p["pooling (~T)"] = cats["pooling"] * (T / T0)
    p["head (per-jet)"] = cats["dense_head"]
    p["einsum wrappers"] = cats["einsum_dense_wrap"]
    p["top-level (held fixed)"] = cats["top_glue"]
    return p


def total(T, F, H, regime, h_model="linear"):
    return sum(parts(T, F, H, regime, h_model).values())


def fmt(x):
    return f"{x:,.0f}"


def main():
    # ---- anchors reproduce exactly ----------------------------------------
    u0 = total(T0, F0, H0, "unfolded")
    f0 = total(T0, F0, H0, "folded")
    assert abs(u0 - CENSUS_TOTAL) < 2, (u0, CENSUS_TOTAL)
    assert abs(f0 - FOLD_PROJ) < 2, (f0, FOLD_PROJ)

    print("=" * 100)
    print("W1.4  SHRINK EXCHANGE-RATE TABLE  (counting-level; no training, no synthesis)")
    print("=" * 100)
    print(f"Flagship: d_model={DMODEL}, H={H0} heads, 2 blocks, FFN={F0}, "
          f"T={T0} tokens, 16 feats, 19,201 params")
    print(f"Device line: VU13P {fmt(DEVICE)} LUT.  Trigger: II <= {II_BUDGET} "
          f"(25 ns).  Unfolded measured II=8 @ 2.157 ns.")
    print(f"Anchors reproduced: unfolded {fmt(u0)} = census {fmt(CENSUS_TOTAL)}; "
          f"folded {fmt(f0)} = fold-only projection {fmt(FOLD_PROJ)}.")
    print(f"Measured fold ratios anchoring the folded frame: dense 9.31x "
          f"(270,382 -> 29,029, e1 arms P/A-v2), attention 6.46x "
          f"(219,748 -> 33,994, e1attn), fold+FR 18.0x (-> 15,042, e1 arm C-v2).")
    print("All non-baseline LUT figures: MODELED, RANKING-GRADE (alpha gate "
          "failed at 24.1% residual; scalings are geometric models of census lines).")

    # ---- FFN consistency check --------------------------------------------
    pred = ALPHA * FFN_BITS + 4 * j["calibration"]["beta"]
    print(f"\nFFN cross-check: alpha*bits+4*beta = {fmt(pred)} vs measured FFN "
          f"LUT/slice {fmt(FFN_MEAS)} ({pred / FFN_MEAS - 1:+.1%}) -- "
          f"calibration frame is coherent on these four layers.")

    # ---- single-cut exchange rates ----------------------------------------
    print("\n" + "-" * 100)
    print("1) SINGLE-CUT EXCHANGE RATES (Delta LUT saved vs baseline; "
          "negative params = weights removed)")
    print("-" * 100)
    hdr = (f"{'cut':<16}{'unfolded dLUT':>15}{'folded dLUT':>13}"
           f"{'d sign-weights':>15}{'  mechanism / regime note':<40}")
    print(hdr)
    singles = [
        ("H 4->2", 10, 64, 2, 0,
         "act x act + softmax ~H (DIRECTED model; see bracket below)"),
        ("FFN 64->48", 10, 48, 4, -128 * (F0 - 48),
         "dense bit-adds ~F; alpha slope (ranking-grade)"),
        ("FFN 64->32", 10, 32, 4, -128 * (F0 - 32),
         "dense bit-adds ~F; alpha slope (ranking-grade)"),
        ("T 10->8", 8, 64, 4, 0,
         "unfolded: dense+glue ~T, attn ~T^2 | folded: attn ~T^2 ONLY"),
        ("T 10->6", 6, 64, 4, 0,
         "unfolded: dense+glue ~T, attn ~T^2 | folded: attn ~T^2 ONLY"),
    ]
    for name, T, F, H, dw, note in singles:
        du = CENSUS_TOTAL - total(T, F, H, "unfolded")
        df = FOLD_PROJ - total(T, F, H, "folded")
        print(f"{name:<16}{fmt(du):>15}{fmt(df):>13}{dw:>15,}  {note}")
    print("Heads and n_part cuts remove ZERO parameters (QKV/Wo shapes fixed at "
          "d_model; weights shared across tokens).")
    print("FFN cuts remove parameters at a scale the capacity ladder says is "
          "already starved (COMPILER.md section 0).")

    # ---- the regime split (key point) -------------------------------------
    print("\n" + "-" * 100)
    print("2) THE REGIME SPLIT ON n_part  (the key point: what T buys depends "
          "on the regime)")
    print("-" * 100)
    print(f"{'T':>3}{'unfolded LUT':>14}{'x dev':>7}{'dense part':>12}"
          f"{'| folded LUT':>13}{'x dev':>7}{'dense part':>12}{'II':>4}"
          f"{'clk budget':>12}")
    for T in (10, 8, 6):
        pu = parts(T, F0, H0, "unfolded")
        pf = parts(T, F0, H0, "folded")
        tu, tf = sum(pu.values()), sum(pf.values())
        print(f"{T:>3}{fmt(tu):>14}{tu / DEVICE:>7.2f}"
              f"{fmt(pu['dense per-token (x T)']):>12}"
              f"{fmt(tf):>13}{tf / DEVICE:>7.2f}"
              f"{fmt(pf['dense folded (1 slice+mux+ctrl)']):>12}{T:>4}"
              f"{BX_NS / T:>9.3f} ns")
    print("\nUNFOLDED: the dense stack is T physical instances -> T buys dense "
          "area linearly, attention quadratically.")
    print("FOLDED:   the dense datapath is ONE instance at II=T -> T buys ZERO "
          "dense area. It buys (a) the ~T^2")
    print("          attention shrink and ~T softmax/pool, and (b) II slack: "
          "II=T <= 11 trivially, and the clock")
    print("          budget relaxes from 25/10 = 2.500 ns to 25/8 = 3.125 ns "
          "(T=8) or 25/6 = 4.167 ns (T=6).")
    print("          Illustrative: the measured fabric-norm failure clock "
          "3.103 ns (operating_points.md precedent,")
    print("          quoted in COMPILER.md section 3) breaks the budget at "
          "T=10 but would be legal at T=8.")
    print(f"          Attention einsum DSPs (measured {ATTN_DSP_RF8:,} @ RF=8) "
          f"model ~T^2: T=8 -> {fmt(ATTN_DSP_RF8 * 0.64)}, "
          f"T=6 -> {fmt(ATTN_DSP_RF8 * 0.36)} (H-independent; not binding).")

    # ---- the menu ---------------------------------------------------------
    print("\n" + "-" * 100)
    print("3) THE MENU  (modeled whole-model LUT; accuracy column is a "
          "PLACEHOLDER everywhere)")
    print("-" * 100)
    menu = [
        ("baseline T10/F64/H4", 10, 64, 4),
        ("H2", 10, 64, 2),
        ("FFN48", 10, 48, 4),
        ("FFN32", 10, 32, 4),
        ("T8", 8, 64, 4),
        ("T6", 6, 64, 4),
        ("T8 + FFN48", 8, 48, 4),
        ("T8 + H2", 8, 64, 2),
        ("T6 + FFN48", 6, 48, 4),
        ("T8 + FFN48 + H2", 8, 48, 2),
        ("T6 + FFN32 + H2", 6, 32, 2),
    ]
    print(f"{'config':<20}{'unfolded':>11}{'x dev':>7}{'folded':>11}{'x dev':>7}"
          f"{'d vs 1,414,413':>15}{'II':>4}{'clk<=':>9}{'accuracy':>15}")
    for name, T, F, H in menu:
        tu = total(T, F, H, "unfolded")
        tf = total(T, F, H, "folded")
        fits_u = "" if tu > DEVICE else " *"
        dflt = tf - FOLD_PROJ
        acc = "measured" if (T, F, H) == (T0, F0, H0) else "TRAINING ARM"
        print(f"{name:<20}{fmt(tu) + fits_u:>11}{tu / DEVICE:>7.2f}"
              f"{fmt(tf):>11}{tf / DEVICE:>7.2f}{fmt(dflt):>15}{T:>4}"
              f"{BX_NS / T:>6.2f} ns{acc:>15}")
    print("(* = fits the device unfolded. None do: even T6+FFN32+H2, under the "
          "H-generous directed model, stays over the line.)")
    print("H2 rows use the task-directed H-linear model -- the OPTIMISTIC end; "
          "see the bracket in section 4.")

    # ---- heads-cut sensitivity bracket ------------------------------------
    print("\n" + "-" * 100)
    print("4) HEADS-CUT SENSITIVITY (H 4->2, folded regime, T=10/F=64) -- the "
          "least reliable price in the menu")
    print("-" * 100)
    sm_save = cats["softmax"] * 0.5
    directed = FOLD_PROJ - (cats["einsum_actxact"] * 0.5 + sm_save)
    low = FOLD_PROJ - sm_save                       # softmax rows only
    mid = FOLD_PROJ - (sm_save + QKT_RF8 * 0.5)     # + QK^T score-grid overhead
    print(f"  directed model (core+softmax ~H):        {fmt(directed):>12}  "
          f"(saves {fmt(FOLD_PROJ - directed)})")
    print(f"  counting check, upper (softmax + QK^T/2): {fmt(mid):>12}  "
          f"(saves {fmt(FOLD_PROJ - mid)})")
    print(f"  counting check, lower (softmax rows only):{fmt(low):>12}  "
          f"(saves {fmt(FOLD_PROJ - low)})")
    print("  Why: at fixed d_model, act x act MACs = H*T^2*(d_model/H) = "
          "T^2*d_model -- H-INVARIANT. Physical")
    print(f"  evidence: attention DSPs {ATTN_DSP_RF8:,} @ RF=8 are per-MAC. "
          f"What halves with H: softmax rows (H*T)")
    print(f"  and the QK^T output/score count (H*T^2; QK^T census {fmt(QKT_RF8)}); "
          f"attn.V outputs (T*d_model) do not.")
    print("  Pricing this properly needs an E-C-style two-arm emission csynth "
          "at H=2 -- cheap, but out of scope here.")

    print("\nNOTES: FR composes on the folded slice (fold+FR projection "
          f"{fmt(j['fold_restruct']['fold_restruct_total'])}, "
          "counting_results.json) -- orthogonal to this menu.")
    print("Mux overhead held at the 10:1 price for T<10 (conservative); "
          "fc2 accumulator-width shrink at FFN<64 ignored")
    print("(second-order, direction: slightly more savings than modeled). "
          "No promote/kill bands: this is a pricing table.")


if __name__ == "__main__":
    main()
