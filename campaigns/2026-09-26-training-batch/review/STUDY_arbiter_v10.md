# STUDY arbiter v10: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-28 (about 23:30Z). Artifact `STUDY.md` at HEAD 22e8692 (2,658 lines); all line numbers here are at HEAD. The working
tree now carries an uncommitted ml-engineer text pass (+12 lines after l. 383, per-arm memory 6 → 8 GiB;
operational, not reviewed here, not a finding per the orchestrator), so working-tree lines after l. 383
are HEAD + 12. Reviews v10: `STUDY_physics_v10.md` (A1; B1, B2;
C1-C5), `STUDY_critical_v10.md` (no A; B1, B2; C1-C5), `STUDY_constructive_v10.md` (no A; B1-B3;
C1-C4). Validators `STUDY_validators_v10.txt`: `prose_lint` score 0, no line marked A. STUDY has no
figures, so there is no plot-validator file. Earlier arbiter: `STUDY_arbiter_v9.md`. Also read:
`docs/methodology/06-review.md` §6.1-6.8; `RUN.md` (the ratio section, committed since in a46bdbf:
the section "In-training vs traced EBOPs (regime-A W&B, for STUDY v10) — 2026-09-28");
`code/tree/campaigns/chang0926/packs_meta.json`; hgq2 0.1.9 `hgq/utils/sugar/beta_pid.py` (uv cache).
Iteration **10**: the §6.5 ESCALATE tier. Arbiter v9 scoped v10 to landing and routed any content-level
A or B arising from the amendments to Kai.

## Independent checks made by the arbiter

- **Landing (arbiter v9 fixes 1-4).** The core paragraph is at l. 1438-1512 with slots T, C and P filled
  and cited (read in full; e.g. slot T `ablation.py:483-489`, slot P `:492-495`, `:783`, `:861-871`).
  Fix 2 at l. 1721; fix 3 at l. 831; fix 4a at l. 1227 ("at or below about 0.86 pt (1.0 / 1.16)");
  fix 1(c) prior labels at l. 1408, 1410, 1447, 1545, 1848, 1892-1893, 2470; fix 1(h) closures at
  l. 1844, 1879, 1890, 2481. This agrees with the critical and constructive landing tables. No landing
  defect.
- **The in-training/traced ratio is now measured, under regime A, far from target** (RUN.md, section
  above; telemetry, not a result). Median in-training / traced [p10, p90]: A-s1 1.0772 [1.0426,
  1.1049], A-s2 1.0739, D-s1 1.0717, E1-s1 1.0920, C′-s1 1.0000 (SAT, no WRAP). A-s1 falls
  1.0837 → 1.0534 over the run. No run entered ±20 % of its target (closest traced: A-s1 431,605,
  +23.3 % over 350k). Regime A resets every epoch, so this is one epoch of drift; regime B allows up
  to nine. **The measured sign is opposite to physics A1's code-derived expectation** (physics:
  in-training ≤ traced). A plausible reading, not a measurement: while EBOPs fall, the in-training
  `i` lags (it can decay at most 0.2 bits per epoch, l. 2116) and stays above the end-of-epoch
  full-split range; near a stationary target that lag vanishes and the per-batch-max effect physics
  named may dominate. The near-target sign under regime B is therefore unknown.
- **Stationary point, arithmetic** (constructive B1's T·r^−0.9 with r = in-training / traced; hgq2
  `PID.__call__` integrates with no anti-windup, `beta_pid.py:29`; β is clamped after, `:158`). At
  the regime-A medians, traced EBOPs would settle near A-s1 327,342, A-s2 328,247, D-s1 328,853,
  E1-s1 323,346: 21-27k under 350k, i.e. 12-15 % of the A/D headroom (178,474) and 10 % of E1's
  (264,237). The arm-to-arm spread (E1 against D) is about 5.5k EBOPs, 1.6 % of the target. So the
  mismatch is real and arm-dependent: confound 10 ("same rule in every arm") holds for the rule, not
  for the effective traced budget.
