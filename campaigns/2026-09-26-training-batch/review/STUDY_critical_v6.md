# STUDY critical review v6: 2026-09-26-training-batch

Critical reviewer, panel mode, fresh context, 2026-09-27. Iteration 6. No verdict (the arbiter
issues it).

Scope, set by the orchestrator per `review/STUDY_arbiter_v5.md` ("One fixer pass closes it"):
(1) did each of arbiter v5's ordered fixes 1-7 land at its listed sites, verbatim where the
arbiter gave text; a new B only if an edited sentence is itself wrong; (2) the new arm FP32-E
[D26] (Kai, `decisions.md` top entry), reviewed in full at the edit sites listed in the
STUDY change log (l. 184-206).

Artifacts read: `STUDY.md` at 54bf3e7 (2,046 lines); `git diff ed73976 1175889` (fixer pass) and
`git diff 1175889 54bf3e7` (FP32-E pass); `review/STUDY_arbiter_v5.md`;
`review/STUDY_validators_v6.txt`; `.claude/memory/decisions.md` l. 1-60;
`code/tree/bnhgq2/{qat.py,ablation.py,ebops_target.py,ebops_calc.py}`;
`code/tree/campaigns/chang0926/configs/chang0926-a-n64-s1.json`;
`code/evidence/{cpu_gate_d25.log,static_floors_arms_s1_d25.json}`;
`bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz`; the local HGQ2 source
`~/hgq2/HGQ2/src/hgq/quantizer/internal/fixed_point_quantizer.py` (and a cached
site-packages copy of the same file).

