# R14 n8 folded (DATAFLOW/PF) silicon — 2026-08-12

**STATUS: VERIFIED (results-analyst, 2026-08-12, pass 3) — every numeric cell re-derived
from the raw `csynth.xml` / `myproject_csynth.rpt` / `fold_manifest.json` /
`mulder_evidence/`. Quotable, subject to the labelling rule above and the timing note
below.**

Whole-model Vitis HLS 2023.2 C-synthesis on mulder, part `xcvu13p-flga2577-2-e`, target
2.5 ns, io_parallel, Latency strategy, model RF=1. Model: `r14-l1x3-n8` W1A8 seed 3,
**export v5** (fx8 β) — the SAME export as the RF=1 reference; the only intervention is
scheduling: model-level `PipelineStyle: dataflow` + `parallelization_factor = pf` on the
13 per-token EinsumDense nodes AND (v2, the softmax fix) on the 2 attention Softmax nodes,
plus the project-local `nnet_activation.h` factor-bound unroll patch. All arms passed
GATE A (emitted-firmware audit) and GATE B (GATE1 Δ=0.0 vs stored baseline; GATE2
bit-exact) before shipping — `fold_manifest.json` in each run leaf.

**Labelling (pre-registered):** these are folded, deployable-class points answering a
DIFFERENT question from the RF=1 max-parallelism reference. Latency ≈ sum over dataflow
processes; the interval (II) is a first-class output. They must never be tabulated as
improvements/regressions of the RF=1 II=1 point in a single column.

## Measured operating points

| metric | pf1 (max fold) | pf2 | pf4 | RF=1 fx8 (context, different question) | VU13P |
|---|---|---|---|---|---|
| estimated clock | 2.162 ns — 10 Timing-Violation flags, see note | 2.685 ns ✗ (misses 2.5) — 4 flags | — | 1.825 ns (0 flags) | — |
| latency (cycles) | 339 | 265 | — | 164 | — |
| initiation interval | **48** | **32** | — | 1 | — |
| LUT | 3,198,568 (185.1 %) | 4,166,195 (241.1 %) | — | 3,178,720 (184.0 %) | 1,728,000 |
| FF | 1,622,766 (47.0 %) | 1,686,829 (48.8 %) | — | 1,704,976 | 3,456,000 |
| DSP | 3,637 (29.6 %) | 3,653 | — | 4,133 | 12,288 |
| BRAM_18K | 32 | 64 | — | 512 | 5,376 |
| URAM | 0 | 0 | — | 0 | 1,280 |

pf4: **NO RESULT** — vitis_hls OOM-killed by the kernel at 127.5 GB anon-RSS during
top-level RTL integration, before `csynth.xml` was written (dmesg 2026-08-11 18:07:15).
No pf4 number exists and none may be quoted.

## Findings

1. **PF-under-DATAFLOW folding does not deliver device fit at whole-model scale.** The
   maximum fold (pf1, token axis fully rolled 8→1) lands at 3,198,568 LUT — 185 % of the
   VU13P and within 0.7 % of the RF=1 reference's 3,178,720 — while the interval rises
   1 → 48. The half fold (pf2) is strictly worse on every axis: +30 % LUT over pf1,
   II=32, and it misses the 2.5 ns target (est 2.685 ns).

**Timing note.** pf1's 2.162 ns estimate is under target but its `csynth.xml` carries
**10 `Timing Violation` entries** (top-level PerformanceEstimates, Module[myproject], and
8 einsum_dense module classes: config 7/9/18/26/41/43/52/60); pf2 carries 4 (top ×2,
config 31/65). The RF=1 fx8 reference has 0. Same caveat class as the fabric point's
18 flags in `hls_r14.md`: quote folded ns figures only with this note until a post-route
or eased-clock check. Evidence: `SummaryOfViolations` blocks in each `csynth.xml`.
2. **Where the savings went (per-module instance sums, `myproject_csynth.rpt`):** the
   folds do shrink the folded modules — einsum_dense 1,630,567 → 1,060,056 (pf1, −35 %,
   far short of the naive ÷8) and the rolled softmax drops 179,200 → ~71,200 — but the
   dataflow conversion adds ~585k LUT of process/glue logic (top-level total minus
   instance sum: 757k at pf1 vs 172k at RF=1), cancelling the module savings almost
   exactly. At pf2 the partially-unrolled einsum_dense *grows* to 2,053,863 —
   worst-of-both-worlds muxing.
3. **The v2 softmax fix is validated as a front-end unblock:** with the 2 Softmax nodes
   rolled (pf on the node + factor-bound unroll patch), the 08-09 wedge is gone. Design
   size, like-for-like at the headline `Unroll/Inline` phase: 10,172,252 (unfolded
   baseline, experiment-log 2026-08-09) → **2,459,717** at pf1 (4.13×;
   `mulder_evidence/csynth_stdout.log:203`), consistent with the v1 pf1df figure
   2,604,475; the later `Unroll/Inline (step 2)` pass reads 1,038,061. The front end no
   longer wedges — it completes in ≈86 min (Compiling Optimization and Transform
   1,418 s + Loop/function optimizations 3,102 s + …, through Architecture Synthesis
   ≈5,173 s), within a 6.1 h total `csynth_design` dominated by Creating RTL model
   (10,154 s). The fix is necessary for ANY dataflow build of this graph; it is not, by
   itself, sufficient for fit.
