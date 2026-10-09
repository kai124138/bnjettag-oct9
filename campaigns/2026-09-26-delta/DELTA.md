---
id: 2026-09-26-delta
date: 2026-09-26
type: delta
status: designed
question: Which of about 100 binarization, recipe, activation-width/EBOPs, architecture and input methods, alone or in pre-registered combinations, change the validation accuracy or 350k feasibility of the binary-weight N=64 tagger relative to the Sun et al. recipe anchor at the same seed, and which of those survive a full-recipe 8-seed confirmation?
supersedes:
superseded_by:
code_sha: not fixed. Delta patches are staged against the screen bundle (tarball sha256 26f3cc40...5a45) and rebased onto the anchor patch series sha once it lands; ml-engineer records both in code/
wandb: BNJetTag-Delta / delta-20260926-w2 (singles), delta-20260926-w3 (combos), delta-20260926-w4 (confirm); proposed, never BNJetTagAug
results:
---

# Delta: a pre-registered queue of about 100 methods on the Sun et al. recipe anchor

**This is a pre-registered queue, not a single experiment.** Nothing here launches. Each wave
below becomes its own campaign with its own STUDY.md through `/new-experiment`, and the panel
reviews that STUDY before any launch. The per-wave STUDY copies its arms from `delta.json`,
its rules from §5 of this file, and may tighten a rule but not loosen one without a dated
amendment made before its own launch. Every number here carries its source and status. The EBOPs
floors written "derived" come from shape arithmetic. It now includes the two terms the CPU trace
named, and it equals the trace for A07 and E. The trace of every other architecture comes in wave 1.

**Rename (2026-09-27; Kai, `decisions.md` 2026-09-27 program renamed Delta; report `review/DELTA_rename.md`).** Names only; no rule, arm, seed, threshold or number changed:
- The program is Delta; its files and constants are `DELTA.md`, `delta.json`, `delta_spec.py`, `delta_tables.py`, `review/DELTA_*`; W&B `BNJetTag-Delta` / `delta-20260926-w2/-w3/-w4`; run prefix `delta0926`.
- The paired accuracy gap is written g (was Δ; g_s, g_rep per seed), its MDE target g₀ = 0.3 pt (was δ), the resolvable target g_res (was δ_res). In ASCII (`delta.json`, `.py`) g₀ is `g_0`, distinct from gate G0 (§5.3). ΔR (angular distance) is unchanged.
- `delta.json` schema: the top-level id key is now `delta_id` (value `2026-09-26-delta`; the old key name is listed in `review/DELTA_rename.md`). No key carried the gap statistic; its text changed only in the values of `screen_seed_rule.rule` and `screen_seed_rule.gate_ii`. `config_delta`, `extra_delta` and `config_delta_semantics` (config differences, not the gap) are unchanged.

**Fixer v1 (2026-09-27; `review/DELTA_critical_v1.md`, report `review/DELTA_fixer_v1.md`).** Changes:
- The floors now include the traced SAT exp-input and LUT terms, carry `floor_traced` for A07 and E,
  and price the baseline weight bits (A1).
- The A07 350k cells are feasibility probes, and the 350k accuracy screens default to arm E (A1, B4).
- The screen seed count depends on Z14, and the screen has a declared ranking fallback (A2).
- Control gaps closed (B1). Retries and the H1-type test added (B2). M040 labelled (B3).
- M014 leaves the screen and becomes confirm-only.

**Fixer v2 (2026-09-27; `review/DELTA_critical_v2.md`, report `review/DELTA_fixer_v2.md`).** Changes:
- The anchor is re-based on Kai's launch-gate answers (`decisions.md` 2026-09-27, 08:40 PDT): [D19]
  and [D21] are Kai-confirmed. **Arm A is E at 350k**; A07 at 350k is the anchor's descriptive arm
  **A07-350**; C stays A07 at 5M; F is E + learned PE. The anchor's arms H and NB are its second
  wave, and NB covers M049's 350k cell. Every "Kai may override at K1" wording is gone.
- The drift-replica plan is in `delta.json` (`drift_replicas`), so the generator can build it (A1-v2).
- The screen sizes n for the whole advance rule: gate (ii) is now mean g ≥ g₀/2, and g₀ = 0.3 pt stays
  the MDE target (B1-v2). m is counted per (entry, target) cell from the role field, and the baselines
  take no G3 test (B2-v2). M047-M049 have their own 350k role, feasibility probe on E (B3-v2). The
  fallback control gaps are closed (B4-v2). n_W3 ≤ n_W2 at each target (B5-v2).
- Bop γ = 1e-4 and τ = 1e-8 are pre-registered as a scan seed (DR-22).

**Amendments from the wave-2 pre-registration (2026-09-28).** The wave-2 STUDY
(`campaigns/2026-09-27-delta-screen/STUDY.md`, frozen 2026-09-28, `review/STUDY_frozen_check.md`)
amends the rules below for wave 2, dated before its launch as the header above requires. §5 is not
rewritten; where it and this list differ for wave 2, this list and the STUDY govern. No rule is
added here; each row points to the STUDY section that states it. Kai's decisions: `decisions.md`
2026-09-27 and 2026-09-28 "(Kai, direct)".

| rule | DELTA (before) | wave 2 (after) | STUDY section |
| --- | --- | --- | --- |
| Primary ranking statistic | §5.1 item 3, §5.3 ranking mode: lower 80 % bound of g | median of the n_p paired g_s, with [min, max]; mean g (family-pooled interval), n_low and the per-cell lower 80 % bound beside it. Kai 2026-09-27 chose mean g, re-decided 2026-09-28 to median g ([DK6]) | Selection rule, "Ranking" |
| Seed count | §5.1 rules 1-3: n ∈ {4, 6, 8} set at K2 from √2 · the anchor's epoch-500 sd (Z14), ranking mode at n = 4 if none qualifies | n = 4 fixed in both families, ranking mode; the lists carry s_int labels (next row); sd_plan input is the replicas' own sd_rep; significance mode not armed. Top-k extension ([DK16]): if 1.0 ≤ s_int ≤ T, the top 16 (5M) / top 6 (350k) H-500 cells run seeds 5-8 | Seeds; Appendix A |
| Label rule | §5.3: list labelled "ranked, not advanced" | "ranked" if s_int ≤ T, else "descriptive"; T = 1.2 pt at 5M, 2.1 pt at 350k (median-g rule, `screen_null.py` §19a) | Selection rule, "Label" |
| Family test | none in ranking mode | Dunnett-type many-to-one max-t of d = cell − placebo, each cell's own paired sd, one-sided α 0.10, critical value simulated for the family's m and n_d; answer "some cell above the placebo" or "no" (not evidence of absence) | Selection rule, "Family test" |
| Compute pause | no sd-based pause (§5.1 item 3 falls to ranking mode); §5.2 base-stability pause | none: the n = 4 design runs whatever sd_rep reads (a v2 sd_rep ceiling pause was added and withdrawn in v5); the §5.2 base-stability pause is kept | Seeds; Controls and pairing, "Base stability" |
| Confirm cap | §5.3: at most 12 cells, ordered by lower 80 % bound | unchanged at 12; ordered by median g | Selection rule, "Cap" |
| Control | §5.1 control row, §5.2 drift trigger: anchor [A6] snapshot, replica on the trigger | the in-wave drift replica at the same seed is always the primary control; g_rep (replica − anchor) is descriptive only ([DK3]) | Controls and pairing |
| Drift replicas | §5.2: base arms at seeds 1-n (A to 1,000, A07-350 to 500, C to 2,000) | rep-A and rep-C at seeds 1-8 (seeds 1-n to 1,000 / 2,000, seeds above n stop at 500); rep-A07-350 at seeds 1-n, to 500 | Arms, "Drift replicas" |
| Placebo | none | P-350 and P-5M: the replica config with identity keys changed, seeds 1-n (= 4), H 500; family-test reference only, not in m, s_pool or s_int | Arms, "Placebo cells" |
| Non-selecting companions | §5.3 winner's-curse note only | last-epoch and split-half companions per run, each with g, interval, rank and Kendall τ; rank-move flag against the last-epoch companion; neither changes the list | Selection rule, "Winner's curse" |
| Memory-growth launch gate | none (§7 K1/K2) | gate 14: one E and one A07 Delta cell ≥ 30 epochs on the leak-fixed bundle, host-RSS slope ≤ 5 MB per epoch per arm, else the wave waits; f2107a04 and e90327d4 not launchable (`decisions.md` 2026-09-28) | Prerequisites and launch gate, gates 11, 14 |
| Launch condition | §7 wave 2a: the anchor's epoch-500 snapshots at seeds 1-n exist | the anchor's regime-B pilot epoch-500 validation readout (Kai, 2026-09-27) | Prerequisites and launch gate, gate 1 |
| Ranked-list membership | §5.3: every G3 cell of the wave × target | H-500 paired cells only (at most 11 at 350k, 35 at 5M); M015, M031, M032 in a "horizon H ≠ 500" list, Welch cells apart | Selection rule, "Lists" |
| Eligible epochs | not stated (DELTA predates regime B) | traced epochs only (regime B, `train.ebops_trace_every: 10`; [DK13]) | Selection rule |
| 350k base | §0: arm A = E, [D21] | unchanged (arm A = E, [D21]) | Arms, "Base arms" |

