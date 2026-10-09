# READOUT: epoch-500 feasibility-pilot rules (2026-09-26-training-batch)

**Status.** Pilot telemetry. Validation only (n_val = 62,000), one seed per arm, never quoted as a
result, never selects an arm or a checkpoint (STUDY.md:1721-1722). This document evaluates the
pre-registered epoch-500 pilot rules (STUDY.md 'Phase 2, feasibility pilot', STUDY.md:1720-1847) and
reports their inputs. It is not a VERIFY.md: nothing here enters the record, no `verify.json` is
written and no experiment-log Result line is filled. Section b5 (K=5 pod: A-s1, A-s2, D-s1, C′-s1,
E1-s1, including the A rule) is added after readout-b5. results-analyst, 2026-09-29; not committed.
Plan and flagged decisions: `plan.md`, section 'results-analyst: epoch-500 pilot readout, b3'.

**Citations** are `file:line`, paths relative to this campaign directory. Short names:

| short | file |
| --- | --- |
| `rules` | `readout/b3/rules-b3.txt`, written by `readout/b3/rules_b3.py`; every computed number below is one of its lines, with its own inputs cited there as `src=file:line` |
| `pvc` | `readout/b3/pvc-extract-b3.json`: the needed keys of each `snapshots/epoch-0500/state.json` and of four `activation_widths.jsonl` records, read-only from the PVC, each with its path, line and sha256 |
| `wb` | `readout/b3/wandb-history-b3.csv`: W&B `kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe`, group `chang-n64-20260926-pilot-b`, read-only, every step; A07-350-s1 at lines 2-501, C-s1 at 502-1001, F-s1 at 1002-1501 |
| `a26` | `readout/b3/readout-epoch-0500-42abed-b3/a26-entropy-epoch-0500.json` |
| `cert` | `readout/b3/readout-epoch-0500-42abed-b3/certify-snapshot-0500.json` |
| `rpod` | `readout/b3/readoutb3-pod.log` |
| `pod` | `logs/pilotb3-vqxc7-final-20260929T1613Z.log` |
| `logA07`, `logC`, `logF` | `logs/chang0926-{a07-350,c,f}-n64-s1-kai-chang0926-pilotb3-42abed-0-final-20260929T1613Z.log` |

Epochs are one-based (arm-log `[epoch N/7000]`, W&B `_step`) unless marked zero-based (the runner's
`epoch` field in `state.json`, `cert` and `pvc`).

## b3 (K=3 pod)

Pod `kai-chang0926-pilotb3-42abed-0-vqxc7`, regime B, manifest 041f981a (`rpod:6`; `code_sha256`
in `state.json`, `pvc:12`), arms A07-350-s1, C-s1 and F-s1, seed 1 each. The readout Job ran on CPU
and exited clean: `READOUT_ARMS … missing= none` (`rpod:7`), `CERTIFICATION_ALL_PASS 4 0` (`rpod:17`),
`READOUT_JOB_DONE certify_exit=0 a26_exit=0 missing= none` (`rpod:51`). Each arm's committed
trajectory is the first attempt up to its resume point (epoch 25) plus every line after the last
`==== ARM_ATTEMPT` (`rules:39-41`; RUN.md:900-905), with 51 traced epochs (1, 10, 20, …, 500).

### Outcome at a glance

| rule | outcome | decided by |
| --- | --- | --- |
| (1) A07-350-s1 attention state against the Falsifier expectation | **Not testable on a feasible checkpoint**: A07-350-s1 has none as of epoch 500. On the fallback checkpoint the attention-logit half matches; the per-constituent half lies outside the expectation's domain (checkpoint over 350k), and the per-layer accounting closes exactly. **No floor-accounting defect found; nothing routed to ml-engineer** (DECISION b3-1, flagged for Kai). | 0 of 51 traced epochs at or under 350,000 (`rules:107`) |
| certification of the feasible snapshots | pass, 4 of 4 (C-s1 and F-s1, primary and AUC-sensitivity) | `rpod:17`; `rules:54-57` |
| (3) C-s1 constraint readout | **not "constraint slack"**: β above its 1e-10 floor on 10 of the last 10 traced epochs; a single-seed indication that decides nothing | `rules:130-132` |
| (4) K1, regime-B PID input rule | **fires on the K=3 inputs**: A07-350-s1's implied traced offset is 1,707.4 against a 694.7 threshold (share of headroom 0.2458); the C-s1 and A07-350-s1 median r also differ by 0.075343 > 0.02 | `rules:136`; `rules:157` |

