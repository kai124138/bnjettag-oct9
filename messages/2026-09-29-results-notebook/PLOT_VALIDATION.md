# Plot validation: results notebook, 2026-09-29 (v1)

Artifact: `messages/2026-09-29-results-notebook/`: `results_summary.ipynb` (executed 2026-09-29
05:56 PDT), figure code `nbhelpers.py`, `figures/fig01…fig11` (.png and .svg), `README.md`.
Checked 2026-09-29 by the plot-validator. Read-only review: no figure, script or notebook was
edited. Every rendered PNG was opened and inspected. Close-up crops were taken where text and
data might collide.

## 1. `tools/plot_check.py` output (verbatim)

`python3 tools/plot_check.py messages/2026-09-29-results-notebook/nbhelpers.py messages/2026-09-29-results-notebook/figures` (exit 0):

```
== messages/2026-09-29-results-notebook/nbhelpers.py
   ok
== messages/2026-09-29-results-notebook/figures
   ok

worst grade: C
```

The checker misses two things here. `nbhelpers.py:14` declares `plot_check: allow-fontsize`.
The slide sizes are also set as inline rcParams in `apply_style()` (`nbhelpers.py:116-126`),
which the checker never inspects (see B13).

## 2. Verdict

- **Red flags: none.**
  - Every AUC or accuracy drawn names its split.
  - Both ROC figures (fig03, fig11) put the mistag rate on a log y axis.
  - Every legend and annotation number recomputed here matches its source (section 5).
  - All 11 figures exist and render as PNG and SVG.
  - The 11 PNGs embedded in the notebook are byte-identical to `figures/*.png`.
- **Category A: 1.** A1: fig05 lacks the post-hoc caveat its VERIFY.md requires on outward text.
- **Category B: 13.** B1-B13. Eleven are violations; B4 and B7 are warnings graded B.
- **Category C: 9.** C1-C9. C8 applies to all 11 figures.
- **Era firewall: holds on every figure.**
  - Current EBOP-constrained results are the only data in fig01-03 and fig07-08.
  - The Round-14 and r15-gamma results are the only data in fig04 and fig11. Both are labelled ARCHIVED.
  - The pT-reweighting results are the only data in fig05-06, labelled "no EBOP target".
  - fig09-10 are infrastructure telemetry.
  - The *reported* A02/A11 numbers appear only in tables, never on a figure.
- **Validation vs held-out: never mixed on one figure.**
  - fig08 is validation only (n = 62,000).
  - All other metric figures are held-out / ROC-test only (n = 260,000).
  - Two wording problems remain: B2 and C5.
- **Status labels in the image:**

  | figure | status label in the image |
  |---|---|
  | fig04, fig11 | "ARCHIVED" |
  | fig07-10 | "telemetry" |
  | fig05-06 | "numbers match VERIFY.md" |
  | fig01-03 | none; they say "recomputed from saved logits" (B1) |

Fix A1 before fig05 goes onto a slide. B9 (type size) and B13 (style) are one change to the slide style. B1-B3, B10 and B11 are one-line caption or label edits.

## 3. Code checks (Part 1)

| check | result |
|---|---|
| No hand-typed arrays | **PASS.** Every plotted value comes from an `.npz`, a csynth JSON, a Vivado report, a JSON record or a saved log. `BUILDS`, `ARM_NAMES` and `ARM_SHORT` are text only. Some provenance text is typed rather than loaded (C6). |
| Readable names, not code identifiers | **VIOLATION (B).** `PTW5`, `PTWNC`, `BASE` (`nbhelpers.py:590, 608`); pilot arm codes (`:430, :638`); `E × k` / `A07 × k` (`:664`); `A07-k3` and a Python `True` (`:702-704`); `r15 gamma` (`:348`). See B10, B11, C2 and C4. |
| Referenced figures exist; unique names; PNG and vector from one run | **PASS.** All 11 exist, each once. SVG canvas sizes equal the PNG sizes to 0.03 in. Quick Look renders of the SVGs match the PNGs (the narrow figures differ only by anti-aliasing, mean abs diff 5.6-8.8/255). Quick Look crops wide SVGs to a square thumbnail; the visible region of fig04 matches its PNG. All 11 notebook-embedded PNGs are byte-identical to the files on disk (sha256). PNGs are 200 dpi, as the README states. |
| Error bars have a stated method | **PASS.** fig05 and fig06 use a 95 % paired t-interval, df 7, over 8 seeds, stated in the image. No other figure draws an error bar. |
| House style applied | **VIOLATION (B), B13.** `docs/style/bnjettag.mplstyle` is loaded, then overridden inline for slides. |
| Axes titles / dual axes / chartjunk | **PASS.** No `set_title`, no dual y axes, one measure per panel (fig04 and fig05 split two measures into two panels). |

## 4. Figures (Part 2)

Slide-size assumption, used for every "effective size" below: each figure is fitted to the
12.3 × 6.0 in content area of a 13.33 × 7.5 in (16:9) slide, under a title band. Effective
size = nominal pt × min(12.3/W, 6.0/H). Nominal sizes come from `apply_style()`: axis labels
14 pt, ticks 12 pt, `small` (direct labels, panel labels, provenance line) 11.7 pt, legend
11 pt. Floor used: 12 pt.

| figure | canvas (in) | scale | ticks | small text | legend |
|---|---|---|---|---|---|
| fig01 | 6.68 × 5.17 | 1.16 | 13.9 | 13.5 | 12.8 |
| fig02 | 6.68 × 5.14 | 1.17 | 14.0 | 13.6 | 12.8 |
| fig03 | 6.45 × 4.95 | 1.21 | 14.5 | 14.1 | 13.3 |
| fig04 | 13.78 × 7.53 | 0.80 | **9.6** | **9.3** | – |
| fig05 | 9.78 × 5.08 | 1.18 | 14.2 | 13.8 | – |
| fig06 | 7.65 × 5.27 | 1.14 | 13.7 | 13.3 | 12.5 |
| fig07 | 13.91 × 7.64 | 0.78 | **9.4** | **9.2** | **8.6** |
| fig08 | 13.91 × 7.08 | 0.85 | **10.2** | **9.9** | – |
| fig09 | 8.88 × 8.72 | 0.69 | **8.3** | **8.0** | – |
| fig10 | 6.21 × 5.18 | 1.16 | 13.9 | 13.5 | 12.7 |
| fig11 | 11.78 × 5.08 | 1.04 | 12.5 | 12.2 | 11.5 |

### fig01_current_auc_vs_ebops: B1, B2, B3, B4; C3

**PASS:**
- The y axis names the metric, the split and n ("held-out macro-OvR AUC (n = 260,000)").
- The image carries "Current era, EBOP-constrained", N = 8, the input set, seed 1 per arm, single run, no interval.
- The 350,000 target is marked on the EBOPs axis.
- All 7 plotted AUCs equal `ablation_metrics.json`: the notebook's check table shows Δ = 0 for all 7, and 3 were recomputed independently (section 5).
- The x range fits the data. The direct labels do not overlap each other or the markers.
- Effective type is 13.5-16.2 pt.