- **Case 5, not raised by any reviewer: A07-350 wind-up.** A07-350's 0-bit floor is 343,053 traced
  (l. 1663; headroom 6,947 at l. 1617-1618). The outcome depends on where the in-training excess
  lives, which nothing measured so far resolves. Reading 1 (the excess scales the whole total, floor
  included, i.e. the `i` drift touches the datalane quantizers that make up the floor): at A's 1.077
  the in-training value at the floor is about 369,468, above 350k; on 9 of 10 epochs the PID sees an
  over-target error no width change can remove, the integral winds up without bound (no anti-windup,
  `beta_pid.py:29`), β goes to its maximum, and the run sits at its floor and can fail (b) or read as
  "A07-350 cannot hold 350k". Reading 2 (the excess lives only in the learned-width part above the
  floor, about 33k of A's roughly 260k above 171,526, so about 13 %): A07's learned-width part is at
  most 6,947, its excess under 1k, the in-training value at the floor about 344k, and there is no
  wind-up. The range is "no wind-up" to "unbounded wind-up"; r for any A07 arm is unmeasured
  (A07-350-s1 went out of memory under regime A; C′ is SAT). Under reading 1 it bites at the K=3 pod's
  gating readout: `packs_meta.json` `wait_for_k3_readout: [7, 8, 9, 10]`, the four A07 production
  pods. That makes the attribution rule time-critical for the K=3 pod's epoch-500 readout.
- **Constructive B2 fact** (no anti-windup): confirmed, `beta_pid.py:27-32` (`self.integral += err`),
  clamp at `:158` after the PID output.
- **Critical B1 / constructive B3 fact** (A07 pods at K=4, timed only at K=3): confirmed,
  `packs_meta.json` `arms_per_pack` [5, 5, 5, 5, 4 × 9]; STUDY l. 1508-1512 names no pod class.
- **Physics B1 fact** (FP32-E candidates): confirmed at l. 695-697 ("all 7,000 epochs that meet
  (c)") against 701 traced candidates for A (l. 1451); the package label (l. 780) and confound
  12 (l. 843-847) still say "the [D20] per-epoch reset trace / dynamics" and name no count.
- **Pilot-b state.** RUN.md records both Jobs applied 2026-09-28T23:05:57Z and both pods **Pending**
  as of 23:13Z; it does not record either pod Running. Read-only `kubectl -n cms-ml get` by the
  arbiter at about 23:38Z: `kai-chang0926-pilotb3-42abed-0-c7tg4` **Running** on
  `gpu-16.nrp.mghpcc.org` (not c6017), Job limit 18Gi, `BNJ_RSS_GATE_LIMIT_MB=6144`;
  `kai-chang0926-pilotb5-42abed-0-v2nll` **Pending** (Job limit 30Gi, 6144). RUN.md must record the
  K=3 pod's node, `FINGERPRINT 11559681 expected 11559681`, `ARM_STARTED` per arm and the epoch-10/20
  RSS reads at about +27 and +52 min after `ARM_STARTED` (RUN.md l. 596-603; manual, the only
  protection before the in-code gate at epoch 105).
- **Memory limit of the running pods (operational, not a STUDY finding at HEAD).** The applied Jobs
  come from the 4dbf6b6 manifests (6,144 MiB gate; 18Gi / 30Gi, i.e. 6 GiB per arm). c7bae4a
  (2026-09-28T16:36-07:00, 30 min after apply) regenerated the manifests at 8,192 MiB, 24Gi / 40Gi,
  "not applied". The uncommitted STUDY text pass says `BNJ_RSS_GATE_LIMIT_MB=8192` "on both pilot-b
  pods" and moves the manual epoch-10/20 threshold to 8,192 MiB. For the running pods that is false,
  and a manual watch at 8,192 would pass an arm whose projection lies between 6,144 and 8,192 MiB,
  which the running pod's in-code gate and container limit reject. Committed as written, this
  becomes a finding (stated pod parameter not equal to the running pod) at v11.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Regime B's PID holds in-training EBOPs at target on 9 of 10 epochs while feasibility and selection read traced EBOPs; no pre-registered rule says how a resulting shift in k, feasibility or budget use is read; the effective traced target differs by arm | phys A1; crit B2; constr B1 | A; B; B | **A → Kai (K1)** | Case 2. The RUN.md pull contradicts physics' predicted sign, not the finding: r is measured at 4-11 % and arm-dependent (E1 1.092, A 1.074-1.077, D 1.072), so arms compared at "iso-EBOPs" (A − NB, the one thesis-bearing gap; A − D; the E/A07 ladders) sit at different effective traced budgets. That is a matched-arms defect (§6.3 items 1, 4), not only an attribution gap. The measurement is regime A, one epoch of drift, far from target, so it cannot settle the regime-B near-target sign; it is not evidence against the finding. Arising from amendment content (96b95f2), so per arbiter v9 it goes to Kai |
| 2 | A07-350: if the in-training excess scales the floor (reading 1), the in-training floor sits above 350k, the PID winds up and a false "A07-350 cannot hold 350k" gates packs 7-10; if it lives only above the floor (reading 2), no wind-up | arbiter (case 5) | – | **A (part of K1)** | Arithmetic above; r at A07 unmeasured, so neither reading can be excluded. The K=3 pod's epoch-500 readout is where reading 1 would bite first |
| 3 | 14-day rule does not say whose s_e decides; A07 pods run at K=4, timed only at K=3; A07 arithmetic (C′ 293.6 s regime A → about 176-183 s regime B, 14.3-14.8 d) is above the 172.8 s bound | crit B1; constr B3 | B; B | **B, fixer** | Case 1. Underspecification of the fix-1(a) text; the "exceeds 14 d → Kai" branch is already registered (l. 1510-1512). No new design choice. Fix F1 |
| 4 | Arm-C "constraint slack" iff β at floor on the last 10 traced epochs can label a run whose traced EBOPs exceed 5M (integral wound up) | constr B2 | B | **B, fixer** | Case 3; fact verified (`beta_pid.py:29`, `:158`). Descriptive label, tightened with a quantity already computed ((i)); no Kai choice. Fix F2 |
| 5 | FP32-E selects over 7,000 epochs, A over 701 traced epochs; the package label predates regime B | phys B1 | B | **B: label → fixer (F3); grid → Kai (K2)** | Case 3. Naming the asymmetry is text. Restricting FP32-E to the slot-T indices changes a registered selection rule (pre-data, dated amendment), which after an amendment is Kai's |
| 6 | A − NB is expected uninformative at 8 pairs (detectable only if sd_diff ≤ about 0.86 pt; N=64 W1A8 sd 3.145 pt); the extra-pair cap is open | phys B2 | B | **B: text → fixer (F4); cap → Kai (K3)** | Case 3. Numbers recomputed by physics and critical (0.862; 3.145). The row (l. 2468) blocks only the extra pairs; the cap is Kai's number |
| 7 | The regime A/B epoch-500 comparison is conditional on a resume of a leaking bundle that nobody plans; a matched traced-epoch table from regime-A W&B history (epochs 10…120) replaces most of it at no GPU cost | constr C1; crit B2 (bullet 3) | C; within B | **C, required (F5)** | It is the only direct regime evidence for #1; under an hour; §6.5.1 forbids dismissing it |
| 8 | Change-log shas missing (96b95f2, cc36f7c); l. 845 "per-epoch reset dynamics"; Pods paragraph stale sentences (lost pod costs one seed of every arm; R crosses GPU type); RSS gate mixed indexing | crit C1-C4; phys C3; constr C2 | C | **C, required (F6)** | Stale text of the kind that becomes a REPORT sentence; one-line edits |
| 9 | stdout `in_training_ebops` prints `saved_ebops` (int, filtered), W&B prints `model_ebops` (float) | crit C5 | C | **C, ml-engineer, next bundle** | Not a STUDY edit. The RUN.md ratio was read from W&B, so it is unaffected |
| 10 | Budget claim is a screen by construction; "upper estimate" wording; operating point at mistag 1e-2 beside A and A − R; β-sampling note; consolidation | phys C1, C2, C4, C5; constr C3, C4 | C | C (optional) | REPORT notes or presentation; constr C3's clause folds into F2 if cheap |

## Earlier A and B findings (arbiter v9), by name

| v9 # | finding | status | evidence at HEAD |
| --- | --- | --- | --- |
| 1 | Canary fired the [D15] "> 14 d" branch; STUDY still said "fits 14 days" | **resolved** | l. 1438-1447 (measured 219.65 / 219.37 / 215.16 s, 17.8 / 17.8 / 17.4 d; branch fired); prior labels at l. 1408, 1410, 1447, 1545, 1848, 2470 |
| 2 | Regime-B amendment at every [D20] / Selection / s_e / canary / readout / resume / confound-10 / fidelity / PID site | **resolved** (content defect raised as #1 here) | l. 1438-1512 slots T, C, P filled and cited to 42abed4b lines, which the critical reviewer sha-matched to the bundle; committed 96b95f2 (2026-09-27 15:08 PDT) before pilot-b apply (2026-09-28T23:05:57Z) |
| 3 | Canary loss / trace-share sources | **resolved** | l. 1721 "Sources (arbiter v9 fix 2) ..." |
| 4 | Confound 9 "same GPU at seed s" | **resolved** | l. 831 (arbiter v9 fix 3); remaining stale Pods sentences are C (#8) |
| 5 | K=7 rules and second-wave K=6 plan | **resolved** | l. 1844, 1879, 1890, 2481 "(closed by Kai's K=5 packing ...)" |

## Regression triggers (§6.7), checked independently

- Selection on held-out, or changed after results: **not met**. No result exists; pilot-b is validation
  only and selects nothing. K2 (FP32-E grid) is pre-data and would enter as a dated amendment.
- Val/ROC gap > 0.01; single-seed headline; cross-N series; gap < sd at < 3 seeds: **not met** (no
  results).
- Reload > 1e-7 / TF32: **not met**.
- EBOPs not remeasured / final-epoch cost mixed with best-checkpoint AUC: **not met**. Certification
  retrace unchanged (l. 1502-1503); only traced epochs are selectable (l. 1464-1466).
- Binary > 2 values; DSP / C-sim / C-synth; per-class hidden; byte-identical arms: **not applicable**.
- **Failed validation accepted without remediation: not met.** The regime-A leak stop has documented
  remediation (patch 0031 `ValidationReloader`, `tests/test_memory_leak_fix.py`, the RSS gates,
  `review/INCIDENT_stall_20260928.md`). The canary's 14-day fail is remediated by the registered branch.
- **[D] replaced without a dated amendment: not met.** The regime-B amendment was committed in 96b95f2
  about 32 h before pilot-b was applied (critical v10). If Kai picks K1(c) or (d), it enters as a
  dated amendment before any affected pod is applied.
- Suspiciously good: none.

**No trigger met.**

## Validation target (§6.8) and competing group

No arm is bound at STUDY; the targets (79.4 / 78.4 / 79.8 / 77.9 %, Sun et al. and the archived round
14) are named and labelled single-model. A competing group running a sparse-trace PID would publish
the controller's input quantity and its measured ratio to the feasibility quantity per arm, and would
not compare arms at nominally equal budgets whose effective budgets differ by 1-2 %. That is #1.

## Disputed facts for the investigator

None that block. The near-target, regime-B value of r per arm (A, D, E1, A07-350, C) is **unmeasured,
not disputed**; pilot-b measures it at its traced epochs. The regime-A value is in RUN.md.

## Dismissals

None.

## Motivated-reasoning check

- The new measurement invites the reading "feasibility gets easier, so the risk is gone". It does not
  follow: the measurement is far from target and one epoch of drift; if r stays above 1, about 12-15 %
  of the A/D headroom goes unused (against the thesis, and not in any uncertainty), arms sit at
  different effective budgets, and A07-350 can wind up at its floor. If r falls below 1 near target,
  physics' original direction returns. Either sign needs the rule.
- The regime comparison registered at v9 as the answer to this risk is now conditional on a resume of
  a leaking bundle. #7 replaces it with data that already exist.

## What Kai must decide (ESCALATE)

**K1. The PID input under regime B (#1, #2).** Nothing here requires stopping the running K=3 pod or
the Pending K=5 pod under any option: pilot-b is validation only, selects nothing, and is the only
source of r under regime B near target, of s_e at K=3/K=5 and of A07 peak memory. Production cannot
launch before the epoch-500 readout in any case, so options (a) and (b) cost no calendar time.

- **(a) Descriptive only.** Register the readout (per run: median r over traced epochs 100-500, the
  implied traced offset 350k × (1 − r^−0.9), and its share of the arm's headroom) and relabel a low k
  or an A07-350 floor sit as "setpoint-quantity mismatch (regime B)". Running pilot: unaffected.
  Weakness: it names the problem and never fixes it; arms at unequal effective budgets would go to
  production.
- **(b) Pre-registered threshold, back to Kai at the epoch-500 readout. Recommended default.** The
  readout of (a), plus a threshold fixed now: if for any run the implied traced offset exceeds 10 % of
  that arm's headroom (A/D 17,847; E1 26,424; A07-350 695), or the per-arm median r differ by more
  than 0.02 between any two arms of an iso-EBOPs comparison (A, D, B, F, A07-350, C), or an A07 run's
  in-training EBOPs stays above 350k on every untraced epoch of the last cycle while its traced EBOPs
  sit within 1 % of its floor (the wind-up of case 5, reading 1; under reading 2 this clause does not
  fire), then production waits for Kai with the remedies (c) and (d) named, and
  a failed A rule or A07-350-s1 rule is reported as "not attributable (regime-B PID input)" beside the
  registered options. Be aware: at the regime-A medians the headroom and the arm-difference tests
  would already fire (offset 12-15 % of headroom; E1 − D 0.020), so (b) in practice means "measure r
  near target under regime B, then choose (c) or (d) at epoch 500". Running pilot: unaffected; it
  produces the numbers (b) reads. Add: ml-engineer prepares the (c) patch in parallel, unapplied, so a
  choice at epoch 500 does not start from zero.
- **(c) PID reads traced EBOPs only and holds β between traces.** Removes the mismatch at its source.
  It is not a free fix: p 1.0 and i 0.05 were set for per-epoch updates; ten times fewer updates is a
  different controller (50 updates per 500-epoch cycle) that needs its own pilot. Cost: code patch,
  CPU gate, re-freeze, PREFLIGHT addendum, new pilot: about 1-2 days. Running pilot: keep it running
  (timing, memory and r still stand), but its checkpoints cannot resume into production
  (`code_sha256` changes) and its A-rule and A07-350-s1 readouts are under a superseded controller
  and would have to be re-read under (c).
- **(d) Keep the 9:1 input and scale the PID setpoint by the measured r** (feasibility stays at 350k
  traced). Config-only, but `config_sha256` changes, so pilot checkpoints cannot resume; it bakes in
  a ratio measured on pilot seeds, and an arm-specific r means an arm-specific setpoint, which must be
  written as part of each arm's package.

**K2. FP32-E candidate grid (#5).** (i) Restrict FP32-E selection to the slot-T epoch indices
(e = 0, (e + 1) % 10 == 0, last), so FP32-E and A select over the same 701 epochs. **Default.** Cost:
one config or analysis change before any FP32-E number; FP32-E is wave 2. (ii) Keep all 7,000 and name
"7,000 against 701 candidate epochs" in the package. Running pilot: unaffected either way.

**K3. Extra A/NB pair cap (#6).** A number (row l. 2468), or keep the row open with its registered
deadline (before the wave-2 epoch-500 readout). Default: set it now, so REPORT can print the
resolvable gap at the cap. Running pilot: unaffected.

## Fixer items (no Kai needed; apply now, before the pilot's epoch-500 readout)

- **F1 (#3).** After l. 1512 add: "T_run is evaluated per production pod class as the largest T_run of
  its arms, and the wave's T_run is the largest over its pod classes: E pods (K=5) from the K=5
  pilot pod's s_e; A07 pods (C, A07-350; K=4 in `packs_meta.json`) from an s_e measured at their
  production K over the Symbols window, or at K=3 if they are packed at K=3. The K=3 pod's s_e is
  not taken for K=4. If the A07 pods exceed 14 d while the E pods pass, production of the A07 pods
  waits for Kai (K=3 or K=2 on more pods, or stop the A07 arms)." Print beside the 136.5 s E
  arithmetic the A07 arithmetic from RUN.md (C′-s1, regime A: 163.3 + 130.4 / 10 ≈ 176.3 s, about
  14.3 d), labelled a projection with constr B3's caveats (five epochs, SAT, K=6).
- **F2 (#4).** In the arm-C rule (l. 1675): "constraint slack" iff (iii) holds **and** no traced
  epoch in the same last-10 window exceeds 5,000,000; if (iii) holds and m > 0 of them exceed it,
  label the run "β at floor (integral wound up), 5M exceeded on m of 10". Same for C′. Add
  "(β at a traced epoch was set at that epoch's `on_epoch_begin` from the preceding epoch's EBOPs,
  an in-training value under regime B)".
- **F3 (#5, label half).** At l. 780 and l. 843-847 replace "the [D20] per-epoch reset trace /
  dynamics" with "the [D20] reset trace every 10 epochs (regime B)" and name "selection over 7,000
  candidate epochs against 701 traced (regime B)" in the package, unless and until Kai picks K2(i),
  in which case write the restriction as a dated amendment instead.
- **F4 (#6, text half).** Every A − NB statement registered for REPORT leads with the resolvable gap
  (the 80 %-power detectable gap at the realised n) in its first sentence.
- **F5 (#7).** Register in the pilot-b readout a descriptive, zero-GPU table: A-s1, A-s2, D-s1 at
  matched traced epochs 10, 20, ..., 120 (one-based) under regime A (W&B, RUN.md) and regime B
  (pilot-b): traced EBOPs, in-training EBOPs, r, β, feasible yes / no. Selects nothing.
- **F6 (#8).** Change-log: "(line numbers at 96b95f2)" in the v9 entry, "(line numbers at cc36f7c)"
  in the cc36f7c entry. Delete the two stale Pods sentences at l. 1518-1520 ("A lost pod costs ...";
  "R against A or D crosses GPU type") or move the "prior plan" parenthetical directly after the first
  sentence; write "K=5 for the E arms, K=4 for the A07 pairs and R (13 pods)". RSS gate l. 1738-1740:
  "zero-based process epochs 5-104; verdict at the end of the 105th process epoch".
- **F7 (#1, the part that does not wait for Kai).** In slot P (3), after "reports their ratio per
  run", add the regime-A measurement with its label: "Measured under regime A (one epoch of drift,
  all runs 23-36 % above target; RUN.md, 'In-training vs traced EBOPs', telemetry): in-training /
  traced median 1.072-1.092 for A, D, E1 and 1.000 for C′. At a constant ratio r the integral term
  settles traced EBOPs near T · r^−0.9 (arithmetic, hgq2 0.1.9 `PID.__call__`, p 1, i 0.05, no
  anti-windup). The near-target regime-B value is unmeasured." Kai's K1 answer is then written in as
  a dated amendment by the fixer.

Orchestrator: (1) the ratio pull is committed (a46bdbf); commit any remaining RUN.md edits, and record
in RUN.md the K=3 pod's Running state, node, fingerprint, `ARM_STARTED` and RSS reads. (2) Before
committing the 8 GiB STUDY text pass, make it distinguish "running pilot-b pods (applied from 4dbf6b6):
6,144 MiB gate, 6 GiB per arm; the manual epoch-10/20 rule for them stays at 6,144" from "fallback,
readout and production manifests (c7bae4a): 8,192 MiB", unless the pilot-b Jobs are re-applied.

## Verdict

**ESCALATE** (STUDY panel, iteration 10, the §6.5 cap). One content-level A (#1 with #2, the regime-B
PID input) and four B (#3-#6), all arising from the amendments' own content. Kai decides K1 (default
(b), with ml-engineer preparing (c) unapplied), K2 (default (i)) and K3 (default: set the cap now).
The fixer applies F1-F7 without waiting. After Kai answers, the fixer writes his choices as dated
amendments and v11 is a landing check of F1-F7 and K1-K3 only. No finding requires stopping the
running K=3 pod (Running on gpu-16.nrp.mghpcc.org) or the Pending K=5 pod. A STUDY PASS still does not launch production by itself (arbiter
v9, "Scope of v10").
