# Review v1 — verdict ITERATE

A1 (all planted violations flagged on flawed note): MET.
  P1 -> check_methods selection=conflict (1.00); check_claims a p(supported)=0.00.
  P2 -> check_methods metrics=conflict (0.87); check_claims b overstated 0.78. Note: Jev
        categorised P2 under "metrics", not a dedicated cost rule; comparability was "missing", not conflict.
  P3 -> check_methods uncertainty=conflict (0.94); check_claims c absent 0.82.
A3 (deterministic check): MET. check-v1.txt exit=0 on corrected note; negative control
  check-v1-negative-control.txt exit=1 with all 9 checks failing on the flawed note.
A2 (corrected note clean on Jev): PARTIAL.
  check_methods: P1-P3 rules now consistent. check_claims b, c "overstated".
  Diagnosis (by reading the sources, not Jev):
  - b cited cost L31-36, but the eBOPs-on-selected-checkpoint and zero/random-input rule is
    L21-22. Citation error of mine, not a method error.
  - a merged two rules across two files; d (the atomic half) was supported 0.92.
  - c bundles four sub-rules in one sentence; likely penalised as compound. Unverified.
  - comparability/provenance "missing": the note does not state matched arms
    (03-phases L74-75) or where code sha/config are recorded (03-phases L95-99).
Iteration 2: note v2 adds matched-arms and provenance sentences; claims split atomically,
each cited to its exact lines; recheck with check_methods + check_claims (2 calls).