Inputs, all read in full for this design: `BRIEF.md` (including the 2026-09-27 anchor
amendment), `plan.md`, `research/THEORY.md`, `inventory/tried-already.md`,
`inventory/code-surface.md`, the five card files (70 cards), the anchor
`campaigns/2026-09-26-training-batch/STUDY.md` (working tree, v2 with [D19]) and its
`review/STUDY_arbiter_v2.md` "Independent checks". Outputs: this file, `delta.json` (one object
per entry, read by the ml-engineer's generator) and `LOG_LINES.md`.

## 0. The anchor, and what changed under it

**Anchor (wave 0), Kai-confirmed [D19] and [D21] (2026-09-27, 08:40 PDT, `decisions.md`).** Arm A
of the training-batch STUDY: the E architecture at 350,000 EBOPs (d_model 24, 2 heads, 1 block,
FFN 32, no PE, norm none, GAP, ReLU FFN), `binary_absmean` weights, the Sun et al. recipe (Adam
defaults, cosine restarts with peak 3e-3 every 500 epochs, batch 2,790, 7,000 epochs), pT ≥ 2 GeV
gate, 90/10 split (n_val = 62,000), our BetaPID to 350,000 EBOPs, selection on validation accuracy
among feasible, non-degenerate checkpoints. The anchor's activation, softmax-output and
softmax-table quantizers are **Chang's** [D19]: WRAP datalane activations and Q/K/V streams with 0
bits reachable, a learned softmax output, and trainable exp/inv tables (kbi `SAT_SYM`, at least 4
bits). The quantizer set belongs to the anchor. It is not a Delta method. The other anchor arms
Delta pairs to ([D21]; anchor STUDY changelog, v1 after arbiter v3):
- **A07-350**: A07 (d_model 32, 4 heads, learned PE) at 350k, one descriptive arm. Its traced
  headroom is 6,947 EBOPs, below the 8,192 that data-dependent attention needs, so it is kept as
  the feasibility reference, not as an accuracy base.
- **C**: A07 at 5,000,000, the A07 anchor at 5M.
- **B** (E at 250k), **D** (E with our optimizer), **R** (our recipe on E) and **F** (E + learned
  PE), all at 350k except B.
- **H** (Chang's jsc150 xfm-n64 on our split, 8 seeds) and **NB** (learned-width weights on the
  arm-A recipe, paired by seed with A) are the anchor study's second wave. NB is M049's 350k cell
  (`covered_by_anchor_study` in `delta.json`, §3.3).

Each entry's delta is applied to the base arm its `base[target]` names: arm A (E) for the 350k
accuracy cells and FF2, A07-350 for the floor family and the 1.4M rung, C for every 5M cell. If arm A
has no feasible checkpoint (pilot rule at epoch 500, or production), the anchor becomes the arm Kai
names; C at 5M is the remaining fallback (§3.3 R2).

**Static floors that set the design.** The traced values are a CPU trace on synthetic input
(n = 256, seed 0), staged in `campaigns/2026-09-26-training-batch/code/evidence/`
(`static_floors_arms_s1.json`, `static_floors_trace_step2.json`; `decisions.md` 2026-09-27
"chang0926 code"). The staged tree is on base source sha 7f9e9307 and was committed at 72a1290. It
is not the final anchor sha and it is not a result. The derived values use the formula below;
old-quantizer E is derived only.

| architecture | quantizer | 0-bit floor | 1-bit-alive floor | at 350k |
| --- | --- | ---: | ---: | --- |
| A07 | old (SAT k=1, fixed 10-bit softmax, fixed tables) | 4,580,398 traced (4,559,008 derived) | 4,580,398 traced (SAT channels never go below 1 bit, so this equals the 0-bit floor) | `STATIC_INFEASIBLE` |
| E | old | 2,690,744 derived | – | `STATIC_INFEASIBLE` |
| A07 (arms A07-350 and C; also the pre-[D21] F, A07 without PE) | [D19] | 343,053 traced | 1,005,741 traced | 6,947 EBOPs above the floor, h 0.010 |
| E (arm A [D21]; also B, D, R; F = E + learned PE, traced at the anchor PREFLIGHT) | [D19] | 171,526 traced | 619,198 traced | 178,474 above the floor, h 0.399 |

The softmax part of the [D19] floor is 16·H·T·S + 4·(H·T·S − H·T) + H·T·S + LUT. The first two
terms are the exp × inv product and the row accumulation at the 4-bit table minimum (the arbiter-v2
formula). The third is the SAT exp input: hgq2 0.1.9 keeps it SAT, the jsc150 MHA default, which
costs 1 bit per score entry. The LUT term is Σ 2^b_in · b_out · 10⁻⁴. The trace names the last
two terms; the arbiter formula omitted them. DR-18 is answered and R3 is the branch that holds.
Substitution check for A07 (H = 4, T = S = 64): 262,144 + 64,512 + 16,384 + 13 = 343,053, which
equals the trace. For E (H = 2): 131,072 + 32,256 + 8,192 + 6 = 171,526, which also equals the
trace. The LUT term is modelled as ⌊13·H/4⌋ per block. That is a fit to these two traced points,
never above 13 EBOPs, and it moves no class boundary. Limiting case: with no attention (H = 0)
every term is 0. The 1-bit-alive floor adds three pieces:
- the dense layers and the head at 1 bit (A07: 400,544);
- Q·K at 1 × 1 bit (T·S·d = 131,072);
- A·V at 1 × 1 bit (131,072).

That gives 343,053 + 400,544 + 262,144 = 1,005,741, the traced value. For E it gives 171,526 +
251,064 + 196,608 = 619,198, also the traced value. Dense terms scale with the weight bits (EBOPs
= b_a · b_w), which matters only for the baselines (§3.2). Delta uses the same formula for
every other architecture (§3.2). Those numbers are labelled **derived**, and the wave-1 trace (Z01)
replaces them. `delta.json` carries `floor_traced` where an entry's architecture equals a traced
config.

Two consequences run through the whole design:
- **A07 at 350k is near-floor, and its 350k cells are not accuracy screens.** A feasible A07
  checkpoint keeps at most 6,947 EBOPs outside the softmax tables, and h = (target −
  floor0)/(floor1 − floor0) = 6,947 / 662,688 = 0.010 (traced). At 1 bit on every channel,
  `input_proj` costs 6,144 and the head 1,024 + 160, so 7,328 > 6,947. No feasible A07 model keeps
  even its first layer and its head fully alive. Wq, Wk and Wv cost 65,536 each at 1 bit, so
  attention is dead by construction. The anchor says the same: pruned by construction, possibly a
  Deep-Set-class model. This is why Kai confirmed [D21]: A07 at 350k is the descriptive arm
  A07-350, a **feasibility reference** (G2 counts, EBOPs split, attention state), never an accuracy
  base, and every 350k **accuracy** screen runs on arm A, which is E (traced h 0.399; §3.3 R2).
  The E-class architectures (E, two heads, one head, table floor 2 bits, Linformer,
  ReLU/N, N = 32) have derived h between 0.27 and 1.0 (§3.2).
- **Statements written against the old quantizer are superseded here.** THEORY M7's reference
  point (six d×d layers at 1-bit mean input width cost 393,216 > 350k) and the phrase "SAT k = 1
  channels are never below 1 bit" describe the old branch. Under [D19] those channels can reach
  0 bits, and the binding floor is the softmax tables. Under WRAP-trainable quantizers `i`
  tracks the data range and only `f` feels the EBOPs gradient, so "width" in THEORY M7 means
  `relu(i+f)` (plus the sign bit, reported separately, as the anchor defines it). Card Q08 (a
  fixed softmax-output sweep) is re-based as M003 (the table floor). Card Q12 (0-bit channels)
  becomes a measurement (Z02), because 0 bits is now reachable by design. Card Q03 (width init)
  becomes M012, stated as an `f0` with `i` tracked.

**The two [D19] branches.** Kai confirmed [D19] on 2026-09-27, so Delta runs as written. The
old-quantizer branch R4 is kept as a reversal contingency only. If the anchor ever reverts to the
old quantizer (the anchor's C′ alternative), every 350k cell in Delta is
`STATIC_INFEASIBLE` (old floors above), every screen runs at 5M against C′ (its in-wave replica
is the primary control, §3.3 R4), the derived floors
are recomputed under the old quantizer, and the parked old-quantizer entry "fixed 4-bit softmax
output" (the E1 retry) is reinstated. §3.3 says which entries survive that branch.

**The 350k base is set by the floor, and Kai confirmed it ([D21]).** Arm A is E, so the 350k
accuracy cells pair with arm A, and nothing here waits for the pilot. Each entry's `base["350000"]`
and `screen_role_350k` in `delta.json` say which of four roles its 350k cell has: an accuracy cell
on arm A, a feasibility probe on arm A (M047-M049), a floor-family cell on its own A07-derived
architecture, or an FF2 cell. §3.3 R2 gives the rules, including fallback C, where there is no
350k base at all.

## 1. How to read an entry

Every entry has an ID `M001`-`M103`, a name, a family, the card(s) it comes from, THEORY
mechanism(s) (M1 capacity and the fan-in-3 first layer, M2 STE bias, M3 flips and inertia, M4
scale loss, M5 attention failure, M6 the norm-free interaction, M7 width learning under the EBOPs
penalty), the exact delta from the config of the base arm named in `base[target]` (arm A = E at
350k, A07-350 for the floor family and the 1.4M rung, C at 5M), a code tier, the tried status, the screen and
confirm targets, the screen horizon H, the pairing to the base, a one-line directional
prediction, the mechanism diagnostic reported beside accuracy, and the derived floors.
`delta.json` carries the same fields plus `code_changes` (patch slugs),
`anchor_patches_required`, `if_floor_fails`, `fallback_E`, `floor_traced`, `screen_role_350k`,
`covered_by_anchor_study`, `hw_labels` (hardware-risk labels per row, §6 lesson 5) and the full
config delta. Top-level keys add `drift_replicas` (§5.2) and
`anchor_arms_after_D21`. `floor_derived.headroom_by_target` is the headroom on the entry's own
architecture. For a 350k cell that runs on arm A (E), the headroom that applies is in
`floor_derived.on_E`.

**Families.** F floor and attention cost; Q activation widths and the controller; B
binarization and latent-weight optimization; R recipe; P inputs and data; A architecture; BL
labelled non-binary baselines (never the thesis); FF1 and FF2 are fractional-factorial cells.

**Code tiers** (from `inventory/code-surface.md` §1, the S runner the anchor pins, not from the
cards):
- **T0**: config-only on a key the S runner reads today (`arch.n_heads`, `arch.n_part`,
  `arch.d_model`, `arch.ffn_dim`, `arch.n_layers`, `arch.pos_enc`, `train.ebops.pid.*`,
  `experiment.recovery_after_epochs`, `train.weight_decay` and the other optimizer fields).
  Inert keys (`train.lr_schedule`, `train.ebops.{controller, beta_schedule, selection,
  stop_on_target}`, `train.es_patience`, `arch.input_std`, `experiment.checkpoint_every_epochs`)
  are **not** T0.
- **T0a**: config-only once the anchor patch series lands, on a key that [A1] (schedule), [A2]
  (optimizer), [A3] (pT gate) or [A20] (quantizer set) introduces. Those key names are not fixed
  yet (the anchor writes "for example `act_overflow wrap`"). `delta.json` uses placeholder names
  (`train.lr` as the peak, `train.lr_cycle_epochs`, `train.optimizer`, `arch.pt_gate_gev`,
  `quant.act_f0`), which the generator maps. This matches the ml-engineer's two-column "ready"
  report (gated on the tarball, gated on the anchor).
- **T1**: a named patch of about 80 lines or less. **T2**: a new module (a new attention kind,
  body, optimizer or weight scheme). A combination takes the highest tier of its parts.
- Optimizer deltas are stated against the explicit [A2] path (`train.optimizer`), because a
  delta that sets `train.weight_decay` alone could be silently ignored under an `adam_default`
  branch.

**Pairing** follows the anchor's own convention:
- **paired**: shapes identical, so the same init at seed s (`matching_initialization` copies by
  path and shape) and the same `order_seed = f(s)`. Paired t, df = k − 1, with the sign count and
  the per-pair seed correlation.
- **paired-if-hash**: some tensors change shape. Paired t only if the PREFLIGHT `kernel_hashes`
  comparison ([A17] method) shows every unchanged-shape tensor identical to the base at seed s;
  otherwise Welch. Recorded before any result.
- **unpaired (Welch)**: the body is replaced, the inputs differ (N, input set), or the init is
  not seed-derived (warm start).
- Every Delta pod runs on a different GPU class and code sha from the anchor's seed-block pods,
  so same-seed pairs are never bit-identical. The per-pair correlation is always reported, and
  each wave carries a drift replica (§5.2).

**Targets.** A screen target is where the entry is screened; the confirm target is where a
survivor is confirmed. 350k cells are subject to the floor rules in §3.3.

## 2. Entries

103 entries: **50 singles** (46 methods and 4 labelled non-binary baselines) and **53
combinations** (31 packages and 22 fractional-factorial cells). By family: F 20, R 18, B 16,
FF1 15, P 12, FF2 7, Q 6, A 5, BL 4 (packages are counted under the family of their theme). By
code tier: T0 11, T0a 8, T1 73, T2 11; singles only: T0 10, T0a 5, T1 30, T2 5; combinations
only: T0 1, T0a 3, T1 43, T2 6. One single, M014, has no screen cell. It is confirm-only and
offered at K3 (§5.3 G0), so the screen runs 49 singles.

**Overlap with the anchor study's second wave (arms H and NB, Kai 2026-09-27).** Arm NB
(learned-width weights on the arm-A recipe, E at 350k, seeds 1-8, 7,000 epochs) is M049's 350k
cell at full length: `covered_by_anchor_study` marks it. The M049 350k screen cell stays in the
budget as an upper bound, and the wave-2 STUDY drops it if NB's epoch-500 snapshot exists by K2.
M049 at 350k is never a separate confirm cell, and M049's `hgq-learnable-weights` patch and NB's
`kbi_learnable` path are one code item. Not covered: M049 at 5M (on C), M047 (ternary), M048 (int8
everywhere), M050 (int8 `input_proj`) and M006 (binary Deep Sets). NB and H are the anchor's
non-binary comparands at 350k beside them; H is Chang's transformer (xfm-n64), not the Deep Sets
body.

### 2.1 Singles (M001-M050)

Pruning applied to the 70 cards, with reasons in §9: duplicates merged (R13 = P09; A14's
placement folded into M016); cards whose own hazards break the thesis parked, unless relabelled
a baseline (a new act×act multiply: A07 PMA or class token, A13 GLU, the square in RMSNorm; more
than two weight values: B03 arbitrary per-channel β, B12 two-set; ternary kept only as the
labelled baseline M047); cards whose treatment the screen cannot measure moved to a longer
horizon (M015, M031, M032), made confirm-only (M014), or parked (P08); unschedulable cards parked (Q11: no source for the
PUPPI bit width). Five singles come from THEORY levers rather than cards (M007, M008, M021,
M022, M049), and M024/M025 restrict card B03 to power-of-two gains.

"h" in the floor column is the derived 350k headroom fraction (target − floor0)/(floor1 −
floor0), clipped at 1, computed on the entry's own architecture. The formula includes the traced
exp-input and LUT terms, and "(= trace)" marks an architecture that equals a traced config.
"350k on E" gives h on arm A (E) for a near-floor cell (§3.3 R2). "trace" means the value
cannot be derived without the wave-1 trace (the Deep Sets body). "n/a" marks a floor that needs
fixed weight bits (M047 waits on Z06; M049 learns its widths). H is the screen horizon in epochs.
The note column carries the pre-registered notes: the hardware labels, the reasons each retry
differs from its recorded failure, and the ladder-only status.

| ID | name | fam. | cards | mech. | delta from the base arm (`base[target]`) | code tier / patches | tried | targets (screen → confirm) | H | pairing | prediction | mechanism diagnostic | floor0 / floor1 (derived), h at 350k; 350k on E | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M001 | Two heads at d32 | F | A01, tried D6 | M5, M7 | `arch.n_heads=2` | T0: — | tried-failed (A08: H=2 at N=16, never feasible under the old SAT quantizer, TR23:33); retried because the D19 softmax floor halves with H (derived 171,526 incl. the SAT exp-input term) | 350k, 5M → 350k, 5M | 500 | paired-if-hash (Wq/Wk/Wv reshape per head; [A17]-style kernel_hashes check, else Welch) | feasible at 350k in more seeds than A07-350; accuracy at 5M flat to slightly down | EBOPs split (softmax / QK / AV / dense), Q/K and V 0-bit fractions, entropy/log n_valid | 171,526 / 834,214; h=0.269 | — |
| M002 | One head at d32 | F | A01, tried D6 | M5, M7 | `arch.n_heads=1` | T0: — | tried-failed-with-mechanism (B01 at N=16, 3 seeds, never feasible, old quantizer, TR23:49); retried for the D19 floor (derived 85,763 incl. the SAT exp-input term) | 350k, 5M → 350k, 5M | 500 | paired-if-hash | 350k feasibility up; accuracy at 5M below M001 | as M001 | 85,763 / 748,451; h=0.399 | — |
| M003 | Softmax table minimum 2 bits | F | Q08 (re-based under D19) | M7 | `quant.softmax_table_min_bits=2` | T1: `softmax-table-min-bits` | untried (E1 lowered the fixed softmax OUTPUT to 4 bits, archived, no target; tables were never trainable before D19) | 350k, 5M → 350k, 5M | 500 | paired (same shapes) | lowers the A07 floor to derived 114,189; accuracy at 5M flat | table widths at the selected checkpoint, EBOPs split | 114,189 / 776,877; h=0.356 | departs from Chang's bc=Min(4); labelled |
| M004 | Linformer projection k=8 | F | A10 | M5, M7 | `arch.attn_kind=linformer`; `arch.linformer_k=8` | T2: `attn-linformer` | untried with binary weights (never implemented, CHG:184); H6 ran Sun et al.'s LUT Linformer with HGQ weights, not comparable | 350k, 5M → 350k, 5M | 500 | paired-if-hash (new E/F projections; other kernels shared) | 350k feasible with real headroom (derived h 0.66); accuracy at 5M within the interval of C | EBOPs split, entropy over k projected keys, attention-ablation delta | 41,997 / 508,077; h=0.661 | — |
| M005 | Softmax-free ReLU/N attention | F | Q10, tried D11 | M5, M7 | `arch.attn_kind=relu_over_n` | T2: `attn-relu-over-n` | tried-negative-as-noise (D11 era-1 softmax-free, old dataset, too-hot LR, no target); retried because it removes the whole D19 softmax floor | 350k, 5M → 350k, 5M | 500 | paired-if-hash | 350k feasible; accuracy at 5M below C (competitive normalization lost) | attention-ablation delta, EBOPs split | 0 / 662,688; h=0.528 | — |
| M006 | Binary Deep Sets body | F | A09 | M5 | `arch.body=deepsets`; `arch.deepsets_dims={"phi":[64,64],"ctx":64,"phi_post":[64],"rho":[64,32,16],"pool_scale":0.0625}` | T2: `body-deepsets` | untried with binary weights (CHG:184) | 350k, 5M → 350k, 5M | 500 | unpaired (Welch): no shared attention tensors | accuracy >= anchor at 350k (Sun et al. collapse argument); at 5M below C | none of the attention diagnostics apply; report per-class AUC and the width map | trace | deepsets_dims from reference-code/HGQ2-examples/jsc150/model.py:88-100 (get_gnn: phi 64, s 64 at l. 88-89; context 64 at l. 90-92; post 64 at l. 95; pool x 1/16 at l. 96; rho 64/32/16 at l. 97-99), in the dict form code/newmods/deepsets.py DEFAULT_DIMS accepts; dims only, no code lifted; no batch norm, binary weights (deviations listed in deepsets.py) |
| M007 | Q/K stream width floor 1 bit | F | THEORY M5 (Q column) | M5 | `quant.qk_min_bits=1` | T1: `qk-stream-min-bits` | untried | 5M → 5M | 500 | paired | forbids the Q/K 0-bit collapse; at 5M accuracy up if attention matters | Q/K 0-bit fraction must be 0; entropy/log n_valid; attention-ablation delta | 474,125 / 1,005,741 | A07 derived floor 474,125 > 350k: 350k only in combination with M001 or M004 |
| M008 | Attention-group EBOPs weight x0.1 | F | THEORY M5/M7 | M5, M7 | `quant.ebops_group_weight={"attention":0.1,"rest":1.0}` | T1: `ebops-group-weight` | untried | 350k, 5M → 350k, 5M | 500 | paired | 350k: attention survives longer, dense layers pruned harder; sign budget-dependent | EBOPs split by group against epoch, Q/K/V 0-bit fractions | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | — |
| M009 | N = 32 constituents (cross-N, the point) | F | P01, tried D3 | M7 | `arch.n_part=32` | T0: — | tried-failed (A05 N=32 at 350k never feasible under the old quantizer, TR23:30); retried: derived D19 floor 85,517 < 350k; the derived 1-bit-alive floor 351,917 is just above 350k (it was 347,808 before the SAT exp-input term) | 350k, 5M → 350k, 5M | 500 | unpaired (Welch): different inputs; crosses N by design, labelled | 350k feasible with nearly every channel alive (h 0.99: the 1-bit-alive floor exceeds 350k by 1,917); accuracy vs A undetermined (context vs bits) | EBOPs split, 0-bit fractions | 85,517 / 351,917; h=0.993 | needs a gated 90/10 N=32 cache (CPU job) |
| M010 | Target 1.4M (ladder rung) | F | Q07 | M7 | `train.ebops.pid.target_ebops=1400000` | T0: — | untried rung (anchor ladder after [D21]: B = E at 250k, A = E at 350k, A07-350 descriptive, C = A07 at 5M) | 1.4M → 1.4M | 500 | paired (A07, same shapes) to A07-350's seeds at a different target: a ladder point, no same-target control, so G3 does not apply | accuracy between A07-350 and C; knee location (descriptive; never advances on accuracy) | feasible count, EBOPs split, 0-bit fractions | 343,053 / 1,005,741 (= trace) | ladder point only: no same-target control exists; G2 counts and the ladder plot are reported, G3 is not applied |
| M011 | Per-value activation widths (Chang value-wise) | Q | Q02 | M7 | `quant.act_granularity=element` | T1: `act-granularity-element` | untried | 350k, 5M → 350k, 5M | 500 | paired | up at 350k (bits placed per particle rank), flat at 5M | 0-bit fraction per position; EBOPs split | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | — |
| M012 | Activation init f0 = 7 (Chang) | Q | Q03 (re-based: under D19 i tracks the range, only f feels the EBOPs gradient) | M7 | `quant.act_f0=7` | T0a: `act-init-f0` | untried | 350k, 5M → 350k, 5M | 500 | paired | slower EBOPs descent (wider start); selected accuracy within the interval | EBOPs against epoch, first feasible epoch | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | key name set by [A20]; T0a if [A20] exposes f0, else the patch |
| M013 | PID gains p 2, i 0.2 | Q | Q04 | M7 | `train.ebops.pid.p=2.0`; `train.ebops.pid.i=0.2` | T0: — | untried (B08 gentler PID planned, never run, PLAN:106-121) | 350k → 350k | 500 | paired | more seeds feasible by epoch 500; accuracy flat | beta trajectory, first feasible epoch, EBOPs overshoot below target | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | 350k only: its purpose is reaching the budget; at 5M the anchor PID already reaches the target (C9/C10 context) |
| M014 | Open-loop beta schedule (Chang code) | Q | Q04, R00 | M7 | `train.ebops.controller=schedule`; `train.ebops.beta_schedule=[[0,2e-08,"linear"],[2000,3e-07,"log"],[7000,3e-06,"constant"]]` | T1: `beta-schedule-s-runner` | tried-once (C2, R13 sighter, archived, 16 features: reached 5e5 about 14 AUC points below its own peak, XL:3690); retried as the Chang-code fidelity element |  → 350k | 500 | paired | fewer seeds feasible than PID at matched epochs (open loop does not aim at a target); testable only over the full 7,000-epoch schedule | EBOPs against epoch, feasible count | 343,053 / 1,005,741 (= trace) | schedule values from jsc150/run_train.py:90; not screenable: at H = 500 only the first linear segment runs (beta 2e-8 to about 9e-8 of a schedule that ends at 3e-6), and even H = 2,000 ends at 3e-7, a tenth of the final beta. No screen cell; offered at K3 as a confirm-only Chang-fidelity element (7,000 epochs, 8 seeds, vs the 350k base at the terminal epoch) |
| M015 | Fixed-width recovery after epoch 500 | Q | Q14, tried B5 | M7 | `experiment.recovery_after_epochs=500` | T0: — | tried-failed-with-mechanism (B5: the selected checkpoint preceded the freeze, ABL:101); retried with a horizon that covers the treatment | 350k, 5M → 350k, 5M | 1000 | paired (vs anchor epoch-1,000 snapshot) | accuracy up after the freeze at unchanged EBOPs | onset = the logged freeze epoch (first feasible epoch >= 500); selected epoch must be later, else 'treatment not measured' | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | — |
| M016 | tanh LUT before attention and FFN (Chang) | Q | Q09, A14 (placement) | M6 | `arch.pre_block_act=tanh_lut` | T1: `pre-block-tanh-lut` | untried | 350k, 5M → 350k, 5M | 500 | paired-if-hash | small accuracy gain (range control on a norm-free graph); EBOPs of the table traced | saturation fraction at the following quantizer; table EBOPs term | 343,053 / 1,005,741; h=0.010; 350k on E: h=0.399 | export path has no LUT layer yet (J10 class) |
| M017 | Uncentered absmean (BitNet/XNOR convention) | B | B02 | M3 | `quant.binary_center=false` | T1: `binarizer-center-flag` | untried as a training arm (A3 compared the formulas on one checkpoint only) | 5M → 5M, 350k | 500 | paired | flat; fewer collective flips (threshold no longer moves with the tensor mean) | FF ratio per epoch | 343,053 / 1,005,741 (= trace) | — |
| M018 | Clipped-identity STE (hard-tanh) | B | B04 | M2 | `quant.ste=clip_identity` | T1: `ste-variants` | untried; the bounded STE replaced qkeras' wc/beta backward after the A4 NaN (2026-07-07) | 5M → 5M, 350k | 500 | paired | flat to up at LR 3e-3; fewer divergences | STE/latent gradient cosine, latent-vs-binary gap | 343,053 / 1,005,741 (= trace) | — |
| M019 | EDE annealed STE, restarted each LR cycle | B | B07 | M2 | `quant.ste=ede`; `quant.ste_ede_period=500` | T1: `ste-variants` | untried | 5M → 5M, 350k | 500 | paired | up (sharpening synced to the cosine cycle) | latent-vs-binary gap per cycle | 343,053 / 1,005,741 (= trace) | — |
| M020 | Bop optimizer on binary latents | B | B10 | M3 | `train.binary_optimizer=bop`; `train.bop_gamma=0.0001`; `train.bop_tau=1e-08` | T2: `bop-optimizer` | untried | 5M → 5M, 350k | 500 | paired (same init; different update rule) | sign unknown (designed for W1A1) | FF ratio, C2I ratio | 343,053 / 1,005,741 (= trace) | Bop gamma 1e-4 (undecayed) and tau 1e-8: scan seed, not tuned for this setup (DR-22). Sources: arXiv:1906.02107 §5.2 (CIFAR-10: gamma 1e-4 decayed x0.1 every 100 epochs, tau 1e-8) and §5.3 (ImageNet: gamma 1e-4 to 1e-6 linear, tau 1e-8); Larq larq.optimizers.Bop defaults threshold 1e-8, gamma 1e-4, no decay (larq/larq master, commit 3d7de8832a477285bbf3c36252e24fcb9299a959, optimizers.py l. 314-316; a master commit, not a tagged release). The paper tuned W1A1 conv nets at batch 50/1024, and tau is an absolute threshold on the EMA gradient, whose units differ in our pipeline (research/DR-22-bop-hyperparameters.md §4). The wave STUDY measures the |m| distribution of the anchor's binary latents (arm A, a few hundred steps) and may pre-register a tau scan before launch. Kai decision at K2, before M020 is packed (code/GATES.md, Bop DECISION): the flip rule. Option 1 (patch 0024, code/newmods/bop.py): a flip reflects the latent about its mean, w <- 2*alpha - w, which keeps |w - alpha| and so the layer scale beta, keeping activation ranges comparable with the Adam anchor; not the paper's rule. Option 2 (Bop as published, arXiv:1906.02107 Algorithm 2): the weight is the sign itself and a flip sets w <- -w with latents at +-1, so beta becomes 1 - alpha^2 and activation scales change against the Adam anchor |
| M021 | Latent clip to [-1, 1] | B | THEORY M3, B09 source (BinaryConnect) | M3 | `quant.latent_clip=1.0` | T1: `latent-clip` | untried | 5M → 5M, 350k | 500 | paired | up late in training (inertia capped); partly redundant with restarts | latent |w|/beta histogram, FF ratio late in each cycle | 343,053 / 1,005,741 (= trace) | — |
| M022 | Beta decoupled from latent magnitude (learned, power of two) | B | THEORY M3/M6 | M3, M6 | `quant.beta_mode=learned_pow2` | T1: `beta-mode` | untried | 5M → 5M, 350k | 500 | paired | up; beta stops tracking latent growth | beta vs integer-bit trajectory correlation | 343,053 / 1,005,741 (= trace) | — |
| M023 | Absmean beta rounded to a power of two (Libra-PB scale) | B | B06 | M4 | `quant.beta_mode=absmean_pow2` | T1: `beta-mode` | untried | 5M → 5M, 350k | 500 | paired | non-inferior accuracy; the beta-restore affines become shifts (LUT/DSP, not EBOPs) | non-inferiority only; the cost claim needs csynth on mulder | 343,053 / 1,005,741 (= trace) | advances on non-inferiority to a synthesis check, not to accuracy confirm |
| M024 | Power-of-two per-channel gain on input_proj | B | THEORY M1, B03 (restricted to shifts) | M1, M4 | `quant.channel_gain={"layers":["input_proj"],"mode":"pow2"}` | T1: `channel-gain-pow2` | untried | 5M → 5M, 350k | 500 | paired | up (the 8 expressible input directions get distinct gains) | distinct sign rows of input_proj, per-channel gain histogram | 343,053 / 1,005,741 (= trace) | per-channel binary gate (two symmetric values per channel); DSP audit before any hardware claim |
| M025 | Power-of-two per-channel gain on every binary layer | B | THEORY M4, B03 (restricted) | M4 | `quant.channel_gain={"layers":"all_binary","mode":"pow2"}` | T1: `channel-gain-pow2` | untried | 5M → 5M, 350k | 500 | paired | up; larger than M024 if scale loss is general (M4) rather than first-layer (M1) | least-squares per-channel alpha spread vs per-tensor beta | 343,053 / 1,005,741 (= trace) | — |
| M026 | Per-channel shift before activation quantizers (RSign) | B | B13 (shift only) | M4, M6 | `quant.pre_quant_shift=channel` | T1: `pre-quant-shift` | untried | 5M → 5M, 350k | 500 | paired | up; possibly lower achieved widths at equal accuracy | dead-ReLU fraction, width map | 343,053 / 1,005,741 (= trace) | — |
| M027 | Warm start from the FP teacher (two-stage) | B | B11/B12 staged idea, THEORY §5.1 | M2, M3 | `experiment.init_checkpoint=teacher-fp32-a07` | T1: `init-from-checkpoint`, `weight-scheme-baselines` | untried | 5M → 5M, 350k | 500 | unpaired (Welch): init not seed-derived; data order shared | up; faster to a given accuracy | C2I ratio (from teacher signs), latent-vs-binary gap | 343,053 / 1,005,741 (= trace) | needs the teacher prerequisite job P-T1; why this retry differs from the early-peak-then-squeeze failures (F1, C3 at 25 %, C4; lesson 2): those runs peaked unconstrained and were then squeezed to a budget far below the peak's cost (F1 2.44M to 350k, x0.14). Here the screen target is 5M, a squeeze from the traced 13.18M init to x0.38, the regime where C3's 75 % budget stayed feasible at a small cost; the 350k claim is tested only at confirm, and G1's H1-type test and the first-feasible-epoch log apply. If the student peaks at the start and falls >= 5 pt while its EBOPs fall, that is recorded as the F1 pattern, not as a null |
| M028 | Peak LR 1e-3 | R | R06, tried H1 | M2, M3 | `train.lr=0.001` | T0a: — | tried-failed-with-mechanism at LR >= 2e-4 (H1: STE collapse at epoch 2-3, archived recipe); the anchor's 3e-3 is the largest single risk | 5M → 5M, 350k | 500 | paired | fewer divergences than the base arm; accuracy flat or up | divergence/collapse count, FF ratio | 343,053 / 1,005,741 (= trace) | T0a assumes [A1] reads train.lr as the peak eta0; why this retry differs from H1 (LR >= 2e-4 collapsed at epoch 2-3, archived recipe; tried-already H1, XL:5797-5798): the anchor runs batch 2,790 (about 11x fewer steps per epoch than batch 256), a cosine decay to 1e-6 inside each 500-epoch cycle, and an EBOPs term; H1's batch size and STE version are not in the inventory, so these are the documented anchor differences, not a shown cause. Both rungs sit between H1's collapse range and the anchor's 3e-3: they locate the stability edge if the anchor arms collapse, and test whether a lower peak helps if they do not. G1's H1-type degradation test is the pre-registered detector |
| M029 | Peak LR 3e-4 | R | R06, tried H1 | M2, M3 | `train.lr=0.0003` | T0a: — | as M028 | 5M → 5M, 350k | 500 | paired | no divergence; accuracy below the base arm if the base is stable | as M028 | 343,053 / 1,005,741 (= trace) | why this retry differs from H1 (LR >= 2e-4 collapsed at epoch 2-3, archived recipe; tried-already H1, XL:5797-5798): the anchor runs batch 2,790 (about 11x fewer steps per epoch than batch 256), a cosine decay to 1e-6 inside each 500-epoch cycle, and an EBOPs term; H1's batch size and STE version are not in the inventory, so these are the documented anchor differences, not a shown cause. Both rungs sit between H1's collapse range and the anchor's 3e-3: they locate the stability edge if the anchor arms collapse, and test whether a lower peak helps if they do not. G1's H1-type degradation test is the pre-registered detector |
| M030 | Linear warm-up, 10 epochs | R | R04 | M2 | `train.lr_warmup_epochs=10` | T1: `lr-schedule-variants` | untried on the Chang schedule (the archived recipe has 1 warm-up epoch at 2e-5) | 5M → 5M, 350k | 500 | paired | fewer early collapses; accuracy flat | epoch of best validation in cycle 1, divergence count | 343,053 / 1,005,741 (= trace) | — |
| M031 | Peak decay m_mul 0.85 per restart | R | R03 | M3 | `train.lr_m_mul=0.85` | T1: `lr-schedule-variants` | untried | 5M → 5M, 350k | 1500 | paired (vs anchor epoch-1,500 snapshot) | fewer late divergences; accuracy flat or up | FF spike height at each restart | 343,053 / 1,005,741 (= trace) | cycle 1 is identical to the anchor; a 500-epoch screen would measure nothing |
| M032 | No restarts: one cosine over the horizon | R | THEORY §6.6, R02/R05 | M3 | `train.lr_cycle_epochs==horizon` | T0a: — | untried | 5M → 5M, 350k | 2000 | paired (vs anchor epoch-2,000 snapshot) | sign open (THEORY §6.6) | FF ratio vs epoch; within-cycle position of the best checkpoint | 343,053 / 1,005,741 (= trace) | screen proxy is one cosine over 2,000; confirm is one cosine over 7,000 |
| M033 | Weight decay 0.01 only (arm D decomposition) | R | R07, THEORY §2 | M3, M6 | `train.optimizer=adam`; `train.beta2=0.999`; `train.weight_decay=0.01`; `train.clipvalue=null` | T0a: — | untried alone (arm D has all three changes) | 5M → 5M, 350k | 500 | paired | higher FF ratio, smaller beta; accuracy sign open | FF ratio, beta trajectory | 343,053 / 1,005,741 (= trace) | stated against the explicit [A2] optimizer path so weight_decay is not silently ignored |
| M034 | EMA of latents, re-binarized for evaluation | R | R08 | M3 | `experiment.latent_ema_decay=0.999` | T1: `latent-ema-eval` | untried | 5M → 5M, 350k | 500 | paired | small gain; less checkpoint jitter | sign agreement EMA vs raw; validation jitter across epochs | 343,053 / 1,005,741 (= trace) | decay 0.999 is a design choice (Mean Teacher range, arXiv:1703.01780) |
| M035 | Logit KD from an FP teacher (T 2, 0.5) | R | R09, tried H5 | M2 | `experiment.distillation={"teacher_artifact":"teacher-fp32-a07","temperature":2,"coefficient":0.5}` | T1: `kd-unblock-s-runner`, `weight-scheme-baselines` | tried-failed-with-mechanism (H5/R6: interim snapshot, the trainer hung, teacher was the unconstrained pilot, ACC:19); retried with a new teacher on the gated 90/10 train split | 5M → 5M, 350k | 500 | paired | up, larger at the lower budget | per-class gap to the teacher | 343,053 / 1,005,741 (= trace) | T and coefficient from the R6 config (code-surface §2d) |
| M036 | Attention-map KD | R | R09, THEORY M5 | M5 | `experiment.distillation={"teacher_artifact":"teacher-fp32-a07","temperature":2,"coefficient":0.0,"attention_coefficient":1.0}` | T1: `kd-unblock-s-runner`, `kd-attention-map`, `weight-scheme-baselines` | untried | 5M → 5M, 350k | 500 | paired | attention stays non-uniform; accuracy up | entropy/log n_valid vs teacher, attention-ablation delta | 343,053 / 1,005,741 (= trace) | — |
| M037 | eta/phi reflection augmentation | P | R13, P09 | M1 | `data.augment={"reflect_eta":true,"reflect_phi":true}` | T1: `augment-eta-phi-reflect` | untried (no augmentation in any record; BNJetTagAug is a project name) | 5M → 5M, 350k | 500 | paired | narrower seed spread; mean flat or up | paired sd of the gap; per-class accuracy | 343,053 / 1,005,741 (= trace) | — |
| M038 | pT gate off (0 GeV) | P | P02 | M5 | `arch.pt_gate_gev=0` | T1: `pt-gate-threshold` | untried as an arm on the Chang recipe (every current run before the anchor is ungated, but under other recipes) | 350k, 5M → 350k, 5M | 500 | paired (same shapes; inputs differ) | sign open: more real low-pT constituents vs more junk in the statistics | padding/gated fraction per jet, entropy/log n_valid | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | needs an ungated 90/10 cache; 0 here means ungated: the generator writes it as an explicit arch.pt_gate_gev null ([A3]: null = ungated; 0 would gate at pT >= 0 with another cache identity), and the null must stay explicit so it overrides the anchor's 2 GeV gate once the anchor base replaces the stand-in |
| M039 | Mask gated and padded keys | P | P03, THEORY M5/§5.5 | M5 | `arch.mask_gated_keys=true` | T1: `gated-key-mask` | untried | 350k, 5M → 350k, 5M | 500 | paired | up; entropy diagnostic no longer inflated by padding | entropy/log n_valid; token-fold hazard noted for export | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 | — |
| M040 | Derived features log pT and Delta R (5 inputs) | P | P05, THEORY M1 | M1 | `arch.n_feat=5`; `arch.derived_features=["log_pt","delta_r"]` | T1: `derived-input-features` | untried (input-set changes were archived and crossed N, G1) | 350k, 5M → 350k, 5M | 500 | paired-if-hash (input_proj fan-in changes); crosses input set by design, labelled | up (more expressible first-layer directions); the iso-EBOPs match excludes the off-model feature computation | distinct sign rows of input_proj | 343,053 / 1,009,837; h=0.010; 350k on E: h=0.396 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) |
| M041 | Standardize over real slots only | P | P06 | M6 | `data.std_scope=real_slots` | T1: `std-real-slots` | untried | 5M → 5M, 350k | 500 | paired | up (operating point of the first binary layer no longer set by padding) | input range at the first quantizer, saturation fraction | 343,053 / 1,005,741 (= trace) | — |
| M042 | d_model 16 | A | A01 | M1, M7 | `arch.d_model=16` | T0: — | tried-failed (D4 D16 at N=16/64, old quantizer) | 350k, 5M → 350k, 5M | 500 | paired-if-hash | 350k: more headroom for widths than A07, still near-floor (derived h 0.026); 5M below C | effective width, EBOPs split | 343,053 / 608,605; h=0.026; 350k on E: h=0.672 | — |
| M043 | FFN 64 | A | A03, tried D1 | M1 | `arch.ffn_dim=64` | T0: — | tried (D1: FFN 32 beat 64 at N=8, 350k, single seed, old quantizer) | 350k, 5M → 350k, 5M | 500 | paired-if-hash | 350k worse (derived h 0.009); 5M flat or up | EBOPs split | 343,053 / 1,136,813; h=0.009; 350k on E: h=0.327 | — |
| M044 | Two blocks (L = 2) | A | A02 | M1 | `arch.n_layers=2` | T0: — | tried-failed at 350k with the old quantizer (A00-A03 N=8/16/64 screens) | 5M → 5M | 500 | paired-if-hash | 5M: up if depth matters | EBOPs split per block | 686,106 / 2,004,154 | derived floor 686,106 > 350k |
| M045 | Head 32/32/32 (Chang) | A | A08 | M1 | `arch.head_dims=[32,32,32]` | T1: `head-dims` | untried | 350k, 5M → 350k, 5M | 500 | paired-if-hash | flat (Sun et al. head depth has no monotone relation to their Table 1) | width map of the head | 343,053 / 1,007,789; h=0.010; 350k on E: h=0.397 | — |
| M046 | No positional encoding (5M cell; at 350k the PE contrast is anchor A vs F) | A | A04 | M5 | `arch.pos_enc=none` | T0: — | designed as anchor arm F at 350k (pre-[D21] F = A07 without PE), not run; tried-failed at N=16 under the old quantizer (D7, largest seed spread) | 5M → 5M | 500 | paired if [A17] shows only pos_table differs, else Welch (anchor rule) | flat or up (permutation invariance); gated tokens become exact duplicates | duplicated-token count, entropy/log n_valid | 343,053 / 1,005,741 (= trace) | exists so the gate x PE x mask cube has a 5M single; at 350k the PE contrast is anchor A (E, no PE) against anchor F (E + learned PE) [D21] |
| M047 | Ternary absmean (labelled baseline) | BL | B14 | M1, M4 | `quant.weight=ternary_absmean` | T1: `ternary-absmean`, `weight-scheme-baselines` | untried at this architecture (A5 archived, old dataset) | 350k, 5M → 350k, 5M | 500 | paired | ternary >= binary on accuracy (Sloot FastML 2026 direction) | zero fraction per layer; how HGQ2 counts the zeros (Z06) | 343,053 / n/a; 350k on E: h=n/a | floor1 n/a until Z06 (how HGQ2 0.1.9 bills a ternary weight); 350k on E is near-floor or not derivable too (on-E h n/a): the 350k cell is a feasibility probe on E, no accuracy reading |
| M048 | int8 static weights, all layers (matched non-binary) | BL | THEORY §6.2, anchor follow-up | M1 | `quant.weight=int8_absmax` | T1: `weight-scheme-baselines` | archived only (A6, no target); never under an EBOPs target | 350k, 5M → 350k, 5M | 500 | paired | above C at 5M; at 350k the weight bits cost more EBOPs | EBOPs split; the same attention diagnostics | 343,053 / 3,809,549; h=0.002; 350k on E: h=0.081 | int8_absmax is a fixed fixed<8,3> grid, not absmax (code-surface §4); floor1 prices every dense and head layer at b_w = 8; 350k on E is near-floor or not derivable too (on-E h 0.081): the 350k cell is a feasibility probe on E, no accuracy reading |
| M049 | HGQ learnable weight widths (matched to Sun et al.) | BL | THEORY §6.2 | M5, M7 | `quant.weight=hgq_learnable` | T2: `hgq-learnable-weights` | untried in-house (H6 ran Sun et al.'s own code, archived, circular selection) | 350k, 5M → 350k, 5M | 500 | paired-if-hash | collapses at 350k like Sun et al. if the collapse is budget geometry | Q/K/V 0-bit fractions, entropy, ablation delta | 343,053 / n/a; 350k on E: h=n/a | floor1 n/a: learned weight widths (0 bits reachable), no fixed b_w; the 350k cell is covered by the anchor study's arm NB (field covered_by_anchor_study), the 5M cell is not; 350k on E is near-floor or not derivable too (on-E h n/a): the 350k cell is a feasibility probe on E, no accuracy reading |
| M050 | 8-bit input_proj only | BL | THEORY M1, §6.3 | M1 | `quant.layer_weight_override={"input_proj":"int8_absmax"}` | T1: `weight-scheme-baselines` | untried | 350k, 5M → 350k, 5M | 500 | paired | gap to the base arm measures the fan-in-3 first-layer loss | distinct sign rows (base arm) vs this arm | 343,053 / 1,048,749; h=0.010; 350k on E: h=0.372 | floor1 prices input_proj at b_w = 8 (+7 x 6,144) |

### 2.2 Combination packages (M051-M103)

Every combination is labelled a **package**. It is read only against its decomposition ladder,
on the same seeds and at the same target: the components (and, for stacks, the pairs below them)
first, then the package. The interaction I = g_package − Σ g_components is reported with its
interval and is descriptive. A package advances only if it beats its best component (§5.3).
Where a component has no cell at a target (M007 alone is statically infeasible at 350k), the
decomposition at that target is one-sided, and the table says so.

**Where the packages come from.**
1. THEORY §5 synergy/redundancy list, crossed as small factorials at matched seeds:
   - KD × progressive binarization (§5.1): M061-M064.
   - Per-channel scale × learned widths (§5.2): M065, M066.
   - Restarts × latent-weight treatments, and Adam × Bop (§5.3): M068-M073.
   - EBOPs target × attention levers (§5.4): every F entry runs at both targets. The floor
     crosses are M051-M060.
   - Gate × PE × masking (§5.5): a full 2³ at 5M (M038, M046 and M039 are the singles;
     M075-M078 are the other cells; M079 adds real-slot standardization to masking). At 350k,
     on arm A (E, no PE), it is the gate × mask square; A against F is the anchor's PE contrast.
   - Input features × first-layer scale (§5.6): M067.
2. **Arm D decomposition.** Arm D changes three optimizer fields at once. M033 (weight decay
   alone), M074 (clipvalue 1 + β₂ 0.98) and M103 (all three, i.e. arm D's optimizer) make, with
   arm C, a 2 × 2 in {weight decay} × {clip + β₂} at 5M. Arm D itself exists only at 350k, on E
   [D21], so M103 is the 5M corner.
3. **Stacks** (M060 floor, M064 teacher, M073 inertia, M080 first layer) are theory-motivated packages written now, before
   any result. They are not "stack the winners" chosen after the screens; that choice belongs to
   Kai at the confirm gate (§7).
4. **Fractional factorials** for the sets THEORY §5 calls additive ("training-only B/R levers
   against P levers on M1; KD against architecture size; data against everything"). The
   factorials test that additivity rather than assume it.

**FF1: 2^(5−1), resolution V, base arm C (A07, 5M), H = 500, n seeds per cell (4 as the lower
bound, §5.1).** Factors: A =
EDE STE (M019, M2), B = derived input features (M040, M1, an input-set change by design), C =
logit KD (M035), D = d_model 16 (M042, architecture size), E = η/φ reflection augmentation (M037).
Generator **E = −ABCD** (defining relation I = −ABCDE). Parity check: the product of the five ±1
levels is −1 in every cell, so a cell has an odd number of low factors. The fraction therefore
holds the all-low cell, the 10 two-high cells and the 5 four-high cells (16 cells, 15 new:
M081-M095). The all-low cell is the **in-wave arm C replica** (§5.2), run at the Delta code sha
on Delta pods like the other 15 cells, not the anchor's own snapshot. The all-low cell sits in the
low group of every contrast, so a pod or sha offset in it would bias all five main effects and
every 2FI. The anchor snapshot stays the drift check. With the opposite sign (+ABCD) the fraction would
hold the five one-high cells and the all-high cell instead, and would lose the anchor cell. The
one-high cells exist anyway as singles, so they augment the fraction. Aliasing: each main effect
is aliased with a four-factor interaction and each two-factor interaction with a
three-factor interaction, so all main effects and all ten 2FIs are estimable. Analysis:
accuracy_val ~ seed block + 5 main effects + 10 2FIs, by OLS on 16 cells × 4 seeds = 64 runs
(19 parameters, 45 residual df).

**FF2: 2^(4−1), resolution IV, base arm A (E: d24, 2 heads, no PE, 350k; [D21]), H = 500, n seeds per
cell (4 as the lower bound).** The Chang-parity elements our config schema lacks: A = per-value widths (M011), B =
Chang init f0 = 7 (M012), C = tanh LUT before attention and FFN (M016), D = head 32/32/32
(M045). Generator **D = ABC** (I = ABCD): an even number of low factors in every cell, so the
fraction holds the all-low cell (the **in-wave arm A replica**, for the same reason as in FF1), the
six two-high cells and the all-high "full parity" cell (7 new: M096-M102). Aliasing: main effects are clear of 2FIs (aliased with three-factor interactions); the
2FIs are aliased in pairs AB = CD, AC = BD, AD = BC. Analysis: seed block + 4 main effects + 3
aliased 2FI pairs by OLS on 8 cells × 4 seeds = 32 runs (11 parameters, 21 residual df). FF2
sits on E because E is the anchor arm with real 350k headroom (traced h 0.399) and is
Chang-sized; after [D21] E is arm A. It is Delta's direct answer to Kai's "some with a changed architecture". If arm A turns
out infeasible at 350k (fewer than 3 of seeds 1-4 feasible at the anchor's epoch-500 snapshot;
with n screen seeds, fewer than ⌈3n/4⌉ of seeds 1-n),
FF2 re-bases to A07 at 5M: the same 7 new cells on arm C, with the in-wave C replica as the
all-low cell and the same analysis (Kai may instead drop it at K1). Under R4 arm C is C′, so FF2
re-bases to C′ at 5M with the C′ replica as the all-low cell. The
open-loop β schedule (M014) is kept out of FF2 because it changes feasibility, not a width
detail, and would confound every cell.

| ID | package | fam. | = components | decomposition ladder | extra delta | code tier | targets (screen → confirm) | H | pairing | prediction | diagnostic | floor0 / floor1 (derived), h at 350k; 350k on E |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M051 | Two heads + table floor 2 bits | F | M001 + M003 | M001, M003 | — | T1 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | 350k headroom beyond either single | EBOPs split, Q/K/V 0-bit fractions | 57,094 / 719,782; h=0.442 |
| M052 | One head + table floor 2 bits | F | M002 + M003 | M002, M003 | — | T1 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | largest attention-keeping headroom among softmax arms | as above | 28,547 / 691,235; h=0.485 |
| M053 | Linformer k8 + two heads | F | M004 + M001 | M004, M001 | — | T2 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | feasible with most headroom; accuracy vs M004 flat | EBOPs split, entropy over projected keys | 20,998 / 487,078; h=0.706 |
| M054 | Linformer k8 + table floor 2 bits | F | M004 + M003 | M004, M003 | — | T2 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | redundant: the table term is already small under Linformer | EBOPs split | 13,837 / 479,917; h=0.721 |
| M055 | Q/K width floor + two heads | F | M007 + M001 | M007 (5M only), M001 | at 350k the decomposition is one-sided: M007 alone is statically infeasible there | T1 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | 350k feasible (derived floor 302,598, h 0.089: near-floor) with attention forced alive | Q/K 0-bit fraction 0; entropy; ablation delta | 302,598 / 834,214; h=0.089; 350k on E: h=0.229 |
| M056 | Q/K width floor + Linformer k8 | F | M007 + M004 | M007 (5M only), M004 | at 350k the decomposition is one-sided | T2 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | 350k feasible with attention alive (derived floor 58,381) | as above | 58,381 / 508,077; h=0.648 |
| M057 | Attention-group weight + two heads | F | M008 + M001 | M008, M001 | — | T1 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | attention survives at 350k | EBOPs split by group | 171,526 / 834,214; h=0.269 |
| M058 | N = 32 + two heads (cross-N) | F | M009 + M001 | M009, M001 | — | T0 | 350k, 5M → 350k, 5M | 500 | unpaired (Welch); crosses N, labelled | every channel alive at 350k with attention | as M009 | 42,758 / 309,158; h=1.000 |
| M059 | ReLU/N attention + Q/K width floor | F | M005 + M007 | M005, M007 (5M only) | at 350k the decomposition is one-sided | T2 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | softmax-free attention kept alive at 350k (derived floor 131,072) | ablation delta | 131,072 / 662,688; h=0.412 |
| M060 | Floor stack: Linformer + two heads + table 2 bits | F | M004 + M001 + M003 | M053, M054, M051 | — | T2 | 350k, 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | no gain over the best pair (redundant) | EBOPs split | 6,918 / 472,998; h=0.736 |
| M061 | Logit KD + warm start from teacher | R | M035 + M027 | M035, M027 | why this retry differs from the early-peak-then-squeeze failures (F1, C3 at 25 %, C4; lesson 2): those runs peaked unconstrained and were then squeezed to a budget far below the peak's cost (F1 2.44M to 350k, x0.14). Here the screen target is 5M, a squeeze from the traced 13.18M init to x0.38, the regime where C3's 75 % budget stayed feasible at a small cost; the 350k claim is tested only at confirm, and G1's H1-type test and the first-feasible-epoch log apply. If the student peaks at the start and falls >= 5 pt while its EBOPs fall, that is recorded as the F1 pattern, not as a null | T1 | 5M → 5M, 350k | 500 | unpaired (Welch): warm start | synergy; THEORY predicts larger at the low budget (tested at confirm) | per-class gap to teacher, C2I | 343,053 / 1,005,741 (= trace) |
| M062 | Attention KD + warm start | R | M036 + M027 | M036, M027 | why this retry differs from the early-peak-then-squeeze failures (F1, C3 at 25 %, C4; lesson 2): those runs peaked unconstrained and were then squeezed to a budget far below the peak's cost (F1 2.44M to 350k, x0.14). Here the screen target is 5M, a squeeze from the traced 13.18M init to x0.38, the regime where C3's 75 % budget stayed feasible at a small cost; the 350k claim is tested only at confirm, and G1's H1-type test and the first-feasible-epoch log apply. If the student peaks at the start and falls >= 5 pt while its EBOPs fall, that is recorded as the F1 pattern, not as a null | T1 | 5M → 5M, 350k | 500 | unpaired (Welch): warm start | synergy | entropy vs teacher | 343,053 / 1,005,741 (= trace) |
| M063 | Logit KD from the int8 teacher (staged, BiT-style) | R | M035 | M035, M048 | `experiment.distillation={"teacher_artifact":"teacher-int8-a07","temperature":2,"coefficient":0.5}`; teacher variant of M035; needs the int8 teacher job P-T2 | T1 | 5M → 5M, 350k | 500 | paired | closer teacher helps more than the FP teacher | per-class gap to both teachers | 343,053 / 1,005,741 (= trace) |
| M064 | Teacher stack: logit + attention KD + warm start | R | M035 + M036 + M027 | M061, M062 | why this retry differs from the early-peak-then-squeeze failures (F1, C3 at 25 %, C4; lesson 2): those runs peaked unconstrained and were then squeezed to a budget far below the peak's cost (F1 2.44M to 350k, x0.14). Here the screen target is 5M, a squeeze from the traced 13.18M init to x0.38, the regime where C3's 75 % budget stayed feasible at a small cost; the 350k claim is tested only at confirm, and G1's H1-type test and the first-feasible-epoch log apply. If the student peaks at the start and falls >= 5 pt while its EBOPs fall, that is recorded as the F1 pattern, not as a null | T1 | 5M → 5M, 350k | 500 | unpaired (Welch): warm start | no gain beyond the best pair | as components | 343,053 / 1,005,741 (= trace) |
| M065 | Per-channel pow2 gain + per-value widths | B | M025 + M011 | M025, M011 | — | T1 | 5M → 5M, 350k | 500 | paired | synergy (gain sets relative contributions, widths re-adapt) | gain histogram, width map | 343,053 / 1,005,741 (= trace) |
| M066 | Per-channel pow2 gain + shift (binary-safe affine) | B | M025 + M026 | M025, M026 | — | T1 | 5M → 5M, 350k | 500 | paired | additive or mildly synergistic; the binary-safe analogue of Chang's fused BN | dead-ReLU fraction, gain histogram | 343,053 / 1,005,741 (= trace) |
| M067 | Derived features + pow2 input_proj gain | P | M040 + M024 | M040, M024 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | strictest component rule (paired / paired-if-hash / Welch) | redundant at the margin (both enlarge input directions, THEORY §5.6) | distinct sign rows | 343,053 / 1,009,837 |
| M068 | No restarts + latent clip | R | M032 + M021 | M032, M021 | — | T1 | 5M → 5M, 350k | 2000 | paired | partly redundant | FF ratio | 343,053 / 1,005,741 (= trace) |
| M069 | No restarts + weight decay | R | M032 + M033 | M032, M033 | — | T0a | 5M → 5M, 350k | 2000 | paired | partly redundant | FF ratio, beta trajectory | 343,053 / 1,005,741 (= trace) |
| M070 | Latent clip + weight decay | R | M021 + M033 | M021, M033 | — | T1 | 5M → 5M, 350k | 500 | paired | redundant (both cap inertia) | latent histogram | 343,053 / 1,005,741 (= trace) |
| M071 | Bop + no restarts | B | M020 + M032 | M020, M032 | Bop gamma 1e-4 (undecayed) and tau 1e-8: scan seed, not tuned for this setup (DR-22). Sources: arXiv:1906.02107 §5.2 (CIFAR-10: gamma 1e-4 decayed x0.1 every 100 epochs, tau 1e-8) and §5.3 (ImageNet: gamma 1e-4 to 1e-6 linear, tau 1e-8); Larq larq.optimizers.Bop defaults threshold 1e-8, gamma 1e-4, no decay (larq/larq master, commit 3d7de8832a477285bbf3c36252e24fcb9299a959, optimizers.py l. 314-316; a master commit, not a tagged release). The paper tuned W1A1 conv nets at batch 50/1024, and tau is an absolute threshold on the EMA gradient, whose units differ in our pipeline (research/DR-22-bop-hyperparameters.md §4). The wave STUDY measures the |m| distribution of the anchor's binary latents (arm A, a few hundred steps) and may pre-register a tau scan before launch. Kai decision at K2, before M020 is packed (code/GATES.md, Bop DECISION): the flip rule. Option 1 (patch 0024, code/newmods/bop.py): a flip reflects the latent about its mean, w <- 2*alpha - w, which keeps |w - alpha| and so the layer scale beta, keeping activation ranges comparable with the Adam anchor; not the paper's rule. Option 2 (Bop as published, arXiv:1906.02107 Algorithm 2): the weight is the sign itself and a flip sets w <- -w with latents at +-1, so beta becomes 1 - alpha^2 and activation scales change against the Adam anchor | T2 | 5M → 5M, 350k | 2000 | paired | restarts do not act on Bop; no interaction expected | FF ratio | 343,053 / 1,005,741 (= trace) |
| M072 | EDE annealed once + no restarts | B | M019 + M032 | M019, M032 | `quant.ste_ede_period="=horizon"` | T1 | 5M → 5M, 350k | 2000 | paired | up over EDE-per-cycle only if restarts fight the anneal | latent-vs-binary gap | 343,053 / 1,005,741 (= trace) |
| M073 | Inertia stack: EDE + latent clip + no restarts | B | M019 + M021 + M032 | M068, M072 | `quant.ste_ede_period="=horizon"` | T1 | 5M → 5M, 350k | 2000 | paired | no gain beyond the best pair | FF ratio | 343,053 / 1,005,741 (= trace) |
| M074 | clipvalue 1 + beta2 0.98 (arm D minus weight decay) | R | — | M033, anchor-arm-D | `train.optimizer="adam"`; `train.beta2=0.98`; `train.weight_decay=null`; `train.clipvalue=1.0` | T0a | 5M → 5M, 350k | 500 | paired | with M033 and arm D: a 2x2 in {wd} x {clip + beta2}; additivity checked | divergence count, FF ratio | 343,053 / 1,005,741 (= trace) |
| M075 | Gate off + no PE | P | M038 + M046 | M038, M046 (5M; the 350k cell is dropped, no-PE is a no-op on arm A) | 350k dropped: on arm A (E, no PE; [D21]) the no-PE factor is a no-op, so this cell duplicates another cell of the gate x mask square on arm A | T1 | 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | 2^3 cell | entropy/log n_valid, duplicated-token count | 343,053 / 1,005,741 (= trace); h=0.010 |
| M076 | Gate off + masking | P | M038 + M039 | M038, M039 | — | T1 | 350k, 5M → 350k, 5M | 500 | paired | 2^3 cell | as above | 343,053 / 1,005,741 (= trace); h=0.010; 350k on E: h=0.399 |
| M077 | No PE + masking | P | M046 + M039 | M046 (5M; the 350k cell is dropped, no-PE is a no-op on arm A), M039 | 350k dropped: on arm A (E, no PE; [D21]) the no-PE factor is a no-op, so this cell duplicates another cell of the gate x mask square on arm A | T1 | 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | 2^3 cell (gated tokens are exact duplicates without PE) | as above | 343,053 / 1,005,741 (= trace); h=0.010 |
| M078 | Gate off + no PE + masking | P | M038 + M046 + M039 | M075, M076, M077 | 350k dropped: on arm A (E, no PE; [D21]) the no-PE factor is a no-op, so this cell duplicates another cell of the gate x mask square on arm A | T1 | 5M → 350k, 5M | 500 | strictest component rule (paired / paired-if-hash / Welch) | 2^3 cell | as above | 343,053 / 1,005,741 (= trace); h=0.010 |
| M079 | Masking + real-slot standardization | P | M039 + M041 | M039, M041 | — | T1 | 5M → 5M, 350k | 500 | paired | natural pair (absent treated consistently) | entropy/log n_valid | 343,053 / 1,005,741 (= trace) |
| M080 | First-layer stack: features + gain + mask + real-slot std | P | M040 + M024 + M039 + M041 | M067, M079 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | strictest component rule (paired / paired-if-hash / Welch) | no gain beyond the best pair | distinct rows, entropy/log n_valid | 343,053 / 1,009,837 |
| M081 | FF1 cell AB: EDE annealed STE, restarted each LR cycle + Derived features log pT and Delta R | FF1 | M019 + M040 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M040 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,009,837 |
| M082 | FF1 cell AC: EDE annealed STE, restarted each LR cycle + Logit KD from an FP teacher | FF1 | M019 + M035 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M035 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,005,741 (= trace) |
| M083 | FF1 cell AD: EDE annealed STE, restarted each LR cycle + d_model 16 | FF1 | M019 + M042 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M042 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 608,605 |
| M084 | FF1 cell AE: EDE annealed STE, restarted each LR cycle + eta/phi reflection augmentation | FF1 | M019 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M037 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,005,741 (= trace) |
| M085 | FF1 cell BC: Derived features log pT and Delta R + Logit KD from an FP teacher | FF1 | M040 + M035 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M040, M035 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,009,837 |
| M086 | FF1 cell BD: Derived features log pT and Delta R + d_model 16 | FF1 | M040 + M042 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M040, M042 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 610,653 |
| M087 | FF1 cell BE: Derived features log pT and Delta R + eta/phi reflection augmentation | FF1 | M040 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M040, M037 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,009,837 |
| M088 | FF1 cell CD: Logit KD from an FP teacher + d_model 16 | FF1 | M035 + M042 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M035, M042 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 608,605 |
| M089 | FF1 cell CE: Logit KD from an FP teacher + eta/phi reflection augmentation | FF1 | M035 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M035, M037 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,005,741 (= trace) |
| M090 | FF1 cell DE: d_model 16 + eta/phi reflection augmentation | FF1 | M042 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M042, M037 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 608,605 |
| M091 | FF1 cell ABCD: EDE annealed STE, restarted each LR cycle + Derived features log pT and Delta R + Logit KD from an FP teacher + d_model 16 | FF1 | M019 + M040 + M035 + M042 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M040, M035, M042 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 610,653 |
| M092 | FF1 cell ABCE: EDE annealed STE, restarted each LR cycle + Derived features log pT and Delta R + Logit KD from an FP teacher + eta/phi reflection augmentation | FF1 | M019 + M040 + M035 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M040, M035, M037 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 1,009,837 |
| M093 | FF1 cell ABDE: EDE annealed STE, restarted each LR cycle + Derived features log pT and Delta R + d_model 16 + eta/phi reflection augmentation | FF1 | M019 + M040 + M042 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M040, M042, M037 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 610,653 |
| M094 | FF1 cell ACDE: EDE annealed STE, restarted each LR cycle + Logit KD from an FP teacher + d_model 16 + eta/phi reflection augmentation | FF1 | M019 + M035 + M042 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M019, M035, M042, M037 | — | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 608,605 |
| M095 | FF1 cell BCDE: Derived features log pT and Delta R + Logit KD from an FP teacher + d_model 16 + eta/phi reflection augmentation | FF1 | M040 + M035 + M042 + M037 | FF1 linear model (15 new cells + the in-wave arm C replica as the all-low cell; seed blocks), M040, M035, M042, M037 | not a hardware candidate until the derived-feature path is costed: log pT and Delta R are computed in prepare_cache, off-model, so HGQ2 never bills them; the EBOPs match excludes the feature computation, and on chip the squares or tables are uncosted (DSP risk) | T1 | 5M → 5M, 350k | 500 | paired-if-hash (seed blocks); analysed as a blocked 2^(5-1) design | main effects and 2FIs estimated from the 16-cell fraction; additivity (THEORY §5 'expected additive') tested, not assumed | each component's diagnostic | 343,053 / 610,653 |
| M096 | FF2 cell AB on E: Per-value activation widths + Activation init f0 = 7 | FF2 | M011 + M012 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M011, M012 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 619,198 (= trace); h=0.399 |
| M097 | FF2 cell AC on E: Per-value activation widths + tanh LUT before attention and FFN | FF2 | M011 + M016 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M011, M016 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 619,198; h=0.399 |
| M098 | FF2 cell AD on E: Per-value activation widths + Head 32/32/32 | FF2 | M011 + M045 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M011, M045 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 621,478; h=0.397 |
| M099 | FF2 cell BC on E: Activation init f0 = 7 + tanh LUT before attention and FFN | FF2 | M012 + M016 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M012, M016 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 619,198; h=0.399 |
| M100 | FF2 cell BD on E: Activation init f0 = 7 + Head 32/32/32 | FF2 | M012 + M045 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M012, M045 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 621,478; h=0.397 |
| M101 | FF2 cell CD on E: tanh LUT before attention and FFN + Head 32/32/32 | FF2 | M016 + M045 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M016, M045 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 621,478; h=0.397 |
| M102 | FF2 cell ABCD on E: Per-value activation widths + Activation init f0 = 7 + tanh LUT before attention and FFN + Head 32/32/32 | FF2 | M011 + M012 + M016 + M045 | FF2 linear model (7 new cells + the in-wave arm A replica (E) as the all-low cell; seed blocks), M011, M012, M016, M045 | `arch.d_model=24`; `arch.n_heads=2`; `arch.pos_enc="none"` | T1 | 350k → 350k | 500 | paired-if-hash vs arm A (= E, [D21]; seed blocks) | main effects clear of 2FIs; 2FIs aliased in pairs AB=CD, AC=BD, AD=BC | each component's diagnostic | 171,526 / 621,478; h=0.397 |
| M103 | Our optimizer at 5M (arm D recipe at the arm C target) | R | — | M033, M074 | `train.optimizer="adam"`; `train.beta2=0.98`; `train.weight_decay=0.01`; `train.clipvalue=1.0` | T0a | 5M → 5M, 350k | 500 | paired | 2x2 corner; with C, M033 and M074 gives the additivity check of arm D's three fields | divergence count, FF ratio, beta trajectory | 343,053 / 1,005,741 (= trace) |

## 3. Wave 1: zero-GPU measurements, prerequisites and the floor-reduction family

Nothing in wave 1 trains a model. Every item runs on CPU (a cluster CPU Job or the lab pod) or is
a code or literature read. Items computed in the lab pod inform the design only and are never
quoted (house rule). W1 cannot finish before the anchor has a code sha, and Z14 also needs the
anchor's epoch-500 readout.

### 3.1 Measurements

| # | measurement | owner | inputs | output, and what it gates |
| --- | --- | --- | --- | --- |
| Z01 | **Traced static floors** (0-bit and 1-bit-alive) of every Delta architecture under [D19], with HGQ2's own `_compute_ebops` ([A7] method). A07 (arms A07-350 and C), E (arm A) and the pre-[D21] F (A07 without PE) are already traced (CPU, synthetic input, staged at 72a1290, not results; §0); the [D21] F (E + learned PE) is traced by the anchor at PREFLIGHT: the exp input stays SAT, so DR-18 is closed. The old quantizer is traced for A07 (4,580,398) and still needs E for the C′ branch | ml-engineer | every distinct architecture in `delta.json` (`floor_derived` lists the derived values to check) | the traced table replaces §3.2; gates every 350k cell (§3.3) |
| Z02 | **0-bit channel maps** (card Q12): fraction of channels at `relu(i+f) = 0` per site; under the old SAT quantizer such channels are "sign-only", not 0 bits | results-analyst | existing `activation_widths.jsonl` (N=8 350k runs R0-R6 and A00-A11; N=64 screen; N=64 5M confirmations), then the anchor pilot at epoch 500 | whether the budget is met by structured channel loss (THEORY M7); the Q/K/V 0-bit baseline for M007 |
| Z03 | **Closed-form accumulator EBOPs** (card Q13): b_acc = b_act + ⌈log₂ fan_in⌉ per binary layer, reported beside native EBOPs, never in place of it | ml-engineer (patch `accumulator-ebops-metric`) | shapes and traced widths | a second cost column on every screen and confirm row; answers "equal EBOPs is not equal LUT" ([L2]) only as a quantity, not as silicon |
| Z04 | **Distinct sign rows of `input_proj`** (THEORY M1, §6.3): at most 8 patterns (4 up to sign) at fan-in 3 | results-analyst (patch `diag-input-proj-rows`) | every existing binary checkpoint with an `input_proj` | the M1 baseline for M024, M040 and M050 |
| Z05 | **Re-selection under other rules** (card Q06, min-EBOPs; AUC vs accuracy): recompute the selected epoch from per-epoch logs | results-analyst | per-epoch logs of existing EBOPs runs | replaces card Q06 as an entry; shows how far the rule moves the pick (tried-already H4) |
| Z06 | **How HGQ2 0.1.9 counts ternary zeros** (THEORY §6.5) | ml-engineer | code read plus a CPU trace of one ternary layer | whether M047's EBOPs are comparable with binary at equal target |
| Z07 | **[A14] accounting check** (anchor-owned): our `compute_ebops` against HGQ2's counter on a REPRO-CHANG checkpoint | ml-engineer (anchor PREFLIGHT) | – | referenced, not duplicated |
| Z08 | **Diagnostics suite** built and CPU-gated: attention entropy / log(n_valid) with gated keys masked in the diagnostic pass, attention-ablation delta (A·V replaced by the mean over V), sign snapshots (flip-flop and C2I ratio), β trajectory, latent-vs-binary gap | ml-engineer (patches `diag-*`) | existing checkpoints | every entry's "mechanism diagnostic" column depends on it |
| Z09 | **Working-point metric** (P12, THEORY §6.7): rejection at signal efficiency 0.5 and per-class signal efficiency at fixed mistag; check whether `publication/results/pre_conference/working_points.json` exists | results-analyst | ROC-test `.npz` arrays | reported beside accuracy and AUC at every confirm |
| Z10 | **Data caches**: gated 90/10 at N=32; ungated 90/10 at N=64; N=64 with derived features; N=64 with real-slot standardization | ml-engineer (CPU Jobs, `prepare_cache`) | the `kai-data` PVC | M009, M038, M040, M041 and their packages |
| Z11 | **Unit tests for delayed treatments**: the schedule variants at restart boundaries (M030, M031, M032), the EDE period, the recovery freeze (M015), the collapse-stop rule | ml-engineer | – | G0 of the advance rule (§5.3) |
| Z12 | **Static-feasibility table**: Z01 applied to every entry × target (keep, move to 5M, drop), written into each wave STUDY | experiment-designer | Z01 | §3.3 |
| Z13 | **Patch gate**: every Delta patch is opt-in and byte-identical when off: unchanged `digest_json(cfg)` and init `kernel_hashes` on every `const0922-*` config and on the anchor configs (code-surface §7 rule 5) | ml-engineer | – | without it the anchor snapshot is not a valid control |
| Z14 | **Screen resolving power**: the epoch-500 validation accuracy sd of anchor arms C and A (E) (and A07-350), seeds 1-8, feasible, non-degenerate seeds only (anchor readout [D13], Selection rule) | results-analyst | the anchor's epoch-500 readout; `screen_power.py` | **gates K2, before any wave-2 pod**: sd_plan = √2 · sd per target, then the seed count n ∈ {4, 6, 8} or the ranking mode by the §5.1 rule, written into the wave STUDY |
| Z15 | **Teacher leakage check**: confirm that no teacher or warm-start checkpoint was trained on jets in the gated 90/10 validation split | ml-engineer | split code | every stored unconstrained checkpoint is 80/20 and ungated, so none is used (§3.4) |

### 3.2 Derived floors of the Delta architectures (N = 64 unless stated; [D19]; arbiter formula)

"Derived" means shape arithmetic with the §0 formula, which includes the traced exp-input and LUT
terms. The trace is filled in for A07 and E, where the formula equals it. Z01 replaces every other
value. h is the 350k headroom fraction, clipped at 1. The table is rendered from
`delta.json["architecture_floors"]` by `delta_tables.py`. Classes: "near-floor" means h < 0.10;
"every channel alive" means the 1-bit-alive floor is below 350k.

| architecture (entries) | 0-bit floor, derived | 1-bit-alive floor, derived | traced (0-bit / 1-bit-alive) | h at 350k | class at 350k |
| --- | ---: | ---: | --- | ---: | --- |
| A07 (anchor arms A07-350 and C [D21]; every A07 delta at 5M; the floor-family base) | 343,053 | 1,005,741 | 343,053 / 1,005,741 | 0.010 | near-floor |
| E, d24/h2/no PE (anchor arm A [D21], also B, D, R; FF2; the 350k base; F = E + learned PE, traced at the anchor PREFLIGHT) | 171,526 | 619,198 | 171,526 / 619,198 | 0.399 | E-class |
| A07 with FFN 64 (M043) | 343,053 | 1,136,813 | – | 0.009 | near-floor |
| A07 with d_model 16 (M042) | 343,053 | 608,605 | – | 0.026 | near-floor |
| A07, head 32/32/32 (M045) | 343,053 | 1,007,789 | – | 0.010 | near-floor |
| A07, 5 input features (M040) | 343,053 | 1,009,837 | – | 0.010 | near-floor |
| A07, int8 weights (M048) | 343,053 | 3,809,549 | – | 0.002 | near-floor |
| A07, int8 input_proj (M050) | 343,053 | 1,048,749 | – | 0.010 | near-floor |
| A07 with 2 heads (M001) | 171,526 | 834,214 | – | 0.269 | E-class |
| A07 with 1 head (M002) | 85,763 | 748,451 | – | 0.399 | E-class |
| A07, table floor 2 bits (M003) | 114,189 | 776,877 | – | 0.356 | E-class |
| A07, Linformer k = 8 (M004) | 41,997 | 508,077 | – | 0.661 | E-class |
| A07, ReLU/N attention (M005) | 0 | 662,688 | – | 0.528 | E-class |
| A07 at N = 32 (M009) | 85,517 | 351,917 | – | 0.993 | E-class |
| A07 + Q/K floor 1 bit (M007) | 474,125 | 1,005,741 | – | – | `STATIC_INFEASIBLE` |
| A07, L = 2 (M044) | 686,106 | 2,004,154 | – | – | `STATIC_INFEASIBLE` |
| 2 heads + table 2 bits (M051) | 57,094 | 719,782 | – | 0.442 | E-class |
| 1 head + table 2 bits (M052) | 28,547 | 691,235 | – | 0.485 | E-class |
| Linformer + 2 heads (M053) | 20,998 | 487,078 | – | 0.706 | E-class |
| Linformer + table 2 bits (M054) | 13,837 | 479,917 | – | 0.721 | E-class |
| Q/K floor + 2 heads (M055) | 302,598 | 834,214 | – | 0.089 | near-floor |
| Q/K floor + Linformer (M056) | 58,381 | 508,077 | – | 0.648 | E-class |
| N = 32 + 2 heads (M058) | 42,758 | 309,158 | – | 1.000 | every channel alive at 1 bit |
| ReLU/N + Q/K floor (M059) | 131,072 | 662,688 | – | 0.412 | E-class |
| floor stack: Linformer + 2 heads + table 2 bits (M060) | 6,918 | 472,998 | – | 0.736 | E-class |

Substitution checks, each with the exp-input term and the LUT term (13 at H = 4):
- **Linformer k = 8** has H·T·k = 4·64·8 = 2,048 score entries. Its softmax floor is 16·2,048 +
  4·(2,048 − 256) + 2,048 + 13 = 32,768 + 7,168 + 2,048 + 13 = 41,997. Its 1-bit-alive floor adds
  the dense layers and head (400,544), Q·K and A·V over k keys (2 × 64·8·32 = 32,768) and the two
  binary sequence projections (2 × 32·64·8 = 32,768): 41,997 + 400,544 + 32,768 + 32,768 = 508,077.
- **N = 32 A07** has dense layers and head 200,864, Q·K and A·V 2 × 32,768, and a softmax of
  65,536 + 15,872 + 4,096 + 13 = 85,517. That gives 351,917, which is **above** 350,000 by 1,917.
  The earlier claim that M009 is "the only single whose derived 1-bit-alive floor fits under 350k"
  was false once the exp term is counted. M009's h is 0.993: nearly every channel stays alive, but
  not all of them. **No single fits every channel at 1 bit under 350k.** The package M058 (N = 32
  with 2 heads) still fits, at 309,158.
- **Baselines** (weight-bit-aware; EBOPs = b_a · b_w):
  - M048 (int8 weights everywhere) prices the dense layers and the head at 8 × 400,544, so its
    1-bit-alive floor is 343,053 + 3,204,352 + 262,144 = 3,809,549 (h 0.002).
  - M050 (int8 `input_proj` only) adds 7 × 6,144 = 43,008, giving 1,048,749.
  - M047 (ternary) has floor1 n/a until Z06 says how HGQ2 bills a zero.
  - M049 (learned weight widths) has floor1 n/a because it has no fixed b_w.
  - All four have the A07 0-bit floor of 343,053, because at 0-bit activations the weight bits
    cost nothing.
- **Limiting case:** with H = 0, the softmax, exp and LUT terms are all 0.

### 3.3 The floor-reduction family and the conditional rules for every 350k cell

The **floor-reduction family** is M001-M009 and the crosses M051-M060. M010, the 1.4M rung, is
screened with it because it shares the base. The family is a prerequisite: wave 2a screens it
first, because its outcome decides which architectures have a 350k base with live channels. The
rules below are pre-registered. They are applied now from the derived and traced values, and again
from the Z01 trace:

- **R1 (static feasibility).** A 350k cell runs only if its 0-bit floor (traced, else derived)
  is below 350,000. Otherwise the cell is removed. Entries whose purpose is floor reduction
  (`if_floor_fails = drop`: M001-M006, M009 and the F crosses) are then dropped. The others keep
  their 5M cell (`5M-only`). Already applied: M007 (derived 474,125) and M044 (686,106) run at 5M
  only.
- **R2 (the 350k base, Kai-confirmed [D21]).** The role of each 350k cell is in `delta.json`
  `screen_role_350k` and `base["350000"]`.
  - **Near-floor cells** have own-architecture h < 0.10. They are A07 itself, which covers every
    A07 width, controller, input, training or baseline delta (M008, M011-M013, M015, M016, M038,
    M039, M040, M045, M047-M050, M076), plus A07 with FFN 64 (M043), A07 with d16 (M042) and the
    Q/K floor with 2 heads (M055, h 0.089). Their A07 versions are not run: the anchor's
    descriptive arm A07-350 stands for them. The delta is applied to arm A's config (E), and the
    cell is paired with arm A at the same seeds at its epoch-H snapshot. The entry's own pairing
    rule applies (paired for training-level deltas, paired-if-hash for shape changes), and so do
    G0-G3. The on-E derived h is in `floor_derived.on_E` and in the table column "350k on E". It
    is 0.33-0.67 for these cells, 0.229 for M055 (on E it is M007 on E), and 0.081 for M048.
  - **Feasibility probes on E** (role "near-floor on A07 and on E"): M048 on E is still
    near-floor, and M047 and M049 cannot be derived. Those three 350k cells run on arm A as
    feasibility probes only: G2 counts, the EBOPs split and the attention state. G3 is not
    applied, and nothing advances on accuracy. M049's 350k cell is also covered by the anchor's
    arm NB (§2).
  - **Floor-family cells** have an A07-derived architecture with h ≥ 0.10, or only a trace for
    the Deep Sets body. They are M001-M006, M009, M051-M054 and M056-M060. They run on
    their own architecture, built from the A07-350 config, and are read for two things:
    - Feasibility, by G2 against A07-350's feasible count among seeds 1-n at epoch H (k_base).
    - Accuracy against arm A (E), by Welch, labelled "cross-architecture".

    They are never compared with A07-350's accuracy, because A07-350 is a remnant of under 7k
    EBOPs outside the softmax.
  - **The no-PE cells on arm A.** Arm A (E) has no PE, so the no-PE factor is a no-op there.
    M075, M077 and M078 therefore duplicate other cells, and their 350k cells are dropped. At
    350k the gate × PE × mask cube becomes the gate × mask square on arm A: arm A, M038, M039 and
    M076. At 5M the full 2³ remains. Arm F is now E + learned PE [D21]; A against F is the
    anchor's own PE contrast at 350k. It is not a Delta control.
  - **If arm A fails at 350k** (fewer than ⌈3n/4⌉ of seeds 1-n feasible at epoch H, the FF2
    rule):
    - The arm-A cells (accuracy screens and probes) have no 350k control. They keep their 5M
      cell, and the 350k question goes to Kai at K3 with the feasibility counts.
    - The floor-family cells lose their accuracy comparator. They are read for feasibility (G2
      against A07-350's k_base) only, with no G3 and no accuracy reading.
    - M013 is 350k only, so it has no 5M cell to keep. It runs as a feasibility probe on A07-350
      against A07-350's k_base, as under fallback C below.
    - FF2 re-bases to arm C at 5M (§2.2).
  - **If Kai names fallback C** (the anchor study's rule when arm A has no feasible checkpoint at
    the pilot or in production; no 350k base at all), every 350k accuracy cell and every probe
    is dropped, and its 5M cell remains. The floor-family 350k cells still run, as feasibility
    probes against k_base = the number of A07-350 seeds 1-n feasible at epoch H. If A07-350 has
    no production seeds, k_base = 0, set by the pilot that failed. G2's rescue then reads k_e ≥ 3
    and k_e − k_base ≥ 2. M013 is 350k only, and its purpose is reaching the budget from a hard
    start. It runs as a feasibility probe on A07-350 against the same k_base. It is not dropped
    silently. M014 has no screen cell (§5.3 G0).
  - **Keeping A07 as the accuracy base is closed.** Kai confirmed [D21] on 2026-09-27, so the
    earlier override branch (A07 350k cells as accuracy screens, re-paired to E when A fell
    short) no longer exists.
- **R3 (exp input SAT): holds.** The trace shows that the exp input stays SAT: +H·T·S per block,
  plus the LUT term. It is folded into every derived floor in this file and in `delta.json`, and
  R1 and R2 are applied to those values.
- **R4 ([D19] reversal branch).** Kai confirmed [D19] on 2026-09-27, so R4 is a contingency
  only. If the anchor ever reverts to the old quantizer (C′), every 350k cell is
  `STATIC_INFEASIBLE`. The old floors are A07 4,580,398 (traced; derived 4,559,008) and E
  2,690,744 (derived), and the arbiter notes that a Linformer projection does not remove the SAT
  dense floor. All screens then run at 5M against C′, which has a traced 419,602 EBOPs of headroom
  (5,000,000 − 4,580,398). C′ exists only as pilot seed 1 (anchor STUDY), so there are no C′
  seeds 1-n snapshots. The **primary control is therefore the in-wave C′ replica**: seeds 1-n,
  at the Delta sha, run to 2,000 epochs, with [A6] snapshots every 500 epochs. It takes the place
  of the C replica in §5.2, and the A and A07-350 replicas are not run. Which entries survive,
  counted from `delta.json`:
  - **Survive at 5M on C′:** the 40 singles and baselines with a 5M cell whose `if_floor_fails`
    is "5M-only" (M007, M008, M011, M012, M015-M050); every package and factorial cell that is
    not a floor cross, at its 5M cell (M061-M095 and M103); and FF2, re-based to C′ at 5M with
    the C′ replica as its all-low cell.
  - **Dropped:** the floor-reduction singles M001-M006 and M009 (`if_floor_fails` "drop") and the
    floor crosses M051-M060 (their purpose is 350k feasibility, and no 350k cell exists); M010
    (the old A07 floor, 4,580,398, is above 1.4M); M013 (350k only, `if_floor_fails` says so);
    M014 (confirm-only at 350k).
  - The parked fixed-4-bit softmax-output entry (the E1 retry) is reinstated.
- **M010 (1.4M) has no same-target control.** G3 does not apply to it. It is a ladder point only
  (G2 counts and the ladder plot), whichever branch holds.
- **Reporting.** Every 350k result states its architecture's traced floor, h and the attention
  state (Q/K and V 0-bit fractions, entropy / log(n_valid)). A near-floor feasible checkpoint is
  labelled "pruned by construction".

### 3.4 GPU prerequisites (not methods; run in wave 2 before the entries that need them)

- **P-T1 FP teacher.** A07-N64 with `quant.weight none` (patch `weight-scheme-baselines`), the
  anchor's [D19] activation and softmax quantizers at their init widths (so the warm-start latents
  and KD logits come from the same activation grids as the students), the gated 90/10 train split, the Chang recipe, no EBOPs pressure (PID target 1e12 with β bounds at
  their minimum, because the S runner hard-codes `BetaPID`), 2,000 epochs, seed 101 (outside
  1-8), selected on validation accuracy. It is the teacher for M027, M035 and M036 and their
  packages. No stored checkpoint qualifies: every one is 80/20 and ungated, and the 90/10
  validation jets were drawn from the same 620,000-jet pool, so a stored teacher has likely
  trained on the student's validation set.
- **P-T2 int8 teacher.** The same with `quant.weight int8_absmax` (M063).
- **Timing canary per new architecture.** 10 epochs in the first pod of the wave that
  introduces it (Linformer, ReLU/N, Deep Sets, N = 32, L = 2, d16, FFN 64, head 32/32/32, tanh
  LUT, KD, which adds a teacher forward pass every step). s_e,arch comes from these; A07 and E
  come from the anchor canary.

## 4. Two EBOPs targets

THEORY §5.4: an attention lever read at one target is uninterpretable, because at 5M attention
is affordable and at 350k it is priced out. Per class:
- **Both 350k and 5M:** every F entry (floor and attention cost), every Q entry that acts on the
  widths (M011, M012, M015, M016), the architecture entries (M042, M043, M045), the input entries
  that touch the token population or the first layer (M038-M040), all four baselines, and every
  package built only from two-target singles. Their 350k cells are A07 near-floor. They run on
  arm A (E, Kai-confirmed [D21]; M047-M049 as feasibility probes, §3.3 R2). The floor family
  runs on its own A07-derived architectures.
- **350k only:** M013 (PID gains) and M014 (open-loop β). Their purpose is reaching the budget
  from a hard start. At 5M the anchor PID already reaches its target (tried-already C10), so a 5M
  cell would measure nothing. M013 runs on arm A (E; §3.3 R2). M014 has no screen cell,
  because its schedule runs for 7,000 epochs. It is confirm-only at 350k and is offered at K3
  (§5.3 G0). FF2 runs at 350k only, because its base (arm A, E) exists only there.
- **5M only (screen), both at confirm:** the training-only levers (B, R, KD, augmentation,
  real-slot standardization, and the no-PE single M046; at 350k the PE contrast is anchor A against
  F). THEORY §3
  classes them EBOPs-invisible, so their mechanism acts on training dynamics, which needs live
  channels. A07 at 350k has traced h = 0.010 and cannot host them. Arm A (E at 350k, traced h
  0.399) could, and that is the §11 alternative. A survivor is confirmed at both 5M and the 350k
  base, arm A (E). This choice is a flagged decision (§11).
- **5M only, structural:** M007 and M044 (`STATIC_INFEASIBLE` at 350k, §3.2).
- **1.4M:** M010, the new rung on the A07 ladder between A07-350 (350k) and C (5M). It is a
  ladder point only: it has no same-target control, so G3 does not apply (§3.3). 250k exists
  only as anchor arm B (E at 250k, [D21]).


## 5. Budget tiers, pre-registered rules and compute

### 5.1 The two tiers

| | screen | confirm |
| --- | --- | --- |
| schedule | the Chang recipe for H epochs. H = 500 (one cosine cycle, LR at its 1e-6 floor at the end) unless the treatment starts later: M015 H = 1,000 (freeze at 500); M031 H = 1,500 (the first decayed peak is at epoch 501); M032 and its packages H = 2,000 (the proxy is one cosine over 2,000 epochs) | the full recipe, 7,000 epochs (M032: one cosine over 7,000) |
| seeds | n per cell (seeds 1-n), n ∈ {4, 6, 8}, set at K2 by the Z14 rule below; 4 is the lower bound | 8 (seeds 1-8) per cell |
| readout | validation only (n = 62,000): top-1 accuracy (primary, as the anchor), macro AUC, feasible count, divergence count, EBOPs and accumulator EBOPs, and the entry's mechanism diagnostic, all at the best-feasible-as-of-H snapshot. **Never quotable**, never enters the record | the anchor protocol [D11]: selection on validation accuracy among feasible checkpoints, tie-break val AUC → −EBOPs → −epoch, AUC-selected sensitivity copy, interim readouts at 500 / 1,000 / 2,000 / 4,000 / 7,000 (validation only), ROC-test (n = 260,000) **once**, after the terminal epoch |
| control | the anchor arm's own [A6] snapshot at epoch H, seeds 1-n: arm A (E, [D21]) for the 350k accuracy cells, the probes and FF2; A07-350 for the floor-family feasibility counts (k_base); arm C (5M). The in-wave replica takes over on the §5.2 trigger, and always under R4 (C′). The 1.4M rung pairs to A07-350's seeds at a different target and is a ladder point only (no G3) | the anchor arm at the same target, seeds 1-8, terminal epoch |
| multiplicity | Benjamini-Hochberg, q = 0.10, within each wave × target (m = the (entry, target) cells with a G3 test, counted by `screen_power.py`); in ranking mode, none (no significance claim) | Holm, α = 0.05, across every cell of one confirm wave |
| validity | a checkpoint counts only if it is feasible and non-degenerate by the anchor's rule (below) | the same |
| reported beside | – | per-class AUC, rejection at signal efficiency 0.5, per-class signal efficiency at fixed mistag (Z09), attention state, EBOPs and accumulator EBOPs, validation − ROC-test gap |

**Validity: the anchor's non-degeneracy rule applies to every Delta checkpoint.** The anchor
STUDY's Selection rule (`campaigns/2026-09-26-training-batch/STUDY.md` l. 386-404, "Non-degeneracy",
commit 5d6c3c9) counts a checkpoint as **feasible** only if (a) its traced EBOPs ([D20] sample) is ≤
the target, (b) EBOPs minus the arm's traced 0-bit floor is > 0, and (c) its validation top-1
accuracy is > p_maj + 5 · √(p_maj (1 − p_maj) / 62,000), with p_maj the majority-class fraction
of the gated `y_val`, computed at the anchor's PREFLIGHT. A checkpoint that meets (a) and fails
(b) or (c) is "feasible, degenerate": counted separately and never carrying an accuracy. The
Delta inherits the rule at both tiers:
- "Feasible" in this file means (a)-(c). The best-feasible-as-of-H snapshot is the anchor's
  selection (highest validation accuracy among (a) checkpoints) followed by the (b)-(c) test on
  it; G2's k_e, k_base, the ⌈3n/4⌉ base rules, Z14's sd and every g_s use feasible,
  non-degenerate seeds only, and the degenerate count is reported beside k_e.
- (b) uses the cell's own architecture's **traced** 0-bit floor. A07 (343,053) and E (171,526)
  are traced; every other Delta architecture needs its Z01 trace before its cells can be read,
  so Z01 gates those cells at both targets, not only at 350k. p_maj is the anchor's value: every
  Delta cell uses the same gated 90/10 validation jets (M009, M038 and M040 change the
  constituents or features, not the jets).
- G1's collapse level (validation accuracy ≤ 0.25 for 10 consecutive epochs after epoch 20) and
  (c) are separate tests: (c) decides whether a checkpoint counts, G1 decides whether a run is
  unstable. If the PREFLIGHT p_maj puts the (c) threshold above 0.25, G1's collapse level is
  raised to that threshold, so a run whose every checkpoint is degenerate is also "collapsed".

**Seeds per screen cell: a rule decided at K2, before any wave-2 pod (Z14; critical reviews v1
A2, v2 B1).** The advance rule (§5.3 G3) has to resolve its own MDE target g₀ = 0.3 pt under the
multiplicity that is actually used, and the power has to be the power of the whole rule, gates
(i) and (ii) together. For a one-sided paired t test with n pairs at level α, gate (i) alone has
80 % power at a true gap of k_t(n, α) · sd_d. Gate (ii) is mean g ≥ g₀/2 (fixer v2; it was mean
g ≥ g₀, which caps the joint power at a true gap of g₀ at 0.5: `screen_power.py` gives 0.43-0.49
for the four families). k_joint(n, α) is the gap, in sd_d units, at which (i) and (ii) together
have 80 % power, with g₀ = k_joint · sd_d. The planning α is α_eff = q/m, the threshold of the first
BH discovery. That is conservative, because the j-th discovery uses j·q/m. k_t comes from the
noncentral t and k_joint from a seeded Monte Carlo (200,000 reps), both in `screen_power.py`.
The family sizes m are counted per (entry, target) cell from `delta.json`: the cells in the wave
× target whose role gets a G3 test. The four baselines take none (they are comparands, reported
without an advance decision, §5.3), and neither do the feasibility probes or M010.

| family | m | α_eff | k_joint(4) | k_joint(6) | k_joint(8) | sd_d ceiling for 0.3 pt at n = 4 / 6 / 8 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| unadjusted (reference) | – | 0.05 | 1.68 | 1.20 | 0.99 | 0.18 / 0.25 / 0.30 pt |
| W2 at 5M (singles) | 43 | 0.0023 | 4.83 | 2.50 | 1.83 | 0.062 / 0.120 / 0.164 pt |
| W2 at 350k (singles) | 19 | 0.0053 | 3.66 | 2.09 | 1.58 | 0.082 / 0.144 / 0.190 pt |
| W3 at 5M (packages) | 31 | 0.0032 | 4.33 | 2.33 | 1.73 | 0.069 / 0.129 / 0.174 pt |
| W3 at 350k (packages) | 11 | 0.0091 | 3.04 | 1.84 | 1.43 | 0.099 / 0.163 / 0.210 pt |

k_joint exceeds k_t by at most 0.03 (1.68 against 1.65 unadjusted at n = 4), because a t test
that rejects at α_eff almost always has a mean above g₀/2. The factorials have their own figures
(per-run σ, BH within the block's effects, the same (ii) floor), by n: FF1 (16n runs, df 15n − 15,
m 15) k_joint = 0.86 / 0.69 / 0.59 at n = 4 / 6 / 8, so 0.3 pt is resolvable if σ ≤ 0.35 / 0.43 /
0.51 pt; FF2 (8n runs, df 7n − 7, m 7) k_joint = 1.14 / 0.91 / 0.78, σ ≤ 0.26 / 0.33 / 0.39 pt.

**The rule, pre-registered:**
1. **sd_plan per target** is √2 · sd of the epoch-500 validation accuracy (Z14): arm C for the
   5M family, arm A (E) for the 350k family, over seeds 1-8, feasible, non-degenerate seeds only.
   √2 is the bound for ρ = 0, which is conservative for cross-sha pairs (same-seed pairs are never
   bit-identical, §1). Once the drift replicas are read (§5.2), sd_plan becomes max(sd_plan,
   sd_null). A measured paired sd can tighten the rule, never loosen it.
2. **n** is the smallest value in {4, 6, 8} with k_joint(n, α_eff) · sd_plan ≤ g₀ = 0.3 pt, applied
   per wave × target family. The wave STUDY extends `seeds_screen` from 1-4 to 1-n. **n_W3 ≤ n_W2
   at the same target** (review v2 B5): the packages and the FF1 one-high augmentation need their
   singles on the same seeds, so a W3 family whose rule asks for more seeds than W2 ran at that
   target runs at n_W2, in ranking mode if n_W2 does not qualify for it. No single is extended.
3. **If no n ≤ 8 qualifies, the default is ranking mode at n = 4.** The screen is then a declared
   ranking: cells are listed by the lower 80 % bound of g, and there are no advance claims. G0,
   G1 and G2 still apply, and every g is reported with its interval. At K2, Kai may instead buy
   n = 8 with the MDE target raised to g_res = k_joint(8, α_eff) · sd_plan and gate (ii) at
   g_res/2, declared before launch, or cut m (for example, BH within a code tier or a family
   letter).
4. **What to expect.** For n = 8 to qualify at W2 5M, the anchor's epoch-500 sd has to be at most
   0.164 / √2 = 0.116 pt. The anchor sends an epoch-500 sd above 0.6 pt to Kai. At 0.6 pt,
   sd_plan = 0.85 and g_res(8) = 1.55 pt. At the archived N=64 W1A8 sd of 3.14 pt (R14, 3 seeds,
   held-out, sizing only), g_res(8) = 8.12 pt. **Ranking mode is therefore the likely outcome.**
   It is still pre-registered, so the selection it produces is a declared one.
5. The confirm tier uses the same arithmetic. The confirm wave STUDY states g_res,confirm =
   k_t(8, 0.05/n_c) · sd_plan,7000 (the confirm has no gate (ii)), and a confirm gap inside
   ±g_res,confirm is "unresolved", not "flat" (§10). The cheap version (3 seeds; k_joint(3) is 2.32 unadjusted) always runs in
   ranking mode.

### 5.2 Pre-screen controls

- **Drift replica.** Every screen wave re-runs its base arms at the Delta code sha on Delta pods
  (seeds 1-n), each to the longest horizon that pairs with it. The [A6] snapshots every 500
  epochs give every shorter horizon from the same run, so the long-horizon entries have a
  replica control too.
  The plan is machine-readable in `delta.json` `drift_replicas`, which the generator reads
  (arm names after [D21]):
  - Wave 2: A (E) at 350k to 1,000 epochs (the 350k accuracy cells, and M015 on A), A07-350 at
    350k to 500 (the floor-family k_base and drift), and C at 5M to 2,000 (M031, M032).
  - Wave 3: A and A07-350 to 500, C to 2,000 (M068, M069, M071-M073).

  The horizons are those of fixer v1 (A07 replica to 500, E to 1,000 in wave 2), so the budget is
  unchanged. Under R4 the C replica is the C′ replica, and it is the primary control; the A and
  A07-350 replicas are not run (§3.3). g_rep =
  replica − anchor snapshot, per seed. If the 95 % interval of g_rep excludes 0, or |mean| > 0.3
  pt, the wave's primary pairing switches to the replica at every horizon (declared here, before
  any result), and both are reported. This separates "code sha, GPU class or wave date" from
  "method".
- **Replicas first.** The replicas take the first pods of wave 2. sd_null, the paired sd of
  g_rep, is read at their epoch-500 snapshot **before any other wave-2 entry starts**. It feeds
  the §5.1 rule as max(sd_plan, sd_null). If the n chosen at K2 no longer qualifies, the wave
  switches to ranking mode (or to g_res at n = 8, if Kai bought that) before its entries launch.
  The replicas then continue to their longer horizons in parallel with the entries.
- **Base stability.** A base with more than a quarter of its seeds 1-n diverged, collapsed or
  H1-type degraded by epoch H (G1 definitions, §5.3; with n = 4 that means 2 or more) is not a
  valid control. The wave pauses and goes to Kai. The LR 3e-3 risk (§6) makes this likely enough
  to plan for. The default proposals:
  - At 350k: anchor arm D, which after [D21] is E with our optimizer on the same schedule, so no
    new base run is needed.
  - At 5M, where the training-only levers screen and arm D does not exist: M103 (arm D's
    optimizer at the arm C target) moves from wave 3 into wave 2 and becomes the base, provided
    its own seeds 1-n are stable.

### 5.3 Screen advance rule (per entry × target; applied in this order)

For seeds s usable in both the entry and the base (feasible and not diverged), g_s =
acc_val(entry, s) − acc_val(base, s), both at the best-feasible-as-of-H snapshot.
- **G0, the treatment was measured.** Every entry declares its treatment onset (epoch 1 for
  most; 501 for M031; for M015 the logged freeze epoch, which is the first feasible epoch ≥ 500
  and may never come on a near-floor base). A selected checkpoint before onset means "treatment not
  measured". If that holds in more than a quarter of the seeds (2 or more of 4), the entry is
  reported as not measured. It is then neither a null nor advanced (the B5 lesson). An entry whose
  treatment no screen horizon can reach has no screen cell. **M014** is the case: its open-loop
  schedule runs to 7,000 epochs, and at H = 500 only the first linear β segment runs, from 2e-8
  to about 9e-8, of a schedule that ends at 3e-6. Even H = 2,000 ends at 3e-7. M014 is therefore
  confirm-only, offered at K3 as a Chang-fidelity element.
- **G1, stability.** Divergence: a non-finite loss (the runner raises). Collapse: validation
  accuracy ≤ 0.25 for 10 consecutive epochs after epoch 20. The run is then stopped by patch
  `screen-collapse-stop` and recorded (precedents: STE collapse at epoch 2-3 at LR ≥ 2e-4,
  tried-already H1; B02 seed 6 at 20.08 % and 0.5000 AUC, D7). Diverged and collapsed runs are
  never relaunched and never dropped.

  **H1-type degradation** is the "peaks at epoch 2-3 and then degrades" signature of
  tried-already H1. It is computed from the per-epoch logs, and the run is not stopped. A run
  has it when all three conditions hold:
  1. Its best validation accuracy is at an epoch ≤ 20.
  2. Validation accuracy then stays ≥ 5 pt below that best for 10 consecutive epochs within the
     first 100 epochs.
  3. Its logged EBOPs over those 10 epochs are still ≥ 50 % of its epoch-1 EBOPs.

  Condition 3 separates H1 from the budget squeeze of lesson 2. F1, C3 and C4 lost accuracy
  *because* the PID removed cost, so their EBOPs fell together with their accuracy. H1 had no
  EBOPs term and lost accuracy at unchanged cost. An F1-shaped run therefore does not trigger the
  test. It is recorded descriptively as "early peak, then squeeze" with its first feasible epoch.
  The test is conservative: at 350k a PID that halves the cost within the degradation window
  masks an H1 collapse. The LR-sensitive levers screen at 5M. There the target is 0.38 × the
  traced init, against 0.027 × at 350k, so the PID has less cost to remove. How fast it removes
  that cost is not known.

  More than a quarter of the seeds (2 or more of 4) diverged, collapsed or H1-type degraded →
  "unstable", reported, not advanced. The same count decides base stability (§5.2).
- **G2, feasibility (count rule, no p-value).** k_e = feasible, non-degenerate (§5.1, the
  anchor's (a)-(c)), non-diverged seeds at the target; the feasible-degenerate count is reported
  beside it. An accuracy reading needs k_e ≥ 3. **Feasibility rescue:** a floor-family entry
  advances on feasibility alone if k_e ≥ 3 and k_e − k_base ≥ 2. The exact McNemar p is
  reported as a description.
- **G3, accuracy.** With n_p ≥ 3 paired seeds, report:
  - the mean g and its 95 % t-interval (df n_p − 1);
  - the lower 80 % bound;
  - the per-pair correlation;
  - the one-sided paired-t p-value (Welch for unpaired entries);
  - the sign count, with its exact one-sided sign-test p. The sign count is descriptive only.

  How a cell is read depends on the mode declared at K2 (§5.1):
  - **Significance mode** (an n in {4, 6, 8} qualified, or Kai bought n = 8 with g_res).
    **Advance** if (i) the Benjamini-Hochberg-adjusted p ≤ 0.10 within the wave × target
    family, and (ii) mean g ≥ g₀/2. Here g₀ = 0.3 pt is the MDE target that n is sized for (§5.1),
    or the declared g_res. Until fixer v2, (ii) read mean g ≥ g₀, which gave at most 50 % power
    at a true gap of g₀ (review v2 B1). The earlier (iii), "g_s >
    0 in at least 3 of 4", is dropped as a gate. Alone it is a sign test with P(≥ 3 of 4 | H0) =
    5/16, and under (i) it is implied almost always.
  - **Ranking mode** (the default when no n qualifies). No cell advances on significance. Cells
    are ranked by the lower 80 % bound of g, and the list is labelled "ranked, not advanced".
  - **Baselines** (M047-M050) are comparands. They get G0-G2 and the G3 report, but no advance
    decision, and they are not in any BH family (§5.1).

  The 0.3 pt MDE target is a design choice. It is about twice the 0.16 pt binomial SE of one
  checkpoint's validation accuracy at n_val = 62,000 (anchor STUDY, "Winner's curse"), which is
  an upper bound on the SE of a paired difference on the same jets, and gate (ii) at 0.15 pt is
  about one such SE. They size the target against measurement noise, not against seed variance,
  and §5.1 handles the seed variance. The target is below the anchor's ±0.5 pt confirm target.
- **Zero advances.** In significance mode, a wave in which no cell advances reports "no entry
  resolved at g₀ in this family". That is the wave's result. The ranked list by lower 80 % bound
  still goes to Kai at K3/K3a, labelled "ranked, not advanced", with the winner's-curse note.
  Kai may send cells from it to confirm as exploratory candidates, and the 8-seed, 7,000-epoch
  confirm with Holm is then the only test. Wave 3 still runs as pre-registered, because the
  package ladders need their singles whatever the singles showed. Kai may cut wave 3 at K3a.
- **G3′, non-inferiority** (cost levers M023 and M024/M025 when read for cost, and floor
  entries at 5M): the lower 95 % bound > −0.3 pt. A non-inferior M023 advances to a
  synthesis check on `mulder` (outside Delta, Kai decision K5), not to accuracy confirm.
- **Packages** must also beat their best component on the same seeds: mean g(package − best
  component) > 0, with at least ⌈3n/4⌉ of n seeds positive. In ranking mode the same comparison is
  reported, not gated. The interaction I is reported with its interval and flagged "synergy" or
  "redundancy", with no gate.
- **Factorial blocks.** Effects (high − low means) come from the OLS models in §2.2, with BH
  within the block's effects, and advance under the same (i)-(ii) thresholds. §5.1 gives their
  own σ ceilings by n (FF1 0.35 pt, FF2 0.26 pt at 4 seeds). If the σ ceiling is not met, the block
  is read in ranking mode as well. A 2FI that clears BH
  flags its pair as non-additive, and THEORY §5's "expected additive" claim is revised for it.
- **Mechanism.** An advanced entry whose pre-registered diagnostic moved against its prediction
  is advanced but flagged "mechanism not confirmed" in the report to Kai.
- **Cap.** At most 12 confirm cells per confirm wave, ranked by the lower 80 % bound of g. Kai
  picks from the ranked list (K3). In ranking mode this ranked list is the selection mechanism,
  pre-registered here. Nothing advances automatically into GPU time.

### 5.4 Compute, in the anchor STUDY's symbols

Symbols as in the anchor Budget: **s_e** = seconds per epoch per process at K processes per pod
(canary: median of epochs 2-10); **T_run** = 7,000 · s_e; pod-hours = run-epochs · s_e /
(3,600 · K); P = pods. Per architecture, s_e,arch comes from its own 10-epoch canary (§3.4), so
the formulas below use one s_e only as a labelled example. Run-epochs are exact counts from
`delta.json`.

**Screen tier (full).** The seed count n is set at K2 (§5.1). The totals below give the 4-seed
lower bound and the 8-seed upper bound. The ranking-mode default runs at n = 4.
- Run-epochs RE_screen(n) = n · [Σ_entries Σ_targets H_e + Σ_replicas H_rep] + teachers. The
  replicas are listed per wave in §5.2. The teachers do not scale with n. Every wave total is
  proportional to n.
  - Wave 2 (singles), at n = 4: 284 entry runs + 12 replica runs = 296 runs, 170,000 run-epochs.
    By horizon: 272 runs at H = 500, 12 at 1,000, 4 at 1,500 and 8 at 2,000 (replicas included).
    M014 has no screen cell.
  - Wave 3 (packages and factorial cells), at n = 4: 256 entry runs + 12 replica runs = 268 runs,
    170,000 run-epochs. By horizon: 244 runs at H = 500 and 24 at H = 2,000. Dropping the 350k
    cells of M075, M077 and M078 on E saves 6,000. The longer C replica adds 6,000.
  - Teachers P-T1 and P-T2: 2 runs × 2,000 = 4,000 run-epochs.
  - **Total at n = 4: 344,000 run-epochs**, the lower bound. At n = 6 the total is 514,000, and
    at n = 8 it is **684,000**, the upper bound.
- Pod-hours_screen = RE_screen(n) · s_e / (3,600 · K).
- Wall clock ≈ Σ_waves Σ_H ⌈runs_H / (P·K)⌉ · H · s_e + 2,000 · s_e (teachers first). This packs
  each horizon serially, so it is an upper estimate. In units of s_e at K = 6:

  | n | P = 2 | P = 10 |
  | ---: | ---: | ---: |
  | 4 | 32,500 · s_e | 13,500 · s_e |
  | 6 | 46,000 · s_e | 15,500 · s_e |
  | 8 | 61,000 · s_e | 18,000 · s_e |

**Confirm tier (plausible).** n_c confirm cells (entry × target):
- Pod-hours_confirm = n_c · 8 · 7,000 · s_e / (3,600 · K).
- Wall = ⌈8 n_c / (P·K)⌉ · T_run.
- A plausible wave: n_c = 12 (9 survivor cells plus the baselines M048 at both targets and M049
  at 5M; M049 at 350k is the anchor study's arm NB, §2) gives 96 runs and 672,000 run-epochs, in 2 waves at P = 10 or 8 waves at P = 2.

**Numeric example, labelled projection.** The only A07-N64 timing on record is 100.09 s for one
epoch of `const0922-a07-n64-s1-fast50-fp32` at batch 256, scaled to 558,000 train jets as
**112.6 s** (anchor STUDY Budget, from `campaigns/2026-09-22-constituent-screen/live-status.json`;
unverified ops number; the number of co-packed processes is unknown; batch 2,790 is
unmeasured). The anchor's 30 s and 60 s are illustrative, not recorded, and are not used here.
At s_e = 112.6 s and K = 6:

| quantity | value (projection) |
| --- | --- |
| one H = 500 screen run | 500 × 112.6 s = 15.6 h |
| T_run (confirm) | 7,000 × 112.6 s = 9.1 d |
| screen pod-hours at n = 4: wave 2 / wave 3 / teachers / total | 886.2 / 886.2 / 20.9 / **1,793.3** |
| screen pod-hours at n = 6 / n = 8 (total) | 2,679.5 / **3,565.7** |
| screen wall clock at n = 4, P = 2 / P = 10 | 42.4 d / 17.6 d |
| screen wall clock at n = 6 and n = 8, P = 2 / P = 10 | 59.9 d / 20.2 d and 79.5 d / 23.5 d |
| confirm (n_c = 12) pod-hours | 3,503.1 |
| confirm wall clock, P = 2 / P = 10 | 73.0 d (8 waves) / 18.2 d (2 waves) |

**Cheap version** (offered beside the full one). It covers only the T0, T0a and T1 singles with a
screen cell, excluding the baselines, the three teacher-dependent entries M027, M035 and M036,
and M014 (38 entries). It runs 3 seeds and one target per entry: 5M for the training-only
levers, and 350k on arm A (E), for the rest. It keeps the longer horizons and runs one
500-epoch drift replica per target. Its long-horizon entries are controlled by the anchor's own
snapshots, as declared here, because it has no long replica. It has no packages and no teachers.
It costs **69,000 run-epochs**, 359.7 pod-hours at the example. It answers which single levers
move the anchor and which make 350k feasible. It loses the packages, the factorial additivity
tests, the T2 architectures (Linformer, ReLU/N, Deep Sets, Bop, HGQ weights) and the 5M cells of
the attention levers. At 3 seeds, k_joint(3) is 10.73 at the W2 5M α_eff and 2.32 unadjusted
(`screen_power.py`), so it always runs in ranking mode.

**What Delta does not spend.** No C-synthesis on `mulder`. The power-of-two levers (M023,
M024, M025), any 0-DSP claim, the tanh-LUT and mask export paths, and the LUT cost of the
accumulator (Z03) need synthesis. That is a separate campaign (K5). No training or synthesis on
the laptop.

## 6. Lessons that bind the design

From `inventory/tried-already.md` ("Lessons for new arms") and the anchor review:

1. **350k reachability binds before accuracy.** Only N=8 has ever produced a feasible
   checkpoint at 350k (tried-already B4, C5-C8, D1). Every N ≥ 16 arm failed. The arbiter shows
   the N=64 screen plateau (4,630,276, W&B, seed 1, not a result) sits 1.6 % above the old
   quantizer's static floor, so it was a floor, not a truncated descent. Binding consequence:
   the Z01 trace gates every 350k cell (R1-R4), and the floor family is screened first.
2. **A PID squeeze after an early unconstrained peak does not recover** (F1; D2; C3 at 25 %; C7
   gradual schedules at N=8, 16 and 64). Consequences: the moving-target entry (card Q05, C7) is
   parked; selection is only ever among feasible checkpoints; every run logs its first feasible
   epoch; the screen reads the best-feasible-as-of-H snapshot, never the unconstrained best.
3. **Binary QAT is LR-fragile.** LR ≥ 2e-4 collapsed at epoch 2-3 with our STE (H1), so the
   Chang peak of 3e-3 is the largest single risk to the anchor and to every entry paired to it.
   Consequences: the divergence and collapse rules (G1) in every screen; the base-stability
   pause (§5.2); an LR ladder (M028, M029), a warm-up (M030), clipped STEs (M018, M019), the arm
   D decomposition (M033, M074, M103) and latent clipping (M021), all screened early. Delta
   waits for the anchor's epoch-500 pilot, which reads A and D at 3e-3 before any Delta GPU time.
4. **Check that each number measures its treatment.** R5's selected checkpoint predates its
   freeze (B5), R6 was read at an interim snapshot (H5), E01-E03 fail reload (F2), val AUC and
   val accuracy pick different models (H4), and the N=64 5M target was set post hoc (C10).
   Consequences: G0 and horizons that cover the onset; one selection rule, fixed as the
   anchor's; reload within 1e-7 as in the anchor; targets fixed now (350k, 1.4M, 5M; 250k only
   through anchor arm B).
5. **EBOPs is not silicon.** β-restore affines are uncounted (C1, J5), softmax has a fixed cost
   (E3), distributed arithmetic is negative on ±1 (J1), SubLN on fabric costs 4.3× LUT (J3),
   scoped binding re-infers DSPs (J4), memory cost logs 0 (F4). Consequences: accumulator EBOPs
   beside native (Z03); no LUT, DSP or latency statement from any Delta number; every entry
   carries its hardware-risk labels per row in `delta.json` `hw_labels`, computed from its
   config delta (packages and factorial cells inherit their components' labels), so a wave STUDY
   that copies its arms inherits them:
   - **"DSP audit required"**: the per-channel power-of-two gain, M024, M025 and the packages
     M065, M066, M067, M080. No Delta entry adds a new act×act multiply (those cards are parked
     or rejected, §9).
   - **"no export path yet (DR-17)", refused by the patch series' export guard**: the
     uncentered binarizer (M017), the β modes (M022, M023), the channel gain (above), the head
     dims (M045), the tanh LUT (M016), the non-binary weight schemes (M047-M050), and the
     packages and factorial cells that contain them, including the FF2 cells M097-M102.
   - **"no export path yet (DR-17)", training path outside the export guard**: the Deep Sets body
     (M006; its training path is wired by patch 0023, HLS export not written), Linformer and
     ReLU/N attention (M004, M005, M053, M054, M056, M059, M060; Linformer is refused by patch
     0022 until [A20], ReLU/N is blocked) and the runtime key mask (M039, M076-M080; blocked on
     [A3]/[A4]). Bop (M020, M071) is wired by patch 0024 and is a training-only knob, so it
     carries no hardware label; its flip rule is a Kai decision at K2 (M020 note).
   - **"not a hardware candidate until the derived-feature path is costed"**: M040 with its
     packages (M067, M080 and the FF1 factor-B cells M081, M085-M087, M091-M093, M095); the
     derived features are computed off-model and not billed.

   All of these stay "not a hardware candidate" until the path exists (J10).
6. **Single-seed gaps have gone flat at more seeds** (D11; D12 at 6 seeds). Every current-era
   EBOPs-constrained comparison with a feasible checkpoint is single-seed. Consequences: 4-seed
   screens, 8-seed confirms, a paired-gap sd from the replica before thresholds are trusted.
7. **Record correction carried into the design.** The 0.0019 accuracy sd the anchor once quoted
   as a 1,000-epoch figure is from the archived 101-epoch, early-stopping recipe
   (`ptw-n8-20260925-base-w1a8.json:35,46`). It is not used to size anything here.

## 7. Wave plan and decision points

| wave | content | starts when | ends with |
| --- | --- | --- | --- |
| **0** | the anchor (training-batch campaign): canary, epoch-500 pilot, production; [A6] snapshots at 500 / 1,000 / 1,500 / 2,000 for arms A (E), A07-350 and C, seeds 1-8 (the screen uses seeds 1-n); its second wave adds arms H and NB | the anchor's own gates | K1 |
| **1** | Z01-Z15 (zero GPU); Delta patch series written and CPU-gated on the tarball, then rebased on the anchor sha (ml-engineer, `code/`); per-wave STUDY for wave 2 via `/new-experiment` | now for code and reads; Z01 after the [A20] patch; Z14 after the anchor's epoch-500 readout | K2 |
| **2a** | the drift replicas first (A, A07-350, C; sd_null read at their epoch-500 snapshot before any other wave-2 entry starts, §5.2), then the floor family: M001-M010 at their listed targets (the 350k cells only if R1-R3 pass), P-T1/P-T2 teachers, per-architecture canaries | K2 (seed count n or ranking mode fixed from Z14), and the anchor's epoch-500 snapshots of seeds 1-n exist | the 350k base map for 2b |
| **2b** | the other singles, ordered by theory priority × code readiness × cost: (1) T0/T0a stability and recipe levers M028-M033, M013, M015 (M014 is confirm-only); (2) T1 M1/M4/M5 levers M024, M025, M039, M040, M050, M011, M012, M016, M018, M019, M021, M022; (3) KD and warm start once the teachers exist (M027, M035, M036); (4) the rest of T1; (5) T2 last (M020 Bop and M049 HGQ weights depend on the largest patches) | 2a done, or in parallel if pods allow | a ranked screen report (validation, never quoted); K3a |
| **3** | packages and factorial cells: the floor crosses first (M051-M060), then FF2 on E, FF1 at 5M, then the synergy crosses and stacks | wave 2 read, because packages need their singles on the same seeds at the same code sha | ranked report; K3 |
| **4** | confirm: survivors × target, 8 seeds, 7,000 epochs, ROC-test once, Holm; baselines M048 (both targets) and M049 (5M) as matched non-binary comparands, if Kai adds them; M049 at 350k is the anchor's arm NB | K3 | VERIFY → K4 |

Ordering rule inside a wave: theory priority (THEORY §4 predictions with a confirming
diagnostic that exists first; §6 open questions next), then code readiness (T0 < T0a < T1 <
T2), then cost (s_e,arch × H). Long-horizon entries (M015, M031, M032 and their packages) go into
the first pods, so they do not set the wave's wall clock.

**Decision points where Kai is asked** (nothing launches before his answer):
- **K1, after the anchor pilot:** [D19] and [D21] are Kai-confirmed (2026-09-27, 08:40 PDT), so
  the quantizer branch and the 350k base are settled: every 350k accuracy cell runs on arm A (E),
  and A07 at 350k is the descriptive arm A07-350 (§3.3 R2). K1 is left with the anchor's own
  fallback: if arm A has no feasible checkpoint at the pilot or in production, Kai names the
  anchor, and C at 5M is the remaining option (fallback C, §3.3 R2).
- **K2, before wave 2 and before any wave-2 pod:** the Z14 readout and the seed rule of §5.1,
  which gives n ∈ {4, 6, 8}, or ranking mode at n = 4 (the default when none qualifies), or
  n = 8 with g_res if Kai buys it; the pod count P (at n = 4, 2 against 10 pods: 42.4 against
  17.6 days of screen at the labelled projection; at n = 8, 79.5 against 23.5); full screen or
  the cheap version; the teacher jobs P-T1/P-T2; the
  training-only target (§4, §11); the Bop flip rule for M020/M071 (reflect the latent about its mean, as
  patch 0024 does, or the published sign flip; M020 note), before M020 is packed; the canonical tree for the patch series (`publication/` is a
  broken worktree; the code-line-merge campaign); Chang code license (relevant only if code is
  lifted; Delta plans re-implementations only).
- **K3a/K3, after each screen wave:** which cells (at most 12) go to confirm. They are chosen
  from the advanced cells in significance mode, or from the declared ranked list in ranking mode
  or after zero advances (§5.3). K3 also decides whether M014 is added as a confirm-only
  Chang-fidelity cell.
- **K4:** any number moving from a confirm VERIFY.md into the record.
- **K5:** a synthesis campaign on `mulder` for the cost levers and any hardware claim.
- **K6:** whether the non-binary baselines (M047-M050) run at all. Kai added arms H and NB to the
  anchor study as its second wave (2026-09-27), so M049's 350k cell is covered by NB; the rest
  stay labelled comparands, never the thesis.


## 8. Deep-research agenda

Each item is a question with an owner and the evidence that settles it. This is the part of
Kai's request where agents research how to move forward. Owners: **PR** physics-researcher
(literature dossier), **RA** results-analyst (recompute from stored arrays or logs), **ML**
ml-engineer (code read or CPU trace). "Before" names the entries that wait on the answer.

| # | question | owner | evidence that settles it | before |
| --- | --- | --- | --- | --- |
| DR-01 | Is 350k reachable at N=64 by binary A07 with a nonzero attention branch? (THEORY §6.1) | ML + RA | answered in part by the trace (§0): at 350k a feasible A07 has 6,947 EBOPs outside the softmax, and Wq, Wk, Wv at 1 bit cost 65,536 each, so no, not with every attention channel alive; the open part is attention in a pruned A07 or in the floor family. Z01 for the other architectures; the anchor pilot's per-channel widths at epoch 500 (Z02) | every 350k A07 cell |
| DR-02 | Is the Sun et al. collapse pure budget geometry? (§6.2) | RA, with M049 | the anchor's arm NB (= M049 at 350k) against arm A, arm H as the external-code reference, and M049 against C at 5M with the three attention numbers and the ablation delta; PR re-reads Sun et al. §3 ("over several trained models") | the reading of any collapse |
| DR-03 | Is the fan-in-3 `input_proj` the binding capacity loss? (§6.3) | RA | Z04 distinct rows; M050 − A at the same seeds | M024, M040, M067 |
| DR-04 | Does our recipe (arm R) train signs at all? (§6.4) | RA | C2I and flip-flop ratio for A against R from sign snapshots (patch `diag-sign-flips`; asks the anchor owner whether it can be added before the anchor launches; otherwise from the wave-2 replicas) | M021, M033, M020 |
| DR-05 | How does HGQ2 count ternary zeros, and what is LUT per EBOP for a ±1 layer at fan-in 32? (§6.5) | ML (Z06); `mulder` part is K5 | code read and trace; single-layer csynth → post-route | M047 reading; [L2] |
| DR-06 | Does a restart schedule beat one cosine of equal steps for binary? (§6.6) | RA, with M032 | flip-flop spikes against best-checkpoint position; M032 at confirm | M068-M073 |
| DR-07 | Does the ordering at the trigger working point match top-1 and AUC? (§6.7) | RA | Z09 on every confirm | every confirm report |
| DR-08 | Literature gaps (§6.8): weights-only binary small transformers with multi-bit activations; Bop or flip-aware optimizers on transformers; SAM for BNNs; whether BinaryBERT's 2-bit → 1-bit cliff has a small-model analogue | PR | dossiers with table numbers (the cards read abstracts only) | M020 (Bop), parked SAM, the thesis framing |
| DR-09 | Chang's activation init: is the default `i0` 2 (Q03 card body, `hgq/quantizer/config.py:249`) or 0 (Q03's own log line), and how does it square with the anchor's `ic=MinMax(0,12)` / "f0 = 7 fractional bits"? The init width (8 or 10 bits) depends on it | ML | read the hgq2 0.1.9 wheel `config.py` and `jsc150/model.py:277-296`; trace one layer's init bits | M012, FF2 |
| DR-10 | Was the 2026-09-15 campaign run on the `beta_schedule`/`ParetoFront` path (Q04: "inferred, not confirmed")? | ML | that campaign's run configs | M014's tried status |
| DR-11 | Card correction: Q05 says a moving target "does not exist in this codebase"; the S runner reads `experiment.target_schedule` per epoch (`ablation.py:126-131`) and it was run (C7) | PR (amend card) | code-surface §1f | the Q05 parking reason |
| DR-12 | Card correction: the Q preamble says the anchor uses per-tensor granularity; the anchor STUDY says `act_granularity channel` (as the A cards do) | PR (amend card) | anchor STUDY Arms preamble | M011 reading |
| DR-13 | Per-field bit width of L1 PUPPI candidates (Q11, P07) | PR | CMS Phase-2 L1T TDR (CERN-LHCC-2020-004), Correlator Layer-2 firmware data-format headers, the L1Phase2NNPuppiTau TWiki (unread) | parked Q11/P07 |
| DR-14 | Does HGQ-LUT undercut a binary transformer's LUT at comparable accuracy? (Q09 threat) | PR | re-check 2604.22293's tables in the PDF (the dossier is HTML-extracted) | the 0-DSP framing |
| DR-15 | A2Q/A2Q+ at table level (Q13) | PR | full-PDF dossier (only abstracts were fetched) | Z03 framing only |
| DR-16 | ReLU-, sigmoid-attention and Softermax numbers (Q10) | PR | dossiers of 2309.08586, 2409.04431, 2103.09301 | M005, M059 |
| DR-17 | hls4ml export questions: is a 0-bit datalane elided or synthesized as a 0-width wire (Q12's open half)? Can a runtime key mask pass the table `QSoftmax` without breaking token folding (P03)? Is there export for a LUT-tanh layer, a Linformer projection and a `head_dims` head? | ML | code read of the hls4ml 1.3.0 / convert_binary path; a toy CPU conversion in the lab pod (not quotable) | the hardware status of M016, M039, M045, M004 |
| DR-18 | Does hgq2 0.1.9 force the softmax exp input to SAT? **Answered: yes** (CPU trace, staged at 72a1290, not a result; `decisions.md` 2026-09-27 "chang0926 code"): +H·T·S per block plus a LUT term | ML | trace | R3 (applied) |
| DR-19 | Sun et al.'s paper states plain η, φ features while `jsc150/data.py` uses η_rel, φ_rel (P02); which one produced Table 1? | PR | the paper's code release history; no outward contact | the 79.4 % comparand's input set |
| DR-20 | The jet-tagging KD paper (2311.14160): what does it report, on which metric? | PR | dossier | M035, M036 |
| DR-21 | XNOR-Net++, Bi-Real, IR-Net, ReSTE, BinaryBERT, BiT: table numbers (abstract-level so far) | PR | dossiers | the B entries' STUDYs |
| DR-22 | Bop's γ and τ values and schedule | PR | **answered** (`research/DR-22-bop-hyperparameters.md`): arXiv:1906.02107 §5.2 (CIFAR-10: γ 1e-4 decayed ×0.1 every 100 epochs, τ 1e-8) and §5.3 (ImageNet: γ 1e-4 → 1e-6 linear, τ 1e-8); Larq `Bop` defaults τ 1e-8, γ 1e-4, undecayed (larq/larq `master` commit 3d7de883, `optimizers.py` l. 314-316; not a tagged release). M020 and M071 carry γ 1e-4 (undecayed) and τ 1e-8, labelled "scan seed, not tuned for this setup (DR-22)"; the wave STUDY measures the anchor's \|m\| distribution and may pre-register a τ scan before launch | M020, M071 |
| DR-23 | Deep Sets dimensions in Sun et al.'s `get_gnn` | ML | **answered**: `jsc150/model.py:88-100`, i.e. phi 64/64, context 64, post 64, pool × 1/16, rho 64/32/16, now in M006's `arch.deepsets_dims` in the `code/newmods/deepsets.py` form; re-implemented, nothing lifted (no LICENSE) | M006 |
| DR-24 | Chang code license | ML reads upstream; Kai decides | upstream repository license | only if anything is lifted verbatim |
| DR-25 | ParT pairwise-feature bias as a binary card: cost pass (the A cards omit it; D12 was flat at 6 seeds, archived) | PR | EBOPs and act×act count of a U-matrix bias | whether to card it |
| DR-26 | JEDI-linear 3-feature row resources (A11) | PR | the paper's tables | parked A11 |
| DR-27 | Round-14 binary instability at N ≥ 32: is the cause 101 against 7,000 epochs? | RA | the anchor's seed spread against R's | the interpretation of every N=64 sd |
| DR-28 | How EMA or SWA latents are re-thresholded so the exported weights equal the evaluated ones (R08) | ML | design note plus a reload test | M034 |
| DR-29 | FastML 2026 (Sloot): ternary beat binary on AUC, LUT and latency. What is the model and flow? | PR | dossier update | M047 framing |
| DR-30 | Does Sun et al.'s MLP-Mixer 79.7 % row come from a 350k-trained model? | PR | their ref. [18] | parked Mixer |

## 9. Parked and rejected

Parked entries can return with a reason and a new ID; rejected entries break the thesis or ask a
different question.

| card / idea | status | one-line reason |
| --- | --- | --- |
| Ensembling (R, omitted) | rejected | N models cost N× LUT inside one fixed L1 envelope |
| B03 per-channel arbitrary learned β | rejected as written | breaks the scalar fold (SCORE_FOLD / EXPLICIT_SCALE); each channel becomes a multiplier and a DSP risk; kept only as power-of-two shifts (M024, M025) |
| B12 "two-set" levels | rejected | risks more than two effective weight values |
| Q11 input width matched to PUPPI | parked | unschedulable: no source for the PUPPI bit width (DR-13) |
| P07 input width sweep | parked | same missing source; under [D19] the input quantizer is learned anyway |
| A07 PMA or class token | rejected unless a labelled baseline | a third act×act pair (DSP risk); the class token changes T to 65 in every shape |
| A13 GLU | rejected | a new act×act multiply per FFN |
| A05 RMSNorm, trainable norm | parked | sum of squares is act×act plus an rsqrt table; SubLN on fabric cost 4.3× LUT (J3); norm-free default since D10 |
| A05 SubLN | rejected here | verified to hurt binary under standardized inputs (D10, archived) and the historical W1-vs-W8 confound |
| A12 Bi-Real shortcuts | parked | predicted no effect at L = 1; revisit if M044 (L = 2) survives |
| A02 weight-tied L = 2 | rejected | no EBOPs saving (activations still pass twice); inlined weights do not share logic |
| A14 tanh FFN activation | merged | Chang uses tanh as a pre-block bound (M016); ReLU is free in hls4ml |
| A15 low-rank binary factorization | parked | no source; predicted not to save EBOPs once the width-r stream is paid |
| A06 max / scaled-sum pooling | parked | scaled sum equals GAP at N = 64; max is predicted negative and hls4ml support is unverified |
| A10 MLP-Mixer | parked | not permutation-invariant; the 79.7 % source is not stated as 350k-trained (DR-30) |
| A11 JEDI-linear | parked | after M006: Deep Sets answers the collapse question first; T2, 60-100 lines |
| A16 Engram memory | rejected here | multi-bit tables, no HLS lowering, memory cost logs 0 (F4); its own campaigns are in flight |
| A01 d_model 48, A03 FFN 16, P01 N = 16, Linformer k = 16, Q07 700k rung | parked | second rungs; run only if the first rung (M042, M043, M009, M004, M010) shows curvature |
| B05 ApproxSign, B08 ReSTE | parked | same backward slot as M018/M019; W1A1 motivation; head-to-head after EDE |
| B09 stochastic sign | parked | its main claim is about spread; low theory priority |
| B11 ternary-weight splitting | parked | doubles the architecture mid-run, which breaks the PID graph and pairing; M027 covers the two-stage idea |
| R05 one-cycle | parked | at the screen horizon it is M030 plus the single anchor cycle; M032 covers the no-restart extreme |
| R06 batch 256 with scaled LR | parked | about 10× the steps per epoch; A − R and D − R already cover the batch package |
| R08 SWA across cycle ends | parked | the same re-threshold issue as M034 (DR-28), horizon ≥ 1,500 |
| R10 label smoothing | parked | no binary mechanism; smoothing a teacher weakens KD (Müller et al.) |
| R11 SAM | parked | 2× step cost; flatness in latent space is not shown to transfer to the signs (DR-08) |
| R12 dropout, stochastic depth | parked | a capacity-limited L = 1 model; interacts with learned widths |
| R13 rotation, smearing, constituent dropout | parked | approximate symmetries; after the exact reflection (M037) |
| R14 / P11 pT reweighting | rejected here | verified negative at N = 8 (PTW5 − BASE −0.0108 [−0.0124, −0.0093] ROC-test AUC, n = 260,000, 8 seeds, `campaigns/2026-09-25-pt-weighting/VERIFY.md`); the recipe has no weights |
| P04 ΔR ordering | parked | predicted to matter at N ≤ 16, not N = 64 |
| P08 80/20 split | parked | changes the validation set, which is the screen readout; a confirm-only question |
| P10 class set | rejected | a different task |
| P12 working point | converted | a reporting rule (Z09), not an entry |
| Q01 tensor granularity | parked | channel won in 3 of 3 single-seed pairs (B4) |
| Q03 low init f0 = 4 | parked | after M012 |
| Q05 moving target | parked | tried and failed at N = 8, 16 and 64 (C7); lesson 2; reinstate only if M014 shows early-pressure harm |
| Q06 min-EBOPs selection | converted | re-selection from logs (Z05) |
| Q08 old-quantizer fixed softmax output 4 bits (E1 retry) | parked, branch | reinstated only in the C′ branch (R4) |
| Q10 sigmoid attention | parked | same mechanism as M005, needs a table |
| Q13 A2Q training | rejected | no weight-magnitude lever after binarization; the metric is Z03 |
| clipvalue-only, β₂-only singles | aliased | read as the pair M074 inside the arm D 2 × 2 |
| key_dim 16 on E, float16 inputs | parked | small fidelity items |
| ParT pairwise features | parked | needs a cost pass (DR-25) |

## 10. Conventions compliance

| rule | how Delta satisfies it |
| --- | --- |
| metric named with its split and n | screen: validation top-1 accuracy, n = 62,000, labelled "screen, not quotable"; confirm: ROC-test top-1 accuracy, n = 260,000, with macro and per-class AUC beside it; validation and ROC-test numbers never share a column unlabelled |
| no comparison across input sets or N unless that is the point | only M009, M058 (N = 32) and M040 with its packages (5 inputs) cross, each labelled "crosses N" or "crosses input set", Welch or paired-if-hash |
| seeds ≥ 3, or justified | n ∈ {4, 6, 8} per screen cell, set at K2 by the Z14 rule, or ranking mode at 4 (§5.1); 8 per confirm cell; the cheap version has 3 and is always a ranking |
| selection rule pre-registered | the anchor's [D11] at confirm; best-feasible-as-of-H at screen; G0-G3 (§5.3) |
| falsifier stated | per entry, the directional prediction plus its diagnostic. An entry is falsified at confirm if the 95 % interval of its paired gap lies below 0, or, for floor entries, if k < 6 of 8 seeds are feasible. A confirm gap inside ±g_res,confirm (§5.1, item 5) is "unresolved", not "flat". At screen it is "not advanced" or "ranked", never "falsified" |
| no local training or synthesis | NRP Nautilus for GPU; CPU gates only locally; no `mulder` in Delta |
| W&B group named | `BNJetTag-Delta` / `delta-20260926-w2`, `-w3`, `-w4` (proposed); never `BNJetTagAug` |
| figures via `docs/style/bnjettag.mplstyle` | per-wave forest plots of paired g with intervals (labelled "validation, n = 62,000, screen"), the floor/headroom chart (derived, then traced), factorial effect plots; `tools/plot_check.py` at each wave's REPORT |
| never report a gap without seeds and an interval | every g carries k, the interval and the sign count; 1-seed gaps never advance |
| numbers never from memory | derived floors show their formula and substitution; every quoted record number names its file |

## 11. Where I am not sure

```
DECISION: training-only levers (B, R, KD, augmentation) screen at 5M on arm C; survivors confirm at 5M and the 350k base
ALTERNATIVES: screen them at 350k on arm A (E, [D21]; traced h 0.399; A07 has traced
  h 0.010, a remnant, and is the descriptive arm A07-350, §3.3 R2); screen at both targets (23 more cells × 4 seeds =
  +56,000 run-epochs)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: seeds per screen cell set at K2 from Z14 (sd_plan = √2 · anchor epoch-500 sd): the smallest n in
  {4, 6, 8} with k_joint(n, q/m) · sd_plan ≤ 0.3 pt, k_joint sized for the whole advance rule;
  n_W3 ≤ n_W2 per target; otherwise ranking mode at n = 4 (no advance claims), which is the likely
  outcome (n = 8 needs an anchor sd ≤ 0.116 pt at W2 5M); advance by BH q = 0.10 within wave ×
  target and mean g ≥ g₀/2 (g₀ = 0.3 pt, the MDE target); sign count descriptive; baselines no advance decision
ALTERNATIVES: n = 8 with g_res = k_joint(8, q/m) · sd_plan (1.55 pt at the anchor's 0.6 pt trigger; 684,000
  run-epochs); a smaller BH family (per code tier or family letter); a fixed-threshold rule without FDR
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: primary screen control is the anchor's own [A6] snapshot (as the brief asks); a drift replica switches the pairing only on a pre-registered trigger
ALTERNATIVES: always pair against the in-wave replica (same code sha and GPU class; +8-12 runs per wave, already budgeted)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: FF2 (Chang parity) on arm A (E) at 350k; FF1 (additivity) at 5M on arm C
ALTERNATIVES: FF2 on A07 at 5M (A07 has no real 350k headroom); FF1 at 350k on arm A
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: teachers P-T1 (FP) and P-T2 (int8), A07, gated 90/10, Chang recipe, 2,000 epochs, seed 101
ALTERNATIVES: 7,000 epochs (+10,000 run-epochs; about 9 d serial at the projection before any KD
  screen); 500 epochs (weaker teacher); no KD in Delta
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION (Kai-confirmed [D21], 2026-09-27): A07 at 350k (traced h 0.010: 6,947 EBOPs outside the
  softmax, less than input_proj plus head at 1 bit, 7,328) is the anchor's descriptive arm A07-350,
  the floor-family k_base and never an accuracy base; every 350k accuracy cell runs on arm A, which
  is E (traced h 0.399; §3.3 R2)
ALTERNATIVES: none open; the earlier override (A07 as the accuracy base) was declined by Kai
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```
```
DECISION: design values chosen here, not from a source: latent clip [-1, 1] (BinaryConnect's range);
  EMA decay 0.999 (Mean Teacher range); PID p 2, i 0.2; collapse = val acc <= 0.25 for 10 epochs
  after epoch 20; table floor 2 bits (departs from Chang's Min(4)); cap of 12 confirm cells
ALTERNATIVES: set each in its wave STUDY from a small pilot
CONFIDENCE: LOW   FLAG FOR HUMAN: YES
```
```
DECISION: park SAM, label smoothing, batch-256 rescaling, JEDI-linear, MLP-Mixer, stochastic sign, ReSTE, ApproxSign (§9)
ALTERNATIVES: include them as singles (+8 × 4 × 500 = +16,000 run-epochs, plus two T2 patches)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: T0a keys use placeholder names until [A1] [A2] [A3] [A20] fix them; the generator maps them
ALTERNATIVES: wait for the anchor sha before writing delta.json
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```
```
DECISION: W&B project BNJetTag-Delta, groups delta-20260926-w2/-w3/-w4
ALTERNATIVES: reuse BNJetTag-ChangRecipe with Delta groups
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```

Also uncertain and stated where it applies: every derived floor other than A07 and E (Z01
replaces them; the LUT term is a two-point fit); a reversal of [D19] (R4, a contingency now
that Kai confirmed it); whether arm A reaches 350k non-degenerately at all (§3.3 R2); the Chang
`i0` default
(DR-09); whether the anchor's LR 3e-3 is stable at all (§5.2). If it is not, most of wave 2
re-bases on arm D, which is the largest single risk to this queue. M027's warm start and M036's
attention-map KD at the 350k confirm (on arm A, E) need an E-shaped teacher, since P-T1 is A07
(open, owner).

## 12. Patch series (for the ml-engineer's generator)

38 unique slugs: 31 method patches and 7 instrumentation patches. Each is opt-in behind a new
key whose absence reproduces current behaviour byte for byte (Z13). Sizes are the cards' or
code-surface's estimates, not counts. Users are the entries whose `code_changes` name the slug.

| slug | tier | size (lines) | touches | what | used by |
| --- | --- | --- | --- | --- | --- |
| `lr-schedule-variants` | T1 | ~15 | ablation.learning_rate | m_mul, t_mul and a linear warm-up on top of the anchor [A1] Chang schedule; unit test at restart boundaries | M030, M031 |
| `beta-schedule-s-runner` | T1 | ~12 | ablation.run_training | honour train.ebops.controller 'schedule' with hgq2 PieceWiseSchedule in the S runner (inert today) | M014 |
| `softmax-table-min-bits` | T1 | ~5 | qat.softmax (after [A20]) | expose the minimum width of the trainable exp/inv tables (Chang bc=Min(4)) | M003, M051, M052, M054, M060 |
| `qk-stream-min-bits` | T1 | ~10 | qat.stream_iq | lower bound on the Q/K stream widths (anti-collapse width floor) | M007, M055, M056, M059 |
| `ebops-group-weight` | T1 | ~30 | qat + ablation | per-layer-group multiplier on the beta*EBOPs term (attention group vs rest) | M008, M057 |
| `attn-linformer` | T2 | ~40-60 + export | qat block, convert_binary | binary sequence projections E,F (N->k) on K and V; hgq2 0.1.9 has no QLinformerAttentionT | M004, M053, M054, M056, M060 |
| `attn-relu-over-n` | T2 | ~80-150 + export | qat.softmax branch | ReLU(scores)/N attention (N=64 is a shift); no exp/inv tables | M005, M059 |
| `body-deepsets` | T2 | ~80-120 + export | new builder beside qat.build_qat_model | binary Deep Sets body (phi MLP, pooled context add, rho MLP), dims re-implemented from the Sun et al. topology, no code lifted | M006 |
| `act-granularity-element` | T1 | ~10-20 | qat.act_iq | act_granularity 'element' (per position and channel, Chang value-wise) | M011, M065, M096, M097, M098, M102 |
| `act-init-f0` | T1 | ~20 (0 if [A20] exposes it) | qat._free_act, ablation.matching_initialization | fixed activation init f0 with i tracked (Chang f0=7) | M012, M096, M099, M100, M102 |
| `pre-block-tanh-lut` | T1 | ~12 train + export new | qat block, convert_binary | hgq2 QAffinedUnaryFunctionLUT('tanh') before attention and before the FFN; EBOPs of its table quantizers checked at W1 | M016, M097, M099, M101, M102 |
| `head-dims` | T1 | ~25 + export | qat head, ablation.expected_binary_layers, binarize, convert_binary | arch.head_dims list (Chang 32/32/32) | M045, M098, M100, M101, M102 |
| `binarizer-center-flag` | T1 | ~10 | qat.bitnet_binary_ste, binarize.absmean_binarize | quant.binary_center false: uncentered absmean | M017 |
| `ste-variants` | T1 | ~25 | qat.bitnet_binary_ste + epoch callback | quant.ste in {bounded (default), clip_identity, ede}; EDE temperature restarted every lr cycle or annealed once | M018, M019, M072, M073, M081, M082, M083, M084 … (12 entries) |
| `bop-optimizer` | T2 | ~60-100 | new optimizer + variable routing | Bop on binary latents (flip on EMA-gradient threshold); Adam on everything else | M020, M071 |
| `latent-clip` | T1 | ~10 | qat kernels (constraint) | clip latent kernels to [-c, c] after each step | M021, M068, M070, M073 |
| `beta-mode` | T1 | ~30 incl. export | qat.bitnet_binary_ste, binarize | quant.beta_mode in {absmean (default), absmean_pow2, learned_pow2} | M022, M023 |
| `channel-gain-pow2` | T1 | ~60 incl. per-channel binary gate + export | qat, ablation.binary_gate, binarize, convert_binary | per-output-channel power-of-two gain (shift) after the +-1 matmul; gate becomes two symmetric values per channel; DSP audit required | M024, M025, M065, M066, M067, M080 |
| `pre-quant-shift` | T1 | ~20-30 | qat.act_iq call sites | learnable per-channel additive shift before each activation quantizer (RSign shift only; no slope) | M026, M066 |
| `init-from-checkpoint` | T1 | ~20 | ablation.matching_initialization | copy latents from a named checkpoint (the FP teacher) instead of the seed init | M027, M061, M062, M064 |
| `kd-unblock-s-runner` | T1 | ~30 | run_engram.validate_cfg, run_study, ablation | allow experiment.distillation in S and supply teacher logits on the S path | M035, M036, M061, M062, M063, M064, M082, M085 … (14 entries) |
| `kd-attention-map` | T1 | ~30-40 | ablation loss + teacher tap | attention-map distillation term (teacher with the same heads) | M036, M062, M064 |
| `latent-ema-eval` | T1 | ~20 | ablation epoch loop | EMA of latents, re-binarized; candidate checkpoint evaluated on the EMA weights | M034 |
| `augment-eta-phi-reflect` | T1 | ~15-25 | ablation.make_epoch_step (train batches only) | random eta_rel and phi_rel sign flips per jet; never on validation or ROC-test | M037, M084, M087, M089, M090, M092, M093, M094 … (9 entries) |
| `pt-gate-threshold` | T1 | ~5 (0 if [A3] exposes it) | anchor [A3] loaders + prepare_cache | gate threshold as a key (0 = ungated); new cache per value | M038, M075, M076, M078 |
| `gated-key-mask` | T1 | ~20-40 | qat attention scores, cache emits mask | additive mask on gated/padded key positions before the softmax | M039, M076, M077, M078, M079, M080 |
| `std-real-slots` | T1 | ~10 | prepare_cache input_std | standardization statistics over real (non-gated) slots only | M041, M079, M080 |
| `derived-input-features` | T1 | ~25 | prepare_cache, run_engram.validate_cfg | append log pT and Delta R computed from the three L1 features; relax the 3-feature assert | M040, M067, M080, M081, M085, M086, M087, M091 … (11 entries) |
| `weight-scheme-baselines` | T1 | ~25 | run_engram.validate_cfg, qat | admit quant.weight none / int8_absmax and quant.layer_weight_override for labelled baselines and teachers | M027, M035, M036, M047, M048, M050, M061, M062 … (18 entries) |
| `ternary-absmean` | T1 | ~30 | qat, ablation.binary_gate (labelled ternary gate) | ternary {-b,0,+b} absmean baseline | M047 |
| `hgq-learnable-weights` | T2 | ~40-60 | qat build branch | HGQ kbi learnable weight widths (the branch kbi_learnable never had) | M049 |
| `accumulator-ebops-metric` | T1 | ~20 | ebops_calc per_layer | closed-form accumulator bits b_act + ceil(log2 fan_in) per binary layer, reported beside native EBOPs | Z03 |
| `diag-sign-flips` | T1 | ~30 | epoch observer | sign snapshot per layer: flip-flop ratio per epoch, C2I ratio | Z08, DR-04 |
| `diag-attention` | T1 | ~40 | eval script | attention entropy / log(n_valid) with gated keys masked in the diagnostic pass; attention-ablation delta (A.V replaced by mean V) | Z08; every entry |
| `diag-beta-trajectory` | T1 | ~10 | epoch observer | per-layer beta and latent |w|/beta histogram | Z08 |
| `diag-input-proj-rows` | T1 | ~15 | checkpoint reader | distinct sign rows of input_proj | Z04, Z08 |
| `diag-latent-binary-gap` | T1 | ~20 | eval script | validation accuracy with latent kernels in place of q*beta | Z08 |
| `screen-collapse-stop` | T1 | ~15 | ablation epoch loop, run_pack | collapse rule: stop and record when validation accuracy <= 0.25 for 10 consecutive epochs after epoch 20 | G1; every screen |

Anchor patch series Delta depends on (owned by the training-batch campaign; these are not Delta slugs): [A1] Chang schedule, [A2] explicit optimizer path, [A3]/[A4] pT gate and 90/10 cache, [A5]/[A6]/[A15] cadence, rollback and 500-epoch snapshots, [A12] failed-arm isolation, [A13] tie-break, [A17] kernel-hash pairing check, [A19] AUC-selected copy, [A20] the [D19] quantizer set.

`delta.json` comes from one script, `delta_spec.py` (this directory; `python3 delta_spec.py <outdir>` also prints the counts and budget totals quoted in §2 and §5.4), and the entry tables in §2 and the floor table in §3.2 are rendered from `delta.json` by `delta_tables.py` (`python3 delta_tables.py <dir-with-delta.json> [outdir]`). `screen_power.py` reads `delta.json` and prints the §5.1 family sizes and k values. Bop's γ and τ (`train.bop_gamma` 1e-4, `train.bop_tau` 1e-8) in M020 and M071 are the DR-22 scan seed, labelled "scan seed, not tuned for this setup (DR-22)" (arXiv:1906.02107 §5.2, §5.3; Larq `Bop` defaults at `master` commit 3d7de883, `optimizers.py` l. 314-316). The wave STUDY measures the anchor's |m| distribution and may pre-register a τ scan before launch. Every config key that an anchor patch registers (`code/key_registry.json`: [A1] `train.lr_cycle_epochs`, [A2] `train.optimizer`, [A3] `arch.pt_gate_gev`, [A20] `quant.act_f0`) has that patch in the entry's `anchor_patches_required`. Counts, IDs, patch slugs, floors and budget totals therefore agree across the files.
