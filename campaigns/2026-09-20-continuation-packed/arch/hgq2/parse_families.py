#!/usr/bin/env python3
"""Per-family LUT/FF/DSP/BRAM attribution from a Vitis HLS csynth report.

`parse_csynth.py` gives the whole-model rollup; this gives the breakdown BY MODULE FAMILY
(einsum_dense, act-by-act einsum, normalize, softmax, relu, add, pool, ...) at any build
point, which is what single-lever attribution needs: a directive or grid change must move
ONE family and leave the others byte-identical.

Reads the `Utilization Estimates > Detail > Instance` table of `myproject_csynth.rpt`.
That table is already per-instance and flat, so summing it needs no hierarchy walk and
cannot double-count parents. Falls back to `csynth.xml` (module areas x instance counts)
only when the .rpt is absent -- that path CAN double-count enclosing modules, so it is
reported as untrusted and flagged.

Stdlib only (runs on the synthesis host's system python3).

Usage:  parse_families.py <myproject_csynth.rpt | csynth.xml> [...]
        parse_families.py --diff <baseline.rpt> <variant.rpt>
        parse_families.py --self-test          # validate against the stored pre_conference_n8 baseline
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# Families we name explicitly; anything else is bucketed under its module-name stem.
def family_of(module):
    if module.startswith("einsum_dense"):
        return "einsum_dense"
    if module.startswith("einsum"):
        return "einsum(actxact)"
    if "softmax" in module:
        return "softmax"
    m = re.match(r"([a-z_]+?)_(?:ap_|config)", module)
    stem = m.group(1) if m else module.split("_ap_")[0]
    return stem or "(top-level)"


def from_rpt(path):
    """Sum the flat per-instance utilization table. Returns {family: {...}}."""
    fam = {}
    rows = 0
    for line in open(path):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7:                      # Instance | Module | BRAM | DSP | FF | LUT | URAM
            continue
        nums = cells[2:7]
        if not all(re.fullmatch(r"-|\d+", n) for n in nums):
            continue
        vals = [0 if n == "-" else int(n) for n in nums]
        rows += 1
        d = fam.setdefault(family_of(cells[1]),
                           {"n": 0, "BRAM_18K": 0, "DSP": 0, "FF": 0, "LUT": 0, "URAM": 0})
        d["n"] += 1
        for k, v in zip(("BRAM_18K", "DSP", "FF", "LUT", "URAM"), vals):
            d[k] += v
    if not rows:
        raise SystemExit(f"{path}: no instance-table rows found (wrong file?)")
    return fam, rows, True


def from_xml(path):
    """Fallback: module AreaEstimates x instance count. May double-count parents."""
    root = ET.parse(path).getroot()
    fam = {}
    for mod in root.iter("Module"):
        name = mod.findtext("Name") or ""
        res = mod.find("AreaEstimates/Resources")
        if res is None:
            continue
        d = fam.setdefault(family_of(name),
                           {"n": 0, "BRAM_18K": 0, "DSP": 0, "FF": 0, "LUT": 0, "URAM": 0})
        d["n"] += 1
        for k in ("BRAM_18K", "DSP", "FF", "LUT", "URAM"):
            d[k] += int(res.findtext(k) or 0)
    return fam, len(fam), False


def load(path):
    if path.endswith(".xml"):
        return from_xml(path)
    return from_rpt(path)


def show(path, fam, rows, trusted):
    tag = "" if trusted else "   [XML FALLBACK -- may double-count enclosing modules]"
    print(f"--- {path}  ({rows} instance rows){tag}")
    for name, d in sorted(fam.items(), key=lambda kv: -kv[1]["LUT"]):
        if not (d["LUT"] or d["DSP"]):
            continue
        print(f"    {name:22s} n={d['n']:5d}  DSP={d['DSP']:6d}  FF={d['FF']:10,d}  "
              f"LUT={d['LUT']:11,d}  BRAM={d['BRAM_18K']:5d}")
    print(f"    {'TOTAL(instances)':22s}        DSP={sum(d['DSP'] for d in fam.values()):6d}"
          f"  FF={sum(d['FF'] for d in fam.values()):10,d}"
          f"  LUT={sum(d['LUT'] for d in fam.values()):11,d}")


def diff(a_path, b_path):
    fa, _, _ = load(a_path)
    fb, _, _ = load(b_path)
    label = lambda q: os.path.basename(os.path.dirname(os.path.abspath(q))) or q
    print(f"=== DELTA  {label(b_path)} - {label(a_path)} ===")
    keys = sorted(set(fa) | set(fb),
                  key=lambda k: -(fb.get(k, {}).get("LUT", 0) - fa.get(k, {}).get("LUT", 0)))
    for k in keys:
        dl = fb.get(k, {}).get("LUT", 0) - fa.get(k, {}).get("LUT", 0)
        dd = fb.get(k, {}).get("DSP", 0) - fa.get(k, {}).get("DSP", 0)
        if not (dl or dd):
            continue
        note = "NO DSP CHANGE" if dd == 0 else f"{dl / abs(dd):.1f} LUT/DSP"
        print(f"    {k:22s}  dLUT={dl:+11,d}  dDSP={dd:+6d}   {note}")
    unchanged = [k for k in keys
                 if fb.get(k, {}).get("LUT", 0) == fa.get(k, {}).get("LUT", 0)
                 and fa.get(k, {}).get("LUT", 0)]
    print(f"    unchanged families (single-lever check): {', '.join(sorted(unchanged)) or 'NONE'}")


# The stored pre_conference_n8 RF=1 baseline, re-derived independently 2026-08-15 and 2026-08-19.
SELF_TEST = {
    "einsum_dense": (1_630_567, 0), "einsum(actxact)": (715_776, 0),
    "normalize": (258_364, 3_621), "softmax": (179_200, 512),
    "thresholded_relu": (164_160, 0), "add": (32_256, 0),
    "dense_latency": (15_531, 0), "global_pooling1d_cl": (10_592, 0),
}


def self_test():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    rpt = os.path.join(root, "results", "synthesis", "runs", "38a20c62",
                       "w1a8-s3-pre_conference_n8", "csynth_rf1", "myproject_csynth.rpt")
    if not os.path.exists(rpt):
        raise SystemExit(f"self-test needs {rpt}")
    fam, rows, _ = load(rpt)
    bad = 0
    for name, (lut, dsp) in SELF_TEST.items():
        got = fam.get(name, {"LUT": None, "DSP": None})
        ok = got["LUT"] == lut and got["DSP"] == dsp
        bad += not ok
        print(f"  {'ok ' if ok else 'FAIL'} {name:22s} LUT {got['LUT']!s:>11} vs {lut:,}"
              f"   DSP {got['DSP']!s:>5} vs {dsp}")
    print(f"self-test: {'PASS' if not bad else str(bad) + ' MISMATCH'}  ({rows} rows)")
    return bad


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    if args[0] == "--self-test":
        sys.exit(1 if self_test() else 0)
    if args[0] == "--diff":
        diff(args[1], args[2])
    else:
        for p in args:
            fam, rows, trusted = load(p)
            show(p, fam, rows, trusted)
            if os.environ.get("FAMILIES_JSON"):
                print(json.dumps(fam, indent=2))
