#!/usr/bin/env python3
"""Budget arithmetic for the Delta wave-2 screen (STUDY.md, Budget). Design arithmetic, not a result.

Reads delta.json (sha256 f4ad2571...9204) and prints run counts, run-epochs by architecture class,
pod-hours, a pack-schedule wall clock at P pods and the certification readout count, for the seed
counts the K2 rule can return. v2 (fixer, 2026-09-27, arbiter v1): A/A placebo cells P-350 and
P-5M (fix 1); rep-A and rep-C at seeds 1-8 to epoch 500, seeds 1-n to their long horizon ([DK2]
default, fix 19); planning K for E separate from the per-slot cost (fix 5); cheap version with
rep-A to 1,000 and rep-C to 2,000 and its own placebos (fix 14); certification count (C27).

v3 (fixer v2, 2026-09-27, STUDY arbiter v2 fix 1(e)-(f)): regime B. The per-epoch cost is the
anchor's regime-B arithmetic, not the regime-A telemetry; E plans at K = 4 (the 90 % memory rule
the Delta canary applies, code/canary_k.py; code/GATES.md §6 "Packs"), with K = 5 (the anchor's
wave-1 packing) printed as the alternative row. Also printed: the (4, 4) row with the cells that
cannot be packed on the anchor tree today left out (code/GATES.md §6: M006 floor untraced; M047,
M048, M049 and both teachers refused by the anchor's [A20] build guard).

Timing basis (labelled projection, not a measurement of any arm's result):
  Per-epoch cost: s_e = 136.5 s per epoch per process at K = 6 on an NVIDIA A10 under regime B
             ([D20] trace every 10 epochs). Anchor STUDY 96b95f2 l. 1453-1457: from the regime-A
             canary split (trace 90.61 s, remainder 127.45 s per epoch), 127.45 + 90.61 / 10 =
             136.5 s; "Neither is a measurement". The regime-B pilot measures it.
  Per-slot cost: 136.5 / 6 = 22.75 pod-seconds per run-epoch, assuming a GPU-throughput-bound pod
             (the per-slot cost does not change with K). K = 3, 4, 5 are not measured.
  E class:   K_E = 4 (floor(0.9 * 23,028 / 4,354), the 90 % rule at the regime-A per-process
             footprint; the Delta canary sets it; STUDY [D16]); alternative K_E = 5 (the anchor's
             wave-1 packing on the A10 class). s_e(E, K) = 136.5 * K / 6.
  A07 class: no [D19] A07 epoch exists. Illustrated with r x 22.75 pod-seconds per run-epoch,
             r in {1, 2}, packed at K_A07 = 3 with s_e(A07, 3) = r * 136.5 * 3 / 6. r is not
             measured.

v4 (fixer v3, 2026-09-27, STUDY arbiter v3 fixes 3, 9, 10 and the 5M-slack default of fix 8):
  - "not packable today" also leaves out the four cells whose Z10 cache is not built (M009 N=32,
    M038 ungated, M040 derived features, M041 real-slot std), as code/GATES.md §6 "Packs" does
    (220 cell-phase arms + 20 replicas = 240 runs);
  - ranking-mode top-k extension ([DK16] default): after the n = 4 readout the top 16 H-500 cells
    at 5M and the top 6 at 350k run seeds 5-8 (pairing with replica seeds 5-8, which already run
    to epoch 500); released when the last H-500 cell or placebo pack of the n = 4 schedule ends;
  - pause default ([DK17]): withdrawn in v5 (fixer v4); the pause rows and their code are removed;
  - follow-up cost if the 5M constraint is slack ([DK18]): the training-only levers (delta.json
    families B and R and M037, teacher cells excluded) at 350k on arm A (E), n = 4, with that
    wave's own rep-A (seeds 1-4 to the longest H, 5-8 to 500) and placebo. Indicative only: a
    follow-up wave gets its own STUDY.
All new rows are printed before the K_E = 5 alternative block, so they use K_E = 4.

v5 (fixer v4, 2026-09-27, STUDY arbiter v4 fix 1): the compute pause is withdrawn, so pause_keep(),
the paused= parameter and the "[DK17] pause default" block are deleted; every other row is
unchanged. The [DK16] extension band is now read on s_int at the n = 4 readout (1.0 pt <= s_int
<= the family's label threshold T, screen_null.py section 18).

v6 (fixer v6, 2026-09-28, STUDY arbiter v6 fix A5): one PACK-MEM line printed last (host memory per
arm = baseline + slope x H); every other line unchanged.

Usage: python3 budget.py [path/to/delta.json]
"""
import heapq, json, math, sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "../2026-09-26-delta/delta.json"
D = json.load(open(PATH))
SE6, K_E, K_A = 136.5, 4, 3   # SE6: s/epoch/process at K = 6 (regime-B arithmetic); planning K for E and A07
TEACHER_CELLS = {"M027", "M035", "M036"}
W2 = [e for e in D["entries"] if e["wave"] == "W2"]


