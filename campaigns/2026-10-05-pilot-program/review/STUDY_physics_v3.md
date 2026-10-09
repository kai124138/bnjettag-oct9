PASS

# STUDY physics review v3 (fresh-context referee), scope [A4] 2026-10-06 06:13 JST

Read: `STUDY.md` and the data it cites for the [A4] rows: `docs/chang-vs-bnjettag.md:90-110,145-152`,
`.claude/memory/research-log.md:9`, `recovery/readout-preparation/analysis/rules-b5.txt:13,56,116,179,227`,
`recovery/readout-preparation/VERIFY.md:112-118`, `evidence/final-tree-98dd28/cpu_gate.log:70-77`,
`gpu-benchmark/VERIFY.md:96-111`, `PROGRAM.json:45-56`, `dev/README.md:66-78`. No methodology,
conventions or earlier review files were read.

## Answer to the question

**The artefact is closed.** Every rule that consumes "healthy" (r1, bracket, r_rec, W, V_bin, the
H1-H5 cells, both positive controls, qualification, production early stop) now requires
`best_feasible_val_acc >= 0.50`. A qkv1 row whose floor forces entropy below 0.95 at val acc about
0.3 lands in "attentive, low-acc" and is unhealthy; it can no longer make a lead, set r1 or win W
on the healthy count. Entropy survives as a rule input only as W's tie-break after mean accuracy
(§7.3), where a tie on a continuous mean is practically only the all-null case (C3 below). The
four-class partition of complete/feasible/non-degenerate rows (acc >= or < 0.50 x entropy < or >=
0.95) is exhaustive and disjoint, and its boundaries match the nondegenerate threshold.

**No new flaw makes the R1 reads uninterpretable.** [A4] does add or expose three places where a
healthy-count comparison now mixes failure mechanisms or reuses selection seeds (B1-B3); they affect
what a lead *means*, not whether R1 can be read, and none blocks launch.

Verified against the cited sources: b5 first-(a) epochs 389 / 299 / 259 and C′-s1, E1-s1 never
(`rules-b5.txt:13,56,116,179,227`); w100 first feedback at 110 (`cpu_gate.log:72,76`); A-s2 0.320871,
D-s1 0.405371 (`VERIFY.md:116-117`); 38.8 s total elapsed per run-epoch and 30.85 s training-only,
RTX 3090, A07, K = 1, n = 1 x 20 epochs (`gpu-benchmark/VERIFY.md:109`); `pod_deadline_s` 20800
(`PROGRAM.json:51`); NB init 12,362,587 vs A 8,913,043 and 368,134 / 619,198 (`dev/README.md:72-73`);
Chang/Sun MHA-64 collapse quoted verbatim (`chang-vs-bnjettag.md:107-110`). Arithmetic rechecked:
0.25 x (1 - 0.75^5) = 0.1907; 20,800 - 300 - 420 = 20,080 s, minus 500 x 38.8 = 680 s (3.4 %),
minus 500 x 30.85 = 4,655 s.

## Findings

### A (launch-blocking)

None.

### B

**B1. H1/H3 leads count healthy rows without conditioning on the control's failure class.**
With four classes, A350-C at 0/2 can now be "attentive, low-acc" rather than "low-acc uniform". H3
reads "attention is starved first (Q/K/V go to 0 bits)"; if the A350-C rows are attentive (entropy
< 0.95), H3's premise is false for the control, yet qkv1 2/2 against it still reads "lead" (§6 H3
row). The same holds for qkv1-450k vs A350-C. §6 (phys B1) forbids attributing the accuracy loss to
attention, but the H3 cell is still labelled as an attention hypothesis. Fix: list the §5 class of
every control row beside each H1/H3/H4 verdict, and read H3 "lead" only when the A350-C rows are
low-acc uniform; otherwise "lead (accuracy, not attention)".

**B2. H2 refutation is asymmetric between the two unhealthy classes at 5M.** §6 H2 "not supported"
counts an E-5M row that is "attentive, low-acc" but excludes "low-acc uniform" (inconclusive, §5
[A3] paragraph). Physically the second is the stronger refutation: the documented collapse
signature at 4,828,474 EBOPs of headroom, with E-unc-C passing (so the recipe and 500 epochs can
reach >= 0.50 on E), is exactly what H2 says cannot happen. The entropy cut being uncalibrated on E
does not rescue it, because the row is unhealthy on accuracy alone. Fix: either let low-acc uniform
at 5M count when E-unc-C passes, or state why the collapse signature at large headroom is weaker
evidence than restored attention at low accuracy.