**Violations:**
- **B1. Status label. VIOLATION (B).** The image carries no status word. The notebook's *verified* means "recomputed here". `campaigns/2026-09-16-accuracy-investigation/` has no VERIFY.md, so these values have not passed the project's VERIFY step. The same applies to fig02 and fig03.
  *Fix:* in the provenance line, write "Status: recomputed here from saved logits; no VERIFY.md for this campaign".
- **B2. Split wording. VIOLATION (B).** The provenance line reads "Held-out split = Zenodo validation archive (held out from training)". That puts the word "validation" under a held-out number on a figure bound for a slide; CLAUDE.md requires that validation and ROC-test numbers never meet unlabelled. Same text in fig02.
  *Fix:* "Held-out (ROC-test) split: the dataset's public val archive, never used in training or checkpoint selection".
- **B3. Missing caveat. VIOLATION (B).** The image lacks the notebook caption's warning: one seed per arm, a 0.0128 AUC span, "the vertical order is not an established ranking". A slide viewer sees a ranking. Two markers touch the target line: gradual budget at 349,550 and fixed-width recovery at 349,390. The image never states that all 7 are under the target. Same in fig02.
  *Fix:* add one line: "All 7 checkpoints ≤ 350,000 EBOPs; one seed per arm, so the vertical order is not a ranking."
- **B4. Unmarked incomplete run. WARNING (B).** The distillation point comes from a run the manifest marks `complete: False` (898 of 1,000 epochs, `generation: epoch-0898`), while `ablation_metrics.json` says `status: finished`. It is drawn as a peer of the six complete runs. Same in fig02.
  *Fix:* use an open marker, or add "(stopped at 898/1,000 epochs)" to its label.
- **C3.** Entity colour reused (see the C list below).

### fig02_current_accuracy_vs_ebops: B1, B2, B3, B4, B5; C3

**PASS:**
- The y axis reads "held-out top-1 accuracy [%] (n = 260,000)".
- Target marked, era label present, values match the JSON (section 5).
- Effective type is 13.6-16.3 pt.

**Violations:**
- **B1, B2, B3, B4** as in fig01.
- **B5. Label ambiguity. VIOLATION (B).** In the right-hand cluster (crop checked), "gradual budget" floats one line above "tensor-wise". "fixed-width recovery" sits directly above the distillation marker at 348,366; its own marker is at 349,390. There are no leader lines, so two of the four labels can be read against the wrong point.
  *Fix:* draw leader lines (`annotate(..., arrowprops=...)`). Or place the right-most label of each pair to the right of the target line.
- **C3** as in fig01.

### fig03_current_roc_best_auc: B1, B6, B7

**PASS:**
- HEP convention: tagging efficiency on a linear x axis, mistag rate on a log y axis.
- Every curve lies below mistag = efficiency.
- The split is named on both axes. n, seed 1 and single run are in the image.
- The legend's per-class AUCs (g 0.806, q 0.857, W 0.857, Z 0.842, t 0.905) equal an independent recompute from `r2-ffn32.npz`. Their unrounded mean equals the JSON's 0.853526.
- The legend clears every curve.
- Effective type is 13.3-17.0 pt.

**Violations:**
- **B1** as in fig01.
- **B6. Selection rule. VIOLATION (B).** The arm is picked as the maximum *held-out* AUC (`nbhelpers.py:559`), which is a selection on the test split. The image does not say why this arm is shown. Selecting by validation AUC picks the same arm (validation 0.8545 against the next best, 0.8518), so the curves would not change.
  *Fix:* select by validation AUC and state "arm with the highest validation AUC" in the provenance line.
- **B7. Overlapping curves. WARNING (B).** W (dotted) and Z (dash-dot) overlap over efficiency 0.3-0.6. There the two patterns merge into one (crop checked), so at slide size the two classes cannot be told apart.
  *Fix:* direct labels at the right-hand end, or line styles that differ more strongly.

### fig04_archived_csynth_dsp_lut: B8, B9; C1, C2, C6

**PASS:**
- ARCHIVED is in the image. So are "Not implemented hardware", the part and the clock. All 11 csynth reports use `xcvu13p-flga2577-2-e` and 2.50 ns, so the single caption clock holds for every row.
- Resources appear as counts and as % of the VU13P: DSP count with %, LUT % with the M-count.
- Every bar and value label equals its `csynth_report.json`.
- Every row is an N = 8, seed-3 build from before 2026-09-10:
  - W1A6 config: `r14-l1x3-n8-w1a6`.
  - W1A4 config: `r14-l1x3-n8-w1a4`.
  - r15-gamma config: `r15-gamma-sm4i0-n8-w1a8`, synthesized 2026-08-23.
- Colours follow the entity order.
- Value labels do not collide with the right-hand panel.

**Violations:**
- **B8. DSP axis range. VIOLATION (B).** The DSP axis runs to 4.2 × 10^8 (`xlim = max × 3000`, `nbhelpers.py:717`). The ticks at 10^6, 10^7 and 10^8 mark three decades that hold no data and exist only to fit the value labels.
  *Fix:* cap the axis near 10^6 and hide ticks above 10^5, or move the value labels into a text column.
- **B9. Legibility. VIOLATION (B).** Effective type is 9.3-9.6 pt at slide size, below the 12 pt floor.
  *Fix:* a slide style with larger type relative to the canvas (see B13), or a narrower tick-label column.
- **C1, C2, C6:** see the C list below.

### fig05_ptw_paired_gaps: A1, B10; C6

**PASS:**
- Every drawn value equals `campaigns/2026-09-25-pt-weighting/VERIFY.md`:
  - PTW5 − BASE macro AUC: −0.0108 [−0.0124, −0.0093].
  - PTWNC − BASE macro AUC: −0.0125 [−0.0148, −0.0101].
  - Accuracy: −1.54 [−1.83, −1.25] pp and −1.84 [−2.23, −1.45] pp.
  - 8/8 seeds lower.
- The error-bar method, the seed count and n are in the image.
- "Round-14 N = 8 W1A8 configuration, no EBOP target" keeps it apart from the current era.
- Effective type is 13.8-16.6 pt.

**Violations:**
- **A1. Missing post-hoc caveat. VIOLATION (A).** The pt-weighting VERIFY.md states: "It does not certify a pre-registered test, and outward text must say so." The in-image provenance says only "numbers match VERIFY.md (2026-09-26)", which on a slide reads as a certified result. The caveat is in the notebook's markdown caption, not in the pixels, and slides are made from the pixels. fig06 carries its own binning caveat; fig05 carries none.
  *Fix:* append to the provenance line "Metric and comparison were fixed after the results: the arithmetic is verified, not a pre-registered test."
