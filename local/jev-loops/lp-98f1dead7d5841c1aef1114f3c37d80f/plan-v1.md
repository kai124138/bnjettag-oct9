# Plan v1 — methods_audit, loop lp-98f1dead7d5841c1aef1114f3c37d80f

SYNTHETIC EXERCISE. The method note audited here is invented; no campaign, run or number in
the record is involved. Numbers inside it are placeholders, not lab results.

## Inputs
- `method-note-flawed-v1.md`: synthetic note with three planted violations:
  P1 checkpoint selected on ROC-test (held-out);
  P2 final-epoch eBOPs reported beside best-checkpoint AUC;
  P3 improvement claimed from one seed with no interval.
- Conventions consulted (actual files, hashes bound by the loop policy):
  docs/conventions/jet-tagging-metrics.md L17-20, L30-31, L40-47;
  docs/conventions/quantization-and-cost.md L31-36;
  docs/methodology/03-phases.md L37-38, L76-80.

## Steps (Jev budget 12; planned 6)
1. jev_check_methods on the flawed note (1 call).
2. jev_rank_snippets: rank 6 convention excerpts against the three violations (1 call).
3. jev_check_claims: each flawed sentence vs. its convention passage (1 call, 3 items).
4. Draft `method-note-corrected-v1.md`.
5. jev_check_methods on corrected note (1 call); jev_check_claims on corrected sentences (1 call).
6. Review artifact with a local deterministic check script output.

## Acceptance criteria
- A1: all three planted violations are flagged by at least one Jev tool on the flawed note.
- A2: the corrected note gets no violation of P1-P3 from check_methods, and each corrected
  sentence is judged supported/consistent by check_claims.
- A3: `check-v1.txt` from a local grep script confirms the corrected note names validation
  selection, cost at the selected checkpoint, >=3 seeds with paired 95 % t-interval, and
  contains no "ROC-test" selection or "final-epoch" cost.
- Unknowns returned by Jev stay listed in the review; Jev verdicts are advisory.