def cls_350k(e):
    role = e["screen_role_350k"] or ""
    return "A07" if role.startswith("floor-family") else "E"


def cells(exclude=TEACHER_CELLS):
    out = []  # (id, target, horizon, class, seed_family)
    for e in W2:
        if e["id"] in exclude:
            continue
        for t in e["targets"]:
            h = e["horizon_screen_epochs"]
            if t == 350000:
                out.append((e["id"], t, h, cls_350k(e), "350k"))
            elif t == 1400000:
                out.append((e["id"], t, h, "A07", "350k"))  # M010 pairs to A07-350 seeds 1-n_350
            else:
                out.append((e["id"], t, h, "A07", "5M"))
    return out


def replicas(n350, n5m, extra_to=8):
    """DELTA.md §5.2 / delta.json drift_replicas W2, one row per run. rep-A and rep-C run seeds
    1-extra_to (default 8) from t = 0: seeds 1-n to the long horizon, the rest to epoch 500 only
    (the df-7 sd read, STUDY [D19]). rep-A07-350 runs seeds 1-n_350 to 500."""
    out = []
    for s in range(1, max(extra_to, n350) + 1):
        out.append(("rep-A", 350000, 1000 if s <= n350 else 500, "E", None))
    for s in range(1, n350 + 1):
        out.append(("rep-A07-350", 350000, 500, "A07", None))
    for s in range(1, max(extra_to, n5m) + 1):
        out.append(("rep-C", 5000000, 2000 if s <= n5m else 500, "A07", None))
    return out


def placebos():
    # STUDY fix 1: A/A placebo per accuracy family; arm A (E) or arm C (A07) config plus a no-op key
    return [("P-350", 350000, 500, "E", "350k"), ("P-5M", 5000000, 500, "A07", "5M")]


def cert_count(rows):
    """Certification readouts: one per selected checkpoint = one per (run, readout horizon).
    Replicas are read at every 500-epoch horizon a cell pairs with (rep-A 500, 1,000; rep-C 500,
    1,000, 1,500, 2,000); a replica seed that stops at 500 is read once."""
    k = 0
    for x in rows:
        k += x[2] // 500 if x[0] in ("rep-A", "rep-C") else 1
    return k


TEACHERS = [("P-T1", None, 2000, "A07", None), ("P-T2", None, 2000, "A07", None)]


def expand(rows, n350, n5m):
    runs = []
    for r in rows:
        fam = r[4]
        n = 1 if fam is None else (n350 if fam == "350k" else n5m)
        runs += [r] * n
    return runs


def se(c, r):
    return SE6 * K_E / 6 if c == "E" else r * SE6 * K_A / 6


def schedule(first, later, P, r, ext=()):
    """Packs of equal (class, horizon); longest first; 'first' packs start at 0, 'later' packs are
    released when every replica has reached epoch 500 (DELTA §5.2: replicas first)."""
    def packs(runs):
        groups = {}
        for x in runs:
            groups.setdefault((x[3], x[2]), []).append(x)
        out = []
        for (c, h), xs in groups.items():
            k = K_E if c == "E" else K_A
            for i in range(0, len(xs), k):
                out.append((h * se(c, r), h))
        return sorted(out, reverse=True)
    rep = [x for x in first if x[0].startswith("rep-")]
    release = max(500 * se(x[3], r) for x in rep)
    pods = [0.0] * P
    heapq.heapify(pods)
    for d, _ in packs(first):
        t = heapq.heappop(pods); heapq.heappush(pods, t + d)
    # entries: a pod becomes available for entries at max(its free time, release)
    pods = [max(t, release) for t in pods]
    heapq.heapify(pods)
    end500 = release
    for d, h in packs(later):
        t = heapq.heappop(pods); heapq.heappush(pods, t + d)
        if h == 500:
            end500 = max(end500, t + d)
    if ext:
        # top-k extension: released when the last H-500 pack of the n = 4 schedule has ended
        pods = [max(t, end500) for t in pods]
        heapq.heapify(pods)
        for d, _ in packs(ext):
            t = heapq.heappop(pods); heapq.heappush(pods, t + d)
    return max(pods), release