- **B10. Code identifiers. VIOLATION (B).** The x tick labels are the arm codes "PTW5 − BASE" and "PTWNC − BASE". Same in fig06's legend.
  *Fix:* "pT-weighted (cap 5) − unweighted" and "pT-weighted (no cap) − unweighted", following VERIFY.md's cap-5 / no-cap naming.
- **C6:** see the C list below.

### fig06_ptw_pt_bins: B10; C6, C9

**PASS:**
- The bins equal VERIFY.md:
  - edges 980/1006/1022/1046/1106 GeV, span 159-3157;
  - 42,580-43,929 jets per bin;
  - bin 1: +0.0047 [+0.0020, +0.0074];
  - bin 6: +0.0165 [+0.0114, +0.0215] and [+0.0109, +0.0222].
- The post-hoc caveat is in the image: "Binning chosen after the results … descriptive, not a test".
- The legend clears the data. Units are GeV.
- Effective type is 12.5-15.9 pt.

**Violations:**
- **B10** as in fig05; here it is the legend entries.
- **C6, C9:** see the C list below.

### fig07_chang_pilot_ebops: B9, B11; C3, C7

**PASS:**
- "Pilot telemetry, not a result" is in the image.
- Log y axis.
- Each panel's target comes from its log: `target=350000` for A, `target=5000000` for C (checked in the raw logs).
- All 8 logs are N = 64 and 7,000-epoch schedules, so the single N and schedule in the caption hold.
- The legend sits outside the axes.
- The arms appear as small multiples on separate axes, not as one trend.

**Violations:**
- **B11. Arm codes. VIOLATION (B).** The panel labels (A-s1, A-s2, A07-350-s1, C-s1, C′-s1, D-s1, E1-s1, F-s1) are campaign arm codes with no key in the image. The dashed target lines sit at two heights (350,000 and 5,000,000) with no value printed, so a viewer cannot tell why C and C′ differ.
  *Fix:* print the target value beside each dashed line. Add a key line to the caption, e.g. "A: Sun et al. recipe on the binary E model at 350k; C: the recipe on A07 at 5M; D: our optimizer, 350k; F: E + learned PE, 350k; A07-350: A07 at 350k" (from the training-batch STUDY.md arm table).
- **B9. Legibility. VIOLATION (B).** Effective type is 8.6-9.4 pt at slide size.
- **C3, C7:** see the C list below.

### fig08_chang_pilot_valacc: B9, B11, B12

**PASS:**
- The y axis reads "validation top-1 accuracy [%] (n = 62,000)". That n matches the STUDY.md split: 90/10 [D8] of 620,000.
- "Pilot telemetry, not a result" and "the pre-registered readout at epoch 500 decides" are in the image.
- No held-out number appears on this figure.

**Violations:**
- **B11.** Arm codes with no key, as in fig07.
- **B12. Panel labels in the data region. VIOLATION (B).** The panel labels sit inside the data region at the top right. In C-s1 the text "last epoch 84" clears the curve (about 63 % near epoch 79) by a few pixels (crop checked). The figure is rebuilt from the newest log copies and the shared epoch axis will stretch, so on a rerun the curves (45-68 %) will run under the labels. fig07 has the same placement, but its EBOPs curves fall away from the labels.
  *Fix:* place the labels above the frame (`y = 1.02` in axes coordinates) or at the lower left.
- **B9. Legibility.** Effective type is 9.3-10.2 pt at slide size.

### fig09_gpu_benchmark_throughput: B9, B11; C9

**PASS:**
- "Benchmark telemetry, provisional" is in the image. Units are "arm-epochs per wall-clock hour".
- The value labels match the saved logs: A10 E×3 took 1,880.3 s for 21 epochs, giving 121; A100 E×16 took 3,902.7 s, giving 310.
- The longest value label fits inside the axes (crop checked).
- The bars keep job order, not throughput order, consistent with "no product ranking".

**Violations:**
- **B9. Legibility. VIOLATION (B).** This is the worst case: effective type is 8.0-8.3 pt. The square 8.9 × 8.7 in canvas (height grows 0.7 in per bar, `nbhelpers.py:663`) must shrink by 0.69 to fit a slide.
  *Fix:* a wider, shorter canvas, or two panels (E and A07).
- **B11. Code identifiers. VIOLATION (B).** The tick labels "E × 3" and "A07 × 1" are campaign codes. The caption gives "E class / A07 class" without saying what E and A07 are, or that "× K" means K arms sharing one GPU.
  *Fix:* a key line in the caption.
- **C9:** see the C list below.

### fig10_delta_canary_gpu_memory: C3, C4

**PASS:**
- "Memory-canary telemetry, not a result" is in the image.
- Every value matches `campaigns/2026-09-27-delta-screen/logs/20260929T0608Z-canary-a07_k_result.json`: phase A07-k3, 3 arms tested, 2 accepted, `oom: true`, card 23,028 MiB, pod peak 22,545 MiB (22.0 GiB on the plot), rule fraction 0.9.
- Units are GiB and minutes. The legend clears the trace.
- Effective type is 12.7-16.2 pt.

**Violations:**
- **C3, C4:** see the C list below.

### fig11_archived_r14_roc_n8: C5, C6, C9

**PASS:**
- HEP convention: linear efficiency on x, log mistag on y. Every curve lies below mistag = efficiency.
- ARCHIVED and "not comparable to the EBOP-constrained runs" are in the image. So are the split on both axes, n = 260,000, seed 3 and single run.
- All 10 legend AUCs equal both the per-seed table in `bnjettag/roc-results/r14/n8/roc_auc.md` and an independent recompute:
  - t: 0.919, 0.920, 0.914, 0.912, 0.908.
  - W: 0.907, 0.905, 0.892, 0.891, 0.854.
- The legends and the "t vs rest" / "W vs rest" labels clear the curves.
- Colours follow the entity order.
- Effective type is 11.5-14.6 pt (the legend is marginally under the floor).

**Violations:**
- **C5, C6, C9:** see the C list below.

### Findings that span figures

- **B13. Style. VIOLATION (B).** `apply_style()` (`nbhelpers.py:116-126`) loads the journal style and then overrides figure size, every font size, line widths, marker size and dpi inline.
  - `docs/conventions/figures.md` says "Font sizes come from the style, not the call". It names `docs/figures/style/bnjettag-c-poster.mplstyle` as the talk alternate: sans 18/20/16 pt, 10 × 6.5 in, light grid.
  - The notebook's override (serif, 14/12/11 pt, 7 × 4.4 in) matches neither file.
  - Because the large canvases (fig04, fig07-09) keep 12 pt type, their text shrinks below the floor on a slide (B9).
  - *Fix:* export the slide figures with the C file. If the serif slide look is preferred, put it on a contact sheet for Kai's pick (the CLAUDE.md taste rule) and save it as a named style file.

