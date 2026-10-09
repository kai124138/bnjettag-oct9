"""Parse Experiment-1 reports fetched from mulder and evaluate the
pre-registered kill conditions (COMPILER.md, 2026-07-24).

Expects the arm project trees under results/adder-graph/e1/<arm>/prj_<arm>/
(fetched with e1_fetch.sh / rsync). Emits results/adder-graph/e1/RESULTS.md
and prints the verdict table.

Baselines and gates:
  census baseline (10 instances of bit_block_0_ffn_fc1, whole_model_rf8_stdnn):
    234,930 LUT. Arm P must land at 1.0 +- 0.15 x.
  predictions (x baseline): A 0.10-0.17 · A2 0.50-0.60 · B 0.30-0.55 · C 0.04-0.09
  kill: (A > 0.25 AND A2 > 0.6)  -> folding infeasible
        (B > 0.74)               -> restructuring pillar dies
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

E1 = Path(__file__).resolve().parents[2] / "results/adder-graph/e1"
CENSUS = 234_930
PRED = {"p": (0.85, 1.15), "a": (0.10, 0.17), "a2": (0.50, 0.60),
        "b": (0.30, 0.55), "c": (0.04, 0.09)}


def csynth(arm):
    x = E1 / arm / f"prj_{arm}/sol1/syn/report/csynth.xml"
    if not x.exists():
        return None
    r = ET.parse(x).getroot()
    res = r.find("AreaEstimates/Resources")
    perf = r.find("PerformanceEstimates")
    lat = perf.find("SummaryOfOverallLatency")
    return dict(
        lut=int(res.find("LUT").text), ff=int(res.find("FF").text),
        dsp=int(res.find("DSP").text), bram=int(res.find("BRAM_18K").text),
        lat=lat.find("Average-caseLatency").text,
        ii=lat.find("Interval-max").text,
        clk=float(perf.find("SummaryOfTimingAnalysis/EstimatedClockPeriod").text))


def export_syn(arm):
    """Vivado synthesis numbers from export_design -flow syn (the arm-V anchor)."""
    for pat in ["impl/report/verilog/export_syn.rpt",
                "impl/report/verilog/myproject_export.rpt"]:
        f = E1 / arm / f"prj_{arm}/sol1" / pat
        if f.exists():
            t = f.read_text()
            lut = re.search(r"LUT:?\s*\|?\s*(\d+)", t)
            ff = re.search(r"FF:?\s*\|?\s*(\d+)", t)
            cp = re.search(r"CP achieved post-synthesis:?\s*\|?\s*([\d.]+)", t)
            return dict(lut=int(lut.group(1)) if lut else None,
                        ff=int(ff.group(1)) if ff else None,
                        clk=float(cp.group(1)) if cp else None)
    return None


def main():
    rows, missing = {}, []
    for arm in ["p", "a", "a2", "b", "c"]:
        r = csynth(arm)
        if r is None:
            missing.append(arm)
            continue
        r["ratio"] = r["lut"] / CENSUS
        r["syn"] = export_syn(arm)
        rows[arm] = r

    lines = ["# Experiment-1 results (parsed from mulder csynth/export reports)",
             "",
             f"Baseline: census 10x bit_block_0_ffn_fc1 = {CENSUS:,} LUT "
             "(whole_model_rf8_stdnn.xml). All arms C-simulated bit-exact before "
             "synthesis (local g++ EXACT_MATCH + on-box csim_design).", "",
             "| arm | LUT | ratio | pred | FF | DSP | lat | II | est clk | post-syn LUT | post-syn clk |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, r in rows.items():
        lo, hi = PRED[arm]
        ok = "Y" if lo <= r["ratio"] <= hi else "MISS"
        s = r.get("syn") or {}
        lines.append(
            f"| {arm.upper()} | {r['lut']:,} | {r['ratio']:.3f}x [{ok}] | "
            f"{lo:.2f}-{hi:.2f} | {r['ff']:,} | {r['dsp']} | {r['lat']} | "
            f"{r['ii']} | {r['clk']:.3f} ns | "
            f"{s.get('lut') if s else '-'} | {s.get('clk') if s else '-'} |")

    verdict = []
    if "p" in rows:
        pr = rows["p"]["ratio"]
        verdict.append(f"parity: {'PASS' if 0.85 <= pr <= 1.15 else 'FAIL'} ({pr:.3f}x)")
    if "a" in rows and "a2" in rows:
        a, a2 = rows["a"]["ratio"], rows["a2"]["ratio"]
        fold_dead = a > 0.25 and a2 > 0.60
        verdict.append(f"folding: {'KILLED' if fold_dead else 'ALIVE'} "
                       f"(A={a:.3f}, A2={a2:.3f})")
    if "b" in rows:
        b = rows["b"]["ratio"]
        verdict.append(f"restructuring: {'KILLED' if b > 0.74 else 'ALIVE'} (B={b:.3f})")
    if "c" in rows and "a" in rows and "b" in rows:
        pred_c = rows["a"]["ratio"] * rows["b"]["ratio"] / max(rows["p"]["ratio"], 1e-9)
        verdict.append(f"composition: C={rows['c']['ratio']:.3f} vs AxB/P={pred_c:.3f} "
                       f"({'within 20%' if abs(rows['c']['ratio']/pred_c - 1) <= 0.2 else 'interaction!'})")
    lines += ["", "## Verdicts (pre-registered)", ""] + [f"- {v}" for v in verdict]
    if missing:
        lines += ["", f"Missing arms: {missing}"]

    out = E1 / "RESULTS.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
