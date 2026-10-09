"""Parse the E-D1 csynth report and evaluate the pre-registered bands
(experiment-log 2026-07-26, E-D1 PRE-REGISTRATION).

Expects the fetched project tree under results/adder-graph/ed1/prj_ed1/
(fetch_ed1.sh). Emits results/adder-graph/ed1/RESULTS.md and prints it.

Registered bands:
  bit-exact  on-box csim EXACT_MATCH required, else nothing below counts
  II         SUCCESS <= 10 (legal <= 11 with II x clk <= 25 ns); KILL ~ sum of
             stage IIs (~40-50): the stages serialize at the softmax barrier
  LUT        component sum 203k, band [142k, 264k], drift alarm > 305k
  DSP        dense stages 0, attention ~640, alarm > 700
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ED1 = Path(__file__).resolve().parents[2] / "results/adder-graph/ed1"
LUT_BAND = (142_000, 264_000)
LUT_ALARM = 305_000
DSP_ALARM = 700


def top_and_modules(xmlpath):
    r = ET.parse(xmlpath).getroot()
    res = r.find("AreaEstimates/Resources")
    lat = r.find("PerformanceEstimates/SummaryOfOverallLatency")
    clk = float(r.find(
        "PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod").text)
    top = dict(
        lut=int(res.find("LUT").text), ff=int(res.find("FF").text),
        dsp=int(res.find("DSP").text), bram=int(res.find("BRAM_18K").text),
        lat_best=lat.find("Best-caseLatency").text,
        lat_worst=lat.find("Worst-caseLatency").text,
        ii_min=lat.find("Interval-min").text, ii_max=lat.find("Interval-max").text,
        clk=clk)
    mods = []
    for m in r.findall("ModuleInformation/Module"):
        name = m.find("Name").text
        mres = m.find("AreaEstimates/Resources")
        mlat = m.find("PerformanceEstimates/SummaryOfOverallLatency")
        if mres is None:
            continue
        mods.append(dict(
            name=name,
            lut=int(mres.find("LUT").text), ff=int(mres.find("FF").text),
            dsp=int(mres.find("DSP").text),
            ii_min=mlat.find("Interval-min").text if mlat is not None else "-",
            ii_max=mlat.find("Interval-max").text if mlat is not None else "-"))
    return top, mods


def csim_verdict():
    """On-box csim result: EXACT_MATCH printed by tb.cpp, and zero csim errors."""
    for p in [ED1 / "prj_ed1/sol1/csim/report/myproject_csim.log",
              ED1 / "vitis_hls.log"]:
        if p.exists():
            t = p.read_text(errors="replace")
            if "EXACT_MATCH" in t:
                return "EXACT_MATCH (on-box)", True
            if "FAIL" in t and "mismatches" in t:
                m = re.search(r"FAIL \d+ mismatches", t)
                return m.group(0), False
    return "csim log not found", False


def main():
    x = ED1 / "prj_ed1/sol1/syn/report/csynth.xml"
    if not x.exists():
        raise SystemExit(f"missing {x} — run fetch_ed1.sh first")
    top, mods = top_and_modules(x)
    csim_txt, csim_ok = csim_verdict()

    ii = int(top["ii_max"])
    envelope_ns = ii * top["clk"]
    ii_verdict = ("SUCCESS" if ii <= 10 else
                  "LEGAL (10 < II <= 11)" if ii <= 11 else
                  "KILL — stages serialize" if ii >= 40 else
                  "MISS (11 < II < 40: partial serialization)")
    lut_verdict = ("in-band" if LUT_BAND[0] <= top["lut"] <= LUT_BAND[1] else
                   "DRIFT ALARM (>1.5x component sum)" if top["lut"] > LUT_ALARM else
                   "out-of-band")
    dsp_verdict = "ok" if top["dsp"] <= DSP_ALARM else "ALARM (>700)"

    lines = [
        "# E-D1 results — token-serial block-0 slice (fold composition)",
        "",
        f"Bit-exactness: {csim_txt}."
        + ("" if csim_ok else " **NO RESOURCE NUMBER BELOW COUNTS.**"),
        "",
        "| quantity | value | band | verdict |",
        "|---|---|---|---|",
        f"| top dataflow interval | {top['ii_min']}–{top['ii_max']} | <=10 (<=11 legal) | **{ii_verdict}** |",
        f"| II x est clk | {envelope_ns:.1f} ns | <= 25 ns | {'PASS' if envelope_ns <= 25 else 'FAIL'} |",
        f"| LUT | {top['lut']:,} | [{LUT_BAND[0]:,}, {LUT_BAND[1]:,}] | {lut_verdict} |",
        f"| FF | {top['ff']:,} | — | — |",
        f"| DSP | {top['dsp']} | ~640, alarm >700 | {dsp_verdict} |",
        f"| BRAM_18K | {top['bram']} | — | — |",
        f"| latency (best/worst) | {top['lat_best']}/{top['lat_worst']} | — | — |",
        f"| est clock | {top['clk']:.3f} ns | <= 2.5 | {'PASS' if top['clk'] <= 2.5 else 'FAIL'} |",
        "",
        "## Per-module (csynth estimates)",
        "",
        "| module | LUT | FF | DSP | II (min–max) |",
        "|---|---|---|---|---|",
    ]
    for m in sorted(mods, key=lambda d: -d["lut"]):
        lines.append(f"| {m['name']} | {m['lut']:,} | {m['ff']:,} | {m['dsp']} | "
                     f"{m['ii_min']}–{m['ii_max']} |")
    lines += [
        "",
        "Component-sum prediction (pre-registered): ~203k LUT — QKV 43.5k (alpha-prop) + "
        "f12 4,789 + softmax 21.1k + f18 29,205 + Wo 14.5k (alpha-prop) + fc1 29,029 + "
        "fc2 ~29.0k (alpha-prop) + glue ~17k + plumbing ~15k. Source: experiment-log "
        "2026-07-26 E-D1 pre-registration.",
    ]
    out = ED1 / "RESULTS.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