C items (WARNING, C):
- **C1. Caption (fig04).** "ARCHIVED (Round 14, …)" also covers the r15-gamma retrain row. Write "Round 14 and its r15-gamma retrain", as the notebook's section 3 text does.
- **C2. Internal jargon (fig04 tick labels).** "r15 gamma", "(structure only)", "PTQ control".
- **C3. Palette.**
  - fig01-02 draw the current-era arms in the W1A8 entity green (`nbhelpers.py:541`). Those arms are EBOP-constrained binary models with learned activation widths, not the Round-14 W1A8 variant. The notebook's own rule is black for single-family plots.
  - fig07's target line and fig10's packing-rule line reuse the W1A6 orange, which means W1A6 in fig04 and fig11.
- **C4. Code-style text (fig10).**
  - The image prints the Python literal "True" and the codes "A07-k3" and "K".
  - The out-of-memory event is not marked. The sampled trace peaks at 22.0 GiB, under the card line, so "Out-of-memory recorded: True" has no visible counterpart.
  - "90%" drops the space the other figures use ("95 %").
- **C5. Split naming across the deck.** fig11 says "ROC-test split"; fig01-03 and fig05-06 say "held-out" for the same 260,000-jet archive (VERIFY.md and `roc_auc.md` both call it ROC-test). Side by side on slides, the two names read as two splits. Use one name, e.g. "held-out (ROC-test)".
- **C6. Typed provenance text.** These strings are typed rather than read from a file. All are correct today, but they will not follow a source change.
  - "Vitis HLS 2023.2" (fig04): consistent with the "Version: 2023.2" line in the saved reports.
  - The dates "2026-09-25" and "2026-09-26" (fig05-06): consistent with the campaign and its VERIFY.md.
  - "l1x3" (fig11): consistent with the `roc_auc.md` header.
- **C7. Unclear label (fig07).** "traced EBOPs (full split)" does not say which split. The caption's "Validation = internal split, n = 62,000" line belongs to fig08.
- **C8. No source in the image (all 11 figures).** No figure names its source file or campaign; `docs/conventions/figures.md` lists the source file as part of the provenance caption. A short "Source: <campaign>/<dir>" tag would close this.
- **C9. Cosmetic.**
  - fig06: "pT" is plain text rather than p_T.
  - fig09: inward y ticks draw into the bars.
  - fig11: FP32 (#243746) and W8A8 (#0072B2) are both dark blue and overlap along most of the t panel.
  - The SVG text is converted to paths, so the SVGs are not text-editable (`svg.fonttype: none` would keep text).

## 5. Spot-check of the headline table

Method: an independent script that does not import `nbhelpers.py`.
1. Each arm in `publication/results/post_conference/ablation_metrics.json` is matched to its array file through `checkpoint_sha256` in `campaigns/2026-09-16-accuracy-investigation/remote-results/manifest.json`.
2. Softmax is applied to the saved logits.
3. `roc_auc_score` runs per class, one-vs-rest, and the macro value is the unweighted mean. It equals `average="macro"`.
4. Top-1 accuracy is the argmax match.
5. Labels come from `labels.npz`: test (260000, 5) and validation (124000, 5), one-hot.

The "raw logits" column is a control: macro AUC on the logits without softmax.

| arm | quantity | notebook table | stored (JSON) | recomputed (softmax) | raw-logit control |
|---|---|---|---|---|---|
| Reduced feed-forward width | held-out macro-OvR AUC, n = 260,000 | 0.8535 | 0.853526 | 0.853526 | 0.817946 |
| | held-out top-1 accuracy | 58.31 % | 0.583131 | 0.583131 | – |
| | validation macro-OvR AUC, n = 124,000 | 0.8545 | 0.854457 (selection time) | 0.854452 | – |
| | validation top-1 accuracy | 58.52 % | 0.585234 | 0.585234 | – |
| | EBOPs | 329,838 | 329,838 | manifest 329,838 = Σ per layer | – |
| Channel-wise quantization | held-out macro-OvR AUC | 0.8508 | 0.850795 | 0.850795 | 0.822529 |
| | held-out top-1 accuracy | 58.74 % | 0.587431 | 0.587431 | – |
| | validation macro-OvR AUC | 0.8518 | 0.851884 (selection time) | 0.851802 | – |
| | validation top-1 accuracy | 58.89 % | 0.588879 | 0.588879 | – |
| | EBOPs | 317,890 | 317,890 | 317,890 | – |
| Tensor-wise quantization (baseline) | held-out macro-OvR AUC | 0.8445 | 0.844527 | 0.844527 | 0.789961 |
| | held-out top-1 accuracy | 57.48 % | 0.574758 | 0.574758 | – |
| | validation macro-OvR AUC | 0.8453 | 0.845267 (selection time) | 0.845266 | – |
| | validation top-1 accuracy | 57.67 % | 0.576710 | 0.576710 | – |
| | EBOPs | 348,526 | 348,526 | 348,526 | – |

Result: all 15 numbers agree.
- The held-out values agree exactly with the JSON.
- Raw logits miss by 0.028-0.055 AUC. So the softmax step is required, as the `nbhelpers.py` docstring says.
- For channel-wise validation AUC, the notebook prints the fresh recompute (0.8518). The JSON's selection-time value rounds to 0.8519. The notebook's check table discloses the −8.2e-05 difference; no action needed.

Other figure numbers checked against their sources:
- fig03 legend: per-class AUCs from `r2-ffn32.npz`.
- fig11 legend: 10 per-class AUCs from `bnjettag/roc-results/r14/n8/*-s3.npz` and `roc_auc.md`.
- fig05-06: VERIFY.md gap and bin tables.
- fig04: 11 csynth JSONs.
- fig09: `PHASE_DONE` lines in the saved benchmark logs.
- fig10: the canary `k_result.json`.
- fig07: `target=` fields in the pilot logs.

All agree.

Source observations for Kai. These are not figure violations and are left unresolved here:
- **Distillation run status.** `manifest.json` records `r6-distill` as `complete: False` (`completed_epochs: 898`, `generation: epoch-0898`). `ablation_metrics.json` records the same checkpoint as `status: finished`. The headline row "898 / 184" and the fig01-02 distillation point rest on this run.
- **Dates.** In `ablation_metrics.json`, `evaluation_date` (2026-09-16) precedes `training_completion_date` (2026-09-20).

## 6. How the checks were run

- **Mechanical check:** `python3 tools/plot_check.py` (section 1).
- **Visual inspection:** all 11 PNGs opened. Crops were taken at 200 dpi pixel scale of:
  - fig01-02, the target-line cluster;
  - fig03, the curves at efficiency 0.3-0.6;
  - fig08, the C-s1 panel;
  - fig09, the longest value label;
  - fig10, the memory peak.
- **SVG and embedding checks:**
  - SVG to PNG agreement: Quick Look (`qlmanage -t`) renders, trimmed, resized and diffed.
  - Canvas sizes compared from the SVG headers.
  - Notebook to disk: sha256 of every base64 PNG in the `.ipynb` outputs against `figures/*.png`.
- **Recompute environment:** `python3` (`.venv-chang`: numpy 2.5.1, scikit-learn 1.9.0). Image crops used `.venv-hgq2` (Pillow). Nothing was computed in the lab pod. No figure, script or notebook was modified.

---

# v2: scoped re-validation after commit 486c545 (2026-09-29)

Scope, as requested:
1. whether each v1 A/B item is resolved in the rendered PNGs;
2. whether the fixes introduced new problems: clipped or overlapping text, status and split
   labels, the era firewall, the log mistag axis, validation vs held-out mixing, and text under
   12 pt on a 16:9 slide;
3. `tools/plot_check.py` on `nbhelpers.py` and `figures/`.

Artifact state: `nbhelpers.py`, `results_summary.ipynb` and `figures/fig01…fig11` (.png and
.svg) as committed in 486c545; the figures were written at 06:30 PDT. All 11 PNGs were opened.
Close-up crops at pixel scale:
- fig01 and fig02: the top of the y label and the target-line cluster;
- fig04: the LUT value labels;
- fig06: the last tick label;
- fig07: the target labels in panels 4, 7 and 8;
- fig10: the annotation leader;
- fig11: the t-panel legend.

This review is read-only: no figure, script or notebook was edited.

## v2.1 `tools/plot_check.py` output (verbatim)

`python3 tools/plot_check.py messages/2026-09-29-results-notebook/nbhelpers.py messages/2026-09-29-results-notebook/figures` (exit 0):

```
== messages/2026-09-29-results-notebook/nbhelpers.py
   ok
== messages/2026-09-29-results-notebook/figures
   ok

worst grade: C
```

The v1 blind spot is closed. `apply_style()` (`nbhelpers.py:116-119`) loads the house style and
then `docs/figures/style/bnjettag-c-poster.mplstyle`, with no inline rcParams. The
`allow-fontsize` pragma (`nbhelpers.py:15`) remains. It covers the one relative size,
`"small"`, which is 15.0 pt nominal under the C style. No text in any figure is set smaller than
`"small"`.

## v2.2 Verdict

- **Red flags: none.**
  - Every AUC and accuracy drawn names its split. Checked in the pixels of fig01-03, fig05-06,
    fig08 and fig11.
  - fig03 and fig11 keep the mistag rate on a log y axis and the efficiency linear on x. Every
    curve lies below mistag = efficiency.
  - Every legend and annotation number equals its source:
    - fig03 and fig11: the legend AUCs are unchanged from v1.
    - fig09: all 12 bars equal an independent recompute from the saved logs (see fig09).
    - fig10: the peak, the out-of-memory flag, the arm count and the accepted K equal the
      canary JSON.
    - fig07: each target equals the `target=` field of its log.
  - All 11 figures exist and render. The 11 PNGs embedded in the notebook are byte-identical to
    `figures/*.png` (sha256).
- **Category A: 1, new.** V2-A1: the y label of fig01 is clipped at the top edge of the image.
  No information is lost, so the arbiter may downgrade it to B. The fix is one line.
- **Category B: 1, new.** V2-B1: the SVG copies now keep their text as text in 'DejaVu Sans'.
  That font is not installed on this Mac, so the SVGs render in a serif fallback. The v1 C9
  suggestion caused this.
- **Category C: 9** (V2-C1 to V2-C9), new or left over from v1.
- **v1 items:**
  - A1 is resolved.
  - B1-B13 are all resolved.
  - C1-C5, C7 and C8 are resolved.
  - C6 and C9 are partly resolved (v2.4).
- **Distillation label: accurate** (v2.5).
- **Era firewall: holds.**
  - fig01-03 show the current era only.
  - fig04 and fig11 show ARCHIVED results only.
  - fig05-06 carry "Round-14 configuration … no EBOP target".
  - fig07-10 are labelled telemetry.
- **Validation vs held-out: not mixed.**
  - fig08 is validation only; n = 62,000 is in its caption.
  - fig03's provenance now gives the validation AUC that picked the arm (0.8545,
    n = 124,000) next to the held-out curves. Both carry split and n, which CLAUDE.md allows:
    the rule is that they never meet unlabelled.
