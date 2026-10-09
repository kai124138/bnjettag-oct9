# Review reports

Solo-tier verdicts (PREFLIGHT, RUN, /rounds, /redteam, session summaries), newest on top.

## 2026-10-07 — campaigns/2026-10-05-pilot-program PREFLIGHT r2 (R1 relaunch, 23 arms) — critical-reviewer (opus) — PASS (conditional, L1-L3)

Full report: `campaigns/2026-10-05-pilot-program/review/PREFLIGHT_critical_r2_v1.md`.
- freeze_p.py 25de26c0: the diff reproduces 87a2e3ab and the flags are opt-in. The default rebuild
  matches 26/26 job.json files, the bundle files and every PREPARED.json handoff and sha. Briefs
  differ only in the gate fields, because the frozen dir holds the cleared briefs.
- The 23 r2 job.json files differ only in name, deadline 18,000 (spec, annotation and 2 script
  lines), the rss-gate annotation, and the removed RSS export and RSS_GATE_FAIL lines. qkv1-s1 is
  excluded. The bundle files are byte-equal.
- Resume traced: run_pack.py:184-187, run_study.py:108-130, ablation.py:261-264, :293-329,
  :909-911, :1173-1187. The relaunched arms resume at epoch 100 and no marker blocks them.
- Tools: validate 3/3 VALID; lint 2/2 WARN only (backoff 1).
- Spend: 119.98 GPU-h against about 126 remaining (the 18 GPU-h spent is estimated from 5 pods).
- Earlier findings: v2 A3 and B-new-1..3 resolved.
- New B (text only):
  - B-r2-1: an OOM may be a single-process kill, giving up to 2 in-pod resumes and then exit 76,
    not 137. Both are final.
  - B-r2-2: the A07 margin is 300-1,340 s, not 1,760 s, once the R1 E wall rate (19.3-19.7 s/epoch)
    exceeds the benchmark by 1.03-1.09×.
- C1-C5: memory.current is 8.3-9.0 GiB, mostly cache; the resume check needs the PVC arm log; put
  the comparability marking in STUDY; the defaults-check log lacks the comparison; PROGRAM
  pod_deadline_s.
- Launch conditions: L1 the B fixes; L2 a gate-cleared re-preparation under the L4 byte rule with
  --prepared-out; L3 exactly the 23 keys.
- Jev jv-33cdb666: 4 claims supported; c5 "OOM final as 137" absent.

## 2026-10-06 — campaigns/2026-10-05-pilot-program PREFLIGHT v2 (bundle 98dd2875) — critical-reviewer (opus) — R1 PASS (conditional, L1-L4); readout PASS (L5)

Full report: `campaigns/2026-10-05-pilot-program/review/PREFLIGHT_critical_v2.md`.
- Recomputed: 12 patch hashes; build_tree TREE_MATCHES; tarball 98dd2875 (393 files, matches code/tree and bundle-manifest); ConfigMap and 26/26 handoffs; run_study manifest e6ff034b unchanged (only campaigns/pilot1005 + 2 tests differ from b3fb22).
- Configs and Jobs: 24 configs match PROGRAM r1_launch and the registered columns. All 24 GPU Jobs have:
  - RTX 3090 and the bad-node exclusions (incl. c6017);
  - pod deadline 20,800 s;
  - FailIndex on exits 5/76/124/137/143, backoffLimitPerIndex 1 (only exit 75 retried, and only within 600 s);
  - fingerprint and RSS gates, stop at 500;
  - distinct outputs, no token, pinned digest.
- Readout: PYTHONPATH fix asserted; deadline 43,200 s; diag outside the exit status; no test data read.
- Tools: validate 7/7 VALID; lint exit 0 (WARN backoff 1, deliberate; pool 48); submitted gate record rh-c11b0c23 differs only in gate/approval/identity fields.
- v1 status:
  - Resolved: A1, A2, B1, B2, B3, B4, B6. B5 resolved by K1 (w100).
  - A3 open: STUDY arbiter v2 missing; L2.