Consequence: production waits for Kai's choice between (c) and (d) (STUDY.md:1765-1769, :1845-1847).
The K=5 arms complete the K1 readout (their own offsets and the A- and D-based pairs), but they cannot
undo the fire, because the rule fires "if, for any run" (STUDY.md:1753).

### (1) A07-350-s1 rule (gates production packs 7-10)

**Registered.** A07-350-s1 "reports whether its attention state matches the pre-registered
expectation (Falsifier, 'A07-350'); a mismatch in the attention logits or the per-constituent layers
goes to ml-engineer as a floor-accounting defect" (STUDY.md:1742-1744). The expectation is stated "for
every feasible A07-350 checkpoint" (STUDY.md:1131-1137). It has two parts: Q·K logits independent of
the jet, and at most three 1-bit input channels in total across `input_proj`, `bit_block_0_attn_Wq`,
`_Wk`, `_Wv`, `_Wo`, `bit_block_0_ffn_fc1` and `_fc2`, at 2,048 EBOPs per input channel at 1 bit.
`head_fc1` and `head_fc2` are reported separately. The pilot rules are evaluated on the
best-feasible-as-of-500 snapshot, "or its minimum EBOPs if none meets (a)" (STUDY.md:1722-1723).

**Feasible checkpoints: none.** 0 of 51 traced epochs are at or under 350,000 (`rules:107`). The
`state.json` `best_feasible` is null (`pvc:15`), and the certification file lists A07-350-s1 as "no
feasible checkpoint" (`cert:102`). So no checkpoint at epoch 500 falls under the expectation.

**Fallback checkpoint.** `model_min_ebops.keras` (`a26:23`) at zero-based epoch 329 (one-based 330),
with traced EBOPs 367,730. That is 24,677 above the 343,053 floor and 17,730 over target (`pvc:18`,
`pvc:21`, `rules:66`, `rules:120`). Its widths are `activation_widths.jsonl` line 330 (`pvc:196`,
line sha256 at `pvc:198`), the same epoch and EBOPs as `state.json` `lowest` (`rules:108`).

| expectation part | measured on the fallback | source | reading |
| --- | --- | --- | --- |
| Q·K logits independent of the jet | Q 32 of 32 and K 32 of 32 channels at 0 bits; entropy / log 64 = 1.000000 on all 4 heads, per-jet sd 0.0 | `a26:81`, `a26:97`, `a26:37-39`, `a26:44`, `a26:51`, `a26:58`; widths `pvc:252`, `pvc:261` | matches |
| at most 3 one-bit input channels across the per-constituent layers | 11 live input channels, 12 channel-bits, 24,576 EBOPs: `input_proj` 1 channel (2,048), `ffn_fc1` 10 channels with 11 channel-bits (22,528); `attn_Wq`, `_Wk`, `_Wv`, `_Wo` and `ffn_fc2` 0 | `rules:110-119` | exceeds the bound, on a checkpoint above 350k: outside the expectation's domain |
| floor accounting | per-layer sum 367,730 equals the logged total; the softmax term is 343,053, the floor; each per-constituent layer bills 2,048 EBOPs per channel-bit, `head_fc1` 32 and `head_fc2` 5, as in the static all-1-bit table; 24,677 = 24,576 + 96 + 5 | `rules:109-118`, `rules:120`; `code/evidence/static_floors_arms_s1_d25.json:1136` (`rules:36`) | closes exactly |
| head (separate, outside the expectation) | `head_fc1` 3 input channels at 1 bit (96 EBOPs), `head_fc2` 1 (5 EBOPs) | `rules:117-118` | reported |
| collapse label (A07-350 is Deep-Set-class by construction; the measured label is printed beside it, STUDY.md:1408-1410) | Deep-Set-class: every head meets (i), (ii) and (iii) | `rules:74` | agrees |

