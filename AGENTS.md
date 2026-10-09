# BNJetTag lab operating rules

The canonical writable lab is `~/lab/bnjettag` on the home PC's Ubuntu WSL.
Mac VS Code edits that directory remotely. Imported historical directories are reference
snapshots. Do not maintain another active editing tree, synchronize personal directories,
or access the Mac to fetch credentials. Networking is configured separately.

Mulder access requires Kai's explicit permission and the UCSD-verified connection
he establishes through his MacBook. Direct SSH from this WSL environment is not an
approved route. Wait for that permission and connection; do not request exported
passwords, private keys or Mac credential configuration. For NRP-only health checks,
use `nrp_doctor.py status`, not `all`, because `all` also attempts Mulder access.

Read `CLAUDE.md` and `SYSTEM.md` for the existing research workflow; preserve their
methodology. This file adds run provenance requirements, not permission to launch.

Before a supported NRP launch, follow `docs/infrastructure/run-handoff.md`:

1. Freeze the actual working files with the existing campaign freeze script. Uncommitted
   contents count; a Git SHA alone is insufficient. Never silently rebuild a historical run.
2. Supply a factual brief: purpose, changes, selected runs/configs, expected metrics and split,
   approved stop rules, approval reference, scientific gate and durable outputs. No private
   reasoning or secrets. Use explicit unknown/pending states rather than invented context.
3. Prepare and validate a content-addressed handoff. Submit only with the supported launcher,
   after existing `nrp_doctor` lint and action-time launch authorization. Missing context,
   a hash mismatch or a pending scientific gate blocks submission.
4. The init container verifies dataset identity and installs the immutable run record on
   `kai-data` before training. Consumers validate that record; missing/invalid records mean
   **context unavailable**, never a guess from a job name. Status events are separate from
   immutable launch records. Never rewrite the brief of an existing run; create a new record.
5. Monitoring is read-only: status/log collection and interpretation against the brief.
   No kill/relaunch/resume or scientific changes without explicit authority. In particular,
   Chang option (c) is chosen (decisions.md, 2026-10-01); K1 remains triggered and does not clear production; do not mark it cleared.

Run `python3 -m unittest discover -s tests -p 'test_run_handoff.py'` after handoff changes.
The Markdown and local hook are workflow guards, not cluster admission policy. Direct
kubectl from another client can bypass them; do not claim otherwise. No service accounts,
RBAC, notification subscriptions, deployments or background monitors are authorized by this file.