- New B, text only:
  - B-new-1: PREFLIGHT §3/§3b describe b3fb22 and a 21,600 s deadline, not the frozen 20,800 s.
  - B-new-2: the 143.87 GPU-h bound omits first-attempt pull/init, init hangs and disruption replacements.
  - B-new-3: STUDY and protocol-r1.json still register w150.
- C: A07 deadline margin 680 s at the 38.8 s bound; readout deadline tight-ish; lint misses pod-level deadlines; PROGRAM r1_launch/r1_readout placeholders.
- Launch conditions:
  - L1: GATE_RESULT PASS;
  - L2: STUDY arbiter v2 PASS;
  - L3: PREFLIGHT text fixes;
  - L4: cleared records byte-equal apart from gate fields;
  - L5: readout only after all pods reach a terminal state.
- Jev audit jv-6b20605fa012428396b01a73e4f167ae: 3 claims supported, PREFLIGHT.md:288 overstated.

## 2026-10-05 — campaigns/2026-10-05-pilot-program PREFLIGHT — critical-reviewer (opus) — (a) CPU gate PASS; (b) R1 ITERATE

Full report: `campaigns/2026-10-05-pilot-program/review/PREFLIGHT_critical_v1.md`.
- Hashes recomputed: 10 patches; build_tree TREE_MATCHES; tarball b3fb22c8 (391 files = code/tree = bundle-manifest); configmap and 25 handoffs; PREPARED.json.
- Tools: run_handoff validate 25/25 VALID; lint on 6 handoffs OK.
- The 23 configs match STUDY R1 column for column.
- Local final-tree checks (not quotable): pytest 166 collected, 164 passed / 2 skipped, gate_check PASS; cpu_gate 23 PASS; NB pairing 8/8.
- Gate launch conditions: L1 diff the cleared record; L2 dated approval; L3 fix A1 by a manifest change, or rerun the gate.
- R1 A findings:
  - A1: readout certify_ebops.py:120 `from evaluate_roc import` raises ModuleNotFoundError under the Job's PYTHONPATH, so every non-degenerate arm becomes cert_fail.
  - A2: no activeDeadlineSeconds and backoffLimitPerIndex 2, so the 138 GPU-h cap is unbounded.
  - A3: STUDY has no panel PASS or protocol freeze, and PROGRAM.json is unsigned with placeholders.
- R1 B findings:
  - B1: integrity `bundle_sha` vs readout `bundle_sha256`.
  - B2: PREFLIGHT §2a empty.
  - B3: dev/README A-unchanged evidence overstated.
  - B4: entropy cut uncalibrated for E.
  - B5: w150 likely time-limited.
  - B6: H2 undefined for E recovery at 5M.
- Jev audit jv-d8887a0d26aa49e0b102073701795646.

## 2026-10-05 — campaigns/2026-10-02-chang-option-c PREFLIGHT — critical-reviewer (opus) — PASS (CPU gate only)

Full report: `campaigns/2026-10-02-chang-option-c/review/PREFLIGHT_critical_v1.md`. All hashes
recomputed and matching (bundle 6919462c…, manifest 7ab48738…, patches 0032/0033, governing docs);
handoff validate VALID; live lint exit 0. Launch conditions: L1 diff the cleared re-prepared
record against rh-c124… (only gate/approval/identity fields may differ); L2 Kai's approval
saved as a dated file. B1 the gate re-traces only the zero-bit floor; B2 require exactly the 2
known skips and every 0032/0033 test passed. Pilots not cleared: B3 pod-3 duration bound wrong
(~30.7 h, not ~19 h), B4 amendment gates unsupplied, B5 GPU product still Kai's.

## 2026-10-05 — local/2026-10-04-session/SESSION.md — critical-reviewer (opus) — PASS

Iteration 1 ITERATE: 5 A findings (overclaimed 350k collapse, PID offset scope, R0 "all 8"
points is 7 of 8, "unknown actor" deletion, c6017 "isolated"), 9 B, 6 C. Iteration 2 ITERATE:
2 B (option (c) claim unsupported, R7 citations swapped), 2 C. Iteration 3 PASS: all resolved
with evidence. Advisory Jev `jev_check_claims` agreed on 5 of 6 iteration-1 claims (audit
jv-f210a88609fa4ca0862c6531da6c4870).
