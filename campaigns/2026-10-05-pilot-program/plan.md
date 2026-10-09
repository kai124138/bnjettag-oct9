# plan.md: pilot program STUDY and PROGRAM.json (experiment-designer)

Written 2026-10-05 10:14 JST, before any pilot of this program exists.

## What will be written

1. `STUDY.md` (at most 250 lines): the question, H1-H5 with predictions, the fixed R1 table
   (19 arms), the R2 and R3 rules, the readout fields, `healthy`, the judging rules, the
   production trigger, stop rules, caps, the not-allowed list, and DECISION blocks.
2. `PROGRAM.json`: a dry-run draft, unsigned. `docs/infrastructure/autopilot.md` is absent at
   10:14 JST, so the fallback schema from the brief is used, and the file says so.
3. `protocol-r1.json`: the R1 protocol for `lab_check_protocol` (scope `screen`).
4. A JOURNAL line.

## Inputs read

- `docs/PILOT_PROGRAM.md`; `decisions.md` top entry; `local/2026-10-04-session/SESSION.md`;
  `docs/ROADMAP.md`.
- training-batch `STUDY.md`: :602-604 floors (E 171,526; A07 343,053), :749 NB, :995-1012
  feasibility (a)-(c), :1747-1765 K1.
- `PREFLIGHT.md:519`: threshold (c) 0.2109624456315518 (p_maj 0.20288709677419356, n_val 62,000).
- `READOUT_epoch500.md` (b3) and recovery `VERIFY.md` (b5): every 350k head is at entropy 1.000000.
  C-s1 at 5M has heads 0.622127, 0.913695, 0.543640, 0.880046 (READOUT_epoch500.md, table (2)).
- option-(c) tree: `static_floors.json` (E attn_narrow 368,134, attn_full 478,726; A07 605,197,
  801,805; synthetic CPU trace). In `ablation.py:535-541`, (c) requires epoch warmup-1 to be
  traced, so the warmup must be 1 or a multiple of 10. The config key is `train.ebops.pid.warmup`
  (currently 1).

## Design choices made (all flagged in STUDY "Where I am not sure")

- tau = 0.95 for the entropy part of `healthy`.
- `healthy` (not only feasible and non-degenerate) defines the recovery rung.
- The H4 warmups are 50 and 150, which (c) allows because epochs 49 and 149 are traced.
- The H3 budget is set by the H3 option's own static floor: E at 350k cannot hold 1-bit
  attention (368,134 > 350,000).
- The production accuracy floor is 0.50 validation accuracy at epoch 500.
- Production handoffs are filled after R2 by rule, and Kai re-signs that fill.
- Production uses seeds 1-8 (pairing with the frozen STUDY).

## Approaches tried and dropped

- Pre-building every production candidate handoff: rejected, because it gives 11 A handoffs plus
  7 NB handoffs, and NB code does not exist before R3.
- Judging H2 by headroom alone: it gives the same predicted A07 rung as the static-attention rule
  in the most likely case, so both are stated and only the rung pattern is judged.

## Jev checks (advisory; audit files are engineering records)

- `lab_check_protocol` on `protocol-r1.json` (19 arms, scope screen): structural_valid true, no
  findings, protocol_sha256 `d12afb42…f86b`, scientific_gate not_evaluated. It is not frozen:
  `lab_freeze_protocol` waits for STUDY PASS.
- `jev_check_methods` (audit `jv-f259c2bf757145f1a35d9f9eadc84d7c`, jev-1.13.0) on a summary
  paragraph:
  - selection: consistent (0.99, suggestion); uncertainty: consistent (0.75, review).
  - comparability: missing (0.39, review); provenance: missing (0.74, review);
    metrics: missing (0.67 p, review); authority: missing (0.75 p, review).
  - Reading: the "missing" verdicts are about the summary text, which left out the data sha, the
    approval reference, product and sha matching, and per-class AUC. STUDY.md §3, §10 and §12 and
    the frontmatter cover the first three. Per-class AUC belongs to production VERIFY; pilots
    record only the readout fields. The code sha is open until PREFLIGHT, and that stays visible.

