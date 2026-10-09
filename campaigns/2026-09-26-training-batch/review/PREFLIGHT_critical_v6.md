# PREFLIGHT gate v6 (solo, critical-reviewer): 2026-09-26-training-batch, scoped to gate v5 findings

2026-09-28 23:48Z. Scope: this checks only the gate v5 flags, in RUN.md "8 GiB swap timing" (RUN.md:564-617, commit c7bfe61), and the K=5 re-apply (RUN.md:640-655).

VERDICT: PASS. A1 and A2 are fixed in RUN.md, and the K=5 re-apply was safe and matches c7bae4a. B2 did not land as written: the prescribed `-v limit=6144` has no effect (flag 1). The flag does not block the swap: under the A1 rule the epoch-10/20 verdict for the K=3 pod cannot trigger a delete.

## By name
- **A1: FIXED.** RUN.md:575-582 says to wait until A07-350-s1, C-s1 and F-s1 each have `latest.json`, to confirm each one from the pod before the delete, and not to swap on an RSS read alone. The earliest time is about 00:22Z (from 116.7-125.3 s/epoch at 25 epochs).
- **A2: FIXED.** RUN.md:582-589 takes the deadline from F-s1 at 72.9-76.0 s/epoch: process epoch 105 comes about 2.2 h after ARM_STARTED, around 01:40Z. The window is about 00:25Z-01:35Z, and the rate is re-measured at swap time.
- **B1, unconditional swap: FIXED.** RUN.md:590-594 says to delete the Job once inside the window. `rss_proj7000_epoch20.awk` is marked informational only.
- **B1, pod NotFound: FIXED.** RUN.md:595-601 requires `kubectl -n cms-ml get pods -l job-name=<job>` to return no resources. The flock caveat is stated as not verified.
- **B2, 6,144 override: NOT EFFECTIVE (see flag 1).**
- **B3, 5.3-6.6 GB correction: FIXED in RUN.md:609-615** ("5.3-6.6 GB (gate form), one arm in four over 6,144"). `manifests/freeze.py:22-23` and the STUDY change log still carry the old text, which RUN.md hands to ml-engineer or the fixer (flag 2).
- **K=5 re-apply: SAFE and MATCHES c7bae4a.** RUN.md:640-647 records the old pod as Pending, with no node and no containerStatuses. The pods were confirmed NotFound with `-l job-name=`, the manifest was re-linted OK, and the re-apply was at 23:45:43Z. `manifests/pilot-b-k5-job.json` parsed: requests = limits = 40Gi memory, 10 CPU, 1 GPU, and `BNJ_RSS_GATE_LIMIT_MB=8192` appears once. `git diff --stat c7bae4a HEAD -- manifests/` is empty, so the applied file is the c7bae4a manifest.

## Flags
1. **B. RUN.md:602-608: `awk -v limit=6144 -f rss_rule_epoch10_20.awk` still judges against 8,192.** awk runs `-v` assignments before BEGIN, and BEGIN sets `limit = 8192` (`manifests/rss_rule_epoch10_20.awk:10`). Test: 20 synthetic epochs with `-v limit=6144` gave `RSS_RULE t OK ... limit_mib 8192`. The text also contradicts itself: it says "-v cannot override" and then prescribes `-v`.
   - Impact: the operator gets an 8,192 verdict labelled as the 6,144 read. The printed `limit_mib 8192` gives it away.
   - Why the swap is not blocked: for the K=3 pod the verdict is not actionable. A STOP at epoch 20, before `latest.json` exists, must not trigger a delete (A1), and the swap is unconditional anyway.
   - Fix: change BEGIN to `if (limit == "") limit = 8192` (ml-engineer or the fixer), or compute rss20 + (rss20 - rss10)/10*85 against 6,144 by hand. Also state in RUN.md that for the K=3 pod the epoch-10/20 STOP rule gives way to A1 and the swap.
2. **B (carried from v5 B3).** `manifests/freeze.py:22-23` and the STUDY v1 change log still say "6.5-6.7 GB, over 6,144". Fix: "5.3-6.6 GB (gate form), one of four over 6,144".

Recomputed: awk `-v` behaviour (above); K=5 manifest resources; manifests diff since c7bae4a (empty).
Next verification: at swap time, run `ls` on `latest.json` for all three K=3 arms and read F-s1's current epoch. After the re-apply, check each arm's `resume_epoch=` (expect 25 or 50).
