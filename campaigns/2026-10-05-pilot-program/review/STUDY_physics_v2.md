ITERATE

# STUDY physics review v2 (fresh-context referee)

Scope: thesis paragraph and `STUDY.md` (status "draft, amended [A3]", 378 lines), plus the data files
it cites, spot-checked: `code/tree/analysis/attn_entropy.py`, `code/tree/campaigns/pilot1005/readout_pilot.py`,
`dev/README.md:56-70`, `2026-09-26-training-batch/READOUT_epoch500.md:118-133`,
`docs/chang-vs-bnjettag.md:100-110`. No earlier review files, methodology or conventions were read.

Arithmetic I recomputed from the STUDY's own inputs: the pod count (2+2+6+4+2+2+2+2+1+1 = 24); the
headrooms (E 350k: 178,474; qkv1 at 350k: 80,170, at 450k: 180,170; A07 500k: 156,947); the
Clopper-Pearson bounds (0/2 upper 0.842, 3/3 lower 0.292, 0/3 upper 0.708); and the spend
(7,000 × 30.85 s × 16 / 3600 = 960 GPU-h, and 1,207 at 38.8 s; pilots 222). All of these agree with
the STUDY. Pilot numbers quoted here are single-seed validation telemetry (n = 62,000) and are
never quotable.

## A (fix before R1 launch)

**A1. "Healthy" has no accuracy content, yet it drives the H3 read, W selection and r1. For the H3 arm
the entropy term is close to satisfied by construction.**
Healthy (§5) = complete ∧ feasible ∧ val acc > 0.211 ∧ mean entropy < 0.95. The only failure
the program set out to explain is low accuracy (0.236-0.405 at 350k). Uniform attention is a
symptom, and the symptom is not itself a failure, because Chang/Sun's own 350k MHA-64 collapsed to a
Deep Set (`chang-vs-bnjettag.md:108-110`). Three consequences follow:
- H3: `A350-C-qkv1` forces Q, K and V to ≥ 1 bit. Under WRAP, the exact 1.000000 that every collapsed
  head shows comes from 0-bit Q giving identically zero logits (§5). A non-zero Q/K stream
  gives non-constant logits and entropy below 1 almost automatically. A "qkv1 2/2 vs A350-C 0/2"
  lead can therefore appear with val acc unchanged at about 0.3. The floor would then have changed
  the measuring instrument, not the network's usefulness.
- Coarse `softmax_out` quantization also lowers the row-renormalized entropy: entries round to 0,
  and the renormalized row turns sparse. The controller sets those bits differently in every arm,
  so the < 0.95 cut does not measure the same thing across arms.
- W (§7.3) states "Accuracy is not a criterion", and r1/r_rec use healthy. A rung or variant can
  win at val acc 0.22-0.40. The production qualification then fails on the 0.50 floor, after R2's
  pods have been spent on the wrong bracket or the wrong W.

Fix (rule text only, before freeze). Either add `best_feasible_val_acc ≥ 0.50` (the internal floor
the STUDY already uses) to *healthy* wherever healthy feeds r1, r_rec, W, V_bin or a lead, or
require an H3/H4/H5 lead to also show a paired val-acc gain on every matched seed. Add the Q/K 0-bit
channel fractions and the zero-entry fraction of `softmax_out` rows (both already computed by
`attn_entropy.py`) to the readout as descriptive columns. Then a reader can tell "attention
restored" apart from "logits no longer exactly zero".

## B

**B1. No arm separates "attention collapsed" from "the accuracy loss comes from attention".**
A binary mean-pool (no-attention) E model at 350k is the control that would show whether
uniform attention costs accuracy at all. If a binary Deep Set at 350k reaches about 0.6 or more, the
collapse diagnosis is wrong and the loss comes from elsewhere: 0-bit activations outside
attention, or the classifier head. The STUDY defers it (§15, "R1 has no free pod"). Until it
runs, the STUDY should state that no R1 or R2 verdict attributes the accuracy loss to attention.
Alternatively, trade one pod (for example w150 s2, whose read is already flagged time-limited and
LR-phase-confounded) for it, if the code can be gated in time.

**B2. E-unc-C is under-specified, and its pass condition is circular.** The STUDY leaves "PID target
≥ init EBOPs" vs "EBOPs term off" to the ml-engineer. These are different controls: the first keeps
a live controller, the second has no bit pressure. Pre-register one. E-unc-C is also called "the
only measured E entropy reference for the 0.95 cut", yet it must pass that same cut. A 2-head d24
model that learns a Deep Set-like solution unconstrained, which Chang/Sun saw in MHA-64, stops the
whole program as an entropy-only positive-control failure. Judge E-unc-C on feasibility,
completion and accuracy, and record its entropy as the calibration value.