## Amendment 2026-10-05 10:46 JST, pre-data (orchestrator)

- NB350-C and A350-C-qkv1 (seeds 1 and 2) are added to R1, which is now 23 pods. Floors come from
  `dev/README.md`: q,k,v at 1 bit gives 269,830; NB gives 171,526.
- R2 is now the bracket plus 3 seeds of W plus the other side at seed 3 (≤ 10 pods). R3 is NB@r_rec,
  run only if P350 fails (≤ 3 pods). Caps are 138, 60, 18 and 960, for a total of 1,176.
- D4 is now q,k,v at 1 bit.
- `lab_check_protocol` on the 23-arm `protocol-r1.json`: structural_valid true, no findings, sha
  `4a199581…b31c`. The pre-amendment STUDY is kept in a scratch copy only.

## Amendment 2026-10-05 14:2x JST, pre-data (experiment-designer; review/PREFLIGHT_critical_v1.md B4-B6, C1, C4, C5)

No pilot data exists (R1 not launched; only the CPU gate was submitted at 14:11).
- B4: an entropy-only failure (complete, feasible, non-degenerate, val acc >= 0.50, entropy >= 0.95)
  stops the program for Kai in every round; H2 is never refuted by such an E row. No healthy E
  (2-head) a26 reference exists locally: searched the b3 and recovery a26 outputs (every 2-head E
  head is at 1.000000, all 350k) and the lab tree for E checkpoints; the Delta canary E runs were
  350k configs on the PVC. No cluster job is run.
- B5: w150 kept; 340 epochs from first feedback (local cpu_gate evidence line 76); a w150 row
  with feasible_any false at epoch 500 reads inconclusive (time-limited); a marked D3 line for Kai.
- B6: E recovering only at 5M puts the A07 prediction beyond the ladder; H2 reads inconclusive.
- C1: production flag mismatch noted as harmless (readers use index.json); no config edit.
- C4: pre-amendment text hash recorded (scratch STUDY_v0.md).
- C5: NB init EBOPs higher than A's; H5 read notes it.
- protocol-r1.json stop_rules gain the B4 rule; lab_check_protocol re-run. PROGRAM.json untouched;
  implied changes reported to the orchestrator.
- lab_check_protocol on amended protocol-r1.json: structural_valid true, no findings, sha `cb51862c…5f70` (was `4a199581…b31c`); a scratch baseline is refused (path outside the lab), so no drift diff. Not frozen.

## Amendment [A3] 2026-10-05 14:35 JST, pre-data (experiment-designer; arbiter fix F6, `review/STUDY_arbiter_v1.md`)

No pilot data exists (R1 not launched; only the b3fb22 CPU gate is running).
- Write F6a-g into STUDY.md as one dated [A3] block plus inline `[A3]` edits: code rule for R2/R3
  (training-code tree byte-equal outside the config/pack/index files, configs built and gated before
  the R1 readout exists); matched production pair (NB = V_bin config with weights changed; P350 only
  when V_bin = A350-C; H5 = NB350-C vs A350-C); fresh-seed qualification (>= 3 healthy seeds not used
  for W/V_bin); no auto-fire, Prec always to Kai, 0.50 floor internal with the Chang/Sun Table 1
  reference (docs/chang-vs-bnjettag.md:100-101, research-log.md:9), production early stop at epoch
  500 (< 6/8 healthy per arm stops both Jobs); R1 = 24 pods (A07-350k -> A350-C-qkv1-450k, + E-unc-C),
  caps 144/60/18; w150 kept with the Kai switch line; F6f text fixes; deferred items with costs.
- Trim: compress the [A2] provenance block (copies now in study-history/), drop text the [A3] edits
  supersede.
- Pre-A3 text copied to `study-history/STUDY_pre_A3_1430.md` (sha 27d43c63).
- protocol-r1.json: 24 arms, new stop rules; lab_check_protocol re-run; jev_check_methods on the
  changed rules. PROGRAM.json is not edited (F7, ml-engineer); the required changes go to the
  orchestrator.
