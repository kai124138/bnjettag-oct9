# VERIFY: historical b5 readout, epoch-500 pilot rules (diagnostic)

**Status: diagnostic, unreviewed.** Every number below was computed on the local laptop from
recovered bytes, or is quoted from a recovered file. Under CLAUDE.md, local computation is not
quotable, so no number here enters the record, the experiment log or any outward text. Every
metric is validation (n_val = 62,000), one seed per run (single seed). There are no seed
intervals, so no gap between arms is claimed. No ROC-test number appears. Epochs are zero-based
(`ep0`, the runner's `epoch` field) unless marked one-based (`ep1`).

Registered rules: `campaigns/2026-09-26-training-batch/STUDY.md:1720-1847` (pilot rules) and
`:995-1021` (feasibility (a)-(c)). The b3 half of the readout is
`campaigns/2026-09-26-training-batch/READOUT_epoch500.md`.

## Sources and short names

| short | file (paths relative to `campaigns/2026-10-01-recovery/`) |
| --- | --- |
| `rules:N` | `readout-preparation/analysis/rules-b5.txt`, line N, written by `analysis/b5_rules.py` (standard library only; streams each JSONL line by line; peak RSS about 29 MB, 8 s) |
| `cert` | `captures/readout-run-20261001T0625Z/terminal-handoff-20261001T0815Z/received/certify-snapshot-0500.json` |
| `a26` | `.../received/a26-entropy-epoch-0500.json` |
| `log:N` | `.../terminal-handoff-20261001T0815Z/readout.log`, line N |
| `hist` | `captures/readout-run-20261001T0625Z/telemetry-raw-01/chang0926-<run>-activation_widths.jsonl` (500 lines each, line n = ep0 n-1) |
| CSV | `readout-preparation/analysis/history-<run>.csv`, the per-epoch scalars extracted from `hist` |

## 1. Integrity

- The six received files match `received/transfer-receipt.json` in SHA-256 and byte count. Their
  sum is 31,791 bytes. `identity.json`, `result.json` and `runtime.json` agree with the handoff
  `rh-b6ae7a233d366d7b15d5120e`. `transfer-receipt.json` itself hashes to `928a14f3…`, and no
  outer receipt binds it.
- `readout.log`, `job.json` and `pod.json` match `terminal-handoff-20261001T0815Z/receipt.json`.
- The five histories match `telemetry-raw-01/receipt.json` and `source-sha256.txt` (for example,
  A-s1 `08f04016…`). Together they hold 880,343,029 bytes, which matches the receipt. The
  receipt's own hash `a489e1f3…` matches `ACTIVE.json`. `pod-before.json` and `pod-after.json`
  are byte-identical.
- Each history has 500 lines with contiguous, unique and monotonic epochs 0-499, and 51 traced
  epochs (ep0 0, 9, 19, …, 499) (`rules:10-11`, `:53-54`, `:113-114`, `:176-177`, `:224-225`). No
  resume duplicates are present. On every traced epoch, the logged
  `ebops_in_training_over_traced` equals in-training / traced exactly (`rules:51`, `:111`, `:174`,
  `:217`, `:265`). The threshold (c) in every line is 0.2109624456315518, which is the registered
  value (`rules:12`).
- **Record discrepancy.** RUN.md (06:57Z and 2 October) records the five telemetry refusals as
  the 8 MiB-guard `ValueError`. The received `transfer-receipt.json` entries instead give
  `"reason":"FileNotFoundError"` for all five. `log:60` names them only as missing. This review
  does not resolve which is right. It does not affect the analysis, because the histories were
  recovered separately and byte-exact.

## 2. Certification (STUDY.md:1785-1797)

The CPU route ran with TF32 off (`cert` `tf32: false`). Its summary is `CERTIFICATION_ALL_PASS 4 0`
(`log:16`).

| run | file | ep0 | logged = retraced = stored EBOPs | rel. diff | above floor | source |
| --- | --- | --- | --- | --- | --- | --- |
| A-s2 | primary `model_best.keras` | 299 | 339,168 | 0.0 | 167,642 | `cert` runs[1].checkpoints[0]; `log:12` |
| A-s2 | AUC-sensitivity | 499 | 336,841 | 0.0 | 165,315 | `cert` runs[1].checkpoints[1]; `log:13` |
| D-s1 | primary | 259 | 323,222 | 0.0 | 151,696 | `cert` runs[2].checkpoints[0]; `log:14` |
| D-s1 | AUC-sensitivity | 269 | 303,516 | 0.0 | 131,990 | `cert` runs[2].checkpoints[1]; `log:15` |

Recomputing the selection rule (accuracy → AUC → −EBOPs → −epoch) over the feasible traced
epochs in `hist` gives the same epochs. A-s2 selects ep0 299 as primary and ep0 499 for AUC
sensitivity (`rules:59-60`). D-s1 selects ep0 259 and ep0 269 (`rules:119-120`). The last
history line's `best_feasible` agrees for both runs (`rules:76`, `:139`). Each stored and retraced value equals the logged value, so the
CPU→GPU re-run clause is not triggered. **Certification check: pass, 4 of 4.**

A-s1, C′-s1 and E1-s1 report "no feasible checkpoint" (`cert` runs[0], [3], [4]). Nothing
certifies a fallback.

## 3. Why A-s1, C′-s1 and E1-s1 have no feasible checkpoint

The runner's per-epoch flags agree with a recomputation of (a)-(c) for all five runs
(`rules:14`, `:57`, `:117`, `:180`, `:228`).

- **A-s1 reached the budget, but its accuracy had already collapsed.** Twelve traced epochs meet
  (a), ep0 389-499, and all 12 are above the floor (b). All 12 fail threshold (c), so they are
  feasible-degenerate: 12 met (a), 0 feasible, 12 degenerate (`rules:13`). The run fails (c) on
  16 traced epochs from ep0 339 onward (`rules:15`). The minimum traced EBOPs is 315,512 at
  ep0 469, which is 0.9015 × target and 0.8068 of the headroom in use. At that epoch val accuracy
  is 0.202129 and val AUC 0.503972 (`rules:17`). Over the last 10 traced epochs, val accuracy
  runs from 0.201919 to 0.207871 against the 0.2110 threshold (`rules:21`). Val accuracy fell
  steadily as EBOPs were driven down: 0.652210 at its peak (ep0 4, untraced, in-training
  8.1M EBOPs), 0.439613 at ep1 100, 0.237565 at ep1 300 and 0.201919 at ep1 500 (`rules:23-35`).
  The failure is a near-constant classifier under budget, not a budget miss.
- **C′-s1 never reached 5,000,000 on the trace.** It was over target on 51 of 51 traced epochs
  (`rules:188`). Its minimum, 5,136,496, is at the last epoch, ep0 499: 1.0273 × target and
  1.1214 × its 4,580,398 floor (`rules:183`, `:222`). The descent was still under way when the
  cosine LR reached 1e-6: 5,910,763 at ep1 100, 5,411,081 at ep1 300 and 5,136,496 at ep1 500
  (`rules:192-200`). In-training EBOPs were at or under 5M on 6 untraced epochs, with a minimum
  of 4,894,773 at ep0 488 (`rules:184`). On the traced series, the one that feasibility reads,
  the run never qualified. β stayed between 5.8e-07 and 6.9e-07, far below the 1e-3 cap
  (`rules:187`).
- **E1-s1 stalled just above its target.** It was over target on 51 of 51 traced epochs
  (`rules:236`). Its minimum is 356,745 at ep0 259, 6,745 over target (1.0193 ×) (`rules:231`).
  In-training EBOPs never reached 350,000 on any untraced epoch; the minimum was 359,256
  (`rules:232`). Over the last 10 traced epochs it sits at 1.0725-1.2320 × target, with β rising
  to 3.77e-06 at ep0 499 (`rules:234-235`, `:250`).

## 4. Rule A (STUDY.md:1725-1731)

The rule stops production only if **neither** A seed has a feasible checkpoint. A-s2 has 15
feasible traced epochs (`rules:56-57`), with a certified primary at ep0 299 (§2). **Rule A:
pass** (single seed, diagnostic). A-s1 fails it on its own (§3).

Descriptive caveat, not part of the rule: the passing checkpoint is weak and attention-free. At
ep0 299, val accuracy is 0.320871 and val AUC 0.644662 (`rules:59`), against threshold (c)
0.2110. It holds 0.9393 of the headroom in use. Q, K and V are 0-bit on all 24 channels
(`rules:103`), and its attention block bills only the 171,526 softmax floor (`rules:106`). A-s2
also had 6 feasible-degenerate epochs, and from ep1 350 to ep1 400 it went through a constant
classifier with val AUC 0.500000 (`rules:56`, `:91-92`).

## 5. Per-run report (STUDY.md:1732-1741)

| run | evaluated snapshot | traced EBOPs | headroom fraction | (a) met / feasible / degenerate, of 51 | val acc (AUC) on it | source |
| --- | --- | --- | --- | --- | --- | --- |
| A-s1 | `model_min_ebops`, fallback | 315,512 † | 0.8068 † | 12 / 0 / 12 | 0.202129 (0.503972) | `rules:13`, `:17`; `a26` runs[0] |
| A-s2 | `model_best`, ep0 299 | 339,168 | 0.9393 | 21 / 15 / 6 | 0.320871 (0.644662) | `rules:56`, `:59` |
| D-s1 | `model_best`, ep0 259 | 323,222 | 0.8500 | 18 / 18 / 0 | 0.405371 (0.730096) | `rules:116`, `:119` |
| E1-s1 | `model_min_ebops`, fallback | 356,745 † | 1.0255 † | 0 / 0 / 0 | 0.278016 (0.674949) | `rules:227`, `:231` |
| C′-s1 | `model_min_ebops`, fallback | 5,136,496 † | 1.3253 † | 0 / 0 / 0 | 0.368161 (0.814757) | `rules:179`, `:183` |

† This is the minimum traced epoch in `hist`. The fallback file's own epoch was not read here,
because `state.json` is not among the inputs. `a26` records only that the lowest-EBOPs file was
used. No run diverged: all 500 epochs are present in every run.

D-s1 did not stay under target after its certified epochs. Over the last 10 traced epochs it is
at 0.8696-1.7613 × target, with 7 of 10 over (`rules:143`). Its traced EBOPs rose from 305,594
at ep1 400 to 599,501 at ep1 450 while the LR was below 2.5e-4 (`rules:155-156`). At ep0 499,
attention channels had come back: Q is 0-bit on 5 of 24 channels, K on 7 of 24 and V on 4 of 24,
and 241,664 EBOPs sit in non-softmax attention (`rules:168-169`). That late re-growth does not
affect the selected checkpoint.

## 6. Attention state and entropy ([A26], `a26`; validation, n = 62,000, epoch-500 snapshots)

| run | heads | H / log 64 (row-renormalized) | per-jet sd | row sum (min = max) | Q / K / V 0-bit | QK live pairs |
| --- | --- | --- | --- | --- | --- | --- |
| A-s1 | 2 | 1.000000, 1.000000 | 0.0 | 0.013733 | 24/24, 24/24, 24/24 | 0, 0 |
| A-s2 | 2 | 1.000000, 1.000000 | 0.0 | 3.515625 | 24/24, 24/24, 24/24 | 0, 0 |
| D-s1 | 2 | 1.000000, 1.000000 | 0.0 | 0.878906 | 24/24, 16/24, 0/24 | 0, 0 |
| E1-s1 | 1 | 1.000000 | 0.0 | 0.109863 | 24/24, 24/24, 24/24 | 0 |
| C′-s1 | 4 | 0.503843, 0.334621, 0.178706, 0.264958 | 0.069-0.147 | 0.996-4.0 (mean 1.047) | 30/32, 25/32, 24/32 (SAT, "silent, billed 1 bit") | 0, 0, 0, 0 |

Sources: `log:30-50`; `a26` runs[*].entropy and runs[*].zero_bit.

- **The 350k-target heads are exactly uniform.** In A-s1, A-s2, D-s1 and E1-s1, every head is at
  1.000000 with zero per-jet spread, and every row sums to a constant. All Q channels are at
  0 bits under WRAP, so the logits are identically zero and the quantized softmax emits a
  constant row. In D-s1, K keeps 8 live channels and V all 24, but with Q dead the Q·K logits
  are still jet-independent, so D-s1's attention reduces to a uniform average of V.
- **A-s1, A-s2 and E1-s1 also have V at 0 bits, so the attention block outputs zero.** Under the
  STUDY collapse criteria these checkpoints are Deep-Set-class, and in practice the whole
  attention path contributes only the billed softmax floor. That floor is the entire 0-bit floor
  of the A/D arm (171,526) and of E1 (85,763) (`rules:46`, `:106`, `:260`).
- **Collapse timing.** In the A, D and E1 runs, Q and K are first all 0-bit at ep0 39, 39, 29
  and 39 respectively (`rules:37`, `:97`, `:160`, `:251`). Some channels revive intermittently
  afterwards, for example A-s2 at ep0 199 and E1 at ep0 399 (`rules:102`, `:258`). C′ never
  reaches 0 bits on the history's `bits` field (`rules:203-211`). That field counts the SAT sign
  bit, while `a26` counts magnitude width b = relu(i + f), so the two counts differ by
  definition.
- **Open inconsistency (C′).** `a26` labels all of C′'s 0-width Q/K channels "silent, billed
  1 bit" and reports 0 live Q·K pairs per head. Even so, the C′ heads have entropy 0.18-0.50,
  per-jet sd above 0, and rows summing up to 4.0. Silent channels and zero live pairs should give
  jet-independent logits. So either `QK_live_pairs_per_head` (same-index pairs only;
  `code/analysis/attn_entropy.py:190`) does not count the actual contraction, or a 0-width SAT
  channel with k = 1 does not output 0. In the second case, the "silent" label in the script
  docstring (`attn_entropy.py:23-24`) is wrong. This needs an ml-engineer check before the C′
  attention state is reported. It does not change any rule outcome.

## 7. C′ rule and constraint readout (STUDY.md:1809-1815, :1841-1844)

C′-s1 has no feasible checkpoint at or under 5,000,000 by epoch 500 (§3). Its minimum is
5,136,496, which is 1.121408 × the 4,580,398 traced floor (`rules:183`, `:222`). **C′ rule
outcome: infeasible, so the report to Kai says that "add C′ at 5M" is not supported by the
pilot** (one seed, descriptive).

Constraint quantities, on the traced series that test (a) reads:

| quantity | value | source |
| --- | --- | --- |
| (i) traced epochs over 5M | 51 of 51 = 1.0000 | `rules:218` |
| (ii) fallback traced EBOPs / 5M | 1.027299 (fallback, no feasible checkpoint) | `rules:219` |
| (iii) β at 1e-10 on last 10 traced | 0 of 10 (β 5.83e-07 to 6.93e-07) | `rules:220` |
| last-10 epochs over 5M | 10 of 10 | `rules:221` |

(iii) fails, so the run is not "constraint slack", and the F2 label does not apply. The
constraint was active and unmet at the end of the cycle.

## 8. K1, regime-B PID input rule (STUDY.md:1747-1778)

The window is one-based traced epochs 100-500, n = 41. The zero-based reading gives the same
verdicts (`rules:49`, `:109`, `:172`, `:215`, `:263`). Intervals are order-statistic intervals on
the median, about 95 % for independent draws. The series is autocorrelated, so they are
optimistic.

| run | median r [interval] | implied offset | threshold (10 % headroom) | share | headroom clause | source |
| --- | --- | --- | --- | --- | --- | --- |
| A-s1 | 1.015389 [1.008298, 1.020782] | 4,777.7 | 17,847.4 | 0.0268 | below | `rules:47` |
| A-s2 | 1.008782 [1.005515, 1.026943] | 2,743.5 | 17,847.4 | 0.0154 | below | `rules:107` |
| D-s1 | 1.033027 [1.027673, 1.041860] | 10,087.2 | 17,847.4 | 0.0565 | below | `rules:170` |
| E1-s1 | 1.022364 [1.008401, 1.038608] | 6,898.1 | 26,423.7 | 0.0261 | below | `rules:261` |
| C′-s1 | 0.999223 [0.993286, 1.000000] | −3,497.7 | 41,960.2 | −0.0083 | below | `rules:213` |

No b5 run fires the headroom clause, and each interval excludes its r* (`rules:48`, `:108`,
`:171`, `:214`, `:262`). C′'s offset is negative: its traced value sits slightly above
in-training. The rule text does not say how a negative offset is read (READOUT_epoch500 §5
item 6).

**Pairwise clause** (iso-EBOPs arms A, D, F, A07-350 and C; b3 medians from READOUT_epoch500
table (4)):

- A-s2 against D-s1: |Δ median r| = 0.024245, which is over 0.02. The gap between the two
  intervals is 0.000730, so the fire is only barely resolved (`rules:274`).
- A-s1 against D-s1: 0.017638, not over 0.02 (`rules:268`).
- D-s1 against A07-350-s1: 0.027579, over (`rules:282`). A-s2 against F-s1: 0.020034, over by
  3.4e-05 (`rules:279`). The A-s* and D-s1 pairs against C-s1 are all over (`rules:272`, `:278`,
  `:283`).
- A-s1 against A-s2 (0.006607) is a seed pair within one arm, not a two-arm comparison
  (`rules:267`).

**K1 verdict: it remains fired.** b3 already fired it, and the rule fires "if, for any run"
(READOUT_epoch500 §4). b5 adds pairwise fires that rest on single seeds, and the A-s2/D-s1 fire
is barely outside the spread. b5 adds no headroom fire. Because K1 fired, a failed A rule or
A07-350 rule is reported "not attributable (regime-B PID input)". Rule A passed (§4), so that
label applies only to A-s1's individual failure, as context.

Interpretation for option (c), descriptive: near target, the regime-B ratios are much smaller
than in regime A. The regime-B medians are 1.009-1.033 for A/D and 1.022 for E1. The regime-A
medians, quoted from `campaigns/2026-09-26-training-batch/RUN.md` 'In-training vs traced EBOPs',
are 1.072-1.092, measured over different epochs. The mixed-cost offset is therefore 1.5-5.7 %
of headroom here. That cannot explain A-s1's failure (accuracy collapse under budget) or
E1-s1's (a 6,745-EBOP stall, with in-training also above target). It also does not explain
D-s1's late re-growth.

## 9. Matched regime-A/B table (STUDY.md:1779-1784)

The regime-B half is computed: A-s1, A-s2, D-s1, E1-s1 and C′-s1 at one-based traced epochs
10-120, with traced and in-training EBOPs, r, β and feasibility (`rules:296-355`). No row is
feasible. For example, at ep1 120 the traced EBOPs are A-s1 481,140, A-s2 499,600, D-s1 555,690,
E1-s1 390,812 and C′-s1 5,965,683 (`rules:307`, `:319`, `:331`, `:343`, `:355`). The regime-A
half needs the per-epoch W&B history of group `chang-n64-20260926-canary`. No local copy is
among these inputs: the regime-A pod logs interleave arms without in-training EBOPs. **Matched
table: undetermined.** It needs a read-only W&B pull of the four or five canary runs; that is
not a cluster job.

## 10. Rule outcomes

| rule | outcome |
| --- | --- |
| Certification check | **pass**, 4 of 4, CPU, relative difference 0.0 |
| A (two-seed) | **pass** via A-s2, which has a weak, attention-free checkpoint; A-s1 alone fails (degenerate) |
| C′ | **infeasible**: "add C′ at 5M" is not supported; not constraint slack |
| K1 | **fired**, unchanged by b5; new single-seed pairwise fires, no headroom fire |
| Per-run attention/entropy | reported; 350k arms uniform/Deep-Set-class; C′ label inconsistency open |
| Matched regime A/B | **undetermined**; regime-A history missing locally |

Production still waits on the option-(c) amendment, new freeze and replacement pilot. That gate
is unchanged by this readout (STUDY.md:1845-1847).

## Commands

```
python3 campaigns/2026-10-01-recovery/readout-preparation/analysis/b5_rules.py
sha256sum campaigns/2026-10-01-recovery/captures/readout-run-20261001T0625Z/{terminal-handoff-20261001T0815Z/received/*,telemetry-raw-01/*.jsonl}
```