- **Type size on a 16:9 slide: every figure is at 12 pt or more** (v2.3).

Before 14:55Z, fix V2-A1 only. V2-B1 affects only the SVG copies. The PNGs embedded in the
notebook and pasted onto slides are not affected. Read v2.6 before any rerun.

## v2.3 Effective type size

The slide assumption is the same as in v1: each figure is fitted to the 12.3 × 6.0 in content
area of a 13.33 × 7.5 in slide, under a title band. Nominal sizes from the C style: ticks 16 pt,
legend 16 pt, axis labels 20 pt. `"small"` is 15.0 pt; it sets the provenance lines, direct
labels, panel labels and value labels, and is the smallest text in every figure.

| figure | canvas (in) | scale | ticks | smallest text | legend | axis labels |
|---|---|---|---|---|---|---|
| fig01 | 9.36 × 6.81 | 0.881 | 14.1 | 13.2 | – | 17.6 |
| fig02 | 9.22 × 6.77 | 0.886 | 14.2 | 13.3 | – | 17.7 |
| fig03 | 9.43 × 6.43 | 0.934 | 14.9 | 14.0 | 14.9 | 18.7 |
| fig04 | 14.26 × 6.72 | 0.863 | 13.8 | 12.9 | – | 17.3 |
| fig05 | 12.68 × 6.25 | 0.961 | 15.4 | 14.4 | – | 19.2 |
| fig06 | 10.72 × 6.69 | 0.897 | 14.3 | 13.4 | 14.3 | 17.9 |
| fig07 | 13.39 × 7.06 | 0.850 | 13.6 | 12.7 | 13.6 | 17.0 |
| fig08 | 13.37 × 6.26 | 0.920 | 14.7 | 13.8 | – | 18.4 |
| fig09 | 14.60 × 6.27 | 0.842 | 13.5 | 12.6 | – | 16.8 |
| fig10 | 8.71 × 5.83 | 1.030 | 16.5 | 15.4 | 16.5 | 20.6 |
| fig11 | 12.66 × 5.73 | 0.971 | 15.5 | 14.6 | 15.5 | 19.4 |

Every figure passes the 12 pt floor. The closest are fig09 (12.6 pt), fig07 (12.7 pt) and fig04
(12.9 pt). In v1, fig04 and fig07-09 fell to 8.0-10.2 pt and the fig11 legend to 11.5 pt.

## v2.4 v1 items

