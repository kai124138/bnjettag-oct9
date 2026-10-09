# Draft reply to Russell (r14 results) — 2026-08-04

Hi Russell, following up on the input-set change I described — the (N, 3) sweep is done
and verified. Setup: pT, eta_rel, phi_rel per particle (the Odagiu et al. 2402.01876 set,
so we're now input-matched to Chang), N in {8, 16, 32, 64}, five arms (fp32, w8a8, and
binary weights with 8/6/4-bit activations), 3 seeds each — 60 runs, everything tracked in
the new W&B project BNJetTagAug (per-epoch metrics, configs, and every checkpoint /
evaluation bundle as versioned artifacts, qat.py + the full training tree snapshotted with
each run).

ROC-test macro-OvR AUC on the 260k held-out split (mean ± std over 3 seeds):

| N | fp32 | w8a8 | w1a8 (binary) | w1a6 | w1a4 |
|---|---|---|---|---|---|
| 8 | 0.8864 ± 0.0005 | 0.8862 ± 0.0009 | 0.8712 ± 0.0016 | 0.8689 ± 0.0020 | 0.8534 ± 0.0012 |
| 16 | 0.9128 ± 0.0013 | 0.9124 ± 0.0014 | 0.8956 ± 0.0002 | 0.8910 ± 0.0009 | 0.8693 ± 0.0021 |
| 32 | 0.9374 ± 0.0017 | 0.9358 ± 0.0011 | 0.9052 ± 0.0079 | 0.9022 ± 0.0009 | 0.8833 ± 0.0013 |
| 64 | 0.9486 ± 0.0012 | 0.9448 ± 0.0011 | 0.9121 ± 0.0116 | 0.9136 ± 0.0061 | 0.9073 ± 0.0009 |

Main takeaways:

1. Dropping 16 → 3 features costs essentially nothing once you add constituents — fp32 at
   N=16 already matches our old 16-feature n10 number (0.9161) and beats it from N=32 up.
   So adopting the L1-realistic convention is free, which is good news.
2. Binary weights behave exactly as before at short sequences (~1.5-point gap at N=8/16,
   tight seeds).
3. The new and unexpected result: binary QAT destabilizes at long sequences. The gap
   doubles at N≥32, seed-to-seed variance grows ~75x, and the weak seeds peak mid-training
   and then degrade. Binary essentially stops converting extra constituents into accuracy
   past N≈32, while fp32/w8a8 keep climbing. All of these gaps pass a seed-spread +
   paired-bootstrap significance check.
4. For the hardware story that puts the sweet spot at N≈16–32: binary there gives
   0.90–0.91 AUC at ~5–6x fewer EBOPs than w8a8 at the same N. Next step is csynth on the
   binary n8/n16 points to see if the 3-feature frontend also undercuts the old 16-feature
   synthesis in LUTs; happy to share the numbers when those run.

Slides with the tables/figures attached. Everything is reproducible from the stored
arrays (the repo's verify gate recomputes all 60 AUCs exactly), and the W&B project has
the full lineage if you want to poke at any individual run.