## Validators (verbatim, `review/STUDY_validators_v6.txt`)

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  29330 words · 715 sentences · mean 25 words (σ=21.5) · 17% bullets · 0 em-dashes
E1-TRACE-PENDING tokens: 0
Diff since v5 review (ed73976):  1 file changed, 330 insertions(+), 84 deletions(-)
```

No red flag. No figures at STUDY, so there is no `plot_check.py` output.

## Recomputed

- R14 N=64, ROC-test, n = 260,000 per file, no NaN or Inf in scores (`d.files` = `y`, `score`,
  `meta`; shapes (260000, 5)). W1A8 seeds 67.176 / 72.638 / 67.207 %, mean 69.007, sd 3.145
  (ddof 1). FP32 seeds 79.422 / 78.828 / 79.095 %, mean 79.115, sd 0.297. Archived, sizing only.
- Fix 1 check case: best seed 72.64; 67.18 and 67.21 lie 5.46 and 5.43 pt below it (2 of 3
  flagged); median 67.21 flags 0 of 3. STUDY l. 901 matches.
- [D26] resolution (STUDY l. 988-991): t(0.975, 7)/√8 = 0.8360 (text 0.836); 1/0.836 = 1.196,
  rounded down to 1.19 (text 1.19); sd_diff at zero correlation = √(3.14² + 0.3²) = 3.154, paired
  half-width 2.637 (text "about 2.6"); Welch half-width 2.628 at df 7.13 (text "about 2.6");
  cheap version t(0.975, 3)/2 = 1.591 (text 1.59). All hold.

## Part 1: arbiter v5 fixes 1-7, by number

| fix | site(s) | status | evidence |
| --- | --- | --- | --- |
| 1 (#1) outlier count | Falsifier, stability, l. 895-903 | **landed, verbatim** | seed range with n = 62,000, count against the arm's best seed, A-against-D discordant counts, median sentence with "0 of 3 ... 2 of 3 ... 5.46 pt"; "All are descriptive". Grammar residue in C4 |
| 2 (#4, C #14) headline, both branches | l. 924-929; "the 95 % half-width" l. 935 | **landed, verbatim** (quotes changed from double to single) | both L branches and the U < 0 clause present; "The claim verdict below sits beneath it" kept |
| 3 (#2, #3, #11) extra pairs, wave-2 readout, table | table l. 943-949; Resolution paragraph l. 950-962; l. 554 → 1.19 (now l. 668); l. 1799 → 1.19 (now l. 2045); second-wave rule (now l. 1312-1315); Kai row (now l. 1863) | **landed, verbatim, every site** | `grep "1\.2 pt\|1\.20\b\|1\.88\|2\.14 pt"` returns only change-log history (l. 128, 168-169), as the arbiter allowed |
| 4 (#6) A07-350 expectation | Falsifier l. 836-846; pilot A07-350-s1 bullet l. 1188-1189 | **landed, verbatim; facts verified** | `static_floors_arms_s1_d25.json`, `chang0926-a07-350-n64-s1`, `one.per_layer`: `input_proj` 6,144 (3 × 2,048); `bit_block_0_attn_Wq`, `_Wk`, `_Wv`, `_Wo`, `bit_block_0_ffn_fc1`, `_fc2` 65,536 each (32 × 2,048); `head_fc1` 1,024 (32 × 32); `head_fc2` 160. `grep "d32 dense"` finds only l. 233, the per-channel cost statement the arbiter kept |
| 5 (#5, #8) [D25], C′ gate | fidelity rows (l. 393-394), [D25] body (l. 1543-1544), [A21] (l. 1712-1713); change-log note l. 111-113; `decisions.md` correction | **landed; facts verified**; text redundant (C5) | `chang0926-a-n64-s1.json:40` reads `"i_decay_speed": 0.001`; `cpu_gate_d25.log` has 58 `I_DECAY_OK` lines, all 0.001 except `:116` `I_DECAY_OK chang0926-cprime-n64-s1 config None quantizers 0 values []`; `decisions.md` [D25] entry ends with the dated fixer correction (append-only respected; the entry's earlier "0.01 on C′" line is left as written) |
| 6 (#7) REPORT-use restriction | Scope | **landed verbatim at 1175889, then superseded at 54bf3e7 by its own condition** ("unless Kai adds the FP32 E arm"); the rewritten Scope (l. 274-281) keeps "A − NB is cited only as an iso-EBOPs gap" | see Part 2, B2, on what the rewritten sentence now licenses |
| 7 (C #9, #10, #12, #13, #16) | l. 300; [A7] l. 1609-1610 (arms file); Selection l. 728-734 (`budget_met`); `xfm` l. 464, 855, 1815; figure l. 1038; [A14] l. 750-752 | **landed, verbatim; facts verified** | `cpu_gate_d25.log` holds `params 31735` (A/B/D/R lines) and `params 61951` (16 lines), so the l. 300 re-cite supports both counts; the d25 floors file holds B on E at 250,000 (headroom 78,474) and A, D, F, R on E at 350,000; `ablation.py:711` per-epoch `'budget_met': int(feasible)`, `:779` summary `measured['total'] <= final_target`, `:806` W&B summary update, all as the new sentence says |

Earlier A and B by name: arbiter v5 had no A; its B #1-#7 are closed by fixes 1-6 above (B #7 by
fix 6, then by [D26]). No earlier B is reopened.

Arbiter v5 launch condition 2 ("fix 5 lands before PREFLIGHT checks [A21]"): met on file times.
1175889 is committed 2026-09-27 10:28:20; `PREFLIGHT.md` (untracked) was last written 10:42:40
and its `I_DECAY_OK` lines (l. 59-67) come from the later shipped-tree gate. Fact only, no
finding.

## Part 2: FP32-E [D26], reviewed in full

Change-log edit-site line numbers (l. 184-206): all 38 checked against the file at 54bf3e7; each
lands on the named text.

Code claims checked: `qat.py:396` `fp32 = wmode == "none"`; the fp32 branches set
`_dummy("weight")`/`_dummy("datalane")` on every `dense_einsum` and `dense` (`:473-475`,
`:490-491`), `stream_iq` (`:500`), the softmax exp/inv inputs (`:516`) and the softmax output into
A·V (`:575-576`); the exp/inv tables are `_table(1, 20)` (`:517`), a `kif` quantizer with k0 0,
i0 1, f0 20, SAT, `trainable=False` (`:358-360`). `ablation.py:161` and `:584` read
`pid.target_ebops`; `ebops_target.py:88-95` refuses a missing or non-positive target;
`ebops_calc.py:15` is `compute_ebops`. The [D26] inventory and the [A25] citations are
accurate. The config guard at `qat.py:417-419` refuses `act_overflow`/`softmax_quant` without
binary weights, so FP32-E configs cannot carry the [D19] keys, consistent with [A25]'s "carry
only keys the path reads".

### Category A

None.

### Category B

**B1. The wave-1 K=7 exception is gated on memory only; wave-1 timing and FP32-E's own canary are
skipped.** STUDY l. 1319-1326: FP32-E-s joins wave-1 pod s "at K=7 only if 7 × the canary's
measured peak GPU memory per process fits". The wave-1 canary runs at K=6 (l. 1136, 1225), so
s_e at K=7 is never measured, and the [D15] 14-day rule (s_e ≤ 172.8 s, l. 1101; already at risk,
about 187 s projected with the trace, l. 1114-1117) would be applied to K=6 timing. A seventh
process on the GPU slows every wave-1 process; if T_run crosses 14 d mid-run, the [D15] options
(terminal epoch 2,000 or 4,000) change what every wave-1 arm trains. That contradicts the
change-log claim "no change to any wave-1 arm, seed, target, pilot or selection rule"
(l. 185-186) in this branch. Second, [A25] is scoped "Before FP32-E's canary" (l. 1773), and the
FP32-E canary checks exist only in the second-wave canary (l. 1300-1302); on the K=7 path FP32-E
enters production with no GPU canary at all (no finite-loss or epoch-10 train-loss check).
Impact: an unmeasured change to wave-1 timing, and a production arm that never ran on a GPU.
Fix: make the K=7 exception require a K=7 re-canary of one wave-1 pod (epochs 1-10) whose
projected T_run including FP32-E is ≤ 14 d and in which FP32-E passes the finite-loss and
epoch-10 checks; otherwise FP32-E stays in the second wave. Or drop the exception. The
pre-existing NB K=7 Kai row was closed by arbiter v4 #13 and is not reopened here; this finding
is only that the new FP32-E text makes "fits" explicitly memory-only.

**B2. The precision-package claim is named "close" but the rule tests a zero null, and Scope now
licenses citing it on "close to full precision".** Falsifier l. 979-980: claim "binary E at
350k EBOPs is close to the same E model in unconstrained FP32"; the rule (l. 985-987) decides
only "resolved cost" (interval below 0, Holm p < 0.05) or "not resolved at this resolution",
with "no non-inferiority pass condition". "Close" has no margin, so no outcome of the rule can
confirm or refute it: a resolved 0.5-pt cost reads as refuting "close", and an unresolved result
at the 2.6-pt half-width (recomputed above) invites the reading "close". Scope (l. 276-278)
then allows REPORT to "cite A − FP32-E as evidence on the thesis's 'close to full precision'
claim". "A wide interval is not support" (l. 984) helps but does not fix the claim string.
Precedent: arbiter v5 #4 rated B a pre-registered headline whose wording a reader would
misread. Fix: word the claim as the zero null the rule tests ("binary weights with
learned-width activations at 350k cost no top-1 accuracy against the same E model in
unconstrained FP32 (package)"), and state in Scope that REPORT reports the interval and never
issues "close" as a verdict. The alternative is to pre-register a margin now, with its
resolvability at 8 pairs.

**B3. The L > 0 branch of the precision headline drops the sign and the anomaly.** l. 983-984:
"when L > 0, 'no accuracy cost against FP32 is resolved'". This is the defect arbiter v5 fix 2
removed from A − NB, recurring in new text: when L > 0 the interval shows A above FP32-E, and
the sentence hides that. A binary model at 350k resolved above the same architecture in
unconstrained FP32 is a red flag (FP32-E under-trained or over-fitted by the 7,000-epoch
all-epoch selection, label or order misalignment, a pairing error), not a headline. Fix: "If
L > 0: 'A exceeds FP32-E by at least L pt (package, n pairs, 95 %)', and the result goes to the
investigator before REPORT, with checks of FP32-E's selection epoch, train/validation curves,
the [A25] pairing record and the byte-equal `y` check."

**B4. The replacement check "no quantizer variables in any layer" cannot pass on FP32-E's own
inventory.** l. 513 (also the conventions row l. 1367, [D26] l. 1554-1560, DECISION l. 1950):
FP32-E asserts "no quantizer variables in any layer and float kernels". The same section keeps
the softmax exp and inv tables as `_table(1, 20)` `kif` quantizers (l. 494-497; `qat.py:358-360`,
`:517`). In the HGQ2 source the `kif` quantizer's `build` creates `_k`, `_i` and `_f` variables
unconditionally (`~/hgq2/HGQ2/src/hgq/quantizer/internal/fixed_point_quantizer.py:371-394`; the
same in a cached site-packages copy; whether it matches the job-YAML pin hgq2 0.1.9 is
unconfirmed). If the pin behaves the same, the pre-registered check fails on every FP32-E
checkpoint by construction, the same class as arbiter v5 #5 (a gate that cannot pass as
written). Fix: at all four sites, "no quantizer variables except the two fixed, non-trainable
softmax tables per block (k0 0, i0 1, f0 20, asserted unchanged from init), and float kernels";
add to [A25] that the check is run on the pinned hgq2 against the built model's variable list.

**B5. Conventions rows "Configurations", "Cost accounting" and "Selection under a budget" are
not amended for FP32-E.** l. 1364-1366 still say, for the campaign as a whole, binary weights
with learned activation widths; native EBOPs remeasured on the selected checkpoint; selection at
or under the budget. FP32-E deviates from all three (float weights and identity activations,
no EBOPs, all-epoch selection with no budget). [D26] justifies each deviation in the body, but
the conventions table is where compliance is checked row by row, and the [D26] edit list
touched the rows around these (l. 1358, 1361, 1367, 1371, 1372, 1376) but not these. Fix: one
clause per row: "FP32-E [D26]: float weights, quantizers off except the fixed softmax tables";
"FP32-E: no EBOPs, reported as 'FP32, unconstrained'"; "FP32-E: no budget; selection over all
epochs meeting (c), a labelled part of the package".

**B6. [A25] omits `binary_gate`, which the runner calls unconditionally.** `ablation.py:582`
calls `binary_gate(model, cfg)` before training, and `:342-343` assert that the binary layer set
equals `expected_binary_layers(cfg)` and that each has two symmetric values. On FP32-E (and on
NB) this fails. [A25] (l. 1773-1795) lists the build, `compute_ebops`, the PID, selection,
certification, pairing, regression and the CPU gate, not this call. The CPU gate would hit it as
a crash, so nothing would pass silently, but [A25] is the runner-path checklist Kai asked for
(`decisions.md`, "an ml-engineer check of the runner path"). Fix: one bullet: "`binary_gate`
(`ablation.py:336-343`, called at `:582`) is skipped for `quant.weight: "none"` and replaced by
the [D26] check at the selected checkpoint; same mechanism as NB under [A22]."

### Category C

- **C1.** The [D24] DECISION block (l. 1961-1963) still reads "own Holm family {A − NB, H − NB}"
  and "4 pods at K=4"; the [D24] label body (l. 1534-1536) is amended, the block is not. Add a
  dated amendment line to the block.
- **C2.** No designer entry for [D26] in `.claude/memory/decisions.md`; only Kai's request is
  there. [D25] set the precedent of logging the designer's decision (controller off, Holm
  membership, K=6/K=7 rules, the reduced selection rule). Append one entry with a Check line.
- **C3.** Second wave: the "Launch gate" bullet (l. 1279-1283) names only [A22] and [A23]; the
  "If only one arm passes its gates" rule (l. 1288-1290) was written for two arms and does not
  say what happens when two of three pass. [A25]'s "the gate's production count rises by 8"
  (l. 1795) changes the recorded expectation `PREFLIGHT_ALL_PASS 58 production 56` (l. 111,
  `decisions.md` 0024 entry) without saying whether FP32-E joins the wave-1 gate or a
  second-wave gate. Name the gate and its new expected line.
- **C4.** Fix 1 grammar (l. 895-896): "the feasible-degenerate count and per arm, the seed
  range" reads as a splice; "per arm, the feasible-degenerate count, the seed range ...".
- **C5.** Fix 5's replacement text is nested inside the old sentences at all three sites, which
  leaves redundancy: l. 393 "... under [D25] set by patch 0024 (...); PREFLIGHT re-asserts on the
  shipped tree, asserted at PREFLIGHT [A21])"; l. 1543 "Set by patch 0024 (...) ...: patch 0024
  sets it, and PREFLIGHT asserts ..."; l. 1712 "patch 0024 sets it (`quant.i_decay_speed:
  0.001`; set by patch 0024 (...)". Not wrong; one clause per site suffices.
- **C6.** FP32-E epoch-500 rule (l. 1339-1340) sends the arm to Kai only if no seed passes (c).
  Given (c) is near-trivial for an unconstrained model (threshold about 0.21, l. 828), consider
  also reporting FP32-E's interim validation accuracy against the archived FP32 sizing value
  as a sanity line (labelled, validation, never quoted), so that a broken FP32 path is seen
  before 7,000 epochs rather than at B3's L > 0 anomaly.

## Competing-group question

A group running the same comparison next month would have an FP32 reference with a stated
closeness margin, or would report the gap without calling it "close" (B2), and a measured
timing for every packing they run (B1). Both are text fixes before any number exists. Nothing
else is missing that STUDY does not already name as a limitation or a Kai row.

## Motivated-reasoning check

Two of the new FP32-E sentences lean thesis-favourable by default. The claim string "is close"
has no rule that can refute it (B2). The L > 0 branch wording ("no cost resolved") turns a
likely pipeline anomaly into a favourable-sounding sentence (B3). The K=7 exception saves pod
count at the cost of an unmeasured wave-1 timing change (B1). None changes a wave-1 config,
seed, target or selection, and none needs a number to fix.
