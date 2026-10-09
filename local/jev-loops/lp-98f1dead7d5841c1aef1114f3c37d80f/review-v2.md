# Review v2 — verdict PASS (local loop acceptance only; not a research arbiter PASS)

B1 MET: no rule "conflict" on v2; selection/uncertainty consistent at 1.00, metrics 0.64,
   comparability moved missing -> consistent 0.70 after the matched-arms sentence.
B2 MET as defined: all 7 atomic claims have "supported" as the top class. Advisory-weak
   (confidence < 0.8 heuristic): b 0.78, c 0.45, e 0.35, g 0.63. Reading the sources, I find
   each claim stays inside its passage; e adds "each arm" and c adds "cost and AUC from the
   same checkpoint", a mild paraphrase of "Report cost at the selected checkpoint". Not
   re-queried: spending calls to raise confidence would be tuning wording toward the model.
B3 MET: check-v2.txt exit=0 (12/12); check-v2-negative-control.txt exit=1 (12/12 fail).
   check-v2-attempt1-FAIL.txt kept: first run failed on my own regex ("paired-by-seed" vs
   "paired by seed"); the pattern was widened to both spellings, the note was not edited.

Unresolved / unknown:
- provenance "missing" 0.95 in all three runs, even after adding code sha / ConfigMap / PREFLIGHT.
  Jev gives no rationale. Possibly it expects dataset provenance (archive, file counts, n) or
  a W&B group; not tested. Unknown.
- authority "missing" 0.88: expected; the synthetic note has no STUDY.md, owner or approval.
- Jev filed P2 (final-epoch cost mix) under "metrics", not a cost-specific rule; the catalog
  has no dedicated cost rule, so P2 detection here rests on metrics=conflict 0.87 and the
  claims check (overstated 0.78).
- All thresholds heuristic, not calibrated on lab data. Scientific gate: not evaluated.