**Verdict.** There is no feasible checkpoint, so the pre-registered expectation cannot be tested at
epoch 500. On the fallback, the attention-logit half matches. The per-constituent layers hold exactly
what the checkpoint's own above-floor budget allows, 12 channel-bits (floor(24,677 / 2,048),
`rules:120`), and nothing in the per-layer accounting disagrees with the floor. This readout reports
**no floor-accounting defect** and routes nothing to ml-engineer.

```
DECISION b3-1: A07-350-s1 has no feasible checkpoint at epoch 500. Report the Falsifier expectation
  as not testable; on the fallback, the attention logits match, the per-constituent excess lies
  outside the expectation's domain (checkpoint 17,730 over target), and the accounting is exact.
  So: no defect, no routing.
ALTERNATIVES: literal reading. The fallback's 12 channel-bits against at most 3 is a mismatch in the
  per-constituent layers. It goes to ml-engineer as a floor-accounting defect and, because K1 fired,
  is reported "not attributable (regime-B PID input)" (STUDY.md:1744-1746, :1768-1769). Packs 7-10
  then also wait for an ml-engineer fix of a defect that the per-layer accounting does not show.
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```

**Gate for packs 7-10.** Pods that hold A07-350 or C launch once this readout exists (it does) and,
on a mismatch, once ml-engineer has fixed the defect (STUDY.md:1684-1687). Under DECISION b3-1 there is
no mismatch, so the A07-350-s1 rule does not hold packs 7-10. K1 fired (section 4), so every
production pod waits for Kai's (c) or (d) in any case (STUDY.md:1845-1847).

**Descriptive, for Kai (validation, single seed, not a result).**
- A07-350-s1 never reached 350,000 in the cycle. Its minimum traced EBOPs was 367,730 at epoch 330,
  and at epoch 500 it was 381,965 (`rules:161-162`, `logA07:517`). Traced EBOPs were over target on
  51 of 51 traced epochs, and at 1.0681-1.1441 × target over the last 10 (`rules:163`).
- β rose to 7.113e-05 at epoch 500, 0.0711 of its 1e-3 cap (`rules:163`).
- It became a constant classifier. From epoch 240 on, every traced epoch fails threshold (c), which
  is 0.2109624456315518 (`PREFLIGHT.md:519`). Validation AUC is exactly 0.500000 on 19 traced epochs
  (`rules:76`).
- At epoch 500 the 38,912 EBOPs above the floor sit in `input_proj` (2,048) and `ffn_fc1` (36,864).
  Every input channel of `ffn_fc2` and `head_fc1` is at 0 bits (`rules:125`), so these EBOPs are billed
  on paths that cannot reach the output.

### (2) Per run

Evaluated snapshot: the best-feasible-as-of-500 snapshot, or `model_min_ebops` when none meets (a)
(STUDY.md:1722-1723). "Feasible" means (a) to (c) of the Selection rule (STUDY.md:995-1021):
threshold (c) is 0.2109624456315518 (`PREFLIGHT.md:519`), and the floors are A07 343,053 and E-family
171,526 (`rules:22`, `rules:27`, `rules:32`).

| run | evaluated snapshot | traced EBOPs | above floor | headroom | headroom fraction | traced epochs, of 51: (a) met / feasible / feasible-degenerate | diverged | class | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A07-350-s1 | `model_min_ebops`, zero-based 329 | 367,730 | 24,677 | 6,947 | 3.5522 | 0 / 0 / 0 | no | no feasible checkpoint | `rules:63-67`; `pod:12011`, `pod:12042` |
| C-s1 | `model_best`, zero-based 19 | 4,880,224 | 4,537,171 | 4,656,947 † | 0.9743 † | 49 / 49 / 0 | no | feasible | `rules:77-81`; `pod:12040`, `pod:12042` |
| F-s1 | `model_best`, zero-based 289 | 325,319 | 153,793 | 178,474 † | 0.8617 † | 4 / 1 / 3 | no | feasible | `rules:91-95`; `pod:8578`, `pod:12042` |

