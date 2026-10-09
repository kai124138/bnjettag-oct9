#!/usr/bin/env python3
"""Single source for DELTA.md tables and delta.json (Delta, 2026-09-27).

Every derived floor below uses the arbiter-v2 accounting (campaigns/2026-09-26-training-batch/
review/STUDY_arbiter_v2.md, "Independent checks") plus the two terms the CPU trace names
(decisions.md 2026-09-27 "chang0926 code"): softmax floor = 16*H*T*S + 4*(H*T*S - H*T) (tables at
their 4-bit minimum) + H*T*S (the exp input stays SAT: 1 bit per score entry; H*T*k for Linformer)
+ a LUT term (sum(2^b_in * b_out) * 1e-4; 13 EBOPs at A07, 6 at E in the trace, modelled here as
floor(13*H/4) per block, a fit to those two points, never above 13 at H <= 4). Dense layers cost
N*fan_in*fan_out*b_a*b_w (b_w = 1 for binary weights); Q.K and A.V cost T*S*d*b*b. With these terms
the formula reproduces the trace exactly for A07 and E. Derived values are shape arithmetic, not
floors; floor_traced carries the CPU trace where the architecture equals a traced config.
"""
import itertools, json, math, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
S_E_EXAMPLE = 112.6   # s/epoch, anchor STUDY Budget: 100.09 s scaled to 558,000 jets; batch 256; unverified projection
K = 6

# ---------------------------------------------------------------- floors (derived)
def lut_term(H):
    return (13 * H) // 4   # fit to the trace (A07 H=4: 13; E H=2: 6); label in floor_derived

def softmax_floor(H, T, S, tb=4, exp_in=1, lut=True):
    hts = H * T * S
    return tb * tb * hts + tb * (hts - H * T) + exp_in * hts + (lut_term(H) if lut else 0)

def dense_1bit(N=64, nf=3, d=32, ffn=32, L=1, head=None, C=5, wbits=1, wbits_in=None):
    """Dense and head EBOPs at 1-bit activations; weight bits multiply (EBOPs = b_a * b_w)."""
    wbits_in = wbits if wbits_in is None else wbits_in
    per_block = 4 * N * d * d + 2 * N * d * ffn
    head_cost = (d * d + d * C) if head is None else sum(a * b for a, b in zip([d] + head, head + [C]))
    return wbits_in * N * nf * d + wbits * (L * per_block + head_cost)

def arch_floors(N=64, nf=3, d=32, H=4, ffn=32, L=1, attn="softmax", k=None, tb=4, qk_min=0, head=None,
                exp_in=1, lut=True, wbits=1, wbits_in=None, wbits_unknown=False):
    """Return (floor0, floor1) derived. attn in softmax|linformer|relu|none."""
    if attn == "none":
        return None, None
    S = k if attn == "linformer" else N
    sm = 0 if attn == "relu" else softmax_floor(H, N, S, tb, exp_in, lut)
    qk1 = N * S * d
    proj = 2 * d * N * k if attn == "linformer" else 0
    f0 = L * (sm + qk_min * qk_min * qk1)
    if wbits_unknown:
        return f0, None
    f1 = dense_1bit(N, nf, d, ffn, L, head, wbits=wbits, wbits_in=wbits_in) + L * (sm + qk1 + qk1 + wbits * proj)
    return f0, f1

# provenance: with the exp-input and LUT terms off, the formula is the arbiter-v2 one
assert arch_floors(exp_in=0, lut=False) == (326656, 989344)
assert arch_floors(d=24, H=2, exp_in=0, lut=False) == (163328, 611000)
# with them on, it equals the CPU trace (static_floors_arms_s1.json, arms a and e)
assert arch_floors() == (343053, 1005741), arch_floors()
assert arch_floors(d=24, H=2) == (171526, 619198), arch_floors(d=24, H=2)
assert dense_1bit() == 400544 and dense_1bit(d=24) == 251064

TRACE_LABEL = ("CPU trace on synthetic input (n = 256, seed 0), staged in campaigns/2026-09-26-training-batch/code/ "
               "(evidence/static_floors_arms_s1.json, static_floors_trace_step2.json; decisions.md 2026-09-27 'chang0926 code'; "
               "staged tree on base source sha 7f9e9307, committed at 72a1290, not the final anchor sha, not shipped); not results")
TRACED = {
    "A07": {"floor0": 343053, "floor1_alive": 1005741, "quantizer": "[D19] (Chang set)", "arms": "a, c, d, f, r under the pre-[D21] arm names (old A, C, D, F, R were A07; old F = A07 without PE); after [D21] A07 is arm A07-350 (350k, descriptive) and arm C (5M)"},
    "E": {"floor0": 171526, "floor1_alive": 619198, "quantizer": "[D19] (Chang set)", "arms": "e under the pre-[D21] arm names; after [D21] E is arm A (350k), and B, D, R run on it"},
    "A07_old_quantizer": {"floor0": 4580398, "floor1_alive": 4580398, "quantizer": "old (SAT k=1, fixed 10-bit softmax, fixed tables)", "arms": "a07-current (trace step 2)"},
}
A07_ARCH = dict(N=64, nf=3, d=32, H=4, ffn=32, L=1, attn="softmax", k=None, tb=4, qk_min=0, head=None,
                exp_in=1, lut=True, wbits=1, wbits_in=None, wbits_unknown=False)
E_ARCH = dict(A07_ARCH, d=24, H=2)
NEAR_FLOOR_H = 0.10

def headroom(f0, f1, target):
    if f0 is None or f1 is None:
        return None
    if f0 >= target:
        return "STATIC_INFEASIBLE"
    return min((target - f0) / (f1 - f0), 1.0)

# ---------------------------------------------------------------- patches
PATCHES = {
 # slug: (tier, lines, file(s), what)
 "lr-schedule-variants": ("T1", "~15", "ablation.learning_rate", "m_mul, t_mul and a linear warm-up on top of the anchor [A1] Chang schedule; unit test at restart boundaries"),
 "beta-schedule-s-runner": ("T1", "~12", "ablation.run_training", "honour train.ebops.controller 'schedule' with hgq2 PieceWiseSchedule in the S runner (inert today)"),
 "softmax-table-min-bits": ("T1", "~5", "qat.softmax (after [A20])", "expose the minimum width of the trainable exp/inv tables (Chang bc=Min(4))"),
 "qk-stream-min-bits": ("T1", "~10", "qat.stream_iq", "lower bound on the Q/K stream widths (anti-collapse width floor)"),
 "ebops-group-weight": ("T1", "~30", "qat + ablation", "per-layer-group multiplier on the beta*EBOPs term (attention group vs rest)"),
 "attn-linformer": ("T2", "~40-60 + export", "qat block, convert_binary", "binary sequence projections E,F (N->k) on K and V; hgq2 0.1.9 has no QLinformerAttentionT"),
 "attn-relu-over-n": ("T2", "~80-150 + export", "qat.softmax branch", "ReLU(scores)/N attention (N=64 is a shift); no exp/inv tables"),
 "body-deepsets": ("T2", "~80-120 + export", "new builder beside qat.build_qat_model", "binary Deep Sets body (phi MLP, pooled context add, rho MLP), dims re-implemented from the Sun et al. topology, no code lifted"),
 "act-granularity-element": ("T1", "~10-20", "qat.act_iq", "act_granularity 'element' (per position and channel, Chang value-wise)"),
 "act-init-f0": ("T1", "~20 (0 if [A20] exposes it)", "qat._free_act, ablation.matching_initialization", "fixed activation init f0 with i tracked (Chang f0=7)"),
 "pre-block-tanh-lut": ("T1", "~12 train + export new", "qat block, convert_binary", "hgq2 QAffinedUnaryFunctionLUT('tanh') before attention and before the FFN; EBOPs of its table quantizers checked at W1"),
 "head-dims": ("T1", "~25 + export", "qat head, ablation.expected_binary_layers, binarize, convert_binary", "arch.head_dims list (Chang 32/32/32)"),
 "binarizer-center-flag": ("T1", "~10", "qat.bitnet_binary_ste, binarize.absmean_binarize", "quant.binary_center false: uncentered absmean"),
 "ste-variants": ("T1", "~25", "qat.bitnet_binary_ste + epoch callback", "quant.ste in {bounded (default), clip_identity, ede}; EDE temperature restarted every lr cycle or annealed once"),
 "bop-optimizer": ("T2", "~60-100", "new optimizer + variable routing", "Bop on binary latents (flip on EMA-gradient threshold); Adam on everything else"),
 "latent-clip": ("T1", "~10", "qat kernels (constraint)", "clip latent kernels to [-c, c] after each step"),
 "beta-mode": ("T1", "~30 incl. export", "qat.bitnet_binary_ste, binarize", "quant.beta_mode in {absmean (default), absmean_pow2, learned_pow2}"),
 "channel-gain-pow2": ("T1", "~60 incl. per-channel binary gate + export", "qat, ablation.binary_gate, binarize, convert_binary", "per-output-channel power-of-two gain (shift) after the +-1 matmul; gate becomes two symmetric values per channel; DSP audit required"),
 "pre-quant-shift": ("T1", "~20-30", "qat.act_iq call sites", "learnable per-channel additive shift before each activation quantizer (RSign shift only; no slope)"),
 "init-from-checkpoint": ("T1", "~20", "ablation.matching_initialization", "copy latents from a named checkpoint (the FP teacher) instead of the seed init"),
 "kd-unblock-s-runner": ("T1", "~30", "run_engram.validate_cfg, run_study, ablation", "allow experiment.distillation in S and supply teacher logits on the S path"),
 "kd-attention-map": ("T1", "~30-40", "ablation loss + teacher tap", "attention-map distillation term (teacher with the same heads)"),
 "latent-ema-eval": ("T1", "~20", "ablation epoch loop", "EMA of latents, re-binarized; candidate checkpoint evaluated on the EMA weights"),
 "augment-eta-phi-reflect": ("T1", "~15-25", "ablation.make_epoch_step (train batches only)", "random eta_rel and phi_rel sign flips per jet; never on validation or ROC-test"),
 "pt-gate-threshold": ("T1", "~5 (0 if [A3] exposes it)", "anchor [A3] loaders + prepare_cache", "gate threshold as a key (0 = ungated); new cache per value"),
 "gated-key-mask": ("T1", "~20-40", "qat attention scores, cache emits mask", "additive mask on gated/padded key positions before the softmax"),
 "std-real-slots": ("T1", "~10", "prepare_cache input_std", "standardization statistics over real (non-gated) slots only"),
 "derived-input-features": ("T1", "~25", "prepare_cache, run_engram.validate_cfg", "append log pT and Delta R computed from the three L1 features; relax the 3-feature assert"),
 "weight-scheme-baselines": ("T1", "~25", "run_engram.validate_cfg, qat", "admit quant.weight none / int8_absmax and quant.layer_weight_override for labelled baselines and teachers"),
 "ternary-absmean": ("T1", "~30", "qat, ablation.binary_gate (labelled ternary gate)", "ternary {-b,0,+b} absmean baseline"),
 "hgq-learnable-weights": ("T2", "~40-60", "qat build branch", "HGQ kbi learnable weight widths (the branch kbi_learnable never had)"),
 "accumulator-ebops-metric": ("T1", "~20", "ebops_calc per_layer", "closed-form accumulator bits b_act + ceil(log2 fan_in) per binary layer, reported beside native EBOPs"),
 "diag-sign-flips": ("T1", "~30", "epoch observer", "sign snapshot per layer: flip-flop ratio per epoch, C2I ratio"),
 "diag-attention": ("T1", "~40", "eval script", "attention entropy / log(n_valid) with gated keys masked in the diagnostic pass; attention-ablation delta (A.V replaced by mean V)"),
 "diag-beta-trajectory": ("T1", "~10", "epoch observer", "per-layer beta and latent |w|/beta histogram"),
 "diag-input-proj-rows": ("T1", "~15", "checkpoint reader", "distinct sign rows of input_proj"),
 "diag-latent-binary-gap": ("T1", "~20", "eval script", "validation accuracy with latent kernels in place of q*beta"),
 "screen-collapse-stop": ("T1", "~15", "ablation epoch loop, run_pack", "collapse rule: stop and record when validation accuracy <= 0.25 for 10 consecutive epochs after epoch 20"),
}