| v1 item | figure(s) | v2 | evidence in the image |
|---|---|---|---|
| A1 post-hoc caveat | fig05 | **resolved** | The first provenance line reads "Metric and comparison were fixed after the results: the arithmetic is verified, not a pre-registered test (the campaign's VERIFY.md)." fig06 opens with the same line. |
| B1 status label | fig01-03 | **resolved** | "Status: verified (recomputed here from saved arrays); this campaign has no VERIFY.md." |
| B2 split wording | fig01-02 | **resolved** | "Held-out (ROC-test) split: n = 260,000 jets never used in training or checkpoint selection." The word "validation" no longer sits under a held-out number. |
| B3 ranking caveat | fig01-02 | **resolved** | "All 7 of 7 checkpoints at or under 350,000 EBOPs. One seed per arm, so the order is not a ranking." True: the highest is 349,550 (gradual budget). |
| B4 incomplete run | fig01-02 | **resolved** | The distillation point has an open marker and the label "distillation (interim snapshot, epoch 898 of 1,000)". The caption adds "Open marker: interim snapshot, not the end of training." The wording is judged in v2.5. |
| B5 label ambiguity | fig02 | **resolved** | Leader lines tie "gradual budget" and "fixed-width recovery" to their own markers (crop). One detail remains: V2-C3. |
| B6 selection rule | fig03 | **resolved** | The notebook cell picks the arm with `max(rows, key=val_auc)`. The image says "the arm with the highest validation AUC (0.8545, n = 124,000)". It is the same arm as before, so the curves did not change. |
| B7 W/Z overlap | fig03 | **resolved** | Z is now grey dash-dot with square markers; W stays black dotted. The two can be told apart over efficiency 0.3-0.6. |
| B8 DSP axis | fig04 | **resolved** | The axis is symlog from 0 to 1.96 × 10^5 (`dmax × 1.4`). The value labels moved to a text column between the panels. No decade is empty. |
| B9 legibility | fig04, fig07-09 | **resolved** | The smallest text is now 12.9, 12.7, 13.8 and 12.6 pt (v2.3). fig09 is now two panels on a wide canvas. |
| B10 PTW codes | fig05-06 | **resolved** | fig05 ticks read "weights, cap 5" and "weights, no cap" under the shared label "pT-weighted arm minus the unweighted arm, paired by seed". fig06's legend reads "pT-weighted, cap 5 minus unweighted" and "pT-weighted, no cap minus unweighted". |
| B11 arm codes | fig07-09 | **resolved** | fig07-08: plain panel labels with target and seed, and a key line in the caption. fig07 prints the target beside each dashed line. fig09: ticks such as "A10, 3 per GPU", with K defined in the caption. One wording point remains: V2-C5. |
| B12 panel labels in the data | fig08 (also fig07) | **resolved** | The labels sit above each frame (`y = 1.04` in axes coordinates). |
| B13 style | all | **resolved** | The C style is loaded with no inline overrides. DejaVu Sans, the light grid and the thick lines show in every PNG. |
| C1 caption | fig04 | resolved | "ARCHIVED (Round 14 and its r15-gamma retrain, pre-EBOP-target)". |
| C2 jargon | fig04 | resolved | Plain tick labels; "r15 gamma", "structure only" and "PTQ control" are gone. |
| C3 palette | fig01-02, fig07, fig10 | resolved | Current-era markers are black. The fig07 target line is black dashed; the fig10 packing rule is grey dotted. |
| C4 code-style text | fig10 | resolved | "Out of memory recorded: yes", "3 arms of the A07 model", "90 %". The out-of-memory event is annotated at the peak. |
| C5 split naming | all | resolved | Every figure says "held-out (ROC-test)". |
| C6 typed text | fig04-06, fig11 | partly | "Vitis HLS 2023.2" and the VERIFY dates are gone. fig04 now reads its part and clock from the report JSON. New typed strings: V2-C6. |
| C7 unclear label | fig07 | resolved | "traced EBOPs (periodic full trace)". |
| C8 no source | all | resolved | Every figure ends with "Source: <path>". |
| C9 cosmetic | fig06, fig09, fig11, SVG | partly | fig06: the axis now uses p_T, but the legend keeps plain "pT" (V2-C7). fig09: the y ticks are gone. fig11: the FP32/W8A8 overlap is unchanged (V2-C2). SVG: text is now kept as text, which caused V2-B1. |

## v2.5 The distillation label ("interim snapshot, epoch 898 of 1,000")

**Judgment: accurate.** The three sources agree once it is clear which run state each one
describes:
- `campaigns/2026-09-16-accuracy-investigation/remote-results/manifest.json`, run `r6-distill`:
  `generation: epoch-0898`, `completed_epochs: 898`, `complete: false`, selected epoch 183
  (zero-based), checkpoint sha256 `5d4979bf…`.
- `publication/results/post_conference/ablation_metrics.json`, arm `knowledge_distillation`:
  the same checkpoint sha256, `completed_epochs: 898`, `selected_epoch_one_based: 184`,
  `status: finished`. Its `evaluation_date` is 2026-09-16 and its `training_completion_date`
  is 2026-09-20.
- `publication/results/post_conference/ablation-training-status-20260920.json`, arm
  `knowledge_distillation`: `training_complete`, `completed_epochs: 1000`,
  `training_horizon_epochs: 1000`. The job completed at 2026-09-20T06:08Z.

Together they say that the plotted checkpoint was selected from a snapshot taken at epoch 898
of a 1,000-epoch run, and that the run later finished.
- "Interim snapshot" and "not the end of training" are both supported.
- "Stopped early" would contradict the status file.
- The 1,000 is read from the status file's horizon (`nbhelpers.py:211-213`), not typed.
- Only this arm gets the open marker. The label and the caption say the same thing in fig01 and
  fig02.

One refinement is listed as V2-C1. "Epoch 898" can be read as the epoch of the plotted
checkpoint. The selected checkpoint is actually epoch 184 (one-based), chosen from the first 898
epochs. Suggested wording: "distillation (selected from an interim snapshot at epoch 898 of
1,000)". The numbers drawn for the point are correct under either reading.

## v2.6 Before any rerun

fig07-fig10 read the newest saved log copies (`load_chang`, `load_bench` globs `*/*.log`,
`load_delta_canary`). A rerun to fix V2-A1 rewrites all 11 figures. If a log copy has landed
since 06:30 PDT, fig07-fig10 can change without notice. After a rerun, compare the PNG hashes
with the set validated here. Re-validate every figure other than fig01 whose hash changed.
fig09 currently shows 12 phases.

```
4091686fc57ab39a fig01_current_auc_vs_ebops.png
1eae370831d1782d fig02_current_accuracy_vs_ebops.png
d9e14f88adecab38 fig03_current_roc_best_auc.png
235b09ebae16555c fig04_archived_csynth_dsp_lut.png
53929bf2f9eaf6a1 fig05_ptw_paired_gaps.png
1481177370da0f1c fig06_ptw_pt_bins.png
475b2fca7111477f fig07_chang_pilot_ebops.png
493cf9df53efb37b fig08_chang_pilot_valacc.png
2243f498114b9418 fig09_gpu_benchmark_throughput.png
80bdaee8adf7abd4 fig10_delta_canary_gpu_memory.png
8ad7ee0c96ee0ef3 fig11_archived_r14_roc_n8.png
```
(first 16 hex digits of each sha256)

## v2.7 Code checks (Part 1)