† C and F are not in the STUDY's "Reported per run" list, which covers A, D, A07-350 and E1
(STUDY.md:1732-1734). Their fractions use the same formula with headroom = target − floor
(`rules:28`, `rules:33`), which is the denominator behind the K1 thresholds for C and F
(STUDY.md:1754-1755).

| run | Q / K / V channels at 0 bits | entropy / log 64 per head (row-renormalized, [A26]) | collapse label | best-feasible validation accuracy (macro-OvR AUC) | source |
| --- | --- | --- | --- | --- | --- |
| A07-350-s1 | 32/32, 32/32, 32/32 | 1.000000 on all 4 heads | Deep-Set-class | none; fallback 0.202597 (0.500000), below threshold (c) | `rules:68-76` |
| C-s1 | 0/32, 0/32, 3/32 (all three in head 3) | 0.622127, 0.913695, 0.543640, 0.880046 | not Deep-Set-class (no head meets (i)-(iii)) | 0.664726 (0.900360) | `rules:82-89` |
| F-s1 | 24/24, 24/24, 24/24 | 1.000000 on both heads | Deep-Set-class | 0.236177 (0.594849), 0.025215 above threshold (c) | `rules:96-103` |

Every entry: validation, n = 62,000, single seed, never quoted. The collapse label follows
STUDY.md:1403-1407, with the per-head criteria printed at `rules:74`, `:88` and `:102`.

**Certification.** C-s1 and F-s1 each certify both files, primary and AUC-sensitivity. Logged,
retraced and stored EBOPs agree with relative difference 0.0: C-s1 4,880,224 and F-s1 325,319
(`cert:18-21`, `cert:36-39`, `cert:62-65`, `cert:80-83`; `rules:54-57`). For each run the two files
are the same checkpoint (same sha256: `cert:17` and `cert:35`; `cert:61` and `cert:79`), and each
agrees with `state.json` (`rules:54-57`). A07-350-s1 has nothing to certify (`cert:101-102`). The
certification ran on CPU with no disagreement, so the CPU-to-GPU re-run rule (STUDY.md:1791-1797) was
not triggered.

**F-s1.** It met (a) on four traced epochs, 260 to 290. Epochs 260, 270 and 280 failed (c), so they
are feasible-degenerate (`logF:309`, `logF:319`, `logF:329`); epoch 290 is its only feasible
checkpoint (`logF:339`). Afterwards its traced EBOPs stayed over target: 47 of 51 traced epochs were
over target over the cycle, and 1.1209-1.3945 × target over the last 10 (`rules:165`).

**Cross-checks** (✓ = identical):
- The epoch-500 telemetry lines for A07-350-s1 and C-s1 in RUN.md:1047-1048 equal the arm logs ✓
  (`rules:59-60`).
- The certified values at RUN.md:1062-1063 equal `cert` ✓.
- The A26 summary at RUN.md:1070-1073, at its printed precision, equals `a26` ✓ (`rules:70-73`,
  `:84-87`, `:98-101`).
- W&B traced EBOPs equal the arm logs on 51 of 51 traced epochs for A07-350-s1 and C-s1, and on 49 of
  51 for F-s1. The two F-s1 differences are at epochs 30 and 40, where W&B holds the first attempt
  (`rules:44`, `:46`, `:48`).
- The four PVC width records equal W&B at their steps ✓ (`rules:50-53`).

### (3) C-s1 constraint readout

**Registered** (STUDY.md:1816-1840). (i) The fraction of traced epochs with traced EBOPs over
5,000,000, denominator 51. (ii) The selected checkpoint's traced EBOPs / 5,000,000. (iii) Whether
β, as logged at the end of each traced epoch, sits at its 1e-10 lower bound (relative difference ≤
1e-6) on every one of the last 10 traced epochs, 410 to 500. The run is "constraint slack" iff (iii)
holds and none of those 10 exceeds 5M. If (iii) holds and m > 0 of them exceed it, the label is "β at
floor (integral wound up), 5M exceeded on m of 10" (STUDY.md:1832-1834).