DIAG_ALWAYS = ["diag-attention", "screen-collapse-stop", "accumulator-ebops-metric"]

# ---------------------------------------------------------------- singles
T350, T5M = 350000, 5000000
S = []
def single(id_, name, fam, cards, mech, tier, delta, patches, tried, targets, pairing, pred, diag,
           horizon=500, arch=None, anchor_keys=None, fallbackE="apply", if_floor="5M-only", kind="single",
           targets_confirm=None, wave="W2", note=""):
    S.append(dict(id=id_, name=name, family=fam, tier=kind, cards=cards, mechanisms=mech, code_tier=tier,
                  combo_of=[], config_delta=delta, code_changes=patches, anchor_keys=anchor_keys or [],
                  tried=tried, targets=targets, targets_confirm=targets_confirm or targets,
                  pairing=pairing, prediction=pred, diagnostic=diag, horizon_screen=horizon,
                  arch=arch or {}, fallback_E=fallbackE, if_floor_fails=if_floor, wave=wave, note=note))

U = "untried"
TS = [T350, T5M]
# F: floor reduction / attention cost
single("M001","Two heads at d32","F",["A01","tried D6"],["M5","M7"],"T0",{"arch.n_heads":2},[],
  "tried-failed (A08: H=2 at N=16, never feasible under the old SAT quantizer, TR23:33); retried because the D19 softmax floor halves with H (derived 171,526 incl. the SAT exp-input term)",
  TS,"paired-if-hash (Wq/Wk/Wv reshape per head; [A17]-style kernel_hashes check, else Welch)",
  "feasible at 350k in more seeds than A07-350; accuracy at 5M flat to slightly down","EBOPs split (softmax / QK / AV / dense), Q/K and V 0-bit fractions, entropy/log n_valid",
  arch=dict(H=2),fallbackE="noop at 350k (E already has 2 heads); 5M cell kept",if_floor="drop")
single("M002","One head at d32","F",["A01","tried D6"],["M5","M7"],"T0",{"arch.n_heads":1},[],
  "tried-failed-with-mechanism (B01 at N=16, 3 seeds, never feasible, old quantizer, TR23:49); retried for the D19 floor (derived 85,763 incl. the SAT exp-input term)",
  TS,"paired-if-hash","350k feasibility up; accuracy at 5M below M001","as M001",arch=dict(H=1),
  fallbackE="restate as E with 1 head",if_floor="drop")
single("M003","Softmax table minimum 2 bits","F",["Q08 (re-based under D19)"],["M7"],"T1",{"quant.softmax_table_min_bits":2},["softmax-table-min-bits"],
  "untried (E1 lowered the fixed softmax OUTPUT to 4 bits, archived, no target; tables were never trainable before D19)",
  TS,"paired (same shapes)","lowers the A07 floor to derived 114,189; accuracy at 5M flat","table widths at the selected checkpoint, EBOPs split",
  arch=dict(tb=2),if_floor="drop",note="departs from Chang's bc=Min(4); labelled")
single("M004","Linformer projection k=8","F",["A10"],["M5","M7"],"T2",{"arch.attn_kind":"linformer","arch.linformer_k":8},["attn-linformer"],
  "untried with binary weights (never implemented, CHG:184); H6 ran Sun et al.'s LUT Linformer with HGQ weights, not comparable",
  TS,"paired-if-hash (new E/F projections; other kernels shared)","350k feasible with real headroom (derived h 0.66); accuracy at 5M within the interval of C",
  "EBOPs split, entropy over k projected keys, attention-ablation delta",arch=dict(attn="linformer",k=8),if_floor="drop")
single("M005","Softmax-free ReLU/N attention","F",["Q10","tried D11"],["M5","M7"],"T2",{"arch.attn_kind":"relu_over_n"},["attn-relu-over-n"],
  "tried-negative-as-noise (D11 era-1 softmax-free, old dataset, too-hot LR, no target); retried because it removes the whole D19 softmax floor",
  TS,"paired-if-hash","350k feasible; accuracy at 5M below C (competitive normalization lost)","attention-ablation delta, EBOPs split",
  arch=dict(attn="relu"),if_floor="drop")
single("M006","Binary Deep Sets body","F",["A09"],["M5"],"T2",{"arch.body":"deepsets","arch.deepsets_dims":{"phi":[64,64],"ctx":64,"phi_post":[64],"rho":[64,32,16],"pool_scale":0.0625}},["body-deepsets"],
  "untried with binary weights (CHG:184)",TS,"unpaired (Welch): no shared attention tensors",
  "accuracy >= anchor at 350k (Sun et al. collapse argument); at 5M below C","none of the attention diagnostics apply; report per-class AUC and the width map",
  arch=dict(attn="none"),fallbackE="apply (compare with E and A)",if_floor="drop",
  note="deepsets_dims from reference-code/HGQ2-examples/jsc150/model.py:88-100 (get_gnn: phi 64, s 64 at l. 88-89; context 64 at l. 90-92; post 64 at l. 95; pool x 1/16 at l. 96; rho 64/32/16 at l. 97-99), in the dict form code/newmods/deepsets.py DEFAULT_DIMS accepts; dims only, no code lifted; no batch norm, binary weights (deviations listed in deepsets.py)")
single("M007","Q/K stream width floor 1 bit","F",["THEORY M5 (Q column)"],["M5"],"T1",{"quant.qk_min_bits":1},["qk-stream-min-bits"],
  U,[T5M],"paired","forbids the Q/K 0-bit collapse; at 5M accuracy up if attention matters","Q/K 0-bit fraction must be 0; entropy/log n_valid; attention-ablation delta",
  arch=dict(qk_min=1),if_floor="5M-only",note="A07 derived floor 474,125 > 350k: 350k only in combination with M001 or M004")
single("M008","Attention-group EBOPs weight x0.1","F",["THEORY M5/M7"],["M5","M7"],"T1",{"quant.ebops_group_weight":{"attention":0.1,"rest":1.0}},["ebops-group-weight"],
  U,TS,"paired","350k: attention survives longer, dense layers pruned harder; sign budget-dependent","EBOPs split by group against epoch, Q/K/V 0-bit fractions")
single("M009","N = 32 constituents (cross-N, the point)","F",["P01","tried D3"],["M7"],"T0",{"arch.n_part":32},[],
  "tried-failed (A05 N=32 at 350k never feasible under the old quantizer, TR23:30); retried: derived D19 floor 85,517 < 350k; the derived 1-bit-alive floor 351,917 is just above 350k (it was 347,808 before the SAT exp-input term)",
  TS,"unpaired (Welch): different inputs; crosses N by design, labelled","350k feasible with nearly every channel alive (h 0.99: the 1-bit-alive floor exceeds 350k by 1,917); accuracy vs A undetermined (context vs bits)","EBOPs split, 0-bit fractions",
  arch=dict(N=32),if_floor="drop",note="needs a gated 90/10 N=32 cache (CPU job)")
single("M010","Target 1.4M (ladder rung)","F",["Q07"],["M7"],"T0",{"train.ebops.pid.target_ebops":1400000},[],
  "untried rung (anchor ladder after [D21]: B = E at 250k, A = E at 350k, A07-350 descriptive, C = A07 at 5M)",[1400000],"paired (A07, same shapes) to A07-350's seeds at a different target: a ladder point, no same-target control, so G3 does not apply","accuracy between A07-350 and C; knee location (descriptive; never advances on accuracy)","feasible count, EBOPs split, 0-bit fractions",
  if_floor="n/a",note="ladder point only: no same-target control exists; G2 counts and the ladder plot are reported, G3 is not applied")
# Q
single("M011","Per-value activation widths (Chang value-wise)","Q",["Q02"],["M7"],"T1",{"quant.act_granularity":"element"},["act-granularity-element"],
  U,TS,"paired","up at 350k (bits placed per particle rank), flat at 5M","0-bit fraction per position; EBOPs split")
single("M012","Activation init f0 = 7 (Chang)","Q",["Q03 (re-based: under D19 i tracks the range, only f feels the EBOPs gradient)"],["M7"],"T0a",{"quant.act_f0":7},["act-init-f0"],
  U,TS,"paired","slower EBOPs descent (wider start); selected accuracy within the interval","EBOPs against epoch, first feasible epoch",
  anchor_keys=["A20"],note="key name set by [A20]; T0a if [A20] exposes f0, else the patch")
single("M013","PID gains p 2, i 0.2","Q",["Q04"],["M7"],"T0",{"train.ebops.pid.p":2.0,"train.ebops.pid.i":0.2},[],
  "untried (B08 gentler PID planned, never run, PLAN:106-121)",[T350],"paired","more seeds feasible by epoch 500; accuracy flat","beta trajectory, first feasible epoch, EBOPs overshoot below target",
  if_floor="350k only: on arm A (E) by default; a feasibility probe on A07-350 (vs its k_base) if arm A fails at 350k; dropped under R4 (no 350k cell exists)",note="350k only: its purpose is reaching the budget; at 5M the anchor PID already reaches the target (C9/C10 context)")
