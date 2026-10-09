# VERIFY — GPU-product throughput benchmark (2026-09-29-gpu-benchmark)

Phase 4, results-analyst, 2026-09-29 (data read 17:20-18:30Z). **Telemetry for a scheduling decision, not a physics
result.** There is no tagging metric, no data split and no comparison of trained models across products (STUDY l. 26). The
validation fields in the arm logs were not read. Every number below was recomputed from the Job artifacts by
`code/verify_bench.py`. That script also wrote every table into this file, and one row per printed number into
`verify.json`. It runs the pre-registered analysis, `code/bench_summary.py`, unchanged, and then checks it with an
independent parse. Governing documents: STUDY.md (Amendment 1, [D1]-[D6], rules 1-6, critical v2 B3 and B6), PREFLIGHT.md,
RUN.md. **The choice of product is Kai's;** this artifact names what the pre-registered rule favours and where the data stop.

## In brief

- **Coverage.** Every Job whose pod started finished every phase (counts table). Seven Jobs never started within 6 h:
  the L40, L40S and A40 in both pod shapes, and the RTX A6000's K_rule shape. By rule 3 they are "not practical now".
- **Gates.** Every arm-run completed 21 epochs with exit 0 and `CHECKPOINT_VERIFICATION_PASS` (rule 6). Every pod printed
  `FINGERPRINT 11559681 expected 11559681` (rule 2). No OOM exit and no non-finite loss occurred. Every arm confirmed its CPU pin,
  and no sampled thread left the pinned CPUs (rule 5, with the v2 B1 filter).
- **One exclusion.** RTX 4090, class E, K=5: the pod peak is 91.9 % of memory.total (rule 1), so the 4090 enters T with E at K=4
  only. Two more phases pass rule 1 narrowly, on 60-s samples: the RTX 3090 E at K=5 (89.2 %) and the A100 E at K=16 (88.8 %).
- **The A10 baseline counts, and is not flagged.** Each A10 Job ran once and completed (B3). The one-sided B6 check against
  the pure-pack canary gives ratios 0.9969 (E, K=4) and 1.0643 (A07, K=2), both under the 1.10 limit.
- **Campaign (a), Chang wave 1.** At each assumed G the pre-registered rule favours a single product, with no tie. That
  product is the A100-SXM4-80GB at G = 1 (the a100 quota allows one GPU now: a single-GPU campaign) and the RTX 4090 at every
  G from 2 to 16. The A10's projected finish is 1.651 to 1.876 times as long as the 4090's. The null ("no practical
  candidate more than 10 % earlier than the A10") is rejected for campaign (a) at every assumed G of the grid, and cannot be
  judged at the G that can actually schedule, since G_p was not measured.
- **Campaign (b), the Delta screen's wave two.** [A1] allows its A07 packs only on the large-memory products, which leaves
  two measured products (≥ 45 GB): the A100 (one GPU under the quota) and the RTX A6000 (its K_low shape only). The A100 leads
  at G = 1 and the A6000 at every larger G. The A10 is not [A1]-eligible, so the pre-registered comparison with the A10 has
  no eligible baseline for campaign (b). If Kai overrides [A1], the RTX 4090 leads at every G above 1.
- **G_p was not measured.** No [D4] probe Job ran, so every T is at an assumed G. The pools differ widely (static ceilings
  table), and the 4090's pool is the smallest of the leaders. The break-even tables give how many GPUs of each product match
  the leader.
- **Node spread was not measured** ([L1]: one node per Job shape). No cross-product ratio here has an interval. The
  pre-registered tie margin of 10 % is the only allowance. Every leader's margin survives inflating that leader's s by the
  factor 1.0643, the largest B6 deviation.
- **One RUN.md claim does not reproduce.** RUN.md l. 53-54 says "proc_threads is 25 on every one of them". Recomputed on the
  same rows, it is 25 on 341 and 61 on 5. The claim is descriptive; the pin result it supports stands.

<!-- table counts -->

## Data and provenance

The PVC directory `/data/chang-n64-20260926/gpu-bench/` was copied read-only through the pilot pod
`kai-chang0926-pilotb5-42abed-0-qqjmt` with GNU tar. The copy leaves out model files, checkpoints, validation predictions
and activation-width traces, none of which the analysis reads. A full inventory of every PVC file (size, mtime) is kept
in `data/pvc_inventory_full.tsv`, and every copied file's size equals its inventory entry. The copy is `chmod a-w`.

The analysis root `data/bench-root/<slug>-<shape>/` is made of symlinks. It points at the PVC copy for `plan.json`,
`samples.csv`, `bench_result.json` and the phase directories. From `logs/kai-gpubench-<slug>-<shape>/` it takes `job.json`,
`pod.json` and the kubectl pod log, the latter as `pod-<pod>.log`. The kubectl log is the PVC tee plus its first two lines
(`BENCH_POD … <stamp>`, `HOSTNAME_NODE`); the script asserts this on all nine pods. `bench_summary.py` needs the `BENCH_POD`
stamp to order A10 attempts (B3). The seven deleted Jobs have no PVC data, and they enter through `--plan` as rule-3 rows.

<!-- table provenance -->

## Headline: every product × class × K (STUDY [D1], rules 1-6)

Definitions (STUDY l. 47-51, PREFLIGHT "Analysis script"):

- **s [D1].** For each arm, (9 × median untraced + median traced) / 10 over one-based epochs 2-21: 18 untraced epochs and the
  traced epochs 10 and 20, from the arm's single fresh attempt (`resume_epoch=0`). The phase's s is its slowest arm. Check:
  with untraced u and traced u + t the formula gives u + t/10, as [D1] states. Every arm's traced epochs are exactly 1, 10
  and 20.
- **R** = K × 3600 / s, run-epochs per GPU-hour; every phase has all K arms at 21 epochs, so R is defined on every row.
- **Total elapsed per run-epoch** = phase wall seconds ÷ (K × 21). It includes epoch 1 (the first trace), the start
  stagger and `verify_selected`, so it is not a steady-state rate.
- **Peak.** The largest pod `nvidia-smi` memory.used in the phase's 60-s samples, against memory.total.
- **Utilization.** The mean over all the phase's samples, and over the steady window (all K arms live, all past epoch 1,
  none at epoch 21).