| check | v2 result |
|---|---|
| No hand-typed arrays | **PASS**, unchanged. `BUILDS`, `ARM_NAMES`, `CHANG_PLAIN`, `CHANG_KEY` and `PTW_PLAIN` are text only. |
| Readable names, not code identifiers | **PASS.** B10, B11, C2 and C4 are resolved. For wording, see V2-C5. |
| Referenced figures exist; unique names; PNG and vector from one run | **PASS** for existence, names and run: one write at 06:30, and the SVG canvas sizes equal the PNG sizes to within 0.04 in. The SVGs no longer render like the PNGs (V2-B1). |
| Error bars have a stated method | **PASS.** fig05 and fig06 state "95 % (paired) t-interval", df 7 and 8 seeds in the image. No other figure draws an error bar. |
| House style applied | **PASS.** The C style is used, with no inline overrides. |
| Axes titles / dual axes / chartjunk | **PASS.** There is no `set_title`. The panel headers in fig07-09 are `ax.text` labels that identify small multiples. No figure has dual y axes. |

## v2.8 Figures (Part 2)

### fig01_current_auc_vs_ebops: V2-A1, V2-C1

**PASS:**
- The y axis reads "held-out (ROC-test) macro-OvR AUC (n = 260,000)".
- The status line is present, and so is the era line with N = 8 and the inputs.
- The image says that all 7 checkpoints are at or under the target and that the order is not a
  ranking.
- The distillation point has an open marker, and the target is marked ("target 350,000").
- The direct labels overlap neither each other nor any marker (crop).
- The smallest text is 13.2 pt.

**Violations:**
- **V2-A1. Clipped text. VIOLATION (A; no information lost, the arbiter may downgrade to B).**
  - What: the image's top edge cuts the closing parenthesis of "(n = 260,000)" at the top of
    the y label. The top pixel row holds 19 dark pixels, and only about 5 of the glyph's
    roughly 33 px remain (crop at 4×).
  - Cause: the label's second line, "macro-OvR AUC (n = 260,000)", is longer than the axes are
    tall.
  - The other ten figures have no ink on any edge row or column. fig02's two-line label is not
    clipped.
  - The notebook embeds this same PNG.
  - *Fix:* split the label into three lines ("held-out (ROC-test)\nmacro-OvR AUC\n(n = 260,000)")
    or make the figure taller. Then confirm that the top pixel row is blank.
- **V2-C1. Distillation wording. WARNING (C).** See v2.5.

### fig02_current_accuracy_vs_ebops: V2-C1, V2-C3

**PASS:**
- The y label reads "held-out (ROC-test) top-1 accuracy [%] (n = 260,000)" and is not clipped:
  the top pixel row is blank.
- The status line, era line, not-a-ranking line, open marker and target are all present.
- Leader lines connect the two right-hand clusters to their markers.
- The smallest text is 13.3 pt.

**Violations:**
- **V2-C1** as in fig01.
- **V2-C3. Leader grazes a marker. WARNING (C).**
  - The "fixed-width recovery" leader passes about 5 px (at 300 dpi) above the open
    distillation marker. It then reaches its own marker at 349,390 (crop).
  - At slide size the leader and the open marker appear to touch.
  - *Fix:* put this label to the right of the target line, or start its leader below the open
    marker.

### fig03_current_roc_best_auc: V2-C4

**PASS:**
- Mistag rate is on a log y axis and efficiency on a linear x axis. Every curve lies below
  mistag = efficiency.
- Both axes name the split.
- The legend AUCs are unchanged from v1: g 0.806, q 0.857, W 0.857, Z 0.842, t 0.905.
- The arm is picked by validation AUC, and the image says so, with n.
- The status line is present.
- The legend clears every curve.
- The smallest text is 14.0 pt.

**Violations:**
- **V2-C4. Line breaks inside numbers. WARNING (C).**
  - The provenance wrap splits "(0.8545, n" from "= 124,000)"; fig05 splits "(df" from "7)".
  - *Fix:* use non-breaking spaces (U+00A0) in "n = 124,000" and "df 7". `textwrap` does not
    break at U+00A0.

### fig04_archived_csynth_dsp_lut: V2-C8

**PASS:**
- The caption says ARCHIVED and names the r15-gamma retrain.
- The tick labels are plain words, and each still matches its `BUILDS` report directory.
- The DSP axis spans the data.
- DSP is shown as count and %; LUT as % of the VU13P with the count in millions. The dashed line
  marks 100 %.
- The part and the clock are read from the report.
- "7.56M" ends inside the canvas and clear of other text (crop).
- The smallest text is 12.9 pt.

**Violations:**
- **V2-C8. Grid drawn over bars. WARNING (C).**
  - The C style turns the grid on, and matplotlib draws it above the bars (default
    `axes.axisbelow: line`).
  - In fig04, a lighter 5 px seam crosses the dark LUT bars at 200 % (pixel value 82 against
    51). fig09 has the same seams at 100, 200 and 300 (pixel value 44 against 0).
  - *Fix:* `ax.set_axisbelow(True)`.

### fig05_ptw_paired_gaps: V2-C4

**PASS:**
- The A1 caveat is in the image.
- The tick labels are plain words under a shared x label.
- Both y axes carry the split and n.
- Each arm shows 8 grey per-seed points (counted) and the mean with its 95 % t-interval; the
  image states df 7.
- The line "Round-14 configuration (N = 8, W1A8), no EBOP target" and the status "verified,
  recomputed here" are present.
- The smallest text is 14.4 pt.

**Violations:**
- **V2-C4** ("(df" / "7)" split across lines), as in fig03.

### fig06_ptw_pt_bins: V2-C7

**PASS:**
- Both caveats are in the image: the metric was fixed after the results, and so was the binning.
- The legend is in plain words and clears every point. It ends left of the last bin, and the
  bin-5 points sit near zero, far below it.
- The last tick label, "1106–3157", is fully inside the canvas (crop).
- The x axis names the split and the unit (GeV).
- The smallest text is 13.4 pt.

**Violations:**
- **V2-C7. Mixed notation. WARNING (C).**
  - The x axis writes p_T in mathtext; the legend and the caption write plain "pT".
  - *Fix:* use `$p_\mathrm{T}$` in `PTW_PLAIN` and in the caption.

### fig07_chang_pilot_ebops: V2-C5

**PASS:**
- "Pilot telemetry, not a result" is in the image.
- The plain panel labels sit above the frames and give target and seed.
- Each black dashed target line has its value beside it.
- The legend is outside the axes, and the y axis is log.
- The caption carries the key.
- The target labels clear the data in every panel. Panels 4, 7 and 8 were cropped: in each, the
  text sits on the opposite side of the line from the trace.
- The smallest text is 12.7 pt.

**Violations:**
- **V2-C5. Arm wording. WARNING (C).**
  - Arm C′ is labelled "A07 model, old quantizer", here and in fig08.
  - The training-batch STUDY.md defines C′ as A07 "on our **current** quantizer (SAT with
    k = 1, fixed 10-bit softmax output, fixed tables)", which is the branch that [D19] declined
    for the batch. "Old" can be read as obsolete.
  - *Fix:* "A07 model, our own quantizer" (or "…, pre-[D19] quantizer").