single("M014","Open-loop beta schedule (Chang code)","Q",["Q04","R00"],["M7"],"T1",{"train.ebops.controller":"schedule","train.ebops.beta_schedule":[[0,2e-8,"linear"],[2000,3e-7,"log"],[7000,3e-6,"constant"]]},["beta-schedule-s-runner"],
  "tried-once (C2, R13 sighter, archived, 16 features: reached 5e5 about 14 AUC points below its own peak, XL:3690); retried as the Chang-code fidelity element",
  [],"paired","fewer seeds feasible than PID at matched epochs (open loop does not aim at a target); testable only over the full 7,000-epoch schedule","EBOPs against epoch, feasible count",
  targets_confirm=[T350],wave="confirm-only (offered at K3)",note="schedule values from jsc150/run_train.py:90; not screenable: at H = 500 only the first linear segment runs (beta 2e-8 to about 9e-8 of a schedule that ends at 3e-6), and even H = 2,000 ends at 3e-7, a tenth of the final beta. No screen cell; offered at K3 as a confirm-only Chang-fidelity element (7,000 epochs, 8 seeds, vs the 350k base at the terminal epoch)")
single("M015","Fixed-width recovery after epoch 500","Q",["Q14","tried B5"],["M7"],"T0",{"experiment.recovery_after_epochs":500},[],
  "tried-failed-with-mechanism (B5: the selected checkpoint preceded the freeze, ABL:101); retried with a horizon that covers the treatment",
  TS,"paired (vs anchor epoch-1,000 snapshot)","accuracy up after the freeze at unchanged EBOPs","onset = the logged freeze epoch (first feasible epoch >= 500); selected epoch must be later, else 'treatment not measured'",
  horizon=1000)
single("M016","tanh LUT before attention and FFN (Chang)","Q",["Q09","A14 (placement)"],["M6"],"T1",{"arch.pre_block_act":"tanh_lut"},["pre-block-tanh-lut"],
  U,TS,"paired-if-hash","small accuracy gain (range control on a norm-free graph); EBOPs of the table traced","saturation fraction at the following quantizer; table EBOPs term",
  arch=dict(extra="tanh-table (trace)"),note="export path has no LUT layer yet (J10 class)")
# B (training-only: screened at 5M, confirmed at 5M and the 350k base)
TO = [T5M]; TOC = [T5M, T350]
single("M017","Uncentered absmean (BitNet/XNOR convention)","B",["B02"],["M3"],"T1",{"quant.binary_center":False},["binarizer-center-flag"],
  "untried as a training arm (A3 compared the formulas on one checkpoint only)",TO,"paired","flat; fewer collective flips (threshold no longer moves with the tensor mean)","FF ratio per epoch",targets_confirm=TOC)
single("M018","Clipped-identity STE (hard-tanh)","B",["B04"],["M2"],"T1",{"quant.ste":"clip_identity"},["ste-variants"],
  "untried; the bounded STE replaced qkeras' wc/beta backward after the A4 NaN (2026-07-07)",TO,"paired","flat to up at LR 3e-3; fewer divergences","STE/latent gradient cosine, latent-vs-binary gap",targets_confirm=TOC)
single("M019","EDE annealed STE, restarted each LR cycle","B",["B07"],["M2"],"T1",{"quant.ste":"ede","quant.ste_ede_period":500},["ste-variants"],
  U,TO,"paired","up (sharpening synced to the cosine cycle)","latent-vs-binary gap per cycle",targets_confirm=TOC)
BOP_NOTE = ("Bop gamma 1e-4 (undecayed) and tau 1e-8: scan seed, not tuned for this setup (DR-22). Sources: arXiv:1906.02107 §5.2 (CIFAR-10: gamma 1e-4 decayed x0.1 every 100 epochs, "
            "tau 1e-8) and §5.3 (ImageNet: gamma 1e-4 to 1e-6 linear, tau 1e-8); Larq larq.optimizers.Bop defaults threshold 1e-8, gamma 1e-4, no decay "
            "(larq/larq master, commit 3d7de8832a477285bbf3c36252e24fcb9299a959, optimizers.py l. 314-316; a master commit, not a tagged release). "
            "The paper tuned W1A1 conv nets at batch 50/1024, and tau is an absolute threshold on the EMA gradient, whose units differ in our pipeline (research/DR-22-bop-hyperparameters.md §4). "
            "The wave STUDY measures the |m| distribution of the anchor's binary latents (arm A, a few hundred steps) and may pre-register a tau scan before launch. "
            "Kai decision at K2, before M020 is packed (code/GATES.md, Bop DECISION): the flip rule. Option 1 (patch 0024, code/newmods/bop.py): "
            "a flip reflects the latent about its mean, w <- 2*alpha - w, which keeps |w - alpha| and so the layer scale beta, keeping activation "
            "ranges comparable with the Adam anchor; not the paper's rule. Option 2 (Bop as published, arXiv:1906.02107 Algorithm 2): the weight "
            "is the sign itself and a flip sets w <- -w with latents at +-1, so beta becomes 1 - alpha^2 and activation scales change against the Adam anchor")
single("M020","Bop optimizer on binary latents","B",["B10"],["M3"],"T2",{"train.binary_optimizer":"bop","train.bop_gamma":1e-4,"train.bop_tau":1e-8},["bop-optimizer"],
  U,TO,"paired (same init; different update rule)","sign unknown (designed for W1A1)","FF ratio, C2I ratio",targets_confirm=TOC,
  note=BOP_NOTE)
single("M021","Latent clip to [-1, 1]","B",["THEORY M3","B09 source (BinaryConnect)"],["M3"],"T1",{"quant.latent_clip":1.0},["latent-clip"],
  U,TO,"paired","up late in training (inertia capped); partly redundant with restarts","latent |w|/beta histogram, FF ratio late in each cycle",targets_confirm=TOC)
single("M022","Beta decoupled from latent magnitude (learned, power of two)","B",["THEORY M3/M6"],["M3","M6"],"T1",{"quant.beta_mode":"learned_pow2"},["beta-mode"],
  U,TO,"paired","up; beta stops tracking latent growth","beta vs integer-bit trajectory correlation",targets_confirm=TOC)
single("M023","Absmean beta rounded to a power of two (Libra-PB scale)","B",["B06"],["M4"],"T1",{"quant.beta_mode":"absmean_pow2"},["beta-mode"],
  U,TO,"paired","non-inferior accuracy; the beta-restore affines become shifts (LUT/DSP, not EBOPs)","non-inferiority only; the cost claim needs csynth on mulder",targets_confirm=TOC,
  note="advances on non-inferiority to a synthesis check, not to accuracy confirm")
single("M024","Power-of-two per-channel gain on input_proj","B",["THEORY M1","B03 (restricted to shifts)"],["M1","M4"],"T1",{"quant.channel_gain":{"layers":["input_proj"],"mode":"pow2"}},["channel-gain-pow2"],
  U,TO,"paired","up (the 8 expressible input directions get distinct gains)","distinct sign rows of input_proj, per-channel gain histogram",targets_confirm=TOC,
  note="per-channel binary gate (two symmetric values per channel); DSP audit before any hardware claim")
single("M025","Power-of-two per-channel gain on every binary layer","B",["THEORY M4","B03 (restricted)"],["M4"],"T1",{"quant.channel_gain":{"layers":"all_binary","mode":"pow2"}},["channel-gain-pow2"],
  U,TO,"paired","up; larger than M024 if scale loss is general (M4) rather than first-layer (M1)","least-squares per-channel alpha spread vs per-tensor beta",targets_confirm=TOC)
single("M026","Per-channel shift before activation quantizers (RSign)","B",["B13 (shift only)"],["M4","M6"],"T1",{"quant.pre_quant_shift":"channel"},["pre-quant-shift"],
  U,TO,"paired","up; possibly lower achieved widths at equal accuracy","dead-ReLU fraction, width map",targets_confirm=TOC)
WHY_WS = ("why this retry differs from the early-peak-then-squeeze failures (F1, C3 at 25 %, C4; lesson 2): those runs peaked unconstrained and were then squeezed to a budget far below the peak's cost (F1 2.44M to 350k, x0.14). Here the screen target is 5M, a squeeze from the traced 13.18M init to x0.38, the regime where C3's 75 % budget stayed feasible at a small cost; the 350k claim is tested only at confirm, and G1's H1-type test and the first-feasible-epoch log apply. If the student peaks at the start and falls >= 5 pt while its EBOPs fall, that is recorded as the F1 pattern, not as a null")
single("M027","Warm start from the FP teacher (two-stage)","B",["B11/B12 staged idea","THEORY §5.1"],["M2","M3"],"T1",{"experiment.init_checkpoint":"teacher-fp32-a07"},["init-from-checkpoint","weight-scheme-baselines"],
  U,TO,"unpaired (Welch): init not seed-derived; data order shared","up; faster to a given accuracy","C2I ratio (from teacher signs), latent-vs-binary gap",targets_confirm=TOC,
  note="needs the teacher prerequisite job P-T1; "+WHY_WS)
# R
WHY_LR = ("why this retry differs from H1 (LR >= 2e-4 collapsed at epoch 2-3, archived recipe; tried-already H1, XL:5797-5798): the anchor runs batch 2,790 (about 11x fewer steps per epoch than batch 256), a cosine decay to 1e-6 inside each 500-epoch cycle, and an EBOPs term; H1's batch size and STE version are not in the inventory, so these are the documented anchor differences, not a shown cause. Both rungs sit between H1's collapse range and the anchor's 3e-3: they locate the stability edge if the anchor arms collapse, and test whether a lower peak helps if they do not. G1's H1-type degradation test is the pre-registered detector")
single("M028","Peak LR 1e-3","R",["R06","tried H1"],["M2","M3"],"T0a",{"train.lr":1e-3},[],
  "tried-failed-with-mechanism at LR >= 2e-4 (H1: STE collapse at epoch 2-3, archived recipe); the anchor's 3e-3 is the largest single risk",
  TO,"paired","fewer divergences than the base arm; accuracy flat or up","divergence/collapse count, FF ratio",anchor_keys=["A1"],targets_confirm=TOC,
  note="T0a assumes [A1] reads train.lr as the peak eta0; "+WHY_LR)
single("M029","Peak LR 3e-4","R",["R06","tried H1"],["M2","M3"],"T0a",{"train.lr":3e-4},[],
  "as M028",TO,"paired","no divergence; accuracy below the base arm if the base is stable","as M028",anchor_keys=["A1"],targets_confirm=TOC,
  note=WHY_LR)