| quantity | value | source |
| --- | --- | --- |
| (i) traced epochs with traced EBOPs over 5,000,000 | 2 of 51 = 0.0392 (epochs 1 and 10) | `rules:128`; `wb:502`, `wb:511` |
| (ii) selected traced EBOPs / 5,000,000 | 4,880,224 / 5,000,000 = 0.976045 (best-feasible-as-of-500, zero-based 19, certified) | `rules:129`; `pvc:71`; `cert:18-21` |
| (iii) β at 1e-10 on the last 10 traced epochs | 0 of 10; β from 1.339e-08 to 1.679e-08, the smallest 133.9 × the floor | `rules:130`; `wb:911-1001` |
| last-10 traced epochs over 5,000,000 | 0 of 10 (traced EBOPs 4,460,863-4,671,737) | `rules:131` |

**Outcome.** (iii) fails, so C-s1 is not "constraint slack". The F2 label does not apply either,
since it also requires (iii) (`rules:132`). Per STUDY.md:1835-1840, this goes to Kai as a single-seed
indication, not a label: it selects, gates and triggers nothing.

**Descriptive.** β rose over the window while traced EBOPs stayed under 5M. The reason: between
traces the PID reads the in-training EBOPs (STUDY.md:1572-1577), and C-s1's in-training EBOPs ran
above its traced EBOPs, with median r 1.080792 over traced epochs 100-500 (`rules:142`). The
stationary point 5,000,000 × r^−0.9 = 4,662,321 (`rules:145`; STUDY.md:1586-1587) lies inside the
last-10 traced range 4,460,863-4,671,737 (`rules:131`). So the constraint is active on the
in-training series. On the traced series, which is the one feasibility reads, C-s1 sits at
0.8922-0.9343 × 5M (`rules:164`).

### (4) K1 inputs (regime-B PID input rule)

**Registered** (STUDY.md:1747-1761). For each run, take r = in-training / traced on traced epochs
(W&B `ebops_in_training` / `ebops`), its median over traced epochs 100-500, the implied traced offset
T × (1 − r^−0.9) and that offset's share of the arm's headroom. The rule fires on any one of three
clauses: an offset above 10 % of headroom (A07-350 695, C 465,695, F 17,847); median r differing by
more than 0.02 between two arms of an iso-EBOPs comparison; or the A07 wind-up clause.

**Window.** "Traced epochs 100-500" is read one-based: W&B steps 100, 110, …, 500, 41 traced epochs.
That is the STUDY's convention for readout windows (STUDY.md:1781, :1829). The zero-based reading
(steps 110-500, 40 epochs) is given beside it. W&B `ebops_in_training / ebops` equals the logged
`ebops_in_training_over_traced` exactly (`rules:45`, `:47`, `:49`). W&B's re-run gaps (epochs 26-43)
lie outside the window.

| run | window | n | median r | implied traced offset | threshold (10 % of headroom) | share of headroom | headroom clause | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A07-350-s1 | one-based | 41 | 1.005448 | 1,707.4 | 694.7 | 0.2458 | exceeds | `rules:135-136` |
| A07-350-s1 | zero-based | 40 | 1.005419 | 1,698.3 | 694.7 | 0.2445 | exceeds | `rules:139-140` |
| C-s1 | one-based | 41 | 1.080792 | 337,678.6 | 465,694.7 | 0.0725 | below | `rules:142-143` |
| C-s1 | zero-based | 40 | 1.081843 | 341,757.3 | 465,694.7 | 0.0734 | below | `rules:146-147` |
| F-s1 | one-based | 41 | 1.028816 | 8,835.3 | 17,847.4 | 0.0495 | below | `rules:149-150` |
| F-s1 | zero-based | 40 | 1.028048 | 8,605.9 | 17,847.4 | 0.0482 | below | `rules:153-154` |

