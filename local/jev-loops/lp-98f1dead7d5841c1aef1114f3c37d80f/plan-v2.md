# Plan v2 — iteration 2 (Jev budget: 5 used of 12; planned 2 more)

Findings carried from review-v1.md: mis-cited claim b, merged-source claim a, compound claim c,
comparability and provenance "missing".

Changes (method substance of P1-P3 unchanged from corrected v1):
- method-note-corrected-v2.md adds: matched arms, only the positional bias differs
  (03-phases L74-75); code sha, ConfigMap and configs recorded in PREFLIGHT.md (03-phases L95-99);
  checkpoint reload within 1e-7 with TF32 off (quant L43).
- Claims split into atomic sentences, each with its own exact source lines:
  quant L21-22 (cost on selected ckpt), quant L31-32 (validation selection under budget),
  quant L35-36 (no final-epoch mix), metrics L17-20 (ROC-test never for selection),
  metrics L40-40 (eight seeds when gap < 0.005), metrics L43-45 (paired t-interval; covers zero = flat).

Acceptance (iteration 2):
- B1: check_methods on v2: selection, uncertainty, metrics "consistent"; no rule "conflict".
- B2: check_claims: every atomic claim p(supported) is the top class. Below the 0.8 heuristic
  threshold counts as "advisory-weak", not a failure, and is listed.
- B3: check-v2.txt (check-v1 rules plus matched-arms/provenance greps) exit 0; negative control exit 1.
- Remaining "missing" on authority is expected: the note is synthetic and has no STUDY/owner.