single("M030","Linear warm-up, 10 epochs","R",["R04"],["M2"],"T1",{"train.lr_warmup_epochs":10},["lr-schedule-variants"],
  "untried on the Chang schedule (the archived recipe has 1 warm-up epoch at 2e-5)",TO,"paired","fewer early collapses; accuracy flat","epoch of best validation in cycle 1, divergence count",targets_confirm=TOC)
single("M031","Peak decay m_mul 0.85 per restart","R",["R03"],["M3"],"T1",{"train.lr_m_mul":0.85},["lr-schedule-variants"],
  U,TO,"paired (vs anchor epoch-1,500 snapshot)","fewer late divergences; accuracy flat or up","FF spike height at each restart",horizon=1500,targets_confirm=TOC,
  note="cycle 1 is identical to the anchor; a 500-epoch screen would measure nothing")
single("M032","No restarts: one cosine over the horizon","R",["THEORY §6.6","R02/R05"],["M3"],"T0a",{"train.lr_cycle_epochs":"=horizon"},[],
  U,TO,"paired (vs anchor epoch-2,000 snapshot)","sign open (THEORY §6.6)","FF ratio vs epoch; within-cycle position of the best checkpoint",horizon=2000,anchor_keys=["A1"],targets_confirm=TOC,
  note="screen proxy is one cosine over 2,000; confirm is one cosine over 7,000")
single("M033","Weight decay 0.01 only (arm D decomposition)","R",["R07","THEORY §2"],["M3","M6"],"T0a",{"train.optimizer":"adam","train.beta2":0.999,"train.weight_decay":0.01,"train.clipvalue":None},[],
  "untried alone (arm D has all three changes)",TO,"paired","higher FF ratio, smaller beta; accuracy sign open","FF ratio, beta trajectory",anchor_keys=["A2"],targets_confirm=TOC,
  note="stated against the explicit [A2] optimizer path so weight_decay is not silently ignored")
single("M034","EMA of latents, re-binarized for evaluation","R",["R08"],["M3"],"T1",{"experiment.latent_ema_decay":0.999},["latent-ema-eval"],
  U,TO,"paired","small gain; less checkpoint jitter","sign agreement EMA vs raw; validation jitter across epochs",targets_confirm=TOC,
  note="decay 0.999 is a design choice (Mean Teacher range, arXiv:1703.01780)")
single("M035","Logit KD from an FP teacher (T 2, 0.5)","R",["R09","tried H5"],["M2"],"T1",{"experiment.distillation":{"teacher_artifact":"teacher-fp32-a07","temperature":2,"coefficient":0.5}},["kd-unblock-s-runner","weight-scheme-baselines"],
  "tried-failed-with-mechanism (H5/R6: interim snapshot, the trainer hung, teacher was the unconstrained pilot, ACC:19); retried with a new teacher on the gated 90/10 train split",
  TO,"paired","up, larger at the lower budget","per-class gap to the teacher",targets_confirm=TOC,note="T and coefficient from the R6 config (code-surface §2d)")
single("M036","Attention-map KD","R",["R09","THEORY M5"],["M5"],"T1",{"experiment.distillation":{"teacher_artifact":"teacher-fp32-a07","temperature":2,"coefficient":0.0,"attention_coefficient":1.0}},["kd-unblock-s-runner","kd-attention-map","weight-scheme-baselines"],
  U,TO,"paired","attention stays non-uniform; accuracy up","entropy/log n_valid vs teacher, attention-ablation delta",targets_confirm=TOC)
# P
single("M037","eta/phi reflection augmentation","P",["R13","P09"],["M1"],"T1",{"data.augment":{"reflect_eta":True,"reflect_phi":True}},["augment-eta-phi-reflect"],
  "untried (no augmentation in any record; BNJetTagAug is a project name)",TO,"paired","narrower seed spread; mean flat or up","paired sd of the gap; per-class accuracy",targets_confirm=TOC)
single("M038","pT gate off (0 GeV)","P",["P02"],["M5"],"T1",{"arch.pt_gate_gev":0},["pt-gate-threshold"],
  "untried as an arm on the Chang recipe (every current run before the anchor is ungated, but under other recipes)",TS,"paired (same shapes; inputs differ)",
  "sign open: more real low-pT constituents vs more junk in the statistics","padding/gated fraction per jet, entropy/log n_valid",anchor_keys=["A3"],note="needs an ungated 90/10 cache; 0 here means ungated: the generator writes it as an explicit arch.pt_gate_gev null ([A3]: null = ungated; 0 would gate at pT >= 0 with another cache identity), and the null must stay explicit so it overrides the anchor's 2 GeV gate once the anchor base replaces the stand-in")
single("M039","Mask gated and padded keys","P",["P03","THEORY M5/§5.5"],["M5"],"T1",{"arch.mask_gated_keys":True},["gated-key-mask"],
  U,TS,"paired","up; entropy diagnostic no longer inflated by padding","entropy/log n_valid; token-fold hazard noted for export")
NOHW = ('not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk)')
single("M040","Derived features log pT and Delta R (5 inputs)","P",["P05","THEORY M1"],["M1"],"T1",{"arch.n_feat":5,"arch.derived_features":["log_pt","delta_r"]},["derived-input-features"],
  "untried (input-set changes were archived and crossed N, G1)",TS,"paired-if-hash (input_proj fan-in changes); crosses input set by design, labelled",
  "up (more expressible first-layer directions); the iso-EBOPs match excludes the off-model feature computation","distinct sign rows of input_proj",arch=dict(nf=5),
  note=NOHW)
single("M041","Standardize over real slots only","P",["P06"],["M6"],"T1",{"data.std_scope":"real_slots"},["std-real-slots"],
  U,TO,"paired","up (operating point of the first binary layer no longer set by padding)","input range at the first quantizer, saturation fraction",targets_confirm=TOC)
# A
single("M042","d_model 16","A",["A01"],["M1","M7"],"T0",{"arch.d_model":16},[],
  "tried-failed (D4 D16 at N=16/64, old quantizer)",TS,"paired-if-hash","350k: more headroom for widths than A07, still near-floor (derived h 0.026); 5M below C","effective width, EBOPs split",arch=dict(d=16))
single("M043","FFN 64","A",["A03","tried D1"],["M1"],"T0",{"arch.ffn_dim":64},[],
  "tried (D1: FFN 32 beat 64 at N=8, 350k, single seed, old quantizer)",TS,"paired-if-hash","350k worse (derived h 0.009); 5M flat or up","EBOPs split",arch=dict(ffn=64))
single("M044","Two blocks (L = 2)","A",["A02"],["M1"],"T0",{"arch.n_layers":2},[],
  "tried-failed at 350k with the old quantizer (A00-A03 N=8/16/64 screens)",[T5M],"paired-if-hash","5M: up if depth matters","EBOPs split per block",arch=dict(L=2),if_floor="5M-only",
  note="derived floor 686,106 > 350k")
single("M045","Head 32/32/32 (Chang)","A",["A08"],["M1"],"T1",{"arch.head_dims":[32,32,32]},["head-dims"],
  U,TS,"paired-if-hash","flat (Sun et al. head depth has no monotone relation to their Table 1)","width map of the head",arch=dict(head=[32,32,32]))
single("M046","No positional encoding (5M cell; at 350k the PE contrast is anchor A vs F)","A",["A04"],["M5"],"T0",{"arch.pos_enc":"none"},[],
  "designed as anchor arm F at 350k (pre-[D21] F = A07 without PE), not run; tried-failed at N=16 under the old quantizer (D7, largest seed spread)",[T5M],
  "paired if [A17] shows only pos_table differs, else Welch (anchor rule)","flat or up (permutation invariance); gated tokens become exact duplicates","duplicated-token count, entropy/log n_valid",
  note="exists so the gate x PE x mask cube has a 5M single; at 350k the PE contrast is anchor A (E, no PE) against anchor F (E + learned PE) [D21]")
# Baselines (labelled, not thesis)
single("M047","Ternary absmean (labelled baseline)","BL",["B14"],["M1","M4"],"T1",{"quant.weight":"ternary_absmean"},["ternary-absmean","weight-scheme-baselines"],
  "untried at this architecture (A5 archived, old dataset)",TS,"paired","ternary >= binary on accuracy (Sloot FastML 2026 direction)","zero fraction per layer; how HGQ2 counts the zeros (Z06)",kind="baseline",
  arch=dict(wbits_unknown=True),note="floor1 n/a until Z06 (how HGQ2 0.1.9 bills a ternary weight)")
single("M048","int8 static weights, all layers (matched non-binary)","BL",["THEORY §6.2","anchor follow-up"],["M1"],"T1",{"quant.weight":"int8_absmax"},["weight-scheme-baselines"],
  "archived only (A6, no target); never under an EBOPs target",TS,"paired","above C at 5M; at 350k the weight bits cost more EBOPs","EBOPs split; the same attention diagnostics",kind="baseline",arch=dict(wbits=8),
  note="int8_absmax is a fixed fixed<8,3> grid, not absmax (code-surface §4); floor1 prices every dense and head layer at b_w = 8")
single("M049","HGQ learnable weight widths (matched to Sun et al.)","BL",["THEORY §6.2"],["M5","M7"],"T2",{"quant.weight":"hgq_learnable"},["hgq-learnable-weights"],
  "untried in-house (H6 ran Sun et al.'s own code, archived, circular selection)",TS,"paired-if-hash","collapses at 350k like Sun et al. if the collapse is budget geometry","Q/K/V 0-bit fractions, entropy, ablation delta",kind="baseline",
  arch=dict(wbits_unknown=True),note="floor1 n/a: learned weight widths (0 bits reachable), no fixed b_w; the 350k cell is covered by the anchor study's arm NB (field covered_by_anchor_study), the 5M cell is not")
single("M050","8-bit input_proj only","BL",["THEORY M1, §6.3"],["M1"],"T1",{"quant.layer_weight_override":{"input_proj":"int8_absmax"}},["weight-scheme-baselines"],
  U,TS,"paired","gap to the base arm measures the fan-in-3 first-layer loss","distinct sign rows (base arm) vs this arm",kind="baseline",arch=dict(wbits_in=8),
  note="floor1 prices input_proj at b_w = 8 (+7 x 6,144)")

ENTRY = {e["id"]: e for e in S}

