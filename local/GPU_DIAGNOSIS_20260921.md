---
title: GPU utilization diagnosis — 21 September 2026 PDT
status: current
date: 2026-09-21
---

# GPU utilization diagnosis — 21 September 2026 PDT

Read live from Nautilus, namespace `cms-ml`, approximately 2026-09-22
00:03–00:10 UTC. No cluster resources changed.

## Findings

- Original single-arm continuation Jobs are still active. Packed replacement
  Jobs prepared on September 20 have not replaced them.
- Architecture: 10 active, 2 succeeded (indexes 3,4).
- Attention: 2 active (indexes 12,13), 13 succeeded.
- Engram: 1 active (index 0), failed indexes 1–3, 21 failed pod attempts.
- All 13 Running continuation pods had recent epoch/checkpoint log output.
  No evidence of a multi-hour training hang in this snapshot.
- Previously warned pod `kai-batch0917-full-e1000-0920-0-xgk9k`
  advanced through epochs 747, 748, 749 at 00:00:47, 00:03:14, 00:05:50 UTC.
  A point-in-time `nvidia-smi` read showed 0%, but a subsequent 15-sample
  `nvidia-smi dmon -s pucm -d 1 -c 15` showed SM utilization
  29,30,31,34,34,29,31,31,30,33,33,33,34,30,31 percent.
  GPU: V100-SXM2-16GB, 838 MiB framebuffer used. This sample is not a
  three-hour average and is not representative evidence for every pod.

The warning is consistent with underutilization of a GPU by a small training
run, rather than continuous inactivity. Earlier measurements recorded one
busy Python core and 27–39% GPU usage; the observed activity here is consistent
with that diagnosis. CPU dispatch, validation and checkpoint overhead are
plausible contributors; this session did not profile their individual costs.

## Remediation implications

Pack useful unfinished runs onto fewer GPUs and measure both utilization and
training throughput. The old packs must be refreshed: 15 public indexes have
finished, architecture index 7 and attention index 12 were at epoch 977,
and Engram indexes 1–3 have exhausted retries. Blindly applying the old packs
would include finished/failed runs and leave uneven tails.

Keep immutable code, configs, checkpoint roots and optimizer state intact;
ensure old writers have stopped before replacements resume. Verify actual
utilization after packing; three processes alone do not guarantee the recorded
40% utilization requirement.

Engram errors are a separate issue: failed attempts show numerical comparison
mismatches and, on some retries, NUMA errors followed by core dumps. Packing
does not fix these. Full tracebacks and checkpoint state need inspection before
relaunching those indexes; no tolerance or numerical protocol was changed here.

## Previous remediation status

`.claude/memory/experiment-log.md` records that the September 20 packing
replacement was prepared and checked, but its deletion/relaunch step was
blocked by that session's permission layer. That is historical evidence,
not an approval rejection in this diagnostic session.