- **Cores per arm.** Steady cgroup CPU cores ÷ K, against rule 5's 2.1.
- **Q.** Job creation (the apply) to the container's `startedAt`: the B1 fallback, because a finished pod carries
  `Ready False`. It is one pod per shape, a snapshot [L3] standing in for the probe's Q_p (critical v2 C7).
- **n.** K arms × 20 epochs per arm for s and R. The sample counts are in the gates table and in `verify.json`.

<!-- table headline -->

The not-practical rows give Q as a lower bound, from the apply to the deletion; those pods never started.

## Gates per phase (rules 1, 2, 5, 6) and the per-arm spread

<!-- table gates -->

The last column is the spread across the arms of a phase, with seeds 1-8 per class; this is a timing study, not a seed
study. The spread comes from start order and the arms' shared GPU, not from nodes. [D1] takes the slowest arm on purpose,
since a pack ends with it.

## [D2] memory check: predicted and measured peaks

<!-- table d2 -->

[D2] sized K_rule from the A10's per-process peaks. The per-process footprint is larger on every other card. That is why the
4090's E at K=5 went over 90 % although PREFLIGHT predicted 88.5 %.

## Reproduction check

The independent parse (`code/verify_bench.py`: its own regular expressions over arm logs, pod logs, `samples.csv`,
`job.json` and `pod.json`) recomputed 19 fields per phase. Each was checked against `bench_summary.py`'s row: equality for
s, R, wall per run-epoch, peak, utilization, cores per arm, Q and RSS, plus the flags. The in-process `summarize_bench` output
equals the CLI's `data/bench_summary.json`.

<!-- table repro -->

The telemetry that RUN.md quotes:

<!-- table run_claims -->

RUN.md's A100 read at about 10:30Z was taken while the phase was running. The first rows of `samples.csv`, as many as RUN.md
counted, reproduce it; its GPU samples include the setup row. The whole phase has more samples, and its values are in the
headline table. The two are not compared with each other.

## Rule 3: the seven "not practical now" Jobs

<!-- table deleted -->

Each pod was Pending with no `startTime` when it was deleted. Every scheduler message counts the product's nodes as short of
GPU, CPU or both. None names the pod anti-affinity, so the self-inflicted wait of critical v2 C7 did not occur. RUN.md records
the K_rule wave's 6-h check at 17:18Z instead of 16:28Z, because the orchestrator's laptop lost DNS. It changes nothing: the
saved pod JSON shows those pods still Pending at 17:18Z.