SLOT = SE6 / 6   # pod-seconds per run-epoch (E); A07 is r x SLOT


def extension(k5m=16, k350=6, fams=("350k", "5M")):
    """[DK16] top-k extension: seeds 5-8 for the top k H-500 paired cells of each family in the band
    (5M on C, A07 class; 350k on arm A, E class)."""
    out = []
    if "5M" in fams:
        out += [("EXT-5M", 5000000, 500, "A07", None)] * (k5m * 4)
    if "350k" in fams:
        out += [("EXT-350", 350000, 500, "E", None)] * (k350 * 4)
    return out


def report(n350, n5m, P=10, exclude=TEACHER_CELLS, teachers=True, ext_fams=()):
    ent = expand(cells(exclude), n350, n5m)
    pla = expand(placebos(), n350, n5m)
    rep = replicas(n350, n5m)
    tea = TEACHERS if teachers else []
    ext = extension(fams=ext_fams) if ext_fams else []
    allr = ent + pla + rep + tea + ext
    re = {c: sum(x[2] for x in allr if x[3] == c) for c in ("E", "A07")}
    print(f"n_350 = {n350}, n_5M = {n5m}: cell runs {len(ent)}, placebo runs {len(pla)}, replica runs {len(rep)}, "
          f"teacher runs {len(tea)}, " + (f"extension runs {len(ext)}, " if ext else "") +
          f"total runs {len(allr)}; run-epochs E {re['E']:,}, A07-class {re['A07']:,}, "
          f"total {re['E'] + re['A07']:,}; certification readouts {cert_count(allr)}")
    for r in (1, 2):
        ph = re["E"] * SLOT / 3600 + re["A07"] * r * SLOT / 3600
        wall, rel = schedule(rep + tea, ent + pla, P, r, ext)
        print(f"   r = {r}: pod-hours {ph:,.1f} (E {re['E'] * SLOT / 3600:,.1f}, A07 {re['A07'] * r * SLOT / 3600:,.1f}); "
              f"replica epoch-500 gate at {rel / 3600:.1f} h; wall clock at P = {P}: {wall / 86400:.1f} d")


def cheap(r_values=(1, 2)):
    """DELTA §5.4 cheap version: T0/T0a/T1 singles with a screen cell, no baselines, no teacher cells,
    3 seeds, one target (350k where the entry has one, on its own role; 1.4M for M010; else 5M),
    one replica per base at seeds 1-3 (fix 14: rep-A to 1,000 for M015, rep-A07-350 to 500, rep-C to
    2,000 for M031 and M032), and the two placebos at seeds 1-3 (fix 1)."""
    sel = [e for e in W2 if e["tier"] == "single" and e["code_tier"] in ("T0", "T0a", "T1")
           and e["id"] not in TEACHER_CELLS and e["targets"]]
    rows = []
    for e in sel:
        t = 350000 if 350000 in e["targets"] else (1400000 if 1400000 in e["targets"] else 5000000)
        c = cls_350k(e) if t == 350000 else "A07"
        rows.append((e["id"], t, e["horizon_screen_epochs"], c, "x"))
    reps = [("rep-A", 350000, 1000, "E", "x"), ("rep-A07-350", 350000, 500, "A07", "x"), ("rep-C", 5000000, 2000, "A07", "x")]
    ent = rows * 3
    pla = [(p[0], p[1], p[2], p[3], "x") for p in placebos()] * 3
    rp = reps * 3
    re = {c: sum(x[2] for x in ent + pla + rp if x[3] == c) for c in ("E", "A07")}
    print(f"cheap: {len(sel)} entries x 3 seeds = {len(ent)} runs + {len(pla)} placebo runs + {len(rp)} replica runs "
          f"= {len(ent) + len(pla) + len(rp)} runs; run-epochs E {re['E']:,}, "
          f"A07-class {re['A07']:,}, total {re['E'] + re['A07']:,}")
    for r in r_values:
        ph = re["E"] * SLOT / 3600 + re["A07"] * r * SLOT / 3600
        wall, rel = schedule(rp, ent + pla, 10, r)
        print(f"   r = {r}: pod-hours {ph:,.1f}; wall clock at P = 10: {wall / 86400:.1f} d")