# ---------------------------------------------------------------- combos
C = []
def merge(ids):
    d, p, ak, arch = {}, [], [], {}
    for i in ids:
        if i == "F":
            d["arch.pos_enc"] = "none"; continue
        e = ENTRY[i]
        for k_, v in e["config_delta"].items():
            if k_ in d and d[k_] != v and isinstance(d[k_], dict) and isinstance(v, dict):
                d[k_] = {**d[k_], **v}
            else:
                d[k_] = v
        p += [x for x in e["code_changes"] if x not in p]
        ak += [x for x in e["anchor_keys"] if x not in ak]
        arch.update(e["arch"])
    return d, p, ak, arch

def combo(id_, name, fam, ids, ladder, targets, pred, diag, horizon=None, pairing=None, kind="package",
          targets_confirm=None, wave="W3", note="", if_floor="drop", base=None, extra_delta=None, anchor_keys=None):
    d, p, ak, arch = merge(ids)
    ak += [x for x in (anchor_keys or []) if x not in ak]
    if extra_delta: d.update(extra_delta)
    if not ids:
        ids_ct = ["M033"]
    else:
        ids_ct = [i for i in ids if i != "F"]
    hz = horizon or max([ENTRY[i]["horizon_screen"] for i in ids if i != "F"] + [500])
    pr = pairing or ("paired" if all((i == "F") or ENTRY[i]["pairing"].startswith("paired (") or ENTRY[i]["pairing"] == "paired" for i in ids) else "strictest component rule (paired / paired-if-hash / Welch)")
    C.append(dict(id=id_, name=name, family=fam, tier=kind, cards=[], mechanisms=sorted({m for i in ids if i != "F" for m in ENTRY[i]["mechanisms"]}),
                  code_tier=max([ENTRY[i]["code_tier"] for i in ids_ct], key=lambda t: {"T0":0,"T0a":1,"T1":2,"T2":3}[t]),
                  combo_of=[i if i != "F" else "anchor-arm-F" for i in ids], ladder=ladder, config_delta=d, code_changes=p, anchor_keys=ak,
                  tried="untried (combination)", targets=targets, targets_confirm=targets_confirm or targets, pairing=pr,
                  prediction=pred, diagnostic=diag, horizon_screen=hz, arch=arch, fallback_E="apply" if base != "E" else "n/a (E base)",
                  if_floor_fails=if_floor, wave=wave, note=note, base=base, extra_delta=extra_delta or {}))
    return id_

cid = [51]
def nid():
    s = f"M{cid[0]:03d}"; cid[0] += 1; return s

# floor combos (THEORY §5.4)
X_h2tb = combo(nid(),"Two heads + table floor 2 bits","F",["M001","M003"],["M001","M003"],TS,"350k headroom beyond either single","EBOPs split, Q/K/V 0-bit fractions")
combo(nid(),"One head + table floor 2 bits","F",["M002","M003"],["M002","M003"],TS,"largest attention-keeping headroom among softmax arms","as above")
X_lh2 = combo(nid(),"Linformer k8 + two heads","F",["M004","M001"],["M004","M001"],TS,"feasible with most headroom; accuracy vs M004 flat","EBOPs split, entropy over projected keys")
X_ltb = combo(nid(),"Linformer k8 + table floor 2 bits","F",["M004","M003"],["M004","M003"],TS,"redundant: the table term is already small under Linformer","EBOPs split")
combo(nid(),"Q/K width floor + two heads","F",["M007","M001"],["M007 (5M only)","M001"],TS,"350k feasible (derived floor 302,598, h 0.089: near-floor) with attention forced alive","Q/K 0-bit fraction 0; entropy; ablation delta",
      note="at 350k the decomposition is one-sided: M007 alone is statically infeasible there")
combo(nid(),"Q/K width floor + Linformer k8","F",["M007","M004"],["M007 (5M only)","M004"],TS,"350k feasible with attention alive (derived floor 58,381)","as above",
      note="at 350k the decomposition is one-sided")
combo(nid(),"Attention-group weight + two heads","F",["M008","M001"],["M008","M001"],TS,"attention survives at 350k","EBOPs split by group")
combo(nid(),"N = 32 + two heads (cross-N)","F",["M009","M001"],["M009","M001"],TS,"every channel alive at 350k with attention","as M009",pairing="unpaired (Welch); crosses N, labelled")
combo(nid(),"ReLU/N attention + Q/K width floor","F",["M005","M007"],["M005","M007 (5M only)"],TS,"softmax-free attention kept alive at 350k (derived floor 131,072)","ablation delta",
      note="at 350k the decomposition is one-sided")
combo(nid(),"Floor stack: Linformer + two heads + table 2 bits","F",["M004","M001","M003"],[X_lh2, X_ltb, X_h2tb],TS,"no gain over the best pair (redundant)","EBOPs split")
# KD x progressive (§5.1): singles are screened at 5M, so the crosses are too
X_kdw = combo(nid(),"Logit KD + warm start from teacher","R",["M035","M027"],["M035","M027"],TO,"synergy; THEORY predicts larger at the low budget (tested at confirm)","per-class gap to teacher, C2I",pairing="unpaired (Welch): warm start",targets_confirm=TOC)
X_akw = combo(nid(),"Attention KD + warm start","R",["M036","M027"],["M036","M027"],TO,"synergy","entropy vs teacher",pairing="unpaired (Welch): warm start",targets_confirm=TOC)
combo(nid(),"Logit KD from the int8 teacher (staged, BiT-style)","R",["M035"],["M035","M048"],TO,"closer teacher helps more than the FP teacher","per-class gap to both teachers",
      extra_delta={"experiment.distillation":{"teacher_artifact":"teacher-int8-a07","temperature":2,"coefficient":0.5}},targets_confirm=TOC,note="teacher variant of M035; needs the int8 teacher job P-T2")
combo(nid(),"Teacher stack: logit + attention KD + warm start","R",["M035","M036","M027"],[X_kdw, X_akw],TO,"no gain beyond the best pair","as components",pairing="unpaired (Welch): warm start",targets_confirm=TOC)
# gain x widths (§5.2, §5.6)
combo(nid(),"Per-channel pow2 gain + per-value widths","B",["M025","M011"],["M025","M011"],TO,"synergy (gain sets relative contributions, widths re-adapt)","gain histogram, width map",targets_confirm=TOC)
combo(nid(),"Per-channel pow2 gain + shift (binary-safe affine)","B",["M025","M026"],["M025","M026"],TO,"additive or mildly synergistic; the binary-safe analogue of Chang's fused BN","dead-ReLU fraction, gain histogram",targets_confirm=TOC)
X_fg = combo(nid(),"Derived features + pow2 input_proj gain","P",["M040","M024"],["M040","M024"],TO,"redundant at the margin (both enlarge input directions, THEORY §5.6)","distinct sign rows",targets_confirm=TOC)
# restarts x latent (§5.3)
X_nrc = combo(nid(),"No restarts + latent clip","R",["M032","M021"],["M032","M021"],TO,"partly redundant","FF ratio",targets_confirm=TOC)
combo(nid(),"No restarts + weight decay","R",["M032","M033"],["M032","M033"],TO,"partly redundant","FF ratio, beta trajectory",targets_confirm=TOC)
combo(nid(),"Latent clip + weight decay","R",["M021","M033"],["M021","M033"],TO,"redundant (both cap inertia)","latent histogram",targets_confirm=TOC)
combo(nid(),"Bop + no restarts","B",["M020","M032"],["M020","M032"],TO,"restarts do not act on Bop; no interaction expected","FF ratio",targets_confirm=TOC)
X_ede1 = combo(nid(),"EDE annealed once + no restarts","B",["M019","M032"],["M019","M032"],TO,"up over EDE-per-cycle only if restarts fight the anneal","latent-vs-binary gap",targets_confirm=TOC,
      extra_delta={"quant.ste_ede_period":"=horizon"})
combo(nid(),"Inertia stack: EDE + latent clip + no restarts","B",["M019","M021","M032"],[X_nrc, X_ede1],TO,"no gain beyond the best pair","FF ratio",targets_confirm=TOC,
      extra_delta={"quant.ste_ede_period":"=horizon"})
# optimizer decomposition
combo(nid(),"clipvalue 1 + beta2 0.98 (arm D minus weight decay)","R",[],["M033","anchor-arm-D"],TO,"with M033 and arm D: a 2x2 in {wd} x {clip + beta2}; additivity checked","divergence count, FF ratio",
      extra_delta={"train.optimizer":"adam","train.beta2":0.98,"train.weight_decay":None,"train.clipvalue":1.0},targets_confirm=TOC,anchor_keys=["A2"])
# gate x PE x mask: full 2^3 at 5M (M046 is the no-PE single); at 350k the gate x mask square on arm A (E)
X_gp = combo(nid(),"Gate off + no PE","P",["M038","M046"],["M038","M046 (5M; the 350k cell is dropped, no-PE is a no-op on arm A)"],TS,"2^3 cell","entropy/log n_valid, duplicated-token count")
X_gm = combo(nid(),"Gate off + masking","P",["M038","M039"],["M038","M039"],TS,"2^3 cell","as above")
X_pm = combo(nid(),"No PE + masking","P",["M046","M039"],["M046 (5M; the 350k cell is dropped, no-PE is a no-op on arm A)","M039"],TS,"2^3 cell (gated tokens are exact duplicates without PE)","as above")
combo(nid(),"Gate off + no PE + masking","P",["M038","M046","M039"],[X_gp, X_gm, X_pm],TS,"2^3 cell","as above")
X_ms = combo(nid(),"Masking + real-slot standardization","P",["M039","M041"],["M039","M041"],TO,"natural pair (absent treated consistently)","entropy/log n_valid",targets_confirm=TOC)
combo(nid(),"First-layer stack: features + gain + mask + real-slot std","P",["M040","M024","M039","M041"],[X_fg, X_ms],TO,"no gain beyond the best pair","distinct rows, entropy/log n_valid",targets_confirm=TOC)

# FF1: 2^(5-1) resolution V, generator E = -ABCD (defining relation I = -ABCDE); contains the anchor cell
FF1 = dict(A="M019", B="M040", C="M035", D="M042", E="M037")
ff1_cells = []
for levels in itertools.product([-1, 1], repeat=4):
    a, b, c, d = levels
    e = -a * b * c * d
    lv = dict(A=a, B=b, C=c, D=d, E=e)
    highs = [f for f in "ABCDE" if lv[f] == 1]
    ff1_cells.append(highs)