## The A10 baseline: B3 attempt rule and B6 one-sided check

<!-- table a10 -->

B3: each A10 Job had one attempt, and it completed, so the first complete attempt counts. No phase is listed out of T, and
both classes have a counted A10 phase with R ("A10 baseline measured"). B6 checks E at K=4 and A07 at K=2 only (STUDY l.
163-165); neither is flagged. The pilot telemetry [L2] is not used anywhere in T.

## Card speed at equal K

K_low was chosen to isolate card speed at equal K ([D2]). A ratio above 1.00 means that product is faster than the A10.

<!-- table equalk -->

These are ratios of single-node measurements. Node spread is unmeasured [L1], so no interval exists on them. Inside 1.10 is
a tie by rule. On the A10 itself, K_low gives the higher R in both classes: 133.8 against 126.2 run-epochs per GPU-hour for
E, and 78.7 against 74.6 for A07 (headline table). That is why T takes the A10 at its K_low K pair (3/1) at every G.

## Noise: what this benchmark can and cannot resolve

- **Arm spread within a phase** is in the gates table (sd over arms, ddof=1). It is small next to the cross-product ratios,
  and [D1] already takes the slowest arm.
- **Node-to-node spread is unmeasured** [L1]. Each Job shape ran on one node, and no product ran the same K on two nodes.
  No interval can be put on any ratio between products. The STUDY's 10 % tie margin is the pre-registered allowance.
- **The only evidence across nodes and bundles** is B6: the same card, class and K on another node and bundle, with W&B on,
  gives ratios 0.9969 and 1.0643.
- **Stress test** (the checks tables): each leader's s is inflated by the factor 1.0643 and T is recomputed. No leader changes
  at any G, and no tie set grows.
- **Design note.** One node per shape can separate the products whose T ratios are well above 1.10, which covers every leader
  here. It cannot separate ratios near 1.10. Two nodes per shape, or a timed probe, would give a spread estimate.

## Projection T(p)

**Formula** (STUDY l. 53-58): T(p) = Q_p + C_p + max(Σ_k W_k·s_k / (3600·K_k·G), max_k H_k·s_k / 3600), in hours. W_k and
H_k come from the STUDY's Question (l. 20-23). Campaign (a) has E and A07 with a 7,000-epoch horizon; its R class (8,000
run-epochs at batch 256) is not timed [A2] and is left out of T. Campaign (b) has E and A07 by base class [A3], with longest
horizons 1,000 and 2,000 epochs. Readings used, each a flagged decision below:

- **K per [D3].** At each G, the K pair (E/A07) with the earliest T, over the non-excluded K of that product. The pair is
  printed beside each T.
- **C_p.** For every product but the A10, Q plus 110 × the larger class s (the two class canaries run in parallel), taken in
  full as an upper bound. The sum reading is in the decomposition tables. C_p is 0 for the A10 (STUDY l. 55-56).
