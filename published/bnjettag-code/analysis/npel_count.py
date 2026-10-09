"""W1.3 — nanoPELICAN-shape counting probe (local; no training, no synthesis).

Question: if the flagship's parameter budget (~19.2k params, 5-class head) were spent
on a nanoPELICAN-shaped tagger — pay activation-x-activation ONCE at the input
(pairwise Minkowski invariants over T=10 constituents), then an all-linear
{-1,+1}-weight stack with NO attention einsums and NO softmax anywhere — what does a
counting-level LUT model say, in (a) the spatial (II~1) regime and (b) the
token/pair-folded regime, against the pre-registered bands:

    PROMOTE  if modeled whole model < 1.0 M csynth-equivalent LUT
             (>=20% under the fold+FR flagship projection 1,283,364)
    KILL     if >= 1.28 M

ACCURACY IS NOT ADDRESSED HERE. nanoPELICAN's 0.9718 AUC (arXiv:2310.16121, 21
params) is 2-class top-tagging, FP32, 80 constituents; our task is 5-class at T=10
under W1A8. Transfer is not assumed; the model has never been quantized or
synthesized by anyone (dossier: docs/literature/jet-tagging-transformers/2310.16121_nanopelican.md).

Every number is recomputed from raw csynth XML reports or from
results/adder-graph/counting_results.json (the alpha/beta calibration). The alpha
LUT model (LUT = 0.923 x bit-adds + 3,412, R^2 = 0.987) FAILED its pre-registered
15% residual gate at 24.1% (COMPILER.md par.3) — every alpha-derived figure below is
**modeled, ranking-grade**, not synthesis-grade.

Run:  .venv-hgq2/bin/python bnjettag/code/analysis/npel_count.py
Outputs: bnjettag/results/adder-graph/npel/npel_counting.json + console table.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adder_graph_study import tree_bit_adds, naive_cost  # noqa: E402  (reused machinery)

REPO = Path(__file__).resolve().parents[2]                # bnjettag/
AG = REPO / "results/adder-graph"
OUT_DIR = AG / "npel"

# ---------------------------------------------------------------- measured anchors

def xml_top(path):
    """Top-level (LUT, DSP, II) from a csynth report."""
    r = ET.parse(path).getroot()
    res = r.find(".//AreaEstimates/Resources")
    lut = int(res.find("LUT").text)
    dsp_el = res.find("DSP") if res.find("DSP") is not None else res.find("DSP48E")
    dsp = int(dsp_el.text)
    ii_el = r.find(".//PerformanceEstimates/SummaryOfOverallLatency/"
                   "PipelineInitiationInterval")
    ii = int(ii_el.text) if ii_el is not None else None
    return lut, dsp, ii


def load_anchors():
    cr = json.load(open(AG / "counting_results.json"))
    a = {"alpha": cr["calibration"]["alpha"],          # 0.9234 LUT/bit-add
         "beta": cr["calibration"]["beta"],            # 3,412 LUT/module
         "device_lut": cr["constants"]["device_lut"],  # 1,728,000 (VU13P)
         "census": cr["fold"]["census_categories"],
         "fold_fr_target": 1_283_364}                  # COMPILER.md par.3 fold+FR projection

    # E-C act-x-act arms (e1attn/RESULTS.md; raw XMLs re-parsed here).
    # Types (RESULTS.md method): Q/K ap_fixed<13,9>, scores ap_fixed<29,21>,
    # softmax out ap_ufixed<23,1>, ctx acc ap_fixed<40,14> -> ap_fixed<15,8>.
    s12 = xml_top(AG / "e1attn/s12/prj_s12/sol1/syn/report/csynth.xml")
    f12 = xml_top(AG / "e1attn/f12/prj_f12/sol1/syn/report/csynth.xml")
    s18 = xml_top(AG / "e1attn/s18/prj_s18/sol1/syn/report/csynth.xml")
    f18 = xml_top(AG / "e1attn/f18/prj_f18/sol1/syn/report/csynth.xml")
    assert (s12[0], f12[0], s18[0], f18[0]) == (29602, 4789, 190146, 29205), \
        "e1attn raw reports moved or changed"
    a["axa_lut_per_mac"] = s12[0] / 3200.0             # 9.25; 3,200 = s12 DSP = MACs
    a["axa_dsp_per_mac"] = s12[1] / 3200.0             # 1.00 measured
    a["fold_axa"] = (s12[0] + s18[0]) / (f12[0] + f18[0])   # 6.46
    a["fold_axa_dsp"] = s12[1] / f12[1]                # 10.0 exactly

    # E1 dense arms (e1/RESULTS.md v2; raw XMLs re-parsed here).
    p = xml_top(AG / "e1/p/prj_p/sol1/syn/report/csynth.xml")
    av2 = xml_top(AG / "e1/a/prj_a/sol1/syn/report/csynth_v2_rewind.xml")
    b = xml_top(AG / "e1/b/prj_b/sol1/syn/report/csynth.xml")
    cv2 = xml_top(AG / "e1/c/prj_c/sol1/syn/report/csynth_v2_rewind.xml")
    assert (p[0], av2[0], b[0], cv2[0]) == (270382, 29029, 130512, 15042), \
        "e1 raw reports moved or changed"
    a["fold_dense"] = p[0] / av2[0]                    # 9.31
    a["fr_dense"] = p[0] / b[0]                        # 2.07 (realized, not counted 3.07)
    a["composed_dense"] = p[0] / cv2[0]                # 18.0

    # E1 parity offset: standalone-emitter frame vs census frame, measured on the
    # same layer (arm P vs the census's 10 instances of bit_block_0_ffn_fc1).
    ffn = next(x for x in cr["small"] if x["name"] == "bit_block_0_ffn_fc1")
    census_layer = ffn["measured_lut"]["per_instance"] * ffn["measured_lut"]["instances"]
    a["parity"] = p[0] / census_layer                  # 1.151
    return a


# ---------------------------------------------------------------- the architecture

# nanoPELICAN shape (arXiv:2310.16121): input = TxT pairwise Minkowski dot products;
# LinEq2->2 (6-aggregator nano basis) -> ReLU -> LinEq2->0 (sum + trace) -> head.
# Scaled to the flagship budget with the parameter mass moved into a per-jet
# {-1,+1} dense stack after the invariant reduction (their C_hidden -> our C).
T = 10
C = 48            # Eq2->2 hidden channels
N_BASIS = 6       # nano basis size (6 of PELICAN's 15 aggregators)
N_EQ20 = 2        # LinEq2->0 aggregators: total sum + trace  -> 2C invariants
D1, D2, N_CLASS = 128, 48, 5
A = 8             # activation width everywhere (W1A8 discipline, requantize between stages)
FLAGSHIP_PARAMS = 19_201   # r8 stdnn flagship (RESEARCH.md par.2)


def param_count():
    eq22 = N_BASIS * C + C                       # 6C binary weights + C bias
    inv = N_EQ20 * C                             # 96 invariants (mixing deferred to stack)
    d = (inv * D1 + D1) + (D1 * D2 + D2) + (D2 * N_CLASS + N_CLASS)
    return eq22 + d, dict(eq22=eq22, invariants=inv, dense=d)


def acc_w(n_terms):
    """Exact no-overflow accumulator width for a sum of n_terms A-bit values."""
    return A + int(np.ceil(np.log2(n_terms)))


# ---------------------------------------------------------------- component pricing

def price(anch):
    al, be = anch["alpha"], anch["beta"]
    rng = np.random.default_rng(20260726)        # matrices are shape-only here
    comp = []                                    # (name, frame, spatial, folded, note)

    # -- 1. pairwise Minkowski block (the ONE act-x-act payment) ------------------
    # d_ij = E_i E_j - px_i px_j - py_i py_j - pz_i pz_j from the A8 4-momentum
    # features already in the input (px/py/pz/e are among the 16 constituent
    # features — code/training/qkerasModel.py line 175). 4 MACs/pair; symmetric:
    # 45 off-diagonal + 10 diagonal = 55 computed, mirror is wiring.
    n_pairs, n_pairs_full = 55, 100
    macs = 4 * n_pairs
    # Exchange rate: s12 QK^T spatial = 29,602 LUT / 3,200 MACs = 9.25 LUT/MAC at
    # ap_fixed<13,9> x ap_fixed<13,9> -> ap_fixed<29,21>. Our MACs are 8x8 -> 18-bit
    # — strictly narrower, so the rate is conservative. Emitter frame -> x parity.
    pw_sp = macs * anch["axa_lut_per_mac"] * anch["parity"] + be
    pw_fo = macs * anch["axa_lut_per_mac"] * anch["parity"] / anch["fold_axa"] + be
    pw_dsp_sp = int(round(macs * anch["axa_dsp_per_mac"]))
    pw_dsp_fo = int(round(pw_dsp_sp / anch["fold_axa_dsp"]))
    comp.append(dict(name=f"pairwise Minkowski block ({n_pairs} pairs, {macs} MACs)",
                     spatial=pw_sp, folded=pw_fo,
                     dsp_spatial=pw_dsp_sp, dsp_folded=pw_dsp_fo,
                     note="s12 rate 9.25 LUT/MAC x1.151 parity; fold 6.46x (e1attn)"))
    pw_full_sp = 4 * n_pairs_full * anch["axa_lut_per_mac"] * anch["parity"] + be

    # -- 2. basis aggregation for LinEq2->2 (weightless adds, computed once) ------
    # Row sums (10 trees over 10), total (tree over the 10 row sums), trace
    # (tree over 10 diagonal entries); transpose/col-sums free by symmetry,
    # broadcasts are wiring. d_ij requantized to A8 first.
    _, b_row, _ = tree_bit_adds(T, A, acc_w(T))
    _, b_tot, _ = tree_bit_adds(T, acc_w(T), acc_w(T * T))
    _, b_trc, _ = tree_bit_adds(T, A, acc_w(T))
    agg_bits = T * b_row + b_tot + b_trc
    agg = al * agg_bits + be
    comp.append(dict(name="LinEq2->2 basis aggregation (weightless)",
                     spatial=agg, folded=agg, dsp_spatial=0, dsp_folded=0,
                     note=f"{agg_bits} bit-adds; tiny — left unfolded in both regimes"))

    # -- 3. LinEq2->2 channel mixing: the per-position +-1 dense ------------------
    # Each of T^2=100 positions x C channels mixes 6 basis values + bias: a 48x6
    # {-1,+1} dense instanced 100x over positions -> the fold axis of this shape.
    S_mix = rng.choice(np.array([-1, 1], np.int8), size=(C, N_BASIS))
    mix1 = naive_cost(S_mix, A, acc_w(N_BASIS + 1))
    mix_bits = mix1["bits"] * T * T
    mix_sp = al * mix_bits + be                   # one emitted module (compiler frame)
    mix_fo = al * mix_bits / anch["fold_dense"] + be
    comp.append(dict(name=f"LinEq2->2 channel mixing (+-1, {C}x{N_BASIS} @ {T*T} pos)",
                     spatial=mix_sp, folded=mix_fo, dsp_spatial=0, dsp_folded=0,
                     note="fold 9.3x over positions (e1 arm A v2); beta once/module"))
    # hls4ml-style per-position-module emission (beta x100) — sensitivity only:
    mix_sp_permod = T * T * (al * mix1["bits"] + be)

    # -- 4. ReLU + requantize glue on the mixing output (G1, counted) -------------
    # Per value: one rounding add at accumulator width + sign-mux at A bits.
    n_mix_vals = C * T * T
    g1_mix_bits = n_mix_vals * (acc_w(N_BASIS + 1) + A)
    g1_mix_sp = al * g1_mix_bits
    g1_mix_fo = g1_mix_sp / anch["fold_dense"]    # elementwise, folds with its stage
    comp.append(dict(name=f"ReLU+requant glue on {n_mix_vals} values (G1 counted)",
                     spatial=g1_mix_sp, folded=g1_mix_fo, dsp_spatial=0, dsp_folded=0,
                     note="counted 19 bit-adds/value; census beta-carry ReLU risk in caveats"))

    # -- 5. LinEq2->0: total sum + trace per channel (weightless) -----------------
    _, b_sum, _ = tree_bit_adds(T * T, A, acc_w(T * T))
    _, b_tr2, _ = tree_bit_adds(T, A, acc_w(T))
    eq20_bits = C * (b_sum + b_tr2)
    eq20_sp = al * eq20_bits + be
    eq20_fo = al * eq20_bits / anch["fold_axa"] + be   # conservative: 6.46x not 9.3x
    comp.append(dict(name=f"LinEq2->0 sum+trace ({C} ch -> {N_EQ20 * C} invariants)",
                     spatial=eq20_sp, folded=eq20_fo, dsp_spatial=0, dsp_folded=0,
                     note="weightless trees; folded 10x over channels at the 6.46x rate"))

    # -- 6. per-jet {-1,+1} dense stack: 96 -> 128 -> 48 -> 5 ---------------------
    # NO fold axis exists here (single instance per jet, like head_fc1/fc2 in the
    # 1.414M projection) — the task's 9.3x dense-fold rate is NOT applied; the
    # folded regime uses measured realized FR 2.07x (e1 arm B) instead.
    shapes = [(D1, N_EQ20 * C), (D2, D1), (N_CLASS, D2)]
    dn_bits = 0
    for m, n in shapes:
        S = rng.choice(np.array([-1, 1], np.int8), size=(m, n))
        dn_bits += naive_cost(S, A, acc_w(n + 1))["bits"]
    dn_sp = al * dn_bits + len(shapes) * be
    dn_fr = al * dn_bits / anch["fr_dense"] + len(shapes) * be
    comp.append(dict(name="per-jet +-1 dense stack 96->128->48->5 (naive | FR 2.07x)",
                     spatial=dn_sp, folded=dn_fr, dsp_spatial=0, dsp_folded=0,
                     note="no fold axis (per-jet); folded regime = FR (e1 arm B realized)"))

    # -- 7. glue on the dense stack (G1 counted) ----------------------------------
    g1_dn_bits = D1 * (acc_w(N_EQ20 * C + 1) + A) + D2 * (acc_w(D1 + 1) + A)
    g1_dn = al * g1_dn_bits
    comp.append(dict(name="ReLU+requant glue on dense stack (176 values)",
                     spatial=g1_dn, folded=g1_dn, dsp_spatial=0, dsp_folded=0,
                     note="per-jet, unfolded in both regimes"))

    # -- 8. top-level glue: census face value (same bracketing as 1.414M proj.) ---
    top = anch["census"]["top_glue"]
    comp.append(dict(name="top-level glue (census face value)",
                     spatial=float(top), folded=float(top), dsp_spatial=0, dsp_folded=0,
                     note="whole_model_rf8_stdnn.xml census line, kept unscaled"))

    # -- removed-by-shape lines (the point of the probe) --------------------------
    removed = dict(attention_einsums=anch["census"]["einsum_actxact"],
                   softmax=anch["census"]["softmax"],
                   pooling=anch["census"]["pooling"],
                   einsum_dense_wrap=anch["census"]["einsum_dense_wrap"])

    extras = dict(mix_sp_permod=mix_sp_permod, pw_full_sp=pw_full_sp,
                  dn_bits=dn_bits, mix_bits=mix_bits, eq20_bits=eq20_bits,
                  g1_bits=g1_mix_bits + g1_dn_bits)
    return comp, removed, extras


# ---------------------------------------------------------------- glue sensitivity

def census_glue_proxy(anch):
    """G2: flagship census glue (374,675 LUT) scaled by glue-touched activation
    count. Flagship: per token 32 (input_proj) + 2 blocks x (96 QKV + 32 attn_out
    + 32 resid + 64 ffn_h + 32 ffn_out + 32 resid) = 608/token x10 + 32 pool
    + 64 head_fc1 = 6,176. Ours: 55 pairwise + 4,800 mixing + 96 invariants
    + 176 dense = 5,127."""
    flag_vals = 10 * (32 + 2 * (96 + 32 + 32 + 64 + 32 + 32)) + 32 + 64
    our_vals = 55 + 48 * 100 + 96 + (128 + 48)
    g2 = anch["census"]["glue_other"] * our_vals / flag_vals
    return g2, flag_vals, our_vals


# ---------------------------------------------------------------- main

def main():
    anch = load_anchors()
    total_params, pbreak = param_count()
    comp, removed, extras = price(anch)

    sp = sum(c["spatial"] for c in comp)
    fo = sum(c["folded"] for c in comp)
    dsp_sp = sum(c["dsp_spatial"] for c in comp)
    dsp_fo = sum(c["dsp_folded"] for c in comp)

    # sensitivity variants
    g1_terms = [c for c in comp if "glue" in c["name"] and "top-level" not in c["name"]]
    g1_sp = sum(c["spatial"] for c in g1_terms)
    g1_fo = sum(c["folded"] for c in g1_terms)
    g2, flag_vals, our_vals = census_glue_proxy(anch)
    # G2 folded: the mixing-output share folds with its stage, the rest is per-jet
    g2_fo = (g2 * (4800 / our_vals)) / anch["fold_dense"] + g2 * (1 - 4800 / our_vals)
    sens = {
        "headline_spatial": sp,
        "headline_folded": fo,
        "G2_census_glue_spatial": sp - g1_sp + g2,
        "G2_census_glue_folded": fo - g1_fo + g2_fo,
        "mixing_per_position_beta_spatial":
            sp - next(c["spatial"] for c in comp if "mixing" in c["name"])
            + extras["mix_sp_permod"],
        "no_toplevel_folded": fo - anch["census"]["top_glue"],
        "alpha_band_+24pct_folded":
            (fo - anch["census"]["top_glue"]) * 1.241 + anch["census"]["top_glue"],
        "pessimistic_composite_folded":
            ((fo - g1_fo - anch["census"]["top_glue"]
              - next(c["folded"] for c in comp if "mixing" in c["name"])
              + extras["mix_sp_permod"] / anch["fold_dense"]) * 1.241
             + g2_fo * 1.241 + anch["census"]["top_glue"]),
    }

    bands = dict(promote_lt=1_000_000, kill_ge=1_280_000,
                 must_beat=anch["fold_fr_target"],
                 must_beat_by=0.20)
    margin_vs_target = 1 - fo / bands["must_beat"]
    verdict = ("PROMOTE" if fo < bands["promote_lt"]
               and margin_vs_target >= bands["must_beat_by"]
               else ("KILL" if fo >= bands["kill_ge"] else "GRAY"))

    # ------------------------------------------------------------ console report
    W = 74
    print("=" * W)
    print("W1.3  nanoPELICAN-shape counting probe  (modeled, ranking-grade)")
    print("=" * W)
    print(f"shape: TxT={T}x{T} Minkowski d_ij -> LinEq2->2 nano ({N_BASIS}-basis, "
          f"C={C}) -> ReLU\n       -> LinEq2->0 (sum+trace -> {N_EQ20*C}) -> "
          f"+-1 dense {N_EQ20*C}->{D1}->{D2}->{N_CLASS}")
    print(f"params: {total_params:,} ({pbreak})  vs flagship {FLAGSHIP_PARAMS:,} "
          f"({100*total_params/FLAGSHIP_PARAMS - 100:+.2f}%)")
    print(f"anchors: alpha={anch['alpha']:.4f} beta={anch['beta']:.0f} "
          f"parity={anch['parity']:.4f}")
    print(f"         fold_dense={anch['fold_dense']:.3f} fr_dense={anch['fr_dense']:.3f} "
          f"fold_axa={anch['fold_axa']:.3f} axa {anch['axa_lut_per_mac']:.3f} LUT/MAC")
    print("-" * W)
    print(f"{'component':<52}{'spatial':>10}{'folded':>10}")
    for c in comp:
        print(f"{c['name'][:52]:<52}{c['spatial']:>10,.0f}{c['folded']:>10,.0f}")
    print("-" * W)
    print(f"{'TOTAL (census-equivalent LUT, modeled ranking-grade)':<52}"
          f"{sp:>10,.0f}{fo:>10,.0f}")
    print(f"{'DSP (pairwise block only)':<52}{dsp_sp:>10,}{dsp_fo:>10,}")
    print(f"removed by shape (census lines): attention {removed['attention_einsums']:,} "
          f"+ softmax/pool/wrap "
          f"{removed['softmax']+removed['pooling']+removed['einsum_dense_wrap']:,}")
    print("-" * W)
    print("sensitivities (folded unless noted):")
    for k, v in sens.items():
        print(f"  {k:<44}{v:>12,.0f}")
    print("-" * W)
    print(f"bands: PROMOTE < {bands['promote_lt']:,}; KILL >= {bands['kill_ge']:,}; "
          f"must beat {bands['must_beat']:,} by >= {bands['must_beat_by']:.0%}")
    print(f"folded headline {fo:,.0f} beats fold+FR target by {margin_vs_target:.1%}")
    print(f"VERDICT: {verdict}   (accuracy on the 5-class task NOT addressed here)")
    print("=" * W)

    # ------------------------------------------------------------ JSON artifact
    OUT_DIR.mkdir(exist_ok=True)
    out = dict(anchors={k: v for k, v in anch.items() if k != "census"},
               census=anch["census"], params=total_params, param_breakdown=pbreak,
               components=comp, removed_by_shape=removed, extras=extras,
               totals=dict(spatial=sp, folded=fo, dsp_spatial=dsp_sp, dsp_folded=dsp_fo),
               sensitivities=sens, bands=bands,
               margin_vs_fold_fr=margin_vs_target, verdict=verdict)
    with open(OUT_DIR / "npel_counting.json", "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(f"wrote {OUT_DIR / 'npel_counting.json'}")


if __name__ == "__main__":
    main()