- Done 14:4x: STUDY.md [A3] written (378 lines; pre-A3 copy sha b3c6bc8d in study-history/).
  lab_check_protocol on the 24-arm protocol-r1.json: structural_valid true, no findings, sha
  `57e6aa0e…a4c` (was `cb51862c…5f70`), matches_snapshot false (not frozen). jev_check_methods
  (audit `jv-da03d3bec72c4bdba3687d3ca473a33d`, advisory): selection consistent 0.99, uncertainty
  consistent 0.47 (review); comparability, provenance, metrics, authority "missing" (review). Same
  pattern as the 10:14 run: the summary text omits the code sha (open until PREFLIGHT), per-class
  AUC (production VERIFY) and the signature (Kai signs PROGRAM.json). Not frozen: lab_freeze_protocol
  waits for STUDY arbiter v2 PASS.

## [A4] pass, 2026-10-06 06:13 JST (arbiter v2 P1-P3, P3a)

Pre-data: R1 not launched; only the 98dd28 CPU gate is running. Pre-[A4] text saved to
`study-history/STUDY_pre_A4_0613.md` (sha `95c9b61f…7294`).
- P1: K1 (decisions.md 2026-10-05 15:21) into STUDY row 6, D3, H4, W order; protocol arms 9-10.
- P2: healthy = four terms AND `best_feasible_val_acc >= 0.50`, one definition everywhere;
  "attentive, low-acc" label; W acc key before entropy; R3 on seeds 2-4; E-unc-C pinned at PID
  target 1e8, judged on completion/feasibility/accuracy, entropy recorded; phys B1 sentence;
  text items C (0.1907 shared-control figure, A-s2/D-s1 path, Linformer vs MHA, dev/README :70-71).
- P3/P3a: §11 20,800 s, A07 margin, deadline = integrity stop; controller-error definition pinned.
- Then `lab_check_protocol`, `lab_freeze_protocol` (declaration snapshot; re-freeze if panel v3
  changes the protocol). PROGRAM.json, code/, manifests*/, handoffs/ not touched (mirror = Q1).
Choices: W's acc key is the mean over the arm's seeds with a null (no best-feasible checkpoint)
entered as 0; the w100 "time-limited" reading is kept (390 epochs after first feedback only just
covers b5's 259-389, and two b5 runs never met (a)).

## [A5] pass, 2026-10-06 06:28 JST (arbiter v3 S1-S4, R1-R3, R5)

Pre-data: R1 not launched; only the 98dd28 CPU gate is running. Pre-[A5] copies in
`study-history/` (`STUDY_pre_A5_0628.md` sha `11005dfb…eac44`, protocol and PREFLIGHT copies too).
- S1: readout-blocker sentence in STUDY [A4] list and PREFLIGHT §3c :442; drop the "or a VERIFY
  recompute" readout source at STUDY:215 (VERIFY recompute = cross-check only).
- S2: PREFLIGHT §4 banner "Superseded by §3c (bundle 98dd2875)" + P7 note "w100 since K1".
- S3: "(0.2110, 0.50)" -> "`nondegenerate_best` and acc < 0.50" at STUDY:194, :197, protocol:633.
- S4: §9 pT sentence (24/24 configs `"pt_gate_gev": 2.0`, re-grepped 06:28); "attention-healthy"
  attributed as the lab's reading (phys C5).
- R1: control class beside H1/H3/H4 verdicts; H3 "lead (accuracy, not attention)" unless A350-C is
  low-acc uniform (arbiter scopes the relabel to H3; H1/H4 get the class column only).
- R2: low-acc uniform E-5M counts for H2 "not supported" when E-unc-C passes.
- R3: §9 "A at r_rec: selected, not independently qualified"; production 6/8 early stop the only
  independent check (K-3 alternative noted).
- R5: controller error adds min(ebops/target) and the settled window epoch >= max(warmup, t_budget),
  n per statistic; `ebops` = traced field (`freeze_p.py:153-154`); log10 optional.
- Not touched: K-1 rule, PROGRAM.json, code/, manifests*/, handoffs/, PREPARED*.json.
- Then lab_check_protocol + lab_freeze_protocol, JOURNAL line.