assert len(ff1_cells) == 16
assert sorted(len(h) for h in ff1_cells) == [0] + [2]*10 + [4]*5
for highs in sorted([h for h in ff1_cells if h], key=lambda h: (len(h), h)):
    ids = [FF1[f] for f in highs]
    combo(nid(), "FF1 cell " + "".join(highs) + ": " + " + ".join(ENTRY[i]["name"].split(" (")[0] for i in ids), "FF1", ids,
          ["FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks)"] + ids, [T5M],
          "main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed",
          "each component's diagnostic", kind="factorial-cell", targets_confirm=TOC,
          pairing="paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design", base="C", horizon=500)

# FF2: 2^(4-1) resolution IV, generator D = ABC (I = ABCD), on the E base; contains the E cell (all low) and the all-high cell
FF2 = dict(A="M011", B="M012", C="M016", D="M045")
ff2_cells = []
for a, b, c in itertools.product([-1, 1], repeat=3):
    d = a * b * c
    lv = dict(A=a, B=b, C=c, D=d)
    ff2_cells.append([f for f in "ABCD" if lv[f] == 1])
assert sorted(len(h) for h in ff2_cells) == [0] + [2]*6 + [4]
for highs in sorted([h for h in ff2_cells if h], key=lambda h: (len(h), h)):
    ids = [FF2[f] for f in highs]
    combo(nid(), "FF2 cell " + "".join(highs) + " on E: " + " + ".join(ENTRY[i]["name"].split(" (")[0] for i in ids), "FF2", ids,
          ["FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks)"] + ids, [T350],
          "main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC", "each component's diagnostic",
          kind="factorial-cell", pairing="paired-if-hash vs arm A (= E, [D21]; seed blocks)", base="E", targets_confirm=[T350],
          extra_delta={"arch.d_model":24,"arch.n_heads":2,"arch.pos_enc":"none"}, horizon=500)

# completes the {wd} x {clip+beta2} 2x2 at 5M (arm D exists only at 350k)
combo(nid(),"Our optimizer at 5M (arm D recipe at the arm C target)","R",[],["M033","M074"],TO,"2x2 corner; with C, M033 and M074 gives the additivity check of arm D's three fields","divergence count, FF ratio, beta trajectory",
      extra_delta={"train.optimizer":"adam","train.beta2":0.98,"train.weight_decay":0.01,"train.clipvalue":1.0},targets_confirm=TOC,anchor_keys=["A2"])

ALL = S + C

# ---------------------------------------------------------------- package notes (review v1, B2/B3)
for e in C:
    if "M027" in e["combo_of"]:
        e["note"] = (e["note"] + "; " if e["note"] else "") + WHY_WS
    if "M020" in e["combo_of"]:
        e["note"] = (e["note"] + "; " if e["note"] else "") + BOP_NOTE
    if "M040" in e["combo_of"]:
        e["note"] = (e["note"] + "; " if e["note"] else "") + NOHW

# ---------------------------------------------------------------- floors per entry
FLOOR_LABEL = ("derived: arbiter-v2 formula plus the traced SAT exp-input term (H*T*S; H*T*k for Linformer) and the LUT term "
               "(fit to the trace, <= 13 EBOPs); dense terms scale with weight bits (b_a * b_w). Shape arithmetic, never quoted as a floor; "
               "floor_traced carries the CPU trace where one exists")

def arch_args(e, on_E=False):
    a = dict(E_ARCH if (on_E or e.get("base") == "E") else A07_ARCH)
    ar = dict(e["arch"])
    extra = ar.pop("extra", None)
    a.update(ar)
    return a, extra

def traced_for(e, a, extra):
    if extra is not None:
        return None
    for name, ref in (("A07", A07_ARCH), ("E", E_ARCH)):
        if a == ref:
            t = TRACED[name]
            return {"architecture": name, "floor0": t["floor0"], "floor1_alive": t["floor1_alive"],
                    "quantizer": t["quantizer"], "trace_arms": t["arms"], "label": TRACE_LABEL}
    return None

def hround(v):
    return round(v, 3) if isinstance(v, float) else v

ROLE = {
    "E-base": "E-base: the cell is built on arm A (E at 350k, Kai-confirmed [D21]) and paired with arm A (FF2)",
    "own-arch": ("floor-family: runs on its own A07-derived architecture, built from the A07-350 config (h >= 0.10 or trace-only); read for "
                 "feasibility by G2 against arm A07-350's feasible count at epoch H (k_base = 0 if A07-350 has no production seeds), and for "
                 "accuracy against arm A (E at 350k, [D21]) by Welch, labelled cross-architecture; never against A07-350's accuracy (a remnant "
                 "of under 7k EBOPs outside the softmax). If arm A fails at 350k, the accuracy reading has no comparator and the cell is read "
                 "for feasibility (G2) only"),
    "near-floor-E": ("near-floor on A07 (own-architecture h < 0.10): the delta is applied to arm A's config (E at 350k, Kai-confirmed [D21]) "
                     "and paired with arm A (accuracy screen, G0-G3). The A07 version is not run; the anchor's descriptive arm A07-350 "
                     "stands for it"),
    "near-floor-E-probe": ("near-floor on A07 and on E (on-E h < 0.10 or not derivable): the delta is applied to arm A's config (E at 350k, "
                           "[D21]) as a feasibility probe on E: G2 counts, EBOPs split, attention state; G3 not applied, no accuracy "
                           "reading, nothing advances on accuracy"),
}

for e in ALL:
    a, extra = arch_args(e)
    f0, f1 = arch_floors(**a)
    fd = {"floor0": f0, "floor1_alive": f1, "extra_term": extra, "label": FLOOR_LABEL}
    if a.get("wbits_unknown"):
        fd["floor1_note"] = "n/a: weight bits not fixed (Z06 for ternary; learned widths for HGQ weights)"
    h = {str(t): headroom(f0, f1, t) for t in e["targets"]}
    fd["headroom_by_target"] = {k_: hround(v) for k_, v in h.items()}
    e["floor_traced"] = traced_for(e, a, extra)
    # 350k cells that are statically infeasible move per if_floor_fails
    if T350 in e["targets"] and h.get(str(T350)) == "STATIC_INFEASIBLE":
        e["targets"] = [t for t in e["targets"] if t != T350]
        e["note"] = (e["note"] + "; " if e["note"] else "") + "350k removed: derived floor >= 350k"
    role = None
    if T350 in e["targets"]:
        h350 = h.get(str(T350))
        if e.get("base") == "E":
            role = "E-base"
        elif (isinstance(h350, float) and h350 < NEAR_FLOOR_H) or (h350 is None and f1 is None and f0 is not None):
            role = "near-floor-E"
        else:
            role = "own-arch"
        if role == "near-floor-E":
            aE, _ = arch_args(e, on_E=True)
            g0, g1 = arch_floors(**aE)
            hE = headroom(g0, g1, T350)
            fd["on_E"] = {"floor0": g0, "floor1_alive": g1, "headroom_350000": hround(hE),
                          "label": "derived on arm A, the E base (d24, 2 heads; [D21]); same formula"}
            if not (isinstance(hE, float) and hE >= NEAR_FLOOR_H):
                e["note"] = (e["note"] + "; " if e["note"] else "") + ("350k on E is near-floor or not derivable too (on-E h "
                             + (f"{hE:.3f}" if isinstance(hE, float) else "n/a") + "): the 350k cell is a feasibility probe on E, no accuracy reading")
                role = "near-floor-E-probe"
            if e["config_delta"].get("arch.pos_enc") == "none":
                e["targets"] = [t for t in e["targets"] if t != T350]
                e["note"] = (e["note"] + "; " if e["note"] else "") + ("350k dropped: on arm A (E, no PE; [D21]) the no-PE factor is a no-op, "
                             "so this cell duplicates another cell of the gate x mask square on arm A")
                del fd["on_E"]
                role = None
    e["screen_role_350k"] = ROLE[role] if role else None
    e["role_key"] = role
    e["floor_derived"] = fd
    e["seeds_screen"] = [1, 2, 3, 4]
    e["seeds_confirm"] = list(range(1, 9))

def base_350(e):
    r = e["role_key"]
    # texts deliberately match none of the pre-[D21] base_text_rules in code/anchor_arms.json, so the generator
    # fails loudly until the orchestrator adds the [D21] rules (fixer v2 report lists them)
    if r == "E-base":
        return "arm A (E at 350k, Kai-confirmed [D21])"
    if r == "near-floor-E":
        return "arm A (E at 350k, Kai-confirmed [D21]); delta applied to arm A's config; accuracy screen"
    if r == "near-floor-E-probe":
        return "arm A (E at 350k, Kai-confirmed [D21]); delta applied to arm A's config; feasibility probe on E, no accuracy reading"
    if r == "own-arch":
        return "floor family on the A07-350 base (own A07-derived architecture): feasibility vs arm A07-350 (G2), accuracy vs arm A (E; Welch, cross-architecture)"
    return "no 350k screen cell"

# ---------------------------------------------------------------- architecture floor table (DELTA.md §0, §3.2)
ARCH_ROWS = [
 ("A07 (anchor arms A07-350 and C [D21]; every A07 delta at 5M; the floor-family base)", {}),
 ("E, d24/h2/no PE (anchor arm A [D21], also B, D, R; FF2; the 350k base; F = E + learned PE, traced at the anchor PREFLIGHT)", dict(d=24, H=2)),
 ("A07 with FFN 64 (M043)", dict(ffn=64)),
 ("A07 with d_model 16 (M042)", dict(d=16)),
 ("A07, head 32/32/32 (M045)", dict(head=[32, 32, 32])),
 ("A07, 5 input features (M040)", dict(nf=5)),
 ("A07, int8 weights (M048)", dict(wbits=8)),
 ("A07, int8 input_proj (M050)", dict(wbits_in=8)),
 ("A07 with 2 heads (M001)", dict(H=2)),
 ("A07 with 1 head (M002)", dict(H=1)),
 ("A07, table floor 2 bits (M003)", dict(tb=2)),
 ("A07, Linformer k = 8 (M004)", dict(attn="linformer", k=8)),
 ("A07, ReLU/N attention (M005)", dict(attn="relu")),
 ("A07 at N = 32 (M009)", dict(N=32)),
 ("A07 + Q/K floor 1 bit (M007)", dict(qk_min=1)),
 ("A07, L = 2 (M044)", dict(L=2)),
 ("2 heads + table 2 bits (M051)", dict(H=2, tb=2)),
 ("1 head + table 2 bits (M052)", dict(H=1, tb=2)),
 ("Linformer + 2 heads (M053)", dict(attn="linformer", k=8, H=2)),
 ("Linformer + table 2 bits (M054)", dict(attn="linformer", k=8, tb=2)),
 ("Q/K floor + 2 heads (M055)", dict(qk_min=1, H=2)),
 ("Q/K floor + Linformer (M056)", dict(qk_min=1, attn="linformer", k=8)),
 ("N = 32 + 2 heads (M058)", dict(N=32, H=2)),
 ("ReLU/N + Q/K floor (M059)", dict(attn="relu", qk_min=1)),
 ("floor stack: Linformer + 2 heads + table 2 bits (M060)", dict(attn="linformer", k=8, H=2, tb=2)),
]
ARCH_FLOORS = []
for label, kw in ARCH_ROWS:
    a = dict(A07_ARCH); a.update(kw)
    f0, f1 = arch_floors(**a)
    hh = headroom(f0, f1, T350)
    tr = traced_for(dict(arch={}), a, None)
    if hh == "STATIC_INFEASIBLE":
        cls = "STATIC_INFEASIBLE"
    elif f1 is not None and f1 < T350:
        cls = "every channel alive at 1 bit"
    elif isinstance(hh, float) and hh < NEAR_FLOOR_H:
        cls = "near-floor"
    else:
        cls = "E-class"
    ARCH_FLOORS.append({"architecture": label, "floor0_derived": f0, "floor1_alive_derived": f1, "headroom_350000": hround(hh),
                        "class_350000": cls, "floor0_traced": tr["floor0"] if tr else None,
                        "floor1_alive_traced": tr["floor1_alive"] if tr else None})

