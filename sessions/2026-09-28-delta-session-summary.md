# Session summary — Delta program (2026-09-26 → 2026-09-28)

Session: Claude Code, Delta orchestrator (session names bnjettag-db → bnjettag-ae over the run).
Handover to Kai on 2026-09-28 at ~17:35 PDT. Onboarding for taking over:
`campaigns/2026-09-26-delta/ONBOARDING.md`.

## What was asked

1. (2026-09-26 night) Combine Chang's recipe with a future-work design: ~100 methods including
   combinations, agents researching the theory, code ready to run for all of them.
2. (2026-09-27) Run them and put everything on GitHub; rename "atlas" to a Greek letter (Delta);
   run the Delta trainings; commit to GitHub as Kai.
3. (2026-09-28) Hand over: onboarding, stop all agents, dated session summary.

## What was done

**Theory and research.** THEORY.md (seven mechanisms of accuracy loss for ±1 weights, each with a
diagnostic), 70 method cards in five families with primary sources, a tried-already inventory
(68 past methods, 12 failed for a recorded reason), a code-surface inventory, the Bop
hyperparameter lookup (DR-22) and a screen-design literature note. Research-log entries appended.

**Design.** DELTA.md + delta.json: 103 entries, four waves, screen and confirm tiers, static-floor
rules. Reviewed four times (critical v1-v4, PASS). Re-based on your [D21] decision (arm A = E at
350k). Renamed atlas → Delta. Wave 2 got its own STUDY (`campaigns/2026-09-27-delta-screen/`),
reviewed by the full panel six times and frozen under your round-6 rule with seven disclosed
limitations. Your decisions this session: Delta name; 10 pods; Bop mirror flip; start on the
regime-B pilot's epoch-500 readout; median-of-4 paired gap as the primary ranking; freeze after
round 6; yield the A10 to the anchor pilot; discriminate-gate-rerun after the canary NaN.

**Code.** 38 opt-in patches (25 tarball-based for the public repo; 38 rebased onto the leak-fixed
anchor bundle 42abed4b), new modules (Deep Sets, Bop, Linformer, diagnostics), strict config
keys, a generator (582 configs), classifier, annotator, packer, bundle freezer, a GPU fingerprint
gate (gate 15) and per-pack host-memory limits. Bugs caught and fixed on the way: unwired keys
silently ignored; `clip_identity` leaving 4-6 weight values per layer; W2/W3 run-name collision;
newmods import shadowing; replica seeds 5-8 not stopping at 500.

**GitHub.** `kai124138/BinaryTransfomerJettager`, branch `delta-methods`: d436e69 (docs, theory,
catalogue), e6089e7 (code), cc8abe2 (wave-2 amendments). Authored as Kai, no assistant trailer,
not merged.

**Cluster (Delta).** Private W&B project `BNJetTag-Delta` created and verified. Canary run 1 failed
on the missing W&B project (the Job still said Succeeded; wrapper fixed). Canary run 2 hit an
epoch-0 NaN on node c6017 at K=4; the investigator ruled out code, config and libraries (CPU
fingerprint 11,559,681 on every tree); discriminator pods showed c6017 healthy single-process.
Canary v2 on c6013 measured class E: K=4 on an A10 (GPU peak 75.7 %), host RSS slope 0.45-0.63
MB/epoch, no NaN, ~104.5 s/epoch (telemetry). Stopped to yield the A10 to the anchor pilot. The A07
canary was withdrawn while Pending for the same reason. **Nothing Delta is running at handover.**

## Open at handover

- A07 memory canary (manifest ready), then K per class, re-freeze, solo PREFLIGHT review.
- Gate 1: the anchor's regime-B pilot epoch-500 readout (~19:00-21:00Z 2026-09-29, projection);
  a possible anchor patch 0032 means one more Delta rebase.
- [A22] non-binary path (anchor session) for 18 runs; four Delta-only caches (28 runs).
- Shared memory logs and INDEX files uncommitted (both sessions edited them).

No number from this session is a result; none has been through a VERIFY.

— Signed: Claude (Fable 5.1), Delta orchestrator session, 2026-09-28