**B3. Prec qualification reuses the seeds that chose r_rec.** r_rec is the lowest bracket rung with
>= 3 of 4 seeds healthy (§7, after R2), and §8/§9 then qualify A at r_rec on seeds 2-4, which are
among the seeds that selected the rung. If r_rec is the rung below r1, seed 1 there is unhealthy by
construction of r1, so r_rec was chosen precisely because seeds 2-4 are all healthy; qualification is
then automatic. "Not used to choose it" (§9) holds for NB@r_rec (3 fresh seeds), not for A. The
lowest-rung rule favours a rung that passed by luck. Fix: say so in §9 (A at r_rec is "selected,
not independently qualified") or require one fresh A seed at r_rec in R3 (1 pod; with NB@r_rec at
3 seeds this exceeds the R3 cap of 3, so the cap would need +1). Otherwise state that the production
early stop at 6/8 is the only independent check on A at r_rec.

**B4. The entropy-only stop now vetoes the one outcome the thesis cares about.** With accuracy
inside "healthy", the entropy term's remaining job is to reject a row at val acc >= 0.50 with
uniform attention. With no mask, a 0-bit Q gives a mean pool over 64 keys, i.e. a Deep Set, and the
cited external row (MHA-64, 77.9 %, `chang-vs-bnjettag.md:107-110`) shows that regime can reach high
accuracy at 350k. At higher E rungs, where the rest of the network has bits, an entropy-only row is
a plausible R1 outcome, not an edge case, and each one stops all derivation (§10.2). Interpretable,
but likely to halt the program on the first such row. Fix: have Kai settle D1 before launch for this
case (e.g. "accuracy-healthy, attention-collapsed" counts for r1 and W but not for H3/H2′ mechanism
reads), so the stop is not reached by a foreseeable outcome.

### C

**C1. Controller-error window differs by arm.** `epoch >= warmup` drops the first 100 epochs for
w100 and 50 for w50 but only epoch 0 for others, so median target tracking is not comparable across
the H4 arms (w100 omits the phase where tracking is worst). Also say which EBOPs `ebops` is (traced
or in-training) in `ebops / target_ebops`. Descriptive only, so C.

**C2. E-unc-C with a live PID at 1e8 target.** The PID error is about +90M EBOPs for the whole run.
If beta is not clamped at >= 0, the controller rewards EBOPs growth and E-unc-C is "inflated", not
"unconstrained". Record the beta trajectory in `readout_diag.json`; the positive-control reading
does not depend on it.

**C3. W entropy tie-break.** After mean accuracy, "lower mean entropy" breaks ties; the realistic tie
is all arms null (accuracy 0), and there qkv1 wins by its floor, not by health. Harmless at that
point (no arm is usable), but the next key could be the fixed arm order instead.

**C4. Deadline margin.** 680 s (3.4 %) on an n = 1, 20-epoch A07 measurement; the amortised startup
in 38.8 s makes it conservative over 500 epochs, so the margin is probably larger. A hit on
A07-5000k-C (the positive control) is an integrity stop, which is the safe behaviour. Note E and NB
at K = 1 are unmeasured (only K = 4/5 on the 3090, 71-86 s/epoch per arm), which also bears on the
§10.5 40 % utilization stop for the small E model at one arm per GPU (pre-[A4], outside scope).

**C5. External reference wording.** "Acc (%) as the source labels it" and the MHA-64 caveat are
correct to the cited text. "Linformer-64 ... the attention-healthy 350k row" is the lab's reading
(research-log: attention bitwidth >= 1 bit), not a statement in the source; attribute it as such.
The 260k test split comes from the lab's comparison note, not the paper table; fine as written.

## Verdict

PASS. [A4] removes the attention-floor artefact from every selection and qualification rule and
introduces no launch-blocking flaw. B1-B4 change what an R1 lead means and should be settled
before the R1 readout (B4 ideally before launch, as a D1 ruling by Kai), not before R1 launch.