- **Q_p.** The benchmark pod's wait for the shape that held that K; the larger of the two when a pair spans both shapes.
- **G.** An assumed G_p, because [D4]'s observed count was not measured. The a100 quota headroom is known: 1 at the 18:28:07Z
  snapshot. The capped view puts each product at min(G, quota headroom, joint static ceiling, pack count or the 10-pod cap).
  The joint static ceiling is the most pods of that K pair (at most the campaign's packs of each class) that the product's
  schedulable nodes could hold at once by allocatable GPU, CPU and memory after the node reserve. It is exact per node, and
  an upper bound, because other tenants' pods are invisible.
- **[A1].** Campaign (b) runs only on the ≥ 45 GB products, since both of its families contain A07 runs. The 24 GB rows are
  shown as references marked †.

<!-- table formula -->

<!-- table constants -->

Inputs per product, class and K, and the static ceilings. The ceilings are upper bounds on G_p and not G_p itself: they
assume empty nodes, and the benchmark's own pods waited hours for one GPU of the 4090, 3090, A6000 and A100 (headline table).

<!-- table t_inputs -->

<!-- table ceilings -->

### Campaign (a): Chang wave 1

T in hours at an assumed G, with the K pair E/A07 in brackets. * marks a G above the a100 quota headroom, ‡ a G above the
joint static ceiling of that K pair on the product's nodes.

<!-- table t_chang -->

What the pre-registered rule favours at equal G. The tie set is every eligible product with T ≤ 1.10 × min T. At equal G
the larger-G_p criterion of [D5] cannot separate products, so the tie goes to the smaller memory.total:

<!-- table sel_chang -->

The [D4]-capped view, with each product at its own bound; ties go to the larger G_eff, then the smaller memory.total:

<!-- table capped_chang -->

Break-even: the fewest GPUs of each product whose T is at or under the RTX 4090's T at G. "Never" means the product's floor
at large G (Q + C + critical path) is above the 4090's T.

<!-- table breakeven_chang -->

Both terms of T (the STUDY's decision packet, l. 89-90), with C_p in its two readings:

<!-- table decomp_chang -->

Leader by G, scanned over every G from 1 to 32:

<!-- table flips_chang -->

Checks on the ranking: the compute term alone, the sum reading of C_p, the LPT schedule of the real equal-horizon packs, and
the stress test on the leader.

<!-- table checks_chang -->

The formula is a lower bound on a pack schedule whenever G does not divide the packs. The REPORT schedules the real packs;
the check below uses LPT on equal-horizon packs, with any partial pack at the full-K s, which is an upper bound.

<!-- table lpt_chang -->

<!-- table lpt_worst -->

If the a100 quota did not bind (hypothetical; a quota change is outside this benchmark):

<!-- table whatif_chang -->

The two matching units of [D5], each on its own at an assumed G, with the K in brackets. First the unit Chang E+R (R untimed,
so this is E alone):

<!-- table unit_chang_E -->

Then the unit Chang A07:

<!-- table unit_chang_A07 -->

### Campaign (b): the Delta screen, wave two

T in hours at an assumed G, with the K pair E/A07 in brackets. G above the 10-pod cap is capped ([D4]). * marks a G above the
a100 quota headroom. † marks a 24 GB card, a reference only unless Kai overrides [A1].

<!-- table t_delta -->

What the pre-registered rule favours at equal G, under [A1]:

<!-- table sel_delta -->

The [D4]-capped view:

<!-- table capped_delta -->

Break-even against the RTX A6000:

<!-- table breakeven_delta -->

Both terms of T, with C_p in its two readings:

<!-- table decomp_delta -->

Leader by G, scanned over every G from 1 to the 10-pod cap:

<!-- table flips_delta -->

Checks on the ranking (the compute term alone, the sum reading of C_p, and the stress test on the leader):

<!-- table checks_delta -->

If Kai overrides [A1], or the a100 quota did not bind:

<!-- table whatif_delta -->

The matching units of campaign (b) are its families (350k, 5M). Their run-epoch split is not in the STUDY, which gives only
base-class totals, and the pack files were not read. Per-family T is left to the REPORT.

## Selection rule, as pre-registered

- **Which numbers.** For each arm, epochs 2-21 of its single fresh attempt; the slowest arm of each phase ([D1]). For the A10,
  the first complete attempt of each Job (B3), which is its only attempt.
- **Which K.** [D3]: the non-excluded K with the earlier T at each G, not the higher R. Rule 1 removes K=5 for the RTX 4090's
  E, and rule 3 removes every K_rule K of the RTX A6000.
- **Which products.** Those with data and no product-wide exclusion under rules 2 and 6: the A10, A100-SXM4-80GB, RTX 3090,
  RTX 4090 and RTX A6000. Rule 3 drops the L40, L40S and A40 as "not practical now" for both shapes.
- **Tie set** ([D5], policy item 3 quoted in STUDY l. 82-85): T ≤ 1.10 × min T, won by the larger G_p and then the smaller
  memory.total. With G_p unmeasured, the equal-G tables apply the memory criterion and the capped tables apply G_eff first.
  No tie set here holds more than one product, so neither criterion decides anything.
- **"More than 10 % earlier than the A10"** is read as T(A10) > 1.10 × T(p), the [D5] tie boundary. The other reading,
  T(p) < 0.90 × T(A10), differs only in a narrow band just above 1.10 that no ratio in the tables falls in.
- **Queue.** "Do not wait for a premium GPU if its queue delay exceeds its measured runtime gain" enters through Q_p and C_p
  inside T. For the A100, the binding delay is a quota change, not a queue, and its length is unknown.
- **Unit of choice** ([D5]). The two matching units of campaign (a), Chang E+R and Chang A07, pick the same product at every G
  of the grid (unit tables). So "one product per campaign if within 10 % of the best split" holds trivially for campaign (a).
  For campaign (b) the family units cannot be priced (per-family run-epochs are not in the STUDY).

## Verdict per claim

- **Question (a), Chang wave 1, at an assumed G.** Resolved at each G of the grid: the A100-SXM4-80GB at G = 1, the RTX 4090
  from G = 2 to 16, each alone in its tie set, in both the equal-G and the capped views. The A100's lead at G = 1 is the
  single-GPU case that the quota allows, a whole campaign on one GPU (1,249.2 h), not a plan anyone would run. **At the
  GPUs that can actually schedule: not resolvable with these data.** G_p was not probed ([D4]), and the ranking at the true
  G_p depends on the pools; see the break-even table.
- **Question (b), the Delta screen's wave two, at an assumed G.** Resolved under [A1] (campaign (b) tables): the A100 at
  G = 1, the RTX A6000 from G = 2. The same caveat on G_p applies. The A6000 is priced from its K_low shape only.
- **"Is any T(p) more than 10 % earlier than the A10's?"** For campaign (a), yes at every assumed G of the grid (the
  selection tables): the null is falsified for campaign (a) at those G. It is **not resolvable at the GPUs that can actually
  schedule**, because no probe ran. It is a telemetry statement from one node per shape; each ratio is far above the 1.10
  margin and survives the stress test. For campaign (b), **not resolvable as posed**, because the A10 is not eligible under
  [A1]. The ratios to the A10 are in the tables, as references.
- **Falsifier (i)** (STUDY l. 92-93): "on the A10 K=5 pilot pod (one node) s over one-based epochs 2-21 differs by over 10 %
  from the latest same-aligned window (10m + 2 to 10m + 21) before the decision". **Not evaluated here.** Its window is "the
  latest … before the decision", and the decision has not been made. Read it at decision time with
  `code/bench_summary.py a10 --offset <10m>` on the pilot-b K=5 logs (PREFLIGHT ran an offset window as the machinery check).
- **Falsifier (ii)** (the chosen product's canary s over 10 % above the screen's): after the rule-4 canary. Not yet
  applicable.
- **Post-launch check** (three-hour utilization under 40 %, or throughput over 10 % below the screen): after launch. Every
  phase here has steady utilization well above 40 % (headline table).

## Rules and quantities the data cannot answer

- **[D4] G_p and Q_p.** No probe Job ran. G is assumed; Q is one pod per shape (C7). Three pods (the RTX 3090 K_low and
  K_rule, the RTX 4090 K_rule) started between 11:57:24Z and 11:57:47Z, just after the A100 K_rule and A10 pods ended. The
  anti-affinity's topologyKey is the hostname, so it is not the cause. Q reflects cluster events, not a per-product queue.
- **Rule 4.** The 110-epoch memory/RSS canary and the EBOP certification are due on whichever product Kai picks; C_p prices
  their duration only.
- **Host-RSS gate.** It needs 105 epochs; the 21-epoch runs record RSS peaks only (gates table).
- **NRP's rolling 3-h 40 % window.** The pod header before the sampler is not sampled. RUN.md records no NRP alert, and no
  phase is under 40 % in its steady window.
- **Unmeasured classes.** Campaign (a)'s R class [A2]; campaign (b)'s variant classes, costed at their base class [A3]; and
  per-family T for campaign (b).
- **Absent products.** The L40, L40S and A40 have no timing at all, and the RTX A6000 has none at its K_rule K. "Not practical
  now" is a snapshot [L3] from one day.
- **Node spread** [L1]: no interval on any cross-product ratio.

## Where I am not sure

```
DECISION: copy the PVC without model files, checkpoints, validation predictions and activation-width traces, all
unread by the analysis (inventory of all files kept).   ALTERNATIVES: the full tar through the GPU-priority pilot pod
(provenance table).   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
DECISION: feed bench_summary.py the kubectl pod log (the PVC tee plus BENCH_POD and HOSTNAME_NODE).   ALTERNATIVES: the
PVC tee, which has no BENCH_POD stamp, so B3 would order attempts by file mtime.   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
DECISION: T per campaign on one product with both classes sharing G, the K pair chosen by the earlier T at each G [D3].
ALTERNATIVES: per-unit T (the unit tables, same leaders); a split across products (needs G_p per product).
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: C_p = Q + 110 x the larger class s (parallel class canaries), taken in full.   ALTERNATIVES: the sum reading
(decomposition tables; no leader changes); C_p near 0 if the canary finishes before the production gate opens.
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: Q_p = the benchmark pod's apply-to-start wait for the shape holding that K.   ALTERNATIVES: the [D4] probe,
not run. The compute-only check (no Q, no C) gives the same leaders.   CONFIDENCE: LOW   FLAG FOR HUMAN: YES
DECISION: bound G by the a100 quota headroom and the static allocatable ceiling (code/gen_bench.py:142-150) in the
capped view.   ALTERNATIVES: equal G only (also shown; same leaders).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: [A1] applied to all of campaign (b), because both of its families contain A07 runs.   ALTERNATIVES: its E-base
runs on 24 GB cards, which splits the 350k family across products.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: "more than 10 % earlier" read as T(A10) > 1.10 x T(p).   ALTERNATIVES: T(p) < 0.90 x T(A10); same answers
here.   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```

## What needs Kai

1. **G_p.** The rankings hold at every assumed G, but the real G_p is unknown. For campaign (a) the 4090 leads from G = 2,
   and its pool is 3 schedulable nodes; both of its benchmark pods waited hours (headline). The 3090's pool is far larger, and
   the break-even table shows how many 3090s match a given number of 4090s. Options: the [D4] probe at decision time
   (`code/gen_bench.py --probe`), or a choice with the table in hand.
2. **[A1] for campaign (b).** The 24 GB cards held A07 at K=2 at 69.0 % (RTX 3090), 70.1 % (RTX 4090) and 73.4 % (A10) of
   memory, and at K=1 near a third of it (headline table). The A07-at-K=3 OOM that motivated [A1] is not what these phases
   ran. With an override, the 4090 leads campaign (b) from G = 2.
3. **The a100 quota.** One A100 is free now. At G = 1 the A100 leads both campaigns; above that it needs a quota change
   (what-if tables).
4. **Near-limit memory.** The RTX 3090's E at K=5 (89.2 %) and the A100's E at K=16 (88.8 %) pass rule 1 on 60-s samples.
   The chosen product's rule-4 canary is where a missed peak would show.
5. **Rule 4 and falsifier (i).** The chosen product still needs the 110-epoch canary and the EBOP certification, and
   falsifier (i) is read at decision time.
6. **RUN.md l. 53-54.** Correct it to "25 on 341 of 346 rows, 61 on 5" when convenient (reproduction table).

## Commands (from `campaigns/2026-09-29-gpu-benchmark/`)

```
# PVC inventory and read-only copy, through the pilot pod (tar of small files only)
kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- sh -c 'cd /data/chang-n64-20260926 && find gpu-bench -type f -printf "%s\t%TY-%Tm-%TdT%TH:%TM:%.2TSZ\t%p\n" | sort -k3' > data/pvc_inventory_full.tsv
kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- tar -C /data/chang-n64-20260926 --exclude='*.keras' --exclude='*.npz' --exclude='activation_widths.jsonl' --exclude='checkpoints' -cf - gpu-bench | tar -xf - -C data/
chmod -R a-w data/gpu-bench data/pvc_inventory_full.tsv
# a100 quota snapshot ([D4] quota term)
kubectl -n cms-ml get resourcequota -o json > data/resourcequota_snapshot.json; date -u +%Y-%m-%dT%H:%M:%SZ > data/resourcequota_snapshot.utc
# analysis root, the pre-registered analysis (CLI), then every recomputed number, verify.json and this file
uv run --no-project python code/verify_bench.py --root-only
python3 code/bench_summary.py bench --root data/bench-root --plan manifests/bench_plan.json --out data/bench_summary.json > data/bench_summary.log
uv run --no-project python code/verify_bench.py > data/verify_bench.log
python3 ../../tools/verify_check.py VERIFY.md
```

`code/verify_bench.py` needs only the standard library; `uv run --no-project` keeps it out of any vendored environment.
Its log `data/verify_bench.log` repeats every table, and `data/verify_tables.md` holds them without the prose.
