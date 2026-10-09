# Setup for campaign discovery-350k-20261008

## The one step that needs Kai

At a terminal on the home PC (an approval cannot be written by an agent, which has no terminal):

```
cd ~/lab/bnjettag
python3 tools/harness.py approve campaigns/2026-10-08-discovery-350k --by Kai
```

When asked, type `discovery-350k-20261008`. This writes `APPROVAL.json`, bound to the limits block
in `BRIEF.md` as it is now. Read `PROPOSAL.md` (with §11 amendments) and `BRIEF.md` first; an
edit to the limits block afterwards voids the approval.

## Done by the agent after the approval

1. Install the crontab entry (below) and verify one scheduled pass from cron in `cron.log`.
2. Then submit wave 1 (baseline and reference) through `harness.py submit --stage wave1`.

The crontab entry runs one scheduled pass every 15 minutes:

```
*/15 * * * * cd /home/kaimoe/lab/bnjettag && PATH=/home/kaimoe/.local/bin:/usr/bin:/bin /usr/bin/python3 tools/harness.py tick campaigns/2026-10-08-discovery-350k --holder cron >> campaigns/2026-10-08-discovery-350k/cron.log 2>&1
```

If the permission check refuses the crontab change, the agent reports it and the line above is
added with `crontab -e`.

## What can need Kai later

- **NRP login.** If `NOTIFY.log` reports a credentials failure, run `kubectl get nodes` at a
  terminal and complete the browser login. Jobs keep running meanwhile.
- **Home PC.** Monitoring needs WSL running. If the PC sleeps, Jobs continue on NRP and the
  campaign resumes on the next pass.
- **Decisions outside the approved scope.** Any of these comes back to Kai:
  - more GPU-hours;
  - a 7,000-epoch production run (K3);
  - a change to the binary-model definition, the 350k target or the evaluator beyond the
    defect rule;
  - anything public.