Formula check: r = 1 gives an offset of 0. The STUDY's regime-A offsets for E1-s1 (26,654) and D-s1
(21,147) are reproduced from their medians 1.0920 and 1.0717 (`rules:156`; STUDY.md:1775-1776).

**Pairwise clause** (median r, one-based window; the gap is between the two median intervals of
`rules:137`, `:144`, `:151`):

| pair | abs difference of median r | over 0.02 | gap between median intervals | source |
| --- | --- | --- | --- | --- |
| A07-350-s1, C-s1 | 0.075343 | yes | 0.048133 | `rules:157` |
| A07-350-s1, F-s1 | 0.023368 | yes | 0.007660 | `rules:158` |
| C-s1, F-s1 | 0.051976 | yes | 0.020460 | `rules:159` |

Which pairs count is not settled. STUDY.md:1755-1756 lists "(A, D, F, A07-350, C)" as arms of an
iso-EBOPs comparison, and the disclosed item C9 says "arms compared at their nominal targets" is meant
(STUDY.md:465-466). On that reading, C-s1 against A07-350-s1 (the A07 target rung) is a compared pair,
and it fires. On a literal iso-EBOPs reading, no two K=3 arms are compared with each other (F and
A07-350 are each compared with A), and this clause waits for A-s1 and A-s2 from the K=5 pod.

**Wind-up clause** (A07-350-s1; "an A07 run" means A07-350, item C1 at STUDY.md:459-460). The last
cycle is one-based epochs 1-500, the pilot's only cycle.
- Reading 1: the in-training excess scales the whole total, floor included
  (`review/STUDY_arbiter_v10.md:43-48`). The first condition holds: in-training EBOPs are above
  350,000 on 449 of 449 untraced epochs, with minimum 367,730 at epoch 331 (`rules:160`). The second
  fails: traced EBOPs are within 1 % of the floor (≤ 346,483.53) on 0 of 51 traced epochs, with
  minimum 367,730 = 1.0719 × floor at epoch 330 (`rules:161`). **The clause does not fire.**
- Reading 2: the excess lives only in the learned-width part above the floor. **The clause does not
  fire**, by definition (STUDY.md:1758-1759).
- The data cannot separate the two readings, because only total in-training EBOPs are logged, not
  per-layer ones.

**K1 verdict: fires.** Two clauses fire: the headroom clause for A07-350-s1, in both windows, and the
pairwise clause for C-s1 against A07-350-s1, under C9's reading. The K=3 inputs alone are enough for
the rule to fire. The full K1 readout still needs the K=5 arms A-s1, A-s2, D-s1, E1-s1 and C′-s1
(STUDY.md:1749-1750): their offsets, the A- and D-based pairs, and E1's and C′'s thresholds. Kai's
choice between (c) and (d) (STUDY.md:1765-1769) should see all eight runs, but the K=5 arms cannot
undo the fire.

**Robustness** (descriptive; the rule is registered as a point comparison and is applied as one).
- A07-350-s1's offset equals its threshold at r* = 1.002210. 23 of the 41 traced-epoch r values lie
  above r*, and the order-statistic interval on the median, [1.000098, 1.013212], contains r*
  (`rules:137`). That interval has coverage 0.972 for independent draws; the series is
  autocorrelated, so it is optimistic. The A07-350-s1 headroom fire is therefore not resolved against
  the epoch-to-epoch spread of r.
- A07-350's threshold (694.7 EBOPs) is smaller than one per-constituent channel-bit (2,048), and the
  median in-training − traced difference is exactly 2,048 (`rules:138`). The clause fires whenever
  the typical traced epoch carries one more channel-bit in training than on the trace.
- The C-s1 against A07-350-s1 pairwise fire is resolved: the two median intervals are 0.048133 apart
  (`rules:157`).

### (5) What the rules cannot decide

1. **Whether the fallback's per-constituent excess counts as a "mismatch".** The Falsifier states
   the expectation for feasible checkpoints, and the pilot rule evaluates on the fallback when none
   exists. The text does not say which governs (DECISION b3-1, flagged).
