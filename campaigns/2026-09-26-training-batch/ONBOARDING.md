# ONBOARDING — campaign 2026-09-26-training-batch (handover to Kai)

**GPU policy update, 2026-09-28 (Kai):** future Chang production and Delta jobs use the measured
[GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md). The A10-only lines
below describe the pilots that were already launched and the superseded production plan. Keep
those pilots running; benchmark and certify any new product before production. Recompute pack K,
pod count and the 14-day estimate from that product's measurements.

Written 2026-09-28 17:30 PDT (2026-09-29 00:32 UTC) by the orchestrator session at handover. All
agents and monitors have been stopped; the cluster jobs below keep running. Nothing in this file
is a result. Every number is telemetry, a CPU trace or a projection, and says so. The record only
takes numbers from a `VERIFY.md`, and none exists yet.

---

## 1. What this campaign is, in one paragraph

Replicate the Sun et al. training recipe (arXiv:2510.24784 code, `reference-code/HGQ2-examples/jsc150`)
on our binary {−1,+1}-weight tagger at N=64. The recipe is 7,000 epochs, batch 2,790, LR 3e-3 with
cosine restarts every 500 epochs, the pT ≥ 2 GeV constituent gate and no sample weights. The
questions: what seed-mean ROC-test top-1 accuracy the binary model reaches at 350k EBOPs, whether it
gets there non-degenerately in at least 6 of 8 seeds, how far that is from the paper's single-model
79.4 % Deep Sets (HGQ) row, and whether this recipe beats ours at the same target. A second wave
adds arm NB (learned-width weights, iso-EBOPs), arm H (Chang's own `xfm` ported to our pipeline)
and arm FP32-E. **STUDY.md is frozen (Kai, 2026-09-28).**

## 2. State right now (2026-09-29 00:32 UTC)

| thing | state |
| --- | --- |
| **Pilot K=5** `kai-chang0926-pilotb5-42abed` | **Running** on `hcc-nrp-shor-c5805.unl.edu` (A10) since 00:11:46Z. 8 GiB per arm (40Gi pod), `BNJ_RSS_GATE_LIMIT_MB=8192`. Arms: A-s1, A-s2, D-s1, C′-s1, E1-s1. Fingerprint OK (11,559,681), all 5 `ARM_STARTED` 00:15–00:16Z. At 00:32Z the arms were at epochs 3–8. Epoch 1 took about 223–230 s including the full-split trace (about 101–109 s); untraced epochs should be faster (telemetry, RUN.md). |
| **Pilot K=3** `kai-chang0926-pilotb3-42abed` | **Pending** on A10 saturation. It was swapped from the 6 GiB to the 8 GiB manifest (24Gi pod) at about 00:26–00:29Z. All three arms (A07-350-s1, C-s1, F-s1) have checkpoint `epoch-0025`, so they resume at 25 once scheduled. Before the swap it ran on `gpu-16.nrp.mghpcc.org`. The fingerprint was OK, A07-350-s1 fit at K=3 (about 8.4 GB GPU; it had OOM'd at K=6), and the epoch-10/20 RSS was fine. |
| Regime-A pilot `kai-chang0926-pilot-77f1ca` | **Stopped** 2026-09-28T05:31Z on your decision, because of a host-memory leak. Checkpoints are under `/data/chang-n64-20260926/pilot/runs/`. Descriptive only; there is no epoch-500 snapshot, so the A-vs-B regime comparison is unavailable. |
| Data cache | Built by `kai-chang0926-cache-c5d6f0`, pT-gated, 90/10 (558,000 / 62,000). Non-degeneracy threshold 0.2110 (PREFLIGHT). |
| ConfigMaps in `cms-ml` | `kai-chang0926-code-42abed4b5d` (**current bundle**), `kai-chang0926-fp-e9511d1aeb` (GPU fingerprint script), `kai-chang0926-code-77f1ca4e9f` (regime-A code, kept for its readout), `kai-chang0926-code-c5d6f02a83` (superseded). |
| W&B | `kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe`, **PRIVATE**. Regime-A pilot group `chang-n64-20260926-canary`; pilot-b runs are keyed by `BNJ_STAGE=pilot-b` (patch 0028; see PREFLIGHT "Regime B addendum"). |
| PVC `kai-data` | 67 G free of 100 G (read 00:32Z). |
| Agents | **All stopped** at handover. Nothing is watching the pods. |

## 3. What you need to do next, in order

### 3.1 In the next hour or two (the pods are unwatched)

1. **When the K=3 pod schedules**, check `kubectl -n cms-ml logs <pod>` and the per-arm logs on the PVC:
   - the node is an A10 and not `hcc-nrp-shor-c6017.unl.edu`;
   - `FINGERPRINT 11559681 expected 11559681`;
   - `MANIFEST_SHA_OK 041f981a…`;
   - three `ARM_STARTED` lines;
   - each arm logs `resume_epoch=25`, with no "History exists without a committed checkpoint".
2. **The epoch-10/20 memory rule, K=5 pod now and the K=3 pod after it resumes.** Epochs are *process* epochs, counted from the pod's start. Per arm, stop the pod if
   `rss20 + (rss20 − rss10)/10 × 85 > 8,192 MiB`. The tool is `manifests/rss_rule_epoch10_20.awk`,
   default limit 8,192; `-v limit=` now works. Do not act on a projection of epoch 20 out to 7,000, because it flags healthy arms.
3. **The automatic RSS gate at process epoch 105.** Each arm fits RSS over process epochs 5–104. If
   baseline + slope × 7,000 > 8,192 MiB, the arm exits 5 and is not retried. Nothing to do unless an arm exits 5.
4. **If a K=3 arm OOMs:** delete the K=3 Job at once, confirm with `kubectl get pods -l job-name=kai-chang0926-pilotb3-42abed` that the pods are gone, wait 15 min, then apply the matching `manifests/pilot-b-fb*-job.json` (the table is in PREFLIGHT). The guards are `ARM_STILL_LIVE` and `ARM_NO_CHECKPOINT`.
5. **If a pod exits 10** (every arm NaN at epoch 0): move the `DIVERGED.json` markers into a dated `abandoned-<UTC>` folder before re-applying; never delete them. See RUN.md "Regime-B pilot: operating rules".
6. **Save pod logs** into `logs/` before the 7-day Job TTL.

### 3.2 At the pilot's epoch-500 readout

The projection for the K=5 pod is about 19:00–21:00Z on 2026-09-29; K=3 comes later because of the swap and the queue.

1. Apply `manifests/readout-b5-job.json` / `readout-b3-job.json` **only after** that pilot Job has
   finished, or has been deleted at the epoch-500 pause. A non-empty `missing=` in its output means not done. The job runs
   full-split EBOPs certification and the attention-entropy script (`analysis/attn_entropy.py`, row-renormalized).
   For a CPU-vs-GPU certification mismatch, follow the four-condition rule at the top of `decisions.md`: re-run once on the pilot's GPU.
2. Have results-analyst read the pre-registered rules. None of this is a result, since the pilot is validation only:
   - **the A rule:** does arm A reach 350k feasibly and non-degenerately (EBOPs ≤ target, above the 0-bit floor, val acc > 0.2110);
   - **the A07-350-s1 rule:** it gates production packs 7–10;
   - **the K1 threshold** (the PID-input rule, STUDY "Regime-B PID input rule"). It fires on any of: an implied traced offset > 10 % of an arm's headroom, arm ratios differing by > 0.02, or A07-350 wind-up. **On the regime-A numbers it would already fire.** The in-training/traced ratio was 1.072–1.092 for A, D and E1 and 1.000 for C′, measured far from target (RUN.md);
   - **the arm-C "constraint active" readout** and the collapse labels.
3. **Your decision if K1 fires:**
   - **(c)** The PID reads traced EBOPs only and holds β between traces. It is staged, not applied: `code/patches-staged/0032-option-c-pid-traced-only.patch` and `code/staged-option-c/`. Stability is **not established**: the loop gain b fits at 0.17–0.30 pooled, but D-s1 and E1-s1 come out at 0.84 and 0.88 against the stability bound of 0.80 (RUN.md, plan.md). Lowering the PID `p` below about 0.75 makes it safe across that range. (c) means a re-freeze and a new pilot, about 19–21 h plus queueing, and the pilot checkpoints cannot resume into it.
   - **(d)** Scale each arm's setpoint by its measured ratio. Config only, with no stability question, but the configs change, so the pilot cannot resume into production either.
4. Tell the Delta session (§6): it launches its 10 pods off this readout.

### 3.3 Production (wave 1, 56 runs)

- Generator and packs are in `code/tree/campaigns/chang0926/`. `packs.json` has 13 pods in the prior A10 planning layout; regroup and re-canary for a faster selected product:
  - 4 E pods at K=5;
  - 3 E pods at K=4;
  - 4 A07 pods at K=4;
  - 2 R pods.
- **Production manifests do not exist yet.** Generate them with `manifests/freeze.py`. They must set:
  - `BNJ_STAGE=production`;
  - 8 GiB per arm;
  - the benchmark-selected single GPU product and its correct Kubernetes resource request;
  - `NotIn` for c6017 and the `KNOWN_BAD_NODES` hosts;
  - the fingerprint gate.
- Judge the 14-day rule **per pod class** (F1). The A07 pods at K=4 are **untimed** and may land around 14.3–14.8 d (projection).
- Packs holding A07-350 or C wait on the K=3 readout.
- **Open production items**, from PREFLIGHT, not built:
  - P1: a pod whose arm hit RSS_GATE_FAIL is re-created by `backoffLimitPerIndex 2`, and `run_pack.py` does not skip that arm;
  - P2: no automatic stop at 0.9 × the memory limit;
  - P3: R-B8;
  - P4: an epoch-0 NaN across a whole pack is not a pod failure inside `run_pack` itself.
- If you choose (c) or (d), production runs on a new bundle or new configs. Re-run the full CPU gate on the shipped bundle and do a PREFLIGHT check.

### 3.4 Wave 2 (code not written yet)

| arm | code item | notes |
| --- | --- | --- |
| NB (learned-width weights, paired with A) | **[A22]** a real `kbi_learnable` path under the [D19] quantizers; the builder raises on unknown types | Delta wants the same path for its weight types; spec in `code/A22_weight_types_request.md`. Today `kbi_learnable` silently builds static int8 (`decisions.md`). |
| H (Chang's `xfm`, 2 heads, d24) | **[A23]** port to the job-YAML pins (TensorFlow, no JAX, drop `StopIf` and the Linformer import), our data, split and seeds | β control = our PID at 350k; traced on a per-epoch clone. |
| FP32-E | **[A25]** `quant.weight: none`, controller off, strip `act_overflow`, `softmax_quant` and `i_decay_speed`, skip `binary_gate`, `n_shared==15` pairing | **Selects only on the 701 slot-T epochs** (your K2 answer). |

A − NB stays at **8 pairs, no extras** (K3). It resolves only about 3.7 pt at the archived spread.
Wave-2 pods overlap wave 1; you accepted about 27 pods at peak across this campaign and Delta.

## 4. The frozen design, in short (full text: `STUDY.md`)

- **Quantizers [D19]:** Chang's set. WRAP datalane activations that can reach 0 bits, a learned softmax output, softmax tables kbi at ≥ 4 bits, and exp input SAT. Under our old quantizer the A07 floor is 4,580,398 EBOPs (CPU trace), so 350k was impossible.
- **Ladder on E [D21]:** d24, 2 heads, 1 block, FFN 32, no positional encoding.
  - A = E at 350k, Chang recipe;
  - B = E at 250k;
  - C = A07 at 5M;
  - D = E on our optimizer;
  - F = E plus learned PE;
  - R = E on our recipe;
  - A07-350 = A07 at 350k, descriptive, with attention dead by construction.

  Traced floors (CPU): E 171,526; A07 343,053; E1 85,763.
- **Regime B:** the full-split EBOPs trace every 10 epochs plus epoch 0, 701 traces over 7,000 epochs. Selection happens only on traced epochs; the chosen checkpoint is re-traced on the full split before ROC-test. The PID reads in-training EBOPs between traces (slot P).
- **[D25]** `i_decay_speed` 1e-3, as in jsc150.
- **Feasible** means EBOPs ≤ target AND above the 0-bit floor AND val acc > p_maj + 5·SE (0.2110).
- **Seeds 1–8; ROC-test** n = 260,000, once per run.

## 5. Decisions you made (newest first; full text at the top of `.claude/memory/decisions.md`)

| date | decision |
| --- | --- |
| 09-28 | STUDY frozen with the C items disclosed; arm B out of the K1 fire list (a descriptive caveat) |
| 09-28 | K1 = pre-register the threshold, decide (c)/(d) at epoch 500; K2 = FP32-E on the slot-T grid; K3 = A − NB at 8 pairs |
| 09-28 | Pilot-b A10 only; launch after the gate-v3 fixes |
| 09-28 | Stop the regime-A pilot (memory leak) |
| 09-27 | Regime B (trace every 10); a second pilot pod; about 27 pods peak |
| 09-27 | PREFLIGHT and the pilot in parallel with the STUDY wording; wave-1 defaults confirmed; wave 2 overlaps; FP32-E added |
| 09-27 | [D19] Chang quantizers; [D21] E primary; 8–10 pods; add arms H and NB |

Orchestrator and agent decisions on the record: per-arm memory 8 GiB, sized from Delta's GPU RSS slope of 0.45–0.63 MB/epoch (telemetry); the CPU→GPU certification re-run rule; a fingerprint gate in every pod; c6017 excluded.

## 6. People and sessions

- **Delta campaign** (`campaigns/2026-09-26-delta/`, `campaigns/2026-09-27-delta-screen/`, STUDY frozen). Its session is now named **`bnjettag-ae`**; it was `bnjettag-db`.
  - It builds on bundle 42abed4b.
  - It waits for this pilot's epoch-500 readout (10 pods) and for [A22] (18 non-binary, teacher and KD runs).
  - It found the c6017 GPU fault and wrote the fingerprint gate.
  - It freed an A10 for our pilot and withdrew its A07 canary so our swapped pod would schedule first.

## 7. Where everything is

| file | what |
| --- | --- |
| `STUDY.md` | frozen design (large; the change log at the top maps every amendment) |
| `PREFLIGHT.md` | build and cluster gates. See "Regime B addendum", "PREFLIGHT gate v3 fixes" and "Per-arm memory 8 GiB" |
| `RUN.md` | launch records, the canary, health checks, incidents, **the operating rules**, the regime-A ratio pull, the stability fit |
| `plan.md` | agent working notes, including "Option (c), staged" and the ml-engineer code plans |
| `review/` | every STUDY and PREFLIGHT review. STUDY v1–v10 plus the v11 landing check; PREFLIGHT gates v1–v6; `INCIDENT_stall_20260928.md` |
| `code/tree`, `code/patches/0001–0031` | the staged pipeline; bundle 42abed4b = `manifests/chang0926-code.tar.gz` |
| `code/patches-staged/0032`, `code/staged-option-c/` | option (c), unapplied |
| `code/analysis/` | the attention-entropy script and tests |
| `code/A22_weight_types_request.md` | Delta's weight-type spec for [A22] |
| `manifests/` | Jobs (pilot-b k5/k3, six fallbacks, readout a/b5/b3, cache), ConfigMap payloads, `freeze.py`, the RSS awk tools |
| `logs/` | saved pod logs (regime-A pilot, pilot-b) |
| `.claude/memory/decisions.md`, `experiment-log.md`, `cluster-inventory.md` | decisions, the log entry, incidents |

## 8. Commands you'll use

```
python3 nrp-lab/nrp_doctor.py status
kubectl -n cms-ml get jobs,pods -o wide | grep chang0926
kubectl -n cms-ml logs <pod>                       # MANIFEST_SHA_OK, FINGERPRINT, ARM_* lines, POD_MEM
kubectl -n cms-ml exec <pod> -- tail -n 3 /data/chang-n64-20260926/pilot-b/logs/<arm>-<job>-0.log
kubectl -n cms-ml exec <pod> -- cat /data/chang-n64-20260926/pilot-b/runs/<arm>/latest.json
kubectl -n cms-ml exec <pod> -- nvidia-smi --query-compute-apps=pid,used_memory --format=csv
kubectl -n cms-ml exec <pod> -- cat /data/.../logs/<arm>-<job>-0.log | awk -f manifests/rss_rule_epoch10_20.awk   # add -v limit=6144 for a 6 GiB pod
python3 nrp-lab/nrp_doctor.py lint <manifest>.json   # the PreToolUse hook also lints on apply
```

## 9. Pitfalls learned the hard way

- **The A10 pool is often full.** Deleting a running pod gives up its GPU, and the replacement can sit in Pending for hours.
- **Node `hcc-nrp-shor-c6017` gives GPU NaN.** Keep it excluded; the fingerprint gate cannot catch its specific fault (Delta ticket §8).
- **Host-memory leak (fixed in 42abed4b).** The validation model is now built once per run. Before the fix, RSS grew about 80–95 MB/epoch/arm, the pod hit its cgroup limit, the kernel thrashed page cache with no OOM kill, GPU sat at 0 % and the watchdog killed the arms. After the fix the GPU slope is about 0.45–0.63 MB/epoch (Delta telemetry).
- **The trainer refuses to resume on a different code or config sha.** A re-freeze therefore means fresh runs. Pod memory and `BNJ_RSS_GATE_LIMIT_MB` are *not* in any sha, so memory swaps are resume-safe.
- **Swap only after every arm has `latest.json`** (the first checkpoint is at epoch 25).
- **Rate limits** stopped long agent runs four times; check the working tree for partial work after one.
- **The pre-kubectl-lint hook** blocks any Bash command whose *text* contains `kubectl create -f <path>`, even inside a heredoc. Write such text with the Write tool.

## 10. Loose ends outside this campaign

- The **confirmation campaign** job `kai-confirm-onegpu-0924-e0c0a3-r2` (N8 at 350k, N64 at 5M) is **dead since about 09-26** (Failed; its last pod errored about a day before it was diagnosed on 09-27). It is resumable from PVC checkpoints and has not been relaunched: its `pack_runner_one_gpu.py` kills the whole pod on one arm's exit. N64 reached epochs 240–280 and N8 281–300, out of 1,000. Also, `campaigns/2026-09-23-confirmation/UPSTREAM_FEEDBACK.md`: its 5M target is about 9 % above the old quantizer's A07 floor of 4,580,398, which is CPU arithmetic.
- `decisions.md` and `project-context.md` say "N64 5M enforced from 2026-09-10", but 5M first appears on 2026-09-24. Unreconciled.
- `.claude/memory/decisions.md`, `experiment-log.md` and `review-reports.md` hold **uncommitted** edits from this and other sessions. `nrp-lab/` and `cluster-inventory.md` are untracked in the repo.