**B3. Best-feasible selection can pick a transient checkpoint.** The only healthy reference, C-s1
(A07, 5M), has its `model_best` at zero-based epoch 19 of 500 (`READOUT_epoch500.md:121`).
Health on the ladder can therefore reflect a checkpoint taken early in the squeeze, before the network
reaches its budget equilibrium. Pre-register how a row reads when its best checkpoint precedes
t_budget, or when its epoch-500 snapshot is uniform or below 0.50. Put the best-checkpoint epoch
in `readout.json`, not only in the descriptive `readout_diag.json`.

**B4. Production seeds overlap the selection seeds.** D8 chooses seeds 1-8. Seeds 1-2 (and 3-5)
of the chosen 350k arm are the pilot runs that chose it. If training is reproducible to epoch 500
(same recipe, same first cosine cycle), the production epoch-500 early stop (§9) replays rows that
are already known and carries information only for the fresh seeds. The paper-tier A − NB at 8
paired seeds also includes seeds that won the selection. State this explicitly and give the
fresh-seed subset beside the 8-seed result, or take the D8 alternative (seeds 9-16).

**B5. The production guard has no synthesis check, but the thesis claims "no DSPs at 40 MHz".**
EBOPs-matched is not resource-matched (§1, phys C4). The variants under test (qkv1 floor, NB
learned-width weights, higher budgets) change exactly the activation×activation products in
Q·K and A·V, where an FPGA flow may infer DSPs. A csynth (`mulder`) DSP, LUT and II/latency check of
the candidate's selected checkpoint is cheap next to roughly 1,000 GPU-h. It should be one of the
§9 guards before Kai is asked to launch, or the STUDY should state that it is absent and why.

## C

**C1. The shared-control false-lead arithmetic.** In §6, 1 − (15/16)^5 = 0.276 treats the 5 comparisons
as independent. With one shared A350-C control at a true rate of 0.5, P(control 0/2) · P(≥ 1 of 5
arms 2/2) = 0.25 · (1 − 0.75^5) = 0.190. The conclusion ("every verdict is a lead") still
holds. The figure should either state that it is a crude independence bound, or be corrected.

**C2. The entropy normaliser depends on multiplicity.** With no attention mask and log 64, a head
that attends uniformly to exactly the real constituents scores log n_real / log 64. That score depends
on class and jet, so the 0.95 cut means something different for low- and high-multiplicity
classes. Report an n_real-normalised entropy descriptively.

**C3. The H2 monotonicity read at n = 1 per rung.** At 350k the seed outcome is bimodal (A-s1
degenerate, A-s2 weak). Near the transition, monotone or non-monotone ladders occur by chance at
n = 1. "Descriptive" covers this. Saying it in the H2 row would stop a reader from over-reading
an "inconclusive (non-monotone)".

**C4. Provenance.** §1 cites the A-s2 0.320871 and D-s1 0.405371 checkpoint accuracies to "b5 `VERIFY.md` §6;
`READOUT_epoch500.md` table (2)". These values are not in `READOUT_epoch500.md`. They appear in
`campaigns/2026-10-01-recovery/readout-preparation/VERIFY.md`. Give that path with line numbers.

**C5. External reference.** The 350k reference row the STUDY quotes, MHA-64 at 77.9 %, is the
model whose attention its own authors call collapsed. The attention-healthy 350k reference in that
table is Linformer-64 (79.8 %), a different architecture. Saying so in §9 keeps Kai from
reading 77.9 % as "attention working at 350k".

## Answers to the four questions

- **Discrimination and confounds.** H1, H4 and H5 are matched single-column changes. The confounds
  that remain are stated (LR phase for w150, NB's initial width and its 0-bit pruning). H2 vs H2′ is
  separated by the ladders. H2 vs H3 rests on one matched-headroom seed. The missing piece is B1:
  nothing tests whether attention is the cause of the accuracy loss.
- **Healthy criteria and positive controls.** These are not yet physically meaningful as a decision
  input (A1). The entropy cut is a 0-bit-Q detector. It stands in for "useful", and the H3
  treatment and the controller's softmax-output bits can move it. The A07 control is sound as a
  pipeline check. The E control is under-specified and circular (B2).
- **R1 at 1-2 seeds.** The STUDY treats every R1 verdict as a lead, which is correct. With the
  bimodal 350k outcomes, only the extreme patterns mean anything, and the STUDY says so.
- **Production qualification.** It is safe in the sense that matters: nothing auto-fires, ≥ 3
  fresh healthy seeds and the 0.50 floor are required, and an epoch-500 early stop limits the loss.
  The open gaps are the seed overlap (B4) and the missing synthesis guard for the thesis's DSP and
  40 MHz claim (B5).