if __name__ == "__main__":
    c = cells()
    print("W2 cells (teacher cells excluded):", len(c), "by target:",
          {t: sum(1 for x in c if x[1] == t) for t in (350000, 1400000, 5000000)},
          "by class:", {k: sum(1 for x in c if x[3] == k) for k in ("E", "A07")})
    print("E-class cells:", sorted({x[0] for x in c if x[3] == "E"}))
    print("per-seed epochs: 350k family", sum(x[2] for x in c if x[4] == "350k"),
          "5M family", sum(x[2] for x in c if x[4] == "5M"))
    for n350, n5m in ((4, 4), (6, 4), (8, 4), (4, 6), (4, 8), (6, 6), (8, 8)):
        report(n350, n5m)
    cheap()
    print("not packable on the anchor tree today (code/GATES.md §6 'Packs'), left out: M006 (floor untraced), "
          "M047, M048, M049, P-T1, P-T2 (GATE_FAIL), M009, M038, M040, M041 (Z10 cache not built):")
    report(4, 4, exclude=TEACHER_CELLS | {"M006", "M047", "M048", "M049", "M009", "M038", "M040", "M041"}, teachers=False)
    print("[DK16] ranking-mode top-k extension at (4, 4) (top 16 at 5M, top 6 at 350k, seeds 5-8, H 500):")
    for fams in (("350k", "5M"), ("5M",), ("350k",)):
        print("  families in the [DK16] band (1.0 pt <= s_int <= T):", fams)
        report(4, 4, ext_fams=fams)
    print("[DK18] follow-up if the 5M constraint is slack: training-only levers at 350k on arm A (E), n = 4 (indicative):")
    tr = [e for e in W2 if (e["family"] in ("B", "R") or e["id"] == "M037") and e["id"] not in TEACHER_CELLS]
    rows = [(e["id"], 350000, e["horizon_screen_epochs"], "E", "350k") for e in tr]
    hmax = max(x[2] for x in rows)
    fu_rep = [("rep-A", 350000, hmax if s <= 4 else 500, "E", None) for s in range(1, 9)]
    fu = expand(rows, 4, 4) + [("P-350", 350000, 500, "E", None)] * 4
    ep = sum(x[2] for x in fu + fu_rep)
    print(f"   entries {len(tr)}: {sorted(e['id'] for e in tr)}; cell runs {len(rows) * 4}, placebo 4, replica 8 "
          f"(seeds 1-4 to {hmax}); total runs {len(fu) + len(fu_rep)}; run-epochs (all E) {ep:,}; "
          f"pod-hours {ep * SLOT / 3600:,.1f}")
    for r in (1,):
        wall, rel = schedule(fu_rep, fu, 10, r)
        print(f"   wall clock at P = 10: {wall / 86400:.1f} d")
    K_E = 5   # alternative row: E packed at K = 5 (the anchor's wave-1 packing on the A10 class)
    print("alternative, E at K = 5:")
    report(4, 4)
    cheap()
    # v6 (fixer v6, 2026-09-28, STUDY arbiter v6 fix A5): host memory per arm, anchor incident
    # review/INCIDENT_stall_20260928.md §5-§6 PACK-MEM (baseline + slope x H), at the gate-14 limit.
    BASE_GB, SLOPE_MB = 2.1, 5.0   # baseline ~2.1 GB per arm (incident §5); gate-14 RSS slope limit, MB/epoch
    print(f"PACK-MEM host memory per arm at baseline {BASE_GB} GB + {SLOPE_MB:.0f} MB/epoch x H "
          f"(6 Gi = {6 * 2 ** 30 / 1e9:.2f} GB): " +
          "; ".join(f"H {h:,}: {BASE_GB + SLOPE_MB * h / 1000:.1f} GB" for h in (500, 1000, 2000)))
