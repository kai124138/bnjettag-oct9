# Handoff: discovery-350k-20261008 (updated 2026-10-08 11:02 UTC)

Read first: PROPOSAL.md (v2 + §11), BRIEF.md (authority approved 9496cf63; operations), RUN.md
(incident and fixes), ideas.json, NOTIFY.log, docs/agent-harness.md §9-10.

## Where things stand
- Wave 1 is running on NRP. Cron `harness.py tick` runs every 15 min (cron.log).
  - baseline: kai-d350-baseline-e-350k-s1-a2. Running since about 10:18 on k8s-3090-01.usd.edu.
    Infrastructure relaunch 1 of 2, after a1 failed admission there.
  - reference: kai-d350-reference-e-5m-s1-a4. Submitted 11:00, Pending, excludes that node.
  - Committed GPU-h 53.79 (cap for wave 1 + search: 90).
- Interpretation is queued automatically only when both current wave-1 Jobs have results.
- Candidate integration passed with the real Codex and Claude runners on a substituted cluster:
  evidence/candidate-integration-PASS.json.
- Candidate training requires the real wave-1 interpretation first (PROPOSAL §5). The rehearsal
  scores and C0/C1 selections are constructed and are not findings.

## Watch for
- E's GPU utilization at one arm per GPU: about 45 % mean over the first 11 minutes. NRP's floor is
  40 % (at most 4 pods below it). Measure over the full run; look at GPU_SAMPLE in the pod log.
- k8s-3090-01.usd.edu: operations.extra_excluded_nodes. The a2 baseline still runs there.

## Rules that are easy to miss
- INVALID is never a number; every seed is reported; classes per eval/INVALID_REASONS.json.
- Recovery after epoch 500 is "under continued training with the existing schedule".
- Only harness.py submit may submit this campaign's handoffs (hook enforced).
- K3, the pilot r3 PVC rename, production approval, local-only notifications unchanged.
