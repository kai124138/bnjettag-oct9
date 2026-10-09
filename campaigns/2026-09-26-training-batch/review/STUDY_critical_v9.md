# STUDY critical review v9: 2026-09-26-training-batch

Critical reviewer, panel mode, fresh context, 2026-09-27. Scope set by `review/STUDY_arbiter_v8.md`
("v9 checks landing only"): every fix 1-5 at every listed site, verbatim where the arbiter gave
text; a new B only if an edited sentence is itself wrong. No verdict (the arbiter issues it).

Artifact `STUDY.md` at c2f5447 (2,353 lines; `git status --short` on it empty). Diff read in full:
`git diff 75ec0cc c2f5447 -- campaigns/2026-09-26-training-batch/STUDY.md` (19 hunks).
`git diff 1115121 c2f5447` touches one line (the change-log sha, l. 284), so line numbers cited
"at 1115121" hold at c2f5447; all line numbers below are at c2f5447.

## Validators

`review/STUDY_validators_v9.txt`, verbatim:

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  33828 words · 862 sentences · mean 25 words (σ=23.4) · 17% bullets · 0 em-dashes
Diff since v8 review (75ec0cc):  1 file changed, 93 insertions(+), 21 deletions(-)
```

No red flag, no Category A line. `tools/plot_check.py`: not applicable (no figure exists at STUDY).

## Completeness of the diff

Every one of the 19 hunks maps to a listed fix (1, 2 ×4 sites, 3 ×2, 4 ×3, 5a-5h, change log).
No hunk falls outside the fix-1-to-5 sites; optional fix 6 not applied, as the change log states
(l. 297). The change-log line numbers were checked site by site against `git show 1115121:STUDY.md`;
all 19 cited ranges (l. 256-257, 364-365, 961-963, 1028, 1049-1050, 1100-1101, 1113-1119,
1178-1179, 1217-1228, 1237-1239, 1246-1247, 1258-1260, 1267-1268, 1374-1394, 1412-1413, 1469,
1536-1541, 2158, 2159, 2167) open on the text they name.

## Landing, fix by fix

| fix | site (c2f5447) | arbiter text | landed |
| --- | --- | --- | --- |
| 1 FP32-E label | l. 1178-1179 | "worded as FP32-E − 79.4 (the same descriptive form as A − 79.4), and triggers nothing (arbiter v7 fix 2; arbiter v8 fix 1)." | verbatim |
| 2 amendment | l. 1375-1394, end of pilot "Pod." bullet after "not triggered." (l. 1374) | full paragraph (1)-(5) | verbatim, word for word |
| 2 Kai row "pod count" | l. 2158 | status cell appended "(superseded by 'wave-1 packing after the A10 out-of-memory' if production runs at K=3; arbiter v8 fix 2)" | verbatim |
| 2 canary rule | l. 1469 | "for every arm that trained in the pod (per-pod reading, arbiter v8 fix 2)" | verbatim |
| 2 new row | l. 2159, directly after "pod count" | four cells | verbatim |
| 3 collapse label | l. 1217-1228, after entropy bullet (l. 1213-1215), before "Widths come from" (l. 1230) | full paragraph | verbatim |
| 3 pilot readout | l. 1412-1413 | "entropy row-renormalized [A26], and the collapse label, arbiter v8 fix 3)" | verbatim; the sentence parses ("the attention state (…, arbiter v8 fix 3), and the best-feasible …") |
| 4 Not falsified | l. 1113-1119, after "about 3.7 pt (Seeds)." | full passage | verbatim |
| 4 Resolution | l. 1100-1101, after "measured sd_diff);" | inserted clause | verbatim |
| 4 Kai row cap | l. 2167 | "and the 80 %-power detectable gap at the cap (arbiter v8 fix 4)" after "at the proxy sd_diff" | verbatim |
| 5a gate counts | l. 1536-1541 | replacement parenthetical | verbatim; old "the shipped bundle 77f1ca4e gate reads 26 / 24 / 2" gone |
| 5b v7 change-log | l. 256-257 | "Line numbers at fba27d5:" | verbatim |
| 5c first Holm copy | l. 1025-1028 | Direction sentence deleted | done; `grep -n Direction` now hits l. 1052 (second copy, kept, as prescribed) and the change log only |
| 5d second Holm copy | l. 1049-1050 | "It leaves the Holm step-down order as well." | verbatim |
| 5e Table 1 rows | l. 364-365 | three Deep Sets (QKeras) rows named | verbatim |
| 5f per-class ROC legends | l. 1246-1247 and l. 1267-1268 | "the legend prints each arm's per-class ROC-test AUC as seed mean ± sd (ddof = 1, k)" | verbatim at both sites, plus tag (below) |
| 5g caption | l. 1237-1239 | caption replacement | verbatim |
| 5g beside A − 79.4 | l. 961-963 | "the same clause" (no verbatim text) | adapted (below) |
| 5h attention figure | l. 1258-1260 | inserted clause after "entropy / log 64" | verbatim |
| change-log line | l. 281-284 | "arbiter v8 fixes 1-5; pilot composition amended (fix 2); no change to any arm, seed, target, batch, selection or certification rule; production packing left to Kai" | verbatim |

### The three sites where the arbiter gave no verbatim text (fixer's note, l. 281-297)

- **5f tag "(arbiter v8 fix 5f)"** at l. 1247 and l. 1268. The house convention since v7 is "new
  tags read 'arbiter vN fix N'" (l. 256); every other v8 insertion carries the same form. The tag
  adds no claim. Closed.
- **5g second half, l. 961-963.** "and beside it: external reference single-model with no
  interval; its noise is unpublished, [L1] puts its scale at about 1 pt or more (arbiter v8 fix
  5g)". The caption's plural ("references … their noise") becomes singular because A − 79.4
  involves one reference (79.4 % Deep Sets (HGQ)). Checked against [L1] (l. 2101-2110): "The
  reference's uncertainty is therefore at least the size of the 1.0-pt descriptive line", so
  "about 1 pt or more" is faithful. The arbiter named one headline site (its l. 943, now l. 961);
  the other A − 79.4 sites already cite [L1] (l. 336-337, l. 978) or are lists (l. 1104, 1225) or
  the conventions / decision rows (l. 1632, 2110, 2223). Closed.
- **"Text only" dropped from the v8 entry (l. 281-284).** Correct and required: fix 2 amends the
  pilot's composition (a separate K=3 pod), so "Text only" would be false, and the arbiter's own
  prescribed change-log line omits it (it also drops v7's "pod, K" from the no-change list). The
  fixer kept "Arbiter's verbatim wording", which holds for every site except the 5g adaptation
  above, itself disclosed. Closed.

## Edited sentences checked for correctness (the only route to a new B)

- **Power numbers, fix 4.** Recomputed (`uv run --with scipy`, noncentral t, df 7, α = 0.05
  two-sided, noncentrality d·√8): power at d = 1.16 is 0.8026 (1.15: 0.796), so 1.16 · sd_diff is
  the 80 % detectable gap. √2 · 3.145 = 4.448 pt → 1.16 · 4.448 = 5.16 → "5.2 pt"; 1.16 · 1.19 =
  1.38 → "1.4 pt"; 1.16 · 1.0 = 1.16 → "1.2 pt". Consistent with the existing 3.7 pt half-width
  (t₀.₉₇₅,₇ = 2.365; 2.365 · 4.448 / √8 = 3.72). Correct.
- **Amendment facts, fix 2.** Against `RUN.md`: A10 23,028 MiB (l. 60); A07-350-s1 attempts 0-2
  OOM, dropped (l. 73, 98); C′-s1 OOM on attempts 0 and 1, training on the third (l. 74, 134,
  146-149: reached epoch 5 at canary close), so "C′-s1 trained only on its third attempt" is
  accurate. The quoted branch matches l. 1476 ("If K=6 does not fit in GPU memory, repeat the
  canary at K=3"). The cited inventory entry exists verbatim
  (`.claude/memory/cluster-inventory.md:30`). "(the A07-350-s1 rule below)" resolves to l. 1419-1421.
  Correct.
- **Collapse label, fix 3.** "Falsifier, 'A07-350'" resolves to l. 946; "no key mask" agrees with
  `code/analysis/attn_entropy.py` docstring ("No attention mask exists in the model, so
  zero-padded constituents are attended keys"). Correct.
- **5h "entropy on validation, n = 62,000".** [A26] (l. 2088) "runs the validation split (n =
  62,000)"; the script feeds all of `x_val` unless `--n_val` is given (`attn_entropy.py:282`) and
  prints "split validation n" (l. 299). Correct (see C3).
- **5a gate arithmetic.** 58 + 8 = 66, 56 + 8 = 64. Correct.

## Earlier A and B findings, by name

- **v8 B #1** FP32-E label: resolved, l. 1178-1179.
- **v8 B #2** pilot amendment: resolved, l. 1375-1394, 1469, 2158, 2159.
- **v8 B #3** collapse label: resolved, l. 1217-1228, 1412-1413, 1258-1260 (cut drawn).
- **v8 B #4** detectable gap: resolved, l. 1113-1119, 1100-1101, 2167; numbers recomputed above.
- **v8 required C #5-#11** (5a-5h): landed, table above.
- **v7 A/B #1-#9**: closed by arbiter v8's table (evidence at fba27d5); the diff touches none of
  their sites except l. 1025-1028 and 1049-1050 (v7 #3, Holm m), where only the prescribed 5c/5d
  edits occur. No regression.

## Findings

**Category A.** None.

**Category B.** None. No edited sentence is wrong.

**Category C** (optional; all inside the arbiter's verbatim text, so none is a landing defect).

- **C1, l. 1098-1101.** The inserted clause breaks the packet list: "carries X, Y, and the n …;
  the 80 %-power detectable gap …; it does not carry …". Fix: move "and" before the new item
  ("…, the n the formula gives …, and the 80 %-power detectable gap …; it does not carry").
- **C2, l. 1117-1118.** "detectable at 8 pairs only if sd_diff comes in near 1 pt" is loose: a
  1.0-pt cost reaches 80 % power at 8 pairs only for sd_diff ≤ 1.0 / 1.16 = 0.86 pt (at 1.0 pt
  the detectable gap is 1.2 pt, as the preceding sentence says). Fix: "only if sd_diff comes in
  at or below about 0.86 pt". REPORT should use the number either way.
- **C3, l. 1259.** The figure states n = 62,000, while `attn_entropy.py:282` accepts `--n_val`
  for a subset. Fix (PREFLIGHT or REPORT, not STUDY): take the figure's n from the script's printed
  "split validation n" line, not from the spec.
- Outside this review's scope, for the orchestrator: under the per-pod rule (l. 1469) C′-s1 is an
  arm that trained in the K=6 pod but has no epoch-10 read (`RUN.md` l. 146-149, 197, 199). The
  STUDY text is correct; the RUN canary record must still carry C′-s1's epoch-10 read (or report
  it as missing) before the canary verdict covers it.

## Competing group

For the four v8 B items, nothing a competing group would add is absent now: the collapse cut is
fixed before the epoch-500 readout, the detectable gap is stated, the reference noise reaches the
figure, and the OOM pilot has a dated amendment. The production packing remains open by design
(Kai, [D15] packet, l. 2159).