# ---------------------------------------------------------------- budget
# n = screen seeds per cell, chosen at K2 from {4, 6, 8} by the Z14 rule (DELTA.md §5.1); 4 is the lower bound
SEED_CHOICES = (4, 6, 8)
def run_epochs(entries, seeds=4):
    return sum(seeds * len(e["targets"]) * e["horizon_screen"] for e in entries)
W2 = [e for e in S]
W3 = [e for e in C]
# drift replicas (seeds 1-n each), one per base arm, run to the longest horizon that pairs to it ([A6] snapshots every 500 epochs
# give every shorter horizon). Arm names after [D21]: A = E at 350k, A07-350 = A07 at 350k (descriptive), C = A07 at 5M.
# W2: A to 1,000 (M015 on A), A07-350 to 500 (floor-family k_base), C to 2,000 (M031, M032);
# W3: A to 500 (E-default packages, FF2 all-low cell), A07-350 to 500 (floor crosses' k_base), C to 2,000 (M068, M069, M071-M073)
DRIFT = {
    "W2": [("A", T350, 1000, "350k accuracy cells and M015 at 1,000; drift"),
           ("A07-350", T350, 500, "floor-family k_base (G2); drift"),
           ("C", T5M, 2000, "5M cells, M031 at 1,500 and M032 at 2,000; FF1 is W3")],
    "W3": [("A", T350, 500, "350k accuracy packages; FF2 all-low cell"),
           ("A07-350", T350, 500, "floor crosses' k_base (G2); drift"),
           ("C", T5M, 2000, "5M packages, M068, M069, M071-M073 at 2,000; FF1 all-low cell")],
}
REP = {w: {} for w in DRIFT}
for w, reps in DRIFT.items():
    for arm, tgt, hz, why in reps:
        REP[w][hz] = REP[w].get(hz, 0) + 1
assert REP == {"W2": {1000: 1, 500: 1, 2000: 1}, "W3": {500: 2, 2000: 1}}, REP
teachers = 2 * 1 * 2000   # FP32 and int8 teachers, 1 seed, 2,000 epochs
def budget(n):
    rw2 = n * sum(h * c for h, c in REP["W2"].items())
    rw3 = n * sum(h * c for h, c in REP["W3"].items())
    re_ = dict(W2=run_epochs(W2, n) + rw2, W3=run_epochs(W3, n) + rw3, teachers=teachers)
    re_["screen_total"] = re_["W2"] + re_["W3"] + re_["teachers"]
    return re_
RE_BY_N = {n: budget(n) for n in SEED_CHOICES}
RE = RE_BY_N[4]

def runs_by_h(entries, n=4):
    out = {}
    for e in entries:
        if e["targets"]:
            out[e["horizon_screen"]] = out.get(e["horizon_screen"], 0) + n * len(e["targets"])
    return out

def wall(entries, reps, P, n=4):
    rb = runs_by_h(entries, n)
    for h, c in reps.items():
        rb[h] = rb.get(h, 0) + n * c
    return sum(math.ceil(m / (P * K)) * h for h, m in rb.items())  # in epochs of s_e

walls_by_n = {}
for n in SEED_CHOICES:
    for P in (2, 10):
        walls_by_n[(n, P)] = wall(W2, REP["W2"], P, n) + wall(W3, REP["W3"], P, n) + 2000  # teachers first; serial upper bound
walls = {P: walls_by_n[(4, P)] for P in (2, 10)}

cheap = [e for e in S if e["code_tier"] in ("T0", "T0a", "T1") and e["tier"] == "single" and e["id"] not in ("M027", "M035", "M036") and e["targets"]]
RE_cheap = sum(3 * 1 * e["horizon_screen"] for e in cheap) + 3 * 500 * 2

conf_cells = 12
RE_conf = conf_cells * 8 * 7000

# ---------------------------------------------------------------- overlap with the anchor study's second wave (arms H, NB; decisions.md 2026-09-27 08:40 PDT)
NB_TXT = ("arm NB of campaigns/2026-09-26-training-batch (second wave, Kai 2026-09-27): learned-width (HGQ kbi_learnable) weights on the arm A "
          "recipe, E at 350k, seeds 1-8, 7,000 epochs, paired by seed with A")
COVERED = {
    "M049": {"350000": "covered: " + NB_TXT + ". It is this entry's 350k cell at full length; the wave STUDY drops the M049 350k screen cell if "
                        "NB's epoch-500 snapshot exists by K2 (the budget keeps it as an upper bound), and M049 at 350k is never a separate "
                        "confirm cell. The hgq-learnable-weights patch and NB's kbi_learnable path are one code item",
             "5000000": "not covered (NB runs only at 350k on E; this cell is on C, A07 at 5M)",
             "related": "arm H (Chang's jsc150 xfm-n64, HGQ weights, our split, 8 seeds) is the external-code reference for the same weight scheme"},
    "M048": {"350000": "not covered (int8 static weights; NB learns its widths)", "5000000": "not covered",
             "related": "NB is the anchor's matched non-binary arm at 350k; this entry stays a distinct weight scheme"},
    "M050": {"350000": "not covered (int8 on input_proj only)", "5000000": "not covered",
             "related": "NB and H are the anchor's non-binary comparands at 350k"},
    "M047": {"350000": "not covered (ternary)", "5000000": "not covered",
             "related": "NB and H are the anchor's non-binary comparands at 350k"},
    "M006": {"350000": "not covered (binary Deep Sets body)", "5000000": "not covered",
             "related": "arm H is Chang's transformer (xfm-n64), not the Deep Sets body; the 79.4 % Deep Sets row stays the external reference"},
}

# ---------------------------------------------------------------- hardware-risk labels per entry (review v3 B2; DELTA.md §6 lesson 5)
# Keys whose HLS export the patch series refuses (delta_keys.register(..., export_ok=False) in code/patches 0002, 0005,
# 0006, 0007, 0015, 0016, 0017, 0018; convert_binary guard, DR-17), and keys with no export path outside the series.
NO_EXPORT_SERIES = {"quant.binary_center": "binarizer-center-flag", "quant.beta_mode": "beta-mode",
                    "quant.channel_gain": "channel-gain-pow2", "arch.head_dims": "head-dims",
                    "arch.pre_block_act": "pre-block-tanh-lut", "quant.weight": "non-binary weight scheme",
                    "quant.layer_weight_override": "non-binary weight scheme"}
NO_EXPORT_OTHER = {"arch.attn_kind": "Linformer / ReLU-over-N attention (training path not wired: Linformer refused by patch 0022 until [A20], ReLU/N blocked, BLOCKED.md)",
                   "arch.body": "Deep Sets body (training path wired by patch 0023)",
                   "arch.mask_gated_keys": "runtime key mask (training path blocked on [A3]/[A4], BLOCKED.md)"}
def hw_labels(e):
    d = e["config_delta"]; out = []
    if "quant.channel_gain" in d:
        out.append("DSP audit required before any hardware claim: per-channel power-of-two gain (two symmetric values per channel)")
    ser = sorted({v for k, v in NO_EXPORT_SERIES.items() if k in d})
    if ser:
        out.append("no export path yet (DR-17): the patch series refuses HLS export for " + ", ".join(ser))
    oth = sorted({v for k, v in NO_EXPORT_OTHER.items() if k in d})
    if oth:
        out.append("no export path yet (DR-17): " + ", ".join(oth) + "; no HLS export written")
    if "arch.derived_features" in d:
        out.append("not a hardware candidate until the derived-feature path is costed (off-model features, DSP risk)")
    return out
for e in ALL:
    e["hw_labels"] = hw_labels(e)

# ---------------------------------------------------------------- write
json_entries = []
for e in ALL:
    json_entries.append({
        "id": e["id"], "name": e["name"], "family": e["family"], "tier": e["tier"], "code_tier": e["code_tier"],
        "combo_of": e["combo_of"], "targets": e["targets"], "targets_confirm": [t for t in e["targets_confirm"]],
        "seeds_screen": e["seeds_screen"], "seeds_confirm": e["seeds_confirm"],
        "horizon_screen_epochs": e["horizon_screen"], "base": {"350000": base_350(e), "5000000": "C", **({"1400000": "the 1.4M rung on the A07-350 base (A07 at 1.4M; paired by seed to A07-350's snapshots, target differs)"} if 1400000 in e["targets"] + e["targets_confirm"] else {})},
        "config_delta": e["config_delta"], "code_changes": e["code_changes"], "anchor_patches_required": e["anchor_keys"],
        "pairing": e["pairing"], "tried": e["tried"], "prediction": e["prediction"], "mechanism_diagnostic": e["diagnostic"],
        "mechanisms": e["mechanisms"], "cards": e["cards"], "ladder": e.get("ladder", []),
        "floor_derived": e["floor_derived"], "floor_traced": e["floor_traced"], "screen_role_350k": e["screen_role_350k"], "if_floor_fails": e["if_floor_fails"], "fallback_E": e["fallback_E"],
        "wave": e["wave"], "note": e["note"], "extra_delta": e.get("extra_delta", {}),
        "covered_by_anchor_study": COVERED.get(e["id"]),
        "hw_labels": e["hw_labels"],
    })