4. **Memory pathology, quantified** (dmesg captures in each leaf's `mulder_evidence/`):
   top-level RTL integration peaks near or beyond the 125 GB box even solo — pf2 wrote
   its report and was then OOM-killed in teardown (anon-rss 127,368,352 kB, 14:04:52);
   pf4 (least folded) OOM'd before its report (anon-rss 127,532,112 kB, 18:07:15).
   Serialized, one-run-at-a-time synthesis is mandatory for these designs; exit status
   must never be trusted over the presence of a parseable `csynth.xml`.

## Provenance

Raw reports (`csynth.xml`, `myproject_csynth.rpt`, `csynth_report.json`):
- pf1: `results/synthesis/runs/38a20c62/w1a8-s3-r14n8-pf1sm1df/csynth_pf1sm1df/`
- pf2: `results/synthesis/runs/38a20c62/w1a8-s3-r14n8-pf2sm2df/csynth_pf2sm2df/`
- pf4: `w1a8-s3-r14n8-pf4sm4df/` — gates, tarball, and `mulder_evidence/` run logs. The run
  got through the full design-size ladder (Array/Struct step 5 at 994,864 instructions,
  HW Transforms step 2 at 969,996) and into per-module RTL generation, 242 m 20 s wall,
  before the OOM at top-level integration; **no `csynth.xml`** in the leaf and zero csynth
  entries in the tarball, hence no resource/latency numbers.
- Each leaf also carries `mulder_evidence/` (csynth_stdout.log, memwatch.log,
  csynth_design_size.rpt, vitis phase lines + dmesg OOM captures), fetched 2026-08-12.

Mulder work dirs `~/bnjet_r14/r14n8-w1a8s3-fx8-pf{1sm1,2sm2,4sm4}df/`, serialized run log
`~/bnjet_r14/r14n8-folded-serial.launch.log` (queue completed 2026-08-12 00:17 PDT).
Driver: `code/hgq2/fold_r14n8.py` v2 (softmax fold + header patch + pf generalisation).
Gates: `fold_manifest.json` per leaf (GATE1 corr 0.9988158043665978, Δ 0.0; GATE2
bit-exact; GATE A pf histogram {pf:15}).

## Verification

- [x] **results-analyst, 2026-08-12 — SIGNED OFF (pass 3).** Every cell above re-derived
  from the raw XML/rpt/JSON/logs; the three pass-2 defects are fixed and re-checked; no
  open items. Detail below.

**Pass 2 (results-analyst, 2026-08-12) — PASSES.** pf1/pf2 clock, latency, II,
LUT/FF/DSP/BRAM/URAM and every percentage recomputed from `csynth.xml` (independent
`parse_csynth.py` re-parse byte-identical to the stored `csynth_report.json`; denominators
from the same file's `avail{}`); RF=1 column transcribes `hls_r14.md` exactly; pf4 has no
`csynth.xml` in the leaf and zero csynth entries in its tarball; the 10/4/0
Timing-Violation counts and the flagged module classes (pf1 config 7/9/18/26/41/43/52/60;
pf2 config 31/65) confirmed against the `SummaryOfViolations` blocks; §2 module sums
re-derived from the instance tables (glue = top-level minus instance sum 172,274 →
757,418, Δ +585,144; DSP closure 3,621 + 512 = 4,133 at RF=1 and 3,621 + 16 = 3,637 at
pf1); §1 "+30 %" = 30.25 %; §4's anon-rss values and timestamps verbatim in
`mulder_evidence/vitis_phases_and_dmesg.txt`, with per-run attribution corroborated by the
`memwatch.log` windows (pf2 07:52→14:02, pf4 14:05→18:05, pf1 18:08→00:08 clean); gates
GATE1 0.9988158043665978 / Δ 0.0, GATE2 bit-exact, GATE A pass {pf:15} in all three
`fold_manifest.json`.

**Pass 3 (results-analyst, 2026-08-12) — the three pass-2 defects are RESOLVED; no open
items.** All three were in §3 / Provenance; the measured-operating-points table, timing
note, §1, §2 and §4 were already clean at pass 2 and are unchanged.
1. Like-for-like design size ✓ — `csynth_stdout.log:203` reads exactly "There were
   2,459,717 instructions in the design after the 'Unroll/Inline' phase", the same headline
   phase as the 2026-08-09 baseline 10,172,252; 10,172,252 / 2,459,717 = 4.1355 → "4.13×";
   the v1 pf1df cross-check 2,604,475 and the separately-labelled
   `Unroll/Inline (step 2)` = 1,038,061 are both correct.
2. Front-end wall time ✓ — Compiling Optimization and Transform 1,418.39 s, Loop/function
   and other optimizations 3,101.98 s; the full sum through Architecture Synthesis
   (35.62 + 1,418.39 + 179.74 + 184.56 + 3,101.98 + 253.07) = 5,173.36 s = 86.2 min;
   `Finished Command csynth_design` 21,960.6 s = 6.100 h; Creating RTL model 10,154.1 s.
3. pf4 provenance ✓, with one correction applied at sign-off: the earlier "reached
   Array/Struct step 5" understated the run. pf4's `csynth_stdout.log` shows the complete
   design-size ladder (through HW Transforms step 2 at 969,996) and per-module RTL
   generation over 242 m 20 s wall before the OOM — which is what Finding 4 describes. The
   load-bearing claim is unchanged and verified: no `csynth.xml` in the leaf, zero csynth
   entries in the tarball, therefore no pf4 resource/latency number exists.