2. **Why A07-350-s1 missed 350,000.** When K1 fires, a failed A07-350-s1 rule is labelled "not
   attributable (regime-B PID input)" automatically. But the implied offset (1,707.4) is an order of
   magnitude below the run's smallest distance to target: 17,730, and 31,965 at epoch 500
   (`rules:162`). The stationary-point formula also assumes a run that has settled at its setpoint
   (STUDY.md:1586-1587). A07-350-s1 never settled (1.0681-1.1441 × target over its last 10 traced
   epochs), and neither did F-s1 (1.1209-1.3945 ×) (`rules:163`, `:165`). The width data show where
   the above-floor EBOPs sit (`rules:125`), but not why β, still at 0.0711 of its cap, did not remove
   them. The registered rules name no cause.
3. **Whether the A07-350-s1 headroom fire would hold over more epochs or seeds.** The margin lies
   within the spread of r (section 4, Robustness).
4. **The pair set of the pairwise clause** (item C9). C-s1 against A07-350-s1 fires under C9's
   reading; the literal reading needs arm A.
5. **Window indexing.** One-based and zero-based give the same verdict for every run (section 4
   table).
6. **The offset's sign.** The rule compares a signed offset with its threshold. All three medians are
   above 1, so a negative offset (traced settling above target) does not arise here, but the text
   does not say how one would be read.
7. **"Sit within 1 % of its floor"** could mean every traced epoch, the last one, or any one. No
   traced epoch comes within 7 % of the floor (`rules:161`), so every reading gives the same result.
8. **C-s1's label when (iii) fails.** The STUDY defines "constraint slack" and the F2 label, and both
   require (iii). A run with β off its floor gets neither, which this readout reports as "not slack".
   The rule does not say whether 5M binds on the traced series. Here the traced series sits under 5M
   while β follows the in-training series (section 3).
9. **W&B against the committed trajectory.** For F-s1 at epochs 30 and 40, W&B holds the first
   attempt's values: 1,217,046 and 710,660, against the committed 1,221,977 and 687,865
   (`rules:48`). All four values are over target and outside the K1 window, so no count here changes.
   The arm logs are the source for those epochs.
10. **C and F headroom fractions** are not pre-registered report items (section 2, †).
11. **F-s1's one feasible checkpoint** is 0.025215 above threshold (c), with Q, K and V all at 0 bits
    (`rules:98-103`). This is descriptive only: F has no pilot rule of its own besides K1.

### Commands (rerun from the campaign directory)

```
cd campaigns/2026-09-26-training-batch
# inputs, read-only: W&B through ~/.netrc (the key is never printed); the PVC through the running K=5 pod
uv run --with wandb python readout/b3/fetch_b3.py
#   runs, per arm R in chang0926-{a07-350,c,f}-n64-s1, with D=/data/chang-n64-20260926/pilot-b/runs:
#   kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- cat $D/$R/snapshots/epoch-0500/state.json
#   kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- sha256sum $D/$R/snapshots/epoch-0500/state.json
#   kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- sed -n '330{p;q}' $D/chang0926-a07-350-n64-s1/activation_widths.jsonl
#   (also A07-350 line 500, C-s1 line 20, F-s1 line 290; jsonl line n holds zero-based epoch n - 1)
uv run --with numpy python readout/b3/rules_b3.py     # writes readout/b3/rules-b3.txt
```

Input sha256 values are listed at `rules:5-17`. Each `state.json` was checked against an in-pod
`sha256sum` at fetch (`pvc:8`, `pvc:60`, `pvc:124`). Output `readout/b3/rules-b3.txt`, sha256
8137874f9245681bec7ff0feebddd107d1ef209312a6ade246cf29196d265fab. The certification and [A26] numbers
come from the readout Job `kai-chang0926-readoutb3-42abed` (RUN.md:1057-1067). Every other number was
computed with `uv` from the saved artifacts above; nothing was computed in the lab pod.
