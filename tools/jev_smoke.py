#!/usr/bin/env python3
"""Exercise the real stdio server; --live adds eight synthetic Jev evaluations."""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "local/jev-runtime/bin/python"
if RUNTIME.exists() and Path(sys.prefix).resolve() != RUNTIME.parent.parent.resolve():
    os.execv(str(RUNTIME), [str(RUNTIME), str(Path(__file__).resolve()), *sys.argv[1:]])

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from jev.common import LabError, write_json


async def run(live: bool):
    async with stdio_client(StdioServerParameters(command=str(RUNTIME), args=[str(ROOT / "tools/jev_lab.py"), "mcp"], cwd=str(ROOT))) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = [tool.name for tool in (await session.list_tools()).tools]
            async def call(name, arguments):
                response = await session.call_tool(name, arguments)
                if response.isError:
                    raise LabError(f"MCP smoke failed at {name}; inspect the local error")
                return response.structuredContent or json.loads(response.content[0].text)
            doctor = await call("jev_doctor", {"live": False})
            if not live:
                print(json.dumps({"tools": names, "doctor": doctor}, indent=2))
                return
            loop = await call("lab_loop_start", {"goal": "Synthetic end-to-end integration verification; no science or cluster actions", "kind": "evidence_review", "max_iterations": 1, "max_seconds": 1800, "max_jev_calls": 8})
            loop_id, directory = loop["loop_id"], ROOT / loop["artifact_directory"]
            def artifact(name, text):
                path = directory / name
                path.write_text(text)
                return str(path.relative_to(ROOT))
            def json_artifact(name, value):
                return artifact(name, json.dumps(value, indent=2))
            await call("lab_loop_record", {"loop_id": loop_id, "stage": "plan", "outcome": "complete", "summary": "Synthetic MCP and method-drift checks planned", "evidence_paths": [artifact("plan-1.md", "Exercise all six workflows, semantic method checking, exact protocol/config drift, and the cooperative loop. All fixtures are synthetic. No jobs or model workers will be launched.\n")]})
            calls = [
                ("jev_triage_logs", json.loads((ROOT / "tools/jev/examples/triage.json").read_text())),
                ("jev_rank_snippets", {"query": "Where must checkpoint selection happen?", "items": [{"id": "selection", "text": "Choose the checkpoint using validation AUC; held-out ROC-test is never used for selection."}, {"id": "unrelated", "text": "The page uses a blue accent color."}]}),
                ("jev_triage_review", {"items": [{"id": "bug", "text": "The function returns a negative array length and the supplied test fails with ValueError.", "severity": "A"}, {"id": "style", "text": "Prefer single quotes over double quotes; observed behavior is identical."}]}),
                ("jev_screen_papers", {"items": [{"id": "paper", "text": "Synthetic abstract: We implement a binary-weight neural network for collider jet tagging on an FPGA with HLS and report resource use and latency."}]}),
                ("jev_check_claims", {"items": [{"id": "claim", "claim": "The method improves all tasks.", "text": "Synthetic source: The method improves one evaluated task; generalization to other tasks has not been tested."}]}),
                ("jev_route_task", {"task": "Investigate supplied dataset-cache failure logs; do not relaunch any job."}),
                ("jev_check_methods", {"candidate": "Synthetic deliberately flawed method: choose the checkpoint with highest ROC-test AUC, report its AUC beside the final epoch's eBOP cost, and call a one-seed difference an established improvement without an interval. Launch while the scientific gate is pending."}),
                ("jev_check_methods", {"candidate": "Synthetic corrected method: matched N and feature sets, paired seeds, fixed identical schedules except preregistered arm factors; choose the highest validation macro-OvR AUC checkpoint within the eBOP cap. Evaluate ROC-test once after selection. Remeasure native HGQ2 cost on that same checkpoint. Recompute raw-artifact metrics with metric, split, actual n, and seed status, and report paired seed intervals without claiming differences inside the spread. Freeze actual working files through the existing campaign freeze and validate the immutable factual handoff before launch. Obtain a cleared scientific gate and current explicit launch authorization. Monitoring is read-only; no kill, relaunch, resume, or science change. Chang K1's choice and b5 readout remain pending; this fixture clears neither."}),
            ]
            results = []
            for name, args in calls:
                result = await call(name, {**args, "loop_id": loop_id})
                results.append({"tool": name, "result": result})
                print(json.dumps({"tool": name, "model": result["model"], "latency_seconds": result["latency_seconds"], "labels": {key: answer.get("choice", answer.get("score")) for key, answer in result["answers"].items()}}), flush=True)
            protocol = copy.deepcopy(json.loads((ROOT / "tools/jev/examples/protocol-screen.json").read_text()))
            protocol["arms"][0]["config_path"] = json_artifact("arm-config.json", {"synthetic": True, "epochs": 3})
            protocol_path = json_artifact("protocol.json", protocol)
            before = await call("lab_check_protocol", {"path": protocol_path})
            snapshot = await call("lab_freeze_protocol", {"path": protocol_path})
            protocol["arms"][0]["schedule"]["epochs"] = 4
            json_artifact("protocol.json", protocol)
            json_artifact("arm-config.json", {"synthetic": True, "epochs": 4})
            after = await call("lab_check_protocol", {"path": protocol_path, "baseline_path": snapshot["snapshot_path"]})
            checks = {
                "all_tools_discovered": len(names) == 14,
                "triage_labels": [x["choice"] for x in results[0]["result"]["results"]] == ["gpu_memory", "environment", "unknown"],
                "unknown_preserved": results[0]["result"]["results"][2]["disposition"] == "review",
                "relevant_excerpt_first": results[1]["result"]["results"][0]["id"] == "selection",
                "category_a_preserved": results[2]["result"]["results"][0]["disposition"] == "mandatory_review",
                "overstatement_detected": results[4]["result"]["results"][0]["choice"] == "overstated",
                "test_selection_conflict": results[6]["result"]["answers"]["selection"]["choice"] == "conflict",
                "valid_synthetic_protocol": before["structural_valid"],
                "protocol_drift_detected": any(x["field"] == "arms" for x in after["drift"]),
                "same_path_config_drift_detected": any(x["field"].startswith("config_sources.") for x in after["drift"]),
                "no_launch_grant": not after["launch_authorized"],
            }
            evidence = [json_artifact("api-results-1.json", results), json_artifact("protocol-results-1.json", {"before": before, "snapshot": snapshot, "after": after}), artifact("execution-1.md", "Ran synthetic tool calls and exact declared/config drift checks over MCP.\n")]
            await call("lab_loop_record", {"loop_id": loop_id, "stage": "execute", "outcome": "complete", "summary": "Synthetic executions captured", "evidence_paths": evidence})
            outcome = "pass" if all(checks.values()) else "iterate"
            review_evidence = [json_artifact("checks-1.json", checks), artifact("review-1.md", "Local synthetic integration checks: " + outcome + ". This is not a research reviewer verdict.\n")]
            final = await call("lab_loop_record", {"loop_id": loop_id, "stage": "review", "outcome": outcome, "summary": "Synthetic acceptance checks recorded", "evidence_paths": review_evidence})
            status = await call("lab_loop_status", {"loop_id": loop_id})
            report = {"kind": "synthetic engineering smoke; no physics metrics", "checks": checks, "loop_id": loop_id, "status": final["status"], "jev_calls": status["jev_calls"], "model": results[0]["result"]["model"], "artifacts": str(directory.relative_to(ROOT))}
            write_json(ROOT / "local/2026-10-02-jev-integration/SMOKE.json", report)
            print(json.dumps(report, indent=2))
            if not all(checks.values()):
                raise LabError("One or more synthetic smoke checks failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.live))
