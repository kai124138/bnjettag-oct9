"""Behavioral checks for bounded tools, method drift, and cooperative loop state."""
from __future__ import annotations

import asyncio
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from jev.common import LabError, digest, local_path, policy_snapshot, reject_secrets, write_json
from jev.engine import Engine, decision, validate_answers
from jev.loops import LoopStore
from jev.methods import check_protocol, freeze_protocol, inspect_protocol
from jev.service import Service


def answer_transport(state, questions):
    answers = {}
    for qid, q in reversed(list(questions.items())):
        if q["type"] == "choice":
            labels = list(q["criteria"])
            answers[qid] = {"type": "choice", "choice": labels[0], "confidence": 0.95,
                            "probabilities": {k: float(k == labels[0]) for k in labels}}
        elif q["type"] == "score":
            answers[qid] = {"type": "score", "score": 1.5, "confidence": 0.9,
                            "probabilities": {str(i): 0.5 if i in (1, 2) else 0.0 for i in range(len(q["criteria"]))}}
        else:
            answers[qid] = {"type": "noul", "noul": 0.8}
    return {"model": "fixture-model", "answers": answers, "usage": {"input_tokens": 1, "output_tokens": 1}}


class LabCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for path in policy_snapshot(ROOT):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.protocol = json.loads((ROOT / "tools/jev/examples/protocol-screen.json").read_text())
        self.engine = Engine(self.root, transport=answer_transport)
        self.service = Service(self.root, self.engine)
        self.loops = LoopStore(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def source(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def start(self, **kwargs):
        return self.loops.start("Synthetic local check", max_seconds=600, **kwargs)["loop_id"]

    def advance_to_review(self, loop_id):
        self.loops.record(loop_id, "plan", "complete", "Plan saved", [self.source("local/plan.md", "plan")])
        self.loops.record(loop_id, "execute", "complete", "Work saved", [self.source("local/output.md", "output")])

    def test_all_six_tools_have_usable_typed_results(self):
        items = [{"id": "first", "text": "Synthetic evidence"}, {"id": "second", "text": "Another excerpt"}]
        for tool in ("jev_triage_logs", "jev_triage_review", "jev_screen_papers"):
            result = self.service.call(tool, {"items": items})
            self.assertEqual({x["id"] for x in result["results"]}, {"first", "second"})
            self.assertTrue(result["advisory_only"])
        self.assertEqual(len(self.service.rank_snippets("query", items)["results"]), 2)
        self.assertEqual(self.service.check_claims([{**items[0], "claim": "Exact claim"}])["results"][0]["id"], "first")
        self.assertEqual(self.service.route_task("Inspect local code")["results"][0]["id"], "task")

    def test_category_a_finding_not_downgraded_when_api_reorders_answers(self):
        result = self.service.triage_review([{"id": "first", "text": "Issue", "severity": "A"}, {"id": "second", "text": "Issue"}])
        by_id = {x["id"]: x for x in result["results"]}
        self.assertEqual(by_id["first"]["disposition"], "mandatory_review")
        self.assertEqual(by_id["second"]["disposition"], "suggestion")

    def test_unknown_is_review_even_with_high_confidence(self):
        self.assertEqual(decision({"type": "choice", "choice": "unknown", "confidence": 1, "probabilities": {"unknown": 1, "known": 0}}), "review")

    def test_duplicate_ids_rejected_before_network(self):
        with self.assertRaises(LabError):
            self.service.triage_logs([{"id": "same", "text": "a"}, {"id": "same", "text": "b"}])

    def test_explicit_line_excerpt_used(self):
        path = self.source("local/source.txt", "first\nsecond\nthird\n")
        item = self.service.items([{"id": "excerpt", "path": path, "start_line": 2, "end_line": 2}])["excerpt"]
        self.assertEqual(item["text"], "second")

    def test_symlink_escape_and_credentials_are_refused(self):
        (self.root / "escape").symlink_to(Path(self.temp.name).parent)
        for path in ("../outside", "escape/outside", "wandb-api-key.txt", "_attic/old.md"):
            with self.assertRaises(LabError):
                local_path(path, self.root)
        with self.assertRaises(LabError):
            reject_secrets({"text": "Bearer this_is_a_synthetic_secret_token"})

    def test_audit_does_not_store_raw_state(self):
        self.service.triage_logs([{"id": "excerpt", "text": "UNIQUE_SYNTHETIC_SOURCE_TEXT"}])
        text = next((self.root / "local/jev-audit").glob("*.json")).read_text()
        self.assertNotIn("UNIQUE_SYNTHETIC_SOURCE_TEXT", text)
        self.assertFalse(json.loads(text)["raw_state_saved"])

    def test_partial_response_refused(self):
        with self.assertRaises(LabError):
            validate_answers({"q": {"type": "noul"}}, {"answers": {}})

    def test_invalid_numeric_response_refused(self):
        for value in (True, float("nan"), -0.1, 1.1):
            with self.assertRaises(LabError):
                validate_answers({"q": {"type": "noul"}}, {"answers": {"q": {"type": "noul", "noul": value}}})

    def test_mismatched_distribution_refused(self):
        q = {"q": {"type": "choice", "criteria": {"a": "a", "b": "b"}}}
        with self.assertRaises(LabError):
            validate_answers(q, {"answers": {"q": {"type": "choice", "choice": "a", "confidence": 0.9, "probabilities": {"a": 0.2, "b": 0.3}}}})

    def test_semantic_methods_stays_advisory(self):
        result = self.service.check_methods("Synthetic method description")
        self.assertEqual(len(result["results"]), 6)
        self.assertFalse(result["launch_authorized"])
        self.assertEqual(result["scientific_gate"], "not_evaluated")

    def test_valid_screen_protocol(self):
        self.assertEqual(check_protocol(self.protocol), [])

    def test_test_selection_and_cost_mismatch_block(self):
        self.protocol["selection"].update(split="ROC-test", cost_checkpoint="final")
        self.assertTrue(check_protocol(self.protocol))

    def test_claim_needs_seeds_and_interval(self):
        self.protocol["scope"] = "claim"
        fields = {x["field"] for x in check_protocol(self.protocol)}
        self.assertIn("arms.baseline", fields)
        self.assertIn("interval_method", fields)

    def test_unregistered_schedule_change_is_found(self):
        arm = copy.deepcopy(self.protocol["arms"][0])
        arm.update(name="changed", group="changed")
        arm["schedule"]["epochs"] += 1
        self.protocol["arms"].append(arm)
        self.assertTrue(any("schedule.epochs" in x["field"] for x in check_protocol(self.protocol)))
        arm["changed_factors"] = ["schedule.epochs"]
        self.assertEqual(check_protocol(self.protocol), [])

    def test_nonfinite_schedule_and_boolean_size_block(self):
        self.protocol["arms"][0]["schedule"].update(learning_rate=float("nan"), epochs=True)
        self.assertEqual(len(check_protocol(self.protocol)), 2)

    def test_protocol_snapshot_detects_drift_and_tampering(self):
        path = self.source("local/protocol.json", json.dumps(self.protocol))
        frozen = freeze_protocol(path, self.root)
        self.assertTrue(inspect_protocol(path, frozen["snapshot_path"], self.root)["matches_snapshot"])
        self.protocol["arms"][0]["schedule"]["epochs"] += 1
        self.source(path, json.dumps(self.protocol))
        self.assertFalse(inspect_protocol(path, frozen["snapshot_path"], self.root)["matches_snapshot"])
        snapshot = self.root / frozen["snapshot_path"]
        record = json.loads(snapshot.read_text())
        record["record"]["protocol"]["purpose"] = "tampered"
        snapshot.write_text(json.dumps(record))
        with self.assertRaises(LabError):
            inspect_protocol(path, frozen["snapshot_path"], self.root)

    def test_protocol_snapshot_detects_methodology_change(self):
        path = self.source("local/protocol.json", json.dumps(self.protocol))
        frozen = freeze_protocol(path, self.root)
        self.source("AGENTS.md", "Changed policy")
        self.assertTrue(inspect_protocol(path, frozen["snapshot_path"], self.root)["findings"])

    def test_catalog_change_stops_loop(self):
        loop_id = self.start()
        self.source("tools/jev/catalog.json", '{"changed": true}')
        self.assertEqual(self.loops.next(loop_id)["stop_reason"], "methodology_changed")

    def test_same_path_config_edit_is_detected(self):
        config = self.source("local/arm.json", '{"epochs": 3}')
        self.protocol["arms"][0]["config_path"] = config
        path = self.source("local/protocol.json", json.dumps(self.protocol))
        frozen = freeze_protocol(path, self.root)
        self.source(config, '{"epochs": 4}')
        result = inspect_protocol(path, frozen["snapshot_path"], self.root)
        self.assertFalse(result["matches_snapshot"])
        self.assertEqual(result["drift"][0]["field"], "config_sources."+config)

    def test_config_snapshot_preserves_actual_newline_bytes(self):
        config = self.source("local/arm.json", '{"epochs": 3}\r\n')
        self.protocol["arms"][0]["config_path"] = config
        path = self.source("local/protocol.json", json.dumps(self.protocol))
        frozen = freeze_protocol(path, self.root)
        self.source(config, '{"epochs": 3}\n')
        self.assertFalse(inspect_protocol(path, frozen["snapshot_path"], self.root)["matches_snapshot"])

    def test_parallel_reservations_cannot_exceed_call_budget(self):
        from concurrent.futures import ThreadPoolExecutor
        loop_id = self.start(max_jev_calls=5)
        def reserve(_):
            try:
                return self.loops.reserve_call(loop_id)
            except LabError:
                return None
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(reserve, range(10)))
        self.assertEqual(sum(x is not None for x in results), 5)
        self.assertEqual(self.loops.status(loop_id)["jev_calls"], 5)

    def test_cannot_skip_loop_stages(self):
        loop_id = self.start()
        with self.assertRaises(LabError):
            self.loops.record(loop_id, "review", "pass", "Done", [])

    def test_loop_pass_requires_distinct_check_evidence(self):
        loop_id = self.start()
        self.advance_to_review(loop_id)
        review = self.source("local/review.md", "Review")
        with self.assertRaises(LabError):
            self.loops.record(loop_id, "review", "pass", "Done", [review, review])
        checks = self.source("local/checks.txt", "Actual synthetic check output")
        result = self.loops.record(loop_id, "review", "pass", "Local acceptance", [review, checks])
        self.assertEqual(result["status"], "complete")
        self.assertFalse(result["launch_authorized"])

    def test_changed_evidence_cannot_pass(self):
        loop_id = self.start()
        self.advance_to_review(loop_id)
        self.source("local/output.md", "Changed after execution")
        with self.assertRaises(LabError):
            self.loops.record(loop_id, "review", "pass", "Done", [self.source("local/review.md", "Review"), self.source("local/checks.txt", "Checks")])

    def test_iteration_limit_stops(self):
        loop_id = self.start(max_iterations=1)
        self.advance_to_review(loop_id)
        result = self.loops.record(loop_id, "review", "iterate", "Needs revision", [self.source("local/review.md", "Finding")])
        self.assertEqual(result["stop_reason"], "iteration_budget_exhausted")

    def test_unchanged_work_stops_loop(self):
        loop_id = self.start(max_iterations=3)
        self.advance_to_review(loop_id)
        self.loops.record(loop_id, "review", "iterate", "Needs revision", [self.source("local/review.md", "Finding")])
        self.advance_to_review(loop_id)
        result = self.loops.record(loop_id, "review", "iterate", "Still failing", ["local/review.md"])
        self.assertEqual(result["stop_reason"], "no_progress")

    def test_methodology_change_stops_loop(self):
        loop_id = self.start()
        self.source("AGENTS.md", "Changed")
        self.assertEqual(self.loops.next(loop_id)["stop_reason"], "methodology_changed")

    def test_elapsed_deadline_stops_loop(self):
        loop_id = self.start()
        with patch("jev.loops.time.time", return_value=10**15):
            self.assertEqual(self.loops.next(loop_id)["stop_reason"], "time_budget_exhausted")

    def test_failed_api_attempt_still_consumes_budget(self):
        loop_id = self.start(max_jev_calls=1)
        def failing(state, questions):
            raise RuntimeError("Synthetic failure")
        engine = Engine(self.root, transport=failing)
        with self.assertRaises(LabError):
            engine.ask("state", {"q": {"type": "noul", "instructions": "Question"}}, loop_id)
        self.assertEqual(self.loops.status(loop_id)["jev_calls"], 1)
        with self.assertRaises(LabError):
            self.loops.reserve_call(loop_id)
        self.assertEqual(self.loops.status(loop_id)["stop_reason"], "jev_call_budget_exhausted")

    def test_tampered_event_context_is_unavailable(self):
        loop_id = self.start()
        path = self.loops.directory(loop_id) / "events/000000.json"
        value = json.loads(path.read_text())
        value["record"]["state"]["status"] = "complete"
        path.write_text(json.dumps(value))
        with self.assertRaises(LabError):
            self.loops.status(loop_id)

    def test_stale_loop_record_rejected(self):
        loop_id = self.start()
        before = self.loops.status(loop_id)["last_event_sha256"]
        self.loops.reserve_call(loop_id)
        with self.assertRaises(LabError):
            self.loops.record(loop_id, "plan", "complete", "Plan", [self.source("local/plan.md", "Plan")], before)

    def test_external_kind_refused(self):
        with self.assertRaises(LabError):
            self.loops.start("Train", kind="training_launch")


class MCPIntegration(unittest.TestCase):
    def test_stdio_discovery_and_offline_doctor(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def run():
            async with stdio_client(StdioServerParameters(command=sys.executable, args=[str(ROOT / "tools/jev_lab.py"), "mcp"], cwd=str(ROOT))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    names = {tool.name for tool in listed.tools}
                    self.assertEqual(len(names), 14)
                    self.assertIn("jev_check_methods", names)
                    self.assertIn("lab_loop_record", names)
                    response = await session.call_tool("jev_doctor", {"live": False})
                    self.assertFalse(response.isError)
                    self.assertEqual(response.structuredContent["workspace"], str(ROOT))
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
