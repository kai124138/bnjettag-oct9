#!/usr/bin/env python3
'Record parsed HLS synthesis measurements as an optional experiment artifact.'
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bnhgq2 import wandb_util as wbu  # noqa: E402


def parse_csynth(path: str) -> dict:
    """Same fields as parse_csynth.py (the the synthesis host-side stdlib parser)."""
    xml = ET.parse(path).getroot()

    def txt(p, default=None):
        e = xml.find(p)
        return e.text if e is not None else default

    res_el = xml.find("AreaEstimates/Resources")
    res = {r.tag: r.text for r in (res_el if res_el is not None else [])}
    lat = xml.find("PerformanceEstimates/SummaryOfOverallLatency")
    timing = xml.find("PerformanceEstimates/SummaryOfTimingAnalysis")
    out = {
        "part": txt("UserAssignments/Part"),
        "top": txt("UserAssignments/TopModelName"),
        "target_clock_ns": float(txt("UserAssignments/TargetClockPeriod") or -1),
        "estimated_clock_ns": float((timing is not None
                                     and timing.findtext("EstimatedClockPeriod")) or -1),
        "LUT": int(res.get("LUT", -1)),
        "FF": int(res.get("FF", -1)),
        "DSP": int(res.get("DSP", res.get("DSP48E", -1))),
        "BRAM_18K": int(res.get("BRAM_18K", -1)),
        "URAM": int(res.get("URAM", -1)),
    }
    for k, tag in (("LatencyBest", "Best-caseLatency"),
                   ("LatencyWorst", "Worst-caseLatency"),
                   ("IntervalMin", "Interval-min"), ("IntervalMax", "Interval-max")):
        v = lat is not None and lat.findtext(tag)
        out[k] = int(v) if v else None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("xml", nargs="+", help="csynth.xml report(s)")
    ap.add_argument("--manifest", default="",
                    help="convert manifest json (carries wandb_run, variant, ...)")
    ap.add_argument("--group", default="", help="W&B group (default env WANDB_GROUP)")
    ap.add_argument("--tags", default="hls,csynth", help="comma list of extra tags")
    ap.add_argument("--dry-run", action="store_true", help="parse + print, no W&B")
    a = ap.parse_args()

    manifest = json.load(open(a.manifest)) if a.manifest else {}
    src_run = manifest.get("wandb_run", "")

    if not a.dry_run and not wbu.wandb_enabled():
        sys.exit("[fatal] WANDB_API_KEY not set (use --dry-run to just parse)")
    for xp in a.xml:
        row = parse_csynth(xp)
        stem = os.path.splitext(os.path.basename(xp))[0]
        print(f"[hls] {stem}: " + json.dumps(row))
        if a.dry_run:
            continue
        import wandb
        run = wandb.init(**wbu.init_kwargs(
            name=f"hls-{stem}", job_type="hls",
            group=a.group or None,
            tags=[t for t in a.tags.split(",") if t],
            config={"report": stem, "part": row["part"], "top": row["top"],
                    "target_clock_ns": row["target_clock_ns"],
                    "wandb_run": src_run,
                    **{k: v for k, v in manifest.items()
                       if isinstance(v, (str, int, float, bool))}}))
        run.summary.update({k: v for k, v in row.items() if v is not None})
        try:
            wbu.log_files_artifact(
                run, name=f"synthesis-{stem}", type="synthesis",
                files=[xp] + ([a.manifest] if a.manifest else []),
                metadata={**row, "wandb_run": src_run})
        except Exception as e:
            print(f"[hls] artifact warn: {e}", flush=True)
        wandb.finish()
        print(f"[hls] logged {stem} -> W&B (job_type=hls, source run: "
              f"{src_run or 'unknown'})")


if __name__ == "__main__":
    main()
