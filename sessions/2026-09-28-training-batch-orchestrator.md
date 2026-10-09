# Session summary: training-batch orchestrator, 2026-09-26 → 2026-09-28

Session `bnjettag-19`, orchestrating `campaigns/2026-09-26-training-batch/`. Handed over to Kai
at 2026-09-28 17:30 PDT (2026-09-29 00:32 UTC). The handover document is
`campaigns/2026-09-26-training-batch/ONBOARDING.md`. Nothing below is a result; every number is
telemetry, a CPU trace or a projection.

## What was asked

1. How Chang Sun's Deep Sets (HGQ) reaches 79.4 % at N=64 with 191k LUT and 44 ns (arXiv:2510.24784).
2. On Saturday night (09-26), launch 40–60 binary-model trainings with Chang's recipe at N=64.

## What happened

**09-26 evening: the answer to question 1.** It rests on three mechanisms. Accuracy rises because
N rises (every model family follows the same curve). LUT stays flat because every row is trained to
the same 350k EBOPs budget, with per-position heterogeneous bits and da4ml. Latency is set by depth,
not by N. The Deep Sets code itself is unpublished.

**09-26 → 09-27: design and review.** STUDY.md was written, then reviewed ten times plus a landing
check. The review loop caught the following, in order of how much it saved:
- **350k was impossible under our quantizer**: A07's floor is 4,580,398 EBOPs (CPU trace), and E
  would have needed the same fix. So the design moved to Chang's quantizer set [D19] and the E
  architecture [D21], both decided by Kai.
- A07 at 350k has only 6,947 EBOPs of headroom, too little for data-dependent attention. It is kept
  as one descriptive arm.
- A non-degeneracy rule was added: a constant classifier can no longer count as "feasible".
- The paper's ≥ 1-bit attention rule is recorded as ambiguous.
- Kai added arms H, NB and FP32-E as a second wave.
- After about round 4 the loop found mostly wording defects in earlier fixes. That was overhead:
  the STUDY should have been offered for a freeze sooner.

**09-27: the regime-A pilot** on bundle 77f1ca4e. Found in PREFLIGHT and at launch:
- a post-pause 256-row re-trace bug, fixed in patch 0025;
- W&B run-id collisions, fixed in 0026;
- the canary: about 218 s/epoch at K=6 on an A10, so T_run of about 17.7 d. The full-split trace
  took 42 % of each epoch. Kai chose regime B, tracing every 10 epochs.
- A07-350-s1 OOM'd at K=6.

**09-28 early UTC: the incident.** Four arms stalled at once. The cause was a host-memory leak of
about 80–95 MB/epoch/arm: the pod hit its cgroup limit, the kernel thrashed with no OOM kill, GPU
sat at 0 % and the watchdog killed the arms. There was also a run_pack retry and heartbeat flaw.
Kai stopped the pilot at 05:31Z.

**09-28: the regime-B freeze**, bundle 42abed4b, patches 0027–0031:
- trace every 10 epochs plus epoch 0;
- the leak fixed by building the validation model once per run;
- run_pack starts a fresh heartbeat per attempt, does not charge POD_STALL to retry budgets, and logs POD_MEM;
- an RSS projection gate;
- a GPU fingerprint gate, taken from Delta's finding of a bad node, c6017;
- A10-only pods (Kai);
- per-arm memory sized to 8 GiB from Delta's GPU slope of 0.45–0.63 MB/epoch.

The PREFLIGHT gates ran v1–v6.

**09-28 → 09-29 UTC: the regime-B pilot.**
- K=5 is running on an A10 since 00:11Z.
- K=3 ran 23:23Z–00:26Z with the fingerprint OK and A07-350 fitting at K=3. It was swapped to 8 GiB
  and is Pending on A10 saturation, with checkpoints at epoch 25.
- STUDY v10 escalated. Kai chose K1: pre-register a PID-input threshold and decide (c) or (d) at
  epoch 500. That threshold would already fire on the regime-A ratio of 1.07–1.09.
- Option (c) is staged and unapplied, and its stability is not established.
- K2: FP32-E selects on the 701 traced epochs. K3: A − NB stays at 8 pairs.
- STUDY was frozen with its C items disclosed.

## State at handover

- Two pilot pods: K=5 running, K=3 pending.
- All agents and monitors stopped.
- The epoch-500 readout is projected for about 19:00–21:00Z on 09-29 (K=5).
- Production (56 runs, 13 A10 pods) waits on that readout and Kai's (c)/(d) choice. Its manifests are
  not generated.
- Wave-2 code ([A22], [A23], [A25]) is not written.
- Delta (session `bnjettag-ae`) is waiting on the same readout.

## What went well, and what didn't

- **Well:** four problems that would each have wasted the whole run were caught before production:
  the impossible 350k target, the memory leak, the post-pause bug and the bad GPU node. Every
  number that left an agent was labelled with its status.
- **Not well:** ten STUDY review rounds, most of them past the point of design value. Rate limits
  stopped agents four times. Two days in, only a pilot is running, not the 40–60 runs asked for.

— Claude (Fable 5.1), orchestrator session bnjettag-19, signed 2026-09-28 (PDT; 2026-09-29 UTC)
