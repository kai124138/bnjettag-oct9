# Note on the stored ROC tables — 2026-08-13

During the workspace reorganization of 2026-08-13, the header text emitted by
`code/hgq2/roc_final.py` changed. It previously read

    # n_eval : 260000 jets    era : 2  (NEVER compare to era-1 numbers)

and now reads

    # n_eval : 260000 jets    (comparable only at matched input set and N)

The stored `roc_auc.md` tables under `../../roc-results/r14/` and
`../../roc-results/r14-localeval/` were **not** regenerated — they are records, and
rewriting them would have detached them from the runs that produced them. They therefore
still carry the old header.

**Consequence.** If `roc_final.py plot` is re-run against a stored array, the regenerated
table will differ from the stored one **in the header line only**. That diff is cosmetic.
Every AUC, every per-class figure, and `n_eval` are unaffected. Do not chase it as a data
discrepancy; step 4 of the verify-roc procedure compares numbers, not header prose.

---

# Note on the `results/final` → `results/synthesis` rename — 2026-08-13

The per-article store was renamed. It had been called `results/final/` after the July
"FINAL" campaign — a campaign Round 14 superseded — and the Round-14 syntheses had been
written into it, so the name pointed at the wrong thing.

Updated: `convert_final.py` (`store_root`, and the checkpoint cache moved from
`models/final/` to `models/cache/`), `fold_r14n8.py` (two `baseline_run_dir` constants),
and every document that referenced the path.

**Not updated, deliberately:** the provenance JSONs already inside the store —
`convert_lineage.json`, `fold_manifest.json`, `convert.json` — record `bnjettag/results/
final/...` as the output path *at the time each was written*. That is what a lineage record
is for, so they were left alone. Nothing reads those paths back to locate files; they are
descriptive, not operational. A regenerated manifest will simply record the new path.