### fig08_chang_pilot_valacc: V2-C5

**PASS:**
- The y label reads "validation top-1 accuracy [%]". The caption gives "Validation = the
  pilots' internal split, n = 62,000".
- No held-out number appears.
- The panel labels sit above the frames and clear the curves.
- The lowest point (E model, seed 1, about 31 % near epoch 58) is inside the axis.
- The caption carries the key.
- The smallest text is 13.8 pt.

**Violations:**
- **V2-C5** as in fig07.

### fig09_gpu_benchmark_throughput: V2-C8

**PASS:**
- "Benchmark telemetry, provisional" is in the image.
- One panel per model, with plain tick labels. K is defined in the caption, and the unit is
  "arm-epochs per wall-clock hour".
- The value labels sit inside the axes.
- All 12 bars equal an independent recompute from `PHASE_DONE` wall time × K × 21 epochs in the
  saved logs, and every phase ended with all arms `ok`:

  | model | A10 | A100-SXM4-80GB | RTX-3090 | RTX-4090 |
  |---|---|---|---|---|
  | E | 120.6 (K = 3), 119.5 (K = 4) | 309.9 (K = 16) | 192.0 (K = 4), 200.5 (K = 5) | 249.4 (K = 5) |
  | A07 | 64.1 (K = 1), 67.6 (K = 2) | 190.1 (K = 8) | 92.7 (K = 1), 113.7 (K = 2) | 128.1 (K = 2) |

- The smallest text is 12.6 pt.

**Violations:**
- **V2-C8** as in fig04 (grid seams across the bars).

### fig10_delta_canary_gpu_memory: V2-C6, V2-C9

**PASS:**
- "Memory-canary telemetry, not a result" is in the image.
- These values equal `20260929T0608Z-canary-a07_k_result.json`, phase A07-k3:
  - out of memory recorded: yes;
  - arms per GPU accepted: 2;
  - arms tested: 3;
  - GPU: NVIDIA A10;
  - card memory: 23,028 MiB;
  - packing rule: 90 %;
  - pod peak: 22,545 MiB.
- The annotation "one arm ran out of memory, 2 kept training" agrees with the per-arm logs.
  `canary-a07-rep-c-s3-20260929T0608Z.log` ends in an out-of-memory error; s1 and s2 end with
  `CHECKPOINT_VERIFICATION_PASS`.
- The legend clears the trace.
- The smallest text is 15.4 pt.

**Violations:**
- **V2-C9. The leader crosses the data. WARNING (C).**
  - The grey leader runs diagonally from the annotation to the peak. On the way it crosses the
    packing-rule line and the 16.5 GiB plateau.
  - At slide size it can read as a fourth series.
  - *Fix:* move the text next to the peak (e.g. minute 10, 21 GiB) with a short leader, or drop
    the leader.
- **V2-C6. Typed text. WARNING (C).**
  - "one arm" is typed, while the "2" is computed: `alive` counts arms that have an RSS-gate
    record.
  - It is correct today. Computing it as `k_tested − alive` would let it follow the data.

### fig11_archived_r14_roc_n8: V2-C2

**PASS:**
- Mistag rate is on a log y axis and efficiency on a linear x axis. Every curve lies below
  mistag = efficiency.
- The caption says ARCHIVED and "not comparable to the EBOP-constrained runs".
- Both axes name the split. n, seed 3 and "single run" are in the image.
- The legend AUCs are unchanged from v1.
- The legends clear the curves. In the t-panel crop, the lowest curve at efficiency 0.46 lies
  above the top legend entry.
- "inputs pt, etarel, phirel" matches `bnjettag/code/hgq2/configs/r14-l1x3-n8-fp32.json`.
- The legend is now 15.5 pt; it was 11.5 pt in v1.

**Violations:**
- **V2-C2. Left over from v1 C9. WARNING (C).**
  - FP32 (#243746) and W8A8 (#0072B2) are both dark blue, and their curves coincide over most of
    the t panel.
  - *Fix:* keep the entity colours and give one of the two a dashed line.

### Findings that span figures

- **V2-B1. The vector copies render in a fallback font. WARNING (B).**
  - Every SVG declares `font-family: 'DejaVu Sans'` with no generic fallback. fig01, for
    example, has 31 `<text>` elements.
  - DejaVu Sans is not in `/System/Library/Fonts`, `/Library/Fonts` or `~/Library/Fonts` on this
    Mac.
  - Quick Look renders the SVGs of fig01, fig04, fig07 and fig09 in a serif font. In fig07 the
    log-axis tick labels come apart ("10 7", "10 5").
  - The PNGs are not affected.
  - Cause: `save()` wraps `savefig` in `svg.fonttype: none` (`nbhelpers.py:131`). The v1 C9
    item suggested exactly that, to keep the SVG text editable. That suggestion did not allow
    for a font missing on the viewing machine, and it is withdrawn.
  - *Fix:* remove the `svg.fonttype: none` context, so that text is written as paths again
    (faithful, not editable). The alternative is to send the SVGs only where DejaVu Sans is
    installed.
- **V2-C6. Typed text, left over from v1 C6. WARNING (C).** These strings are typed, not read
  from a file. All are correct today:
  - fig11: "inputs pt, etarel, phirel" (checked against the config);
  - fig05-06: "Round-14 configuration (N = 8, W1A8)";
  - fig07-08: the `CHANG_KEY` and `CHANG_PLAIN` text (checked against the training-batch
    STUDY.md arm table and its C′/E1 pilot paragraph);
  - fig10: "one arm".

## v2.9 How the checks were run

- **Mechanical check:** `python3 tools/plot_check.py` (v2.1).
- **Visual check:**
  - All 11 PNGs were opened.
  - Crops at 1:1 were taken of the regions listed at the top of v2, plus a 4× zoom of the top
    of fig01's y label.
  - An edge-ink scan counted pixels darker than 128 in the outer row and column of every PNG.
  - Pixel-value scans measured the grid seams inside the bars of fig04 and fig09.
- **SVG:** font declarations were read with `grep`. fig01, fig04, fig07 and fig09 were rendered
  with Quick Look (`qlmanage -t`), which crops wide figures to a square.
- **Sources:**
  - fig09: `PHASE_START`/`PHASE_DONE` lines, parsed with `awk` independently of `nbhelpers.py`.
  - fig10: the canary `k_result.json` and the per-arm canary logs.
  - Distillation label: the manifest, `ablation_metrics.json` and the 2026-09-20 status file.
  - fig07-08 arm wording: the training-batch STUDY.md.
  - fig11 inputs: the Round-14 N = 8 config.
  - Notebook to disk: sha256 of every base64 PNG in the `.ipynb` against `figures/*.png`
    (11 of 11 identical).
- **Environment:** `.venv-hgq2` (Pillow, numpy) for crops and scans. Nothing was computed in
  the lab pod. No figure, script or notebook was modified.