delta = {
    "delta_id": "2026-09-26-delta", "date": "2026-09-26", "status": "designed",
    "anchor": ("campaigns/2026-09-26-training-batch/STUDY.md arm A = E at 350k (d24, 2 heads, 1 block, FFN 32, no PE), [D19] Chang quantizers, "
               "both Kai-confirmed 2026-09-27 08:40 PDT (.claude/memory/decisions.md, [D21] and [D19]); B = E at 250k; D and R on E; F = E + learned PE; "
               "A07-350 = A07 at 350k, one descriptive arm (traced headroom 6,947 < the 8,192 data-dependent attention needs); C = A07 at 5M. "
               "Arms H (Chang's jsc150 xfm-n64 on our split) and NB (learned-width weights on the arm A recipe) are that study's second wave. "
               "If arm A has no feasible checkpoint (pilot or production), the anchor becomes the arm Kai names (C at 5M is the remaining fallback)"),
    "anchor_arms_after_D21": {
        "A": "E at 350k: d_model 24, n_heads 2, pos_enc none on the A07 config; the 350k base",
        "A07-350": "A07 at 350k (descriptive arm; floor-family base; k_base for G2)",
        "B": "E at 250k", "C": "A07 at 5M", "D": "E at 350k with our optimizer (beta2 0.98, weight decay 0.01, clipvalue 1.0)",
        "F": "E + learned PE at 350k", "R": "E at 350k on our recipe",
        "label": "from campaigns/2026-09-26-training-batch/STUDY.md changelog (v1 after arbiter v3, l. 72-74) and decisions.md 2026-09-27 08:40 PDT; code/anchor_arms.json still carries the pre-[D21] arms and must be updated by the orchestrator"},
    "drift_replicas": {
        "rule": ("DELTA.md §5.2: every screen wave re-runs these base arms at the Delta code sha on Delta pods, seeds 1-n (n from the K2 rule), each to "
                 "the horizon listed; [A6] snapshots every 500 epochs give every shorter horizon. The replicas take the first pods of the wave; "
                 "sd_null is read at their epoch-500 snapshot before any other entry of the wave starts. Drift trigger: if the 95 % interval of "
                 "replica - anchor snapshot excludes 0 or |mean| > 0.3 pt, the wave's primary pairing switches to the replica at every horizon"),
        "R4": "if the [D19] reversal branch R4 holds (old quantizer), the C replica is the C' replica and is the primary control; the A and A07-350 replicas are not run (no 350k cell exists)",
        "seeds": "1-n per wave x target (n_W3 <= n_W2 at the same target, DELTA.md §5.1)",
        **{w: [{"arm": a, "target": t, "horizon_epochs": h, "serves": why} for a, t, h, why in reps] for w, reps in DRIFT.items()},
    },
    "traced_floors": {"label": TRACE_LABEL, **TRACED},
    "architecture_floors": ARCH_FLOORS,
    "screen_seed_rule": {"seed_choices": list(SEED_CHOICES), "lower_bound": 4, "upper_bound": 8,
        "rule": "DELTA.md §5.1: at K2, sd_plan = sqrt(2) * epoch-500 validation-accuracy sd of the base arm (C at 5M, arm A = E at 350k; seeds 1-8, feasible only), or max(sd_plan, sd_null) once the drift replicas are read; n = smallest of 4, 6, 8 with k_joint(n, alpha_eff) * sd_plan <= g_0 = 0.3 pt, where k_joint sizes the whole advance rule, (i) BH and (ii) mean g >= g_0 / 2, for 80 % power at a true gap of g_0; alpha_eff = q / m one-sided (q = 0.10, m = (entry, target) cells with a G3 test in the wave x target family, baselines and feasibility probes excluded); n_W3 <= n_W2 at the same target (packages need their singles on the same seeds; a W3 family that would need more seeds runs at n_W2, in ranking mode if n_W2 does not qualify); if none qualifies, the wave runs at n = 4 as a declared ranking (no advance claims) unless Kai buys n = 8 with g_res = k_joint(8, alpha_eff) * sd_plan as the MDE target and g_res / 2 as gate (ii)",
        "gate_ii": "mean g >= g_0 / 2 (0.15 pt, or g_res / 2); g_0 itself is the MDE target, not the gate (fixer v2, review v2 B1: with (ii) at mean >= g_0 the joint power at a true gap of g_0 is at most 0.5)",
        "seeds_screen_field": "seeds_screen lists seeds 1-4 (the lower bound); the wave STUDY extends it to 1-n",
        "k_table": "screen_power.py (this directory)"},
    "config_delta_semantics": "train.bop_gamma 1e-4 / train.bop_tau 1e-8 (M020, M071) are the DR-22 scan seed (Larq default, arXiv:1906.02107 §5.2/§5.3), not tuned for this setup; the wave STUDY may pre-register a tau scan after measuring |m|. Nulls (train.clipvalue, train.weight_decay) mean 'unset' on the explicit [A2] optimizer path. arch.pt_gate_gev 0 (M038 and its packages) means ungated and is written by the generator as an explicit null ([A3] semantics), which must stay explicit to override the anchor's 2 GeV gate. dotted config paths relative to the config of the base arm named in base[target] (after [D21]: arm A = E for the 350k accuracy cells and FF2, A07-350 for the floor family and the 1.4M rung, C for 5M), after the anchor patch series; T0a keys are placeholders named after code-surface §3 suggestions and are mapped by the generator once [A1]/[A2]/[A3]/[A20] fix their names; '=horizon' means the screen horizon (7000 at confirm)",
    "tier_legend": {"single": "one method against the anchor", "baseline": "labelled non-binary comparand, never the thesis", "package": "pre-registered combination, read against its ladder", "factorial-cell": "cell of FF1 or FF2 (DELTA.md §2.2)", "note": "this is the entry kind, not the budget tier; the budget tier (screen / confirm) is set per wave"},
    "code_tier_legend": {"T0": "config-only on a key the S runner reads today", "T0a": "config-only once the anchor patch series lands (key introduced by [A1]/[A2]/[A3]/[A20])", "T1": "small patch, <= ~80 lines", "T2": "new module"},
    "patches": {k_: {"code_tier": v[0], "size_lines": v[1], "touches": v[2], "what": v[3]} for k_, v in PATCHES.items()},
    "always_on_diagnostics": DIAG_ALWAYS,
    "prerequisite_jobs": {
        "P-T1": {"what": "FP teacher: A07-N64, quant.weight none, the anchor [D19] activation/softmax quantizer set at its init widths, gated 90/10 train split, Chang recipe, no EBOPs pressure (pid target 1e12, beta bounds at min)", "epochs": 2000, "seeds": [101], "selection": "validation accuracy", "patches": ["weight-scheme-baselines"]},
        "P-T2": {"what": "int8 teacher: as P-T1 with quant.weight int8_absmax", "epochs": 2000, "seeds": [101], "patches": ["weight-scheme-baselines"]},
        "caches": ["gated 90/10 N=32", "ungated 90/10 N=64", "N=64 with derived features", "N=64 real-slot standardization"],
    },
    "entries": json_entries,
}
json.dump(delta, open(f"{OUT}/delta.json", "w"), indent=1, default=str)

# sanity
slugs = [p for e in ALL for p in e["code_changes"]]
assert all(p in PATCHES for p in slugs), set(slugs) - set(PATCHES)
ids = [e["id"] for e in ALL]
assert len(ids) == len(set(ids))

# summary for the designer
from collections import Counter
print("entries", len(ALL), "singles", len(S), "combos", len(C))
print("tier", Counter(e["tier"] for e in ALL))
print("family", Counter(e["family"] for e in ALL))
print("code_tier all", Counter(e["code_tier"] for e in ALL))
print("code_tier singles", Counter(e["code_tier"] for e in S))
print("code_tier combos", Counter(e["code_tier"] for e in C))
print("RE", RE, "RE_cheap", RE_cheap, "cheap n", len(cheap), "RE_conf", RE_conf)
print("walls (epochs of s_e)", walls)
for n in SEED_CHOICES:
    r = RE_BY_N[n]
    print("n", n, "RE", r, "pod-hours", {k_: round(v * S_E_EXAMPLE / 3600 / K, 1) for k_, v in r.items()},
          "wall days P2/P10", round(walls_by_n[(n, 2)] * S_E_EXAMPLE / 86400, 1), round(walls_by_n[(n, 10)] * S_E_EXAMPLE / 86400, 1))
se = S_E_EXAMPLE
for k_, v in RE.items():
    print(k_, "pod-hours @112.6s K6", round(v * se / 3600 / K, 1))
print("cheap pod-hours", round(RE_cheap * se / 3600 / K, 1), "conf pod-hours", round(RE_conf * se / 3600 / K, 1))
for P, w in walls.items():
    print("P", P, "screen wall days", round(w * se / 86400, 1))
for P in (2, 10):
    print("P", P, "confirm wall days", round(math.ceil(conf_cells*8/(P*K)) * 7000 * se / 86400, 1), "waves", math.ceil(conf_cells*8/(P*K)))
print("runs W2", sum(4*len(e['targets']) for e in W2), "+ replicas", 4*sum(REP["W2"].values()), "runs W3", sum(4*len(e['targets']) for e in W3), "+ replicas", 4*sum(REP["W3"].values()))
print("roles 350k", Counter(e["role_key"] for e in ALL if e["role_key"]))
for e in ALL:
    if e["role_key"] in ("near-floor-E", "near-floor-E-probe"):
        print("  onE", e["id"], e["floor_derived"]["on_E"]["floor0"], e["floor_derived"]["on_E"]["floor1_alive"], e["floor_derived"]["on_E"]["headroom_350000"])
for r in ARCH_FLOORS:
    print("ARCH", r)
print("runs by h W2", runs_by_h(W2), "W3", runs_by_h(W3))
used = sorted(set(slugs) | set(DIAG_ALWAYS) | {"diag-sign-flips","diag-beta-trajectory","diag-input-proj-rows","diag-latent-binary-gap"})
print("patch slugs used", len(used), "defined", len(PATCHES), "unused", set(PATCHES) - set(used))
for e in ALL:
    fd = e["floor_derived"]
    print(e["id"], e["code_tier"], e["targets"], e["horizon_screen"], fd["floor0"], fd["floor1_alive"], fd["headroom_by_target"], e["name"][:60])
print("drift replicas (runs at n = 4):", {w: [(a, t, h, 4) for a, t, h, _ in r] for w, r in DRIFT.items()})
print("covered_by_anchor_study:", sorted(COVERED))
print("hw_labels:", {e["id"]: len(e["hw_labels"]) for e in ALL if e["hw_labels"]})
