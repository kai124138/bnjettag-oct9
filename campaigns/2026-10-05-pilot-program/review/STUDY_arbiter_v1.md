STUDY: ITERATE. R1 launch: ITERATE (not launchable; PREFLIGHT A1-A3 open). No ESCALATE: iteration 1, every A finding has a pre-data fix of at most 2.5 agent-h.

# STUDY arbiter v1: pilot program, 2026-10-05

Arbiter, opus (06-review §6.5, §6.5.1). Written 2026-10-05 ~14:35 JST.

Inputs:
- `STUDY.md`, sha256 `27d43c637f456432d5a27a1e1b79d630d097d96c4eaf56041841b2e691640e86` (recomputed).
- `PROGRAM.json`, sha256 `5bdad964…b3c3`, mtime 10:47. This is the snapshot the critical reviewer read. An
  ml-engineer is editing it, and no save had landed when this file was written.
- `protocol-r1.json`.
- `PREFLIGHT.md`.
- `review/STUDY_{physics,critical,constructive}_v1.md` and `review/PREFLIGHT_critical_v1.md`.

## Independent checks (by the arbiter, read-only)

| claim | check | result |
| --- | --- | --- |
| The bundle holds only R1 configs (crit A1, cons A1) | `code/tree/campaigns/pilot1005/index.json`: `round` R1, `count` 23, the round Counter is {R1: 23}. `configs/` has 23 files. `generate.py:38` sets `ROUND = 'R1'`. `readout_pilot.py:230-233` errors "no index rows for round" | **confirmed** |
| The certify import fails (PREFLIGHT A1) | `certify_ebops.py:45-46` inserts only HERE and the tree root into `sys.path`. `:120` runs `from evaluate_roc import targets` | **confirmed** (code read; the reviewer's repro was not rerun) |
| The 38.8 s basis (crit B6) | gpu-benchmark `VERIFY.md:109`, row RTX 3090 / klow / A07 / K = 1, n = 1 × 20 epochs, verdict "in T". The row gives s/epoch 30.85 and "total elapsed s per run-epoch" 38.8 (header `VERIFY.md:96`). The total-elapsed column covers a 20-epoch run, so startup is spread over only 20 epochs. At 500 or 7,000 epochs the true rate lies between 30.85 and 38.8. E at K = 1 on the 3090 is unmeasured | **confirmed as a bound, not a point rate** |
| Production spend arithmetic | 7,000 × 38.8 s = 75.44 h per pod; × 16 = 1,207 GPU-h; + 138 + 60 + 18 = 1,423. At 30.85 s the production figure is 959.8 | **confirmed** |
| CP bounds | 3/3 lower = 0.025^(1/3) = 0.292; 0/2 upper = 1 − 0.025^(1/2) = 0.842 | **confirmed** |
| Matched-headroom H3 budget | 269,830 + 178,474 = 448,304. At 450k the headroom is 180,170 | **confirmed** (arithmetic on the static trace, not a result) |
| CPU gate state | `kubectl get job -n cms-ml`: `kai-pilot1005-cpugate-b3fb22` Running, 0/1, age 14m at the time of the check | running |

Jev `jev_triage_review`, audit `jv-79269cf45d394d0e858e9064ce9f1b5c` (jev-1.13.0). This is advisory and is not a category.

Jev's labels are its own taxonomy:
- `likely_bug`: crit-A1 (0.96), pre-A1 (0.99), crit-B6 (0.77), phys-A1 (0.36), crit-A2 (0.34), cons-A1 (0.55), pre-A2 (0.20).
- `insufficient_evidence`: phys-A2 (0.71), phys-A3 (0.78), cons-A3 (0.31), cons-A4 (0.41), pre-A3 (0.64).
- `maintainability`: cons-A2 (0.89).

Where Jev reads a reviewer A as `insufficient_evidence` or `maintainability`, the A still stands, for two reasons:
- The STUDY text is the evidence. §9 lets Prec auto-fire at any r_rec ≤ 5M (D6, confidence LOW). The §9 and §5 floor of 0.50 cites only internal pilots (STUDY:168-171, 240-241). STUDY:5 says "not reviewed".
- Nothing independent refutes these findings (06-review §6.5.1).

## Rulings on every A finding (all stand; none dismissed)

| finding | ruling | fix (number in the list below) |
| --- | --- | --- |
| phys A1: selection seeds reused as confirmation seeds | stands, A | F6c |
| phys A2: Prec can auto-launch at up to 5M | stands, A | F6d |
| phys A3: the 0.50 floor has no external anchor | stands, A | F6d, F6e |
| crit A1: R2/R3 configs are absent, and §12 stops the program on a new sha | stands, A | F6a + F9 |
| crit A2: the production NB config is undefined, and A − NB / H5 are unmatched | stands, A | F6b |
| cons A1: make R2/R3 reachable | stands, A. Closed by the same route as crit A1 | F6a + F9 |
| cons A2: descriptive trajectory table | stands, A | F5 |
| cons A3: a26 on `model_unconstrained.keras` | stands, A | F5 |
| cons A4: unconstrained E positive control as the 24th pod | stands, A | F2 (fallback in F2 note) |
| PREFLIGHT A1: readout import | stands, A | F3 |
| PREFLIGHT A2: no spend bound | stands, A | F4 |
| PREFLIGHT A3: STUDY unreviewed | stands, A. Closed only by a STUDY arbiter PASS at v2 | F10 |

## Consolidated fix list (ordered by critical path)

"Rebuild" means a new bundle sha and a CPU-gate rerun. Agent-hours (ah) are this arbiter's estimates.

| # | fix | owner | rebuild | cost | closes |
| --- | --- | --- | --- | --- | --- |
| F1 | Ask Kai about D3 now, w100 or w150 (see K1). The answer is needed only before the bundle freeze in F2. If no answer is recorded by then, F2 builds w150 as registered | orchestrator | — | 0.1 | PREFLIGHT B5, cons B3 |
| F2 | **R1 config change, then rebuild.** (i) Replace `A07-350k-C` with `A350-C-qkv1-450k`, E, 450k, (c), w1, s1 (headroom 180,170 ≈ A350-C's 178,474). (ii) Add `E-unc-C` s1 (E, (c), w1, PID target ≥ init or EBOPs off) as the 24th pod, but only if `generate.py` can express it as config alone. (iii) If K1 says w100, change the two w150 configs to w100. (iv) Regenerate with `campaign.production: false`. Then rebuild the tarball, ConfigMap and 25+ handoffs, run cpu_gate locally, and run `check_a_unchanged` on the final tree with A-s2 and C-s1 added. Training code stays byte-equal to b3fb22c8 | ml-engineer | **yes** | 1.5 | cons A4, cons B1, phys B5, crit B2 (enables), cons B3, PREFLIGHT C1, B3 |
| F3 | Readout handoff: `PYTHONPATH=/work/code:/work/code/campaigns/chang0926` (manifest only). Then run a **CPU dry run of the whole readout chain** (a26 → certify → monitor_p → readout_pilot) on synthetic or 3-epoch `stop_after` run dirs for NB, qkv1 and noC. Put the log in `evidence/` | ml-engineer | no | 1.0 | PREFLIGHT A1 |
| F4 | Pod-level `activeDeadlineSeconds` = 6 h on every GPU Job, plus a `podFailurePolicy` FailIndex for deadline-exceeded and the RSS-gate exit. Record the arithmetic in PREFLIGHT §3: 24 × 6 h = 144 GPU-h, with a retry only for non-deadline infrastructure failures, each counted against the cap. 500 × 38.8 s = 5.39 h fits inside 6 h | ml-engineer (freeze_p.py) | no | 0.75 | PREFLIGHT A2, crit B6 (R1 part) |
| F5 | Add `readout_diag.json`, descriptive only and never a rule input. It holds cons A2 items 1-6 (t_uniform taken from `widths` with Q OR K at 0 bits, t_budget, site order, cost split, controller error, NB `weight_bits_mean`). It also holds a26 on `epoch-0500/model_unconstrained.keras` for every E row and A07-5M, and a26 plus val acc on the epoch-500 snapshot (`model_last` or equivalent) for every row. Implement it as a stdlib script in the readout manifest, using a26 already in the bundle | ml-engineer | no | 1.5 | cons A2, cons A3, crit B5 (first part), phys B6 (first_feasible_epoch) |
| F6 | **STUDY amendment [A3], pre-data**, sub-items a-e below | experiment-designer | no | 2.5 | see a-e |
| F6a | §7, §12, frontmatter. "One bundle" becomes "one training-code tree". R2/R3 bundles must be byte-equal to the R1 bundle outside `campaigns/pilot1005/{configs,packs,index.json,config_map.json,r1_packs.json}`, checked by a file-by-file diff. They are generated by the same `generate.py` with only round, seed, budget and arm changed, built and CPU-gated **before the R1 readout exists** (F9). Any other diff stops the program | | | | crit A1, cons A1 (ii) |
| F6b | §9. NB production = V_bin's configuration with only `quant.weight` changed. P350 qualifies only when V_bin = A350-C. Any other V_bin goes to Kai with the readout. H5 at R2 = NB350-C vs A350-C at matched seeds | | | | crit A2, B7 D-5 |
| F6c | §9. A P350 or Prec candidate is "qualified" only with ≥ 3 healthy seeds per production arm **that were not used to choose W or V_bin**. Otherwise it is reported as unqualified | | | | phys A1, crit B5 (n = 3 part) |
| F6d | §9 retitled "Production candidate (Kai decides)". The rule computes and qualifies the candidate, but nothing auto-fires. Prec always stops for Kai, with no r_rec ceiling needed, since Kai rules. The 0.50 floor is stated as internal-only and not a physics reference. Add a pre-registered production early stop: a readout at production epoch 500 with the same health rule stops both Jobs if fewer than 6/8 seeds per arm are healthy. Add PROGRAM's production-PREFLIGHT PASS to the guards. This needs K3 | | | | phys A2, phys A3 (partly), crit B5, crit C4, B7 D-4 |
| F6e | §5 and §9: one sentence saying that no external 350k reference is in hand (Chang/Sun at 350k on this split and N was not located), so the floor is internal. The Kai gate in F6d carries the risk. A physics-researcher lookup (~1 ah) is optional before production, not before R1 | | | | phys A3 |
| F6f | Text only, in this order: crit B1 (§5 definition verbatim at STUDY:26-27 and :183; the acc band (0.211, 0.50) with entropy ≥ 0.95 reads H2 "inconclusive"); crit B2 and cons B2 (strike STUDY:91-92; qkv1@350k failing reads "inconclusive (headroom-confounded)", and H3 can be refuted only by qkv1-450k failing while A350-C also fails, read as a 1-seed lead); crit B3 (no healthy A07 rung = beyond 5M); crit B4 (0/n vs 0/n = no separation; drop "budget, not binary"); crit B6 (§11 basis = R1-measured wall time per epoch of the chosen arm × 7,000 × 16, and production deadline from the same figure); phys B2 (register H2′ whole-network starvation: E 750k / A07 2M; state absolute headroom as the variable); phys B3 and cons C2 (H2 in R1 is descriptive; r1 is a 1-seed locator); phys B4 (every R1 "supported" is a lead for R2); phys B7 (rename H5 "learned-width (prunable) weights"); phys B1 (state the padding mask and the entropy normaliser; the mean-pool control is deferred, see Deferred); cons B4 (A07-5M-s1 is the pipeline positive control, and if it is not healthy, stop); the new arms in §4 (qkv1-450k, E-unc, A07 ladder from 500k, 24 pods) and §11 R1 cap 144; crit C1-C7, phys C1-C5 (C3 related-work line; C4 one line), cons C3. Update `protocol-r1.json` and run `lab_check_protocol` | | | | listed |
| F7 | PROGRAM.json reconcile after F6 lands: crit B7 D-1 to D-6 (entropy-only stop before every derivation; `bundle_sha256`; amendments [A2] and [A3]; production goes to Kai; NB config; the 350k bracket naming), PREFLIGHT B1 and C2 (arm ids), the 24-arm R1, the A07 rungs without 350k, caps 144/60/18, and the A07-5M positive-control stop | ml-engineer (the current editor) | no | 1.0 | crit B7, PREFLIGHT B1, C2 |
| F8 | PREFLIGHT.md: fill §2a with logs (PREFLIGHT B2), fix the 47-node count (C3), correct dev/README A-unchanged (B3), add the F2 diff, F4 arithmetic and F3 dry run | ml-engineer | no | 0.5 | PREFLIGHT B2, B3, C3 |
| F9 | **During R1, before its readout:** generate every R2/R3 candidate config. That covers E rungs × seeds 2-4, the 6 variants × seeds 3-5, NB at each E rung above 350k × seeds 1-3, and NB with V_bin settings for the variants at seeds 1-3. Build them into a configs-only bundle, run the F6a byte-diff, run cpu_gate + pair_nb on the new configs, and get a solo PREFLIGHT review. This is off the critical path. It must finish before the R1 readout Job writes `readout.json`, so that the configs are pre-data | ml-engineer | configs-only bundle | 2.0 + gate | crit A1, cons A1 (complete) |
| F10 | Re-review: STUDY panel v2 (physics fresh; critical and arbiter receive this file), PREFLIGHT critical v2 on the F2-F5 diff, the CPU gate on the F2 bundle, then STUDY arbiter v2 and Kai's signature on PROGRAM.json | orchestrator | — | ~1.5 wall, parallel with the gate | PREFLIGHT A3 |

Critical path: F1 → F2 → gate rerun. F3, F4, F5 and F6 run in parallel with F2. F7 follows F6. F8 and F10 overlap the gate.

## Deferred or dismissed (each with a cost and a reason)

- **cons B5, epoch_observer entropy hook. Deferred.** Cost: ~2.5 ah (30 lines + test + a_unchanged evidence), a pytest-count change in `gate_check.py:32`, and a gate rerun.
  - It changes the training path, which would break F6a's byte-equal training code for R2/R3 unless it lands now, and that adds risk to the R1 freeze.
  - It does not change any R1 decision. F5 t_uniform covers the documented 0-bit cause exactly, and the epoch-500 snapshot entropy covers the end state.
  - Address it in the next code bundle after the program (production or later).
- **phys B1, no-attention (mean-pool) control. Deferred.** Cost: an architecture code path ~3-4 ah, a gate, and 1 pod. R1 has no free pod after F2(ii).
  - It reframes what H1-H5 explain, but it does not change which configuration is healthy, which is what R1 decides.
  - The text half (mask and normaliser) is adopted in F6f.
  - Register it as the first post-program follow-up.
- **phys B7 / cons C1, NB arm with 1-bit init. Deferred.** Cost: a b0 code path ~2 ah, a gate, and 2 pods. F5 item 6 quantifies the confound at no cost. It is the R3/post-program follow-up if H5 reads "NB ≤ binary".
- **phys B3, R2 bracket including the rung above r1. Not adopted as a rule.** Cost: +3-4 pods (≤ 24 GPU-h at the 6 h basis), over the R2 cap of 10. Making H2 descriptive in R1 (F6f) removes the over-claim. r_rec still needs 3/4 at a rung.
- **cons B2 rule variant, a guaranteed 3-seed H3 arm in R2. Not adopted.** Cost: 3 pods (18 GPU-h), over the R2 cap. The text half is adopted, and F2(i) gives a matched-headroom read at 1 seed.
- **cons A4 fallback.** If E-unc needs code rather than config, drop F2(ii). Cost of the code: ~1.5 ah + test. F5's a26 on `model_unconstrained.keras` then supplies the E entropy reference, which is opportunistic but free. Report which happened.

## Rebuild now vs no rebuild

**Recommendation: rebuild now (F2), and use option (a) for R2/R3 (F6a + F9).** Do not cancel the running b3fb22 gate. Its PASS keeps b3fb22c8 as a validated fallback if F2 fails its local checks.

Wall time to R1 launch, from ~14:35. These are the arbiter's estimates, not measurements:
- **No rebuild.** F3, F4, F5, F6 and F7 run in parallel (~2.5 h, set by the STUDY text and PROGRAM). Then panel v2, PREFLIGHT v2, arbiter v2 and the signature take ~1-1.5 h. The b3fb22 gate finishes inside that window. Launch is about 18:00-18:30.
- **Rebuild.** The same parallel work, with F2 (1.5 h) also on the ml-engineer track. The gate on the new bundle (1-1.5 h) overlaps the reviews. Launch is about 19:00-19:30.
- So the delay is about **1-1.5 h**, the length of one gate run. The STUDY v2 review and the signature are on both paths.

What the hour buys, with the R1 pods as R1 is now written:
- **A07-350k (1 pod, ~5.4 GPU-h)** has headroom 6,947. Every hypothesis predicts it unhealthy, so its information is near zero. As `A350-C-qkv1-450k` it becomes the only arm that can separate H3 from H2. STUDY §2 admits R1 "cannot tell them apart". Without it, H3 can only come out "supported" or "inconclusive".
- **w150 (2 pods)**: first feedback at epoch 160 leaves 340 epochs, against b5's 259-389 to first meet (a) (local, not quotable). The likely read is "inconclusive (time-limited)". w100 leaves 390.
- **E-unc (1 pod)** is the only measured E entropy reference. The entropy-only stop is the most likely way for the program to halt for Kai with no E calibration (PREFLIGHT B4).

In total, 3-4 of 24 pods move from near-zero information to informative, at 0 extra GPU-h beyond the E-unc pod (+6 GPU-h cap). The cost is about one gate length of wall time and ~1.5 ah. For a program whose next step is chosen from R1, that trade is worth it.

The no-rebuild route stays defensible if Kai rules speed over these arms (K1/K2 answered "keep"). In that case: F2 is skipped, crit B2's text ruling applies (qkv1 failure reads "inconclusive"), and F5 is the only E entropy reference.

## Needs Kai (one at a time, in this order)

- **K1. D3: w100 or w150?** Recommended default: **w100**, because the bundle is rebuilt anyway (STUDY D3's own default). This blocks only the F2 freeze. With no answer by then, w150 builds as registered.
- **K2. R1 = 24 pods with E-unc and qkv1-450k replacing A07-350k; R1 cap 138 → 144 GPU-h.** Recommended default: **approve**. The pilot caps become 144 + 60 + 18 = 222, inside the ~250 pilot allowance (decisions.md 2026-10-05 10:08 item 5). This needs Kai because it is spend beyond the signed plan (RULES §3).
- **K3. Production no longer auto-fires.** The rule qualifies a candidate, and Kai decides at the production gate (F6d). Recommended default: **approve**. Kai already re-signs the production IDs (STUDY:234), so the added delay is one reply. It closes phys A1-A3 without an external reference being found first.
- **K4. Spend ceiling, which is needed before production, not before R1.** At the measured bound, production is 1,207 GPU-h and the program 1,423, against ~1,200 approved. At 30.85 s it is 960 and 1,176. The true rate for E at K = 1 is unmeasured, and R1 measures it. Recommended default: **decide at the production gate on the R1-measured projection**. If the projection exceeds the remainder, raise the ceiling to it (≤ ~1,450 GPU-h) rather than shorten production below 7,000 epochs, because 7,000 pairs with the frozen training-batch.

## What v2 must show

For STUDY arbiter v2 / critical v2:
- each A above resolved by name with a line cite;
- F6a's byte-equal rule present in §7 and §12;
- PROGRAM.json reconciled (F7) and `lab_check_protocol` clean;
- the F3 dry-run log;
- the F4 arithmetic.

For PREFLIGHT v2: the F2 config diff limited to the three registered changes, and `GATE_RESULT PASS` on the new bundle.
