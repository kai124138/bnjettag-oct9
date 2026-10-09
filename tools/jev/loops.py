"""Durable cooperative loops: agents perform steps, this store tracks their evidence.

No subprocesses, shell execution, model spawning, polling, or cluster mutations.
"""
from __future__ import annotations

import fcntl
import json
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .common import ROOT, LabError, digest, local_path, policy_snapshot, read_text, reject_secrets, utc_now, write_json

KINDS = {"local_engineering", "methods_audit", "literature_review", "evidence_review"}
STAGES = {"plan": "execute", "execute": "review"}


class LoopStore:
    def __init__(self, root: Path = ROOT):
        self.root = root

    def directory(self, loop_id: str) -> Path:
        if not re.fullmatch(r"lp-[a-f0-9]{32}", loop_id):
            raise LabError("Invalid loop ID")
        path = local_path(f"local/jev-loops/{loop_id}", self.root)
        if not path.is_dir():
            raise LabError("Loop does not exist")
        return path

    @contextmanager
    def locked(self, loop_id: str):
        directory = self.directory(loop_id)
        with (directory / ".lock").open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield directory

    def load(self, directory: Path) -> tuple[dict, list[dict]]:
        events = []
        previous = None
        for i, path in enumerate(sorted((directory / "events").glob("*.json"))):
            event = json.loads(path.read_text())
            if path.name != f"{i:06d}.json" or event.get("previous") != previous or event.get("sha256") != digest(event.get("record")):
                raise LabError("Loop event chain is invalid; context unavailable")
            if not isinstance(event["record"], dict) or event["record"].get("previous") != previous:
                raise LabError("Loop event linkage is invalid; context unavailable")
            events.append(event)
            previous = event["sha256"]
        if not events:
            raise LabError("Loop has no valid initial event")
        return events[-1]["record"]["state"], events

    def save(self, directory: Path, state: dict, events: list[dict], action: str, detail: dict) -> None:
        previous = events[-1]["sha256"] if events else None
        record = {"at": utc_now(), "action": action, "detail": detail, "state": state, "previous": previous}
        reject_secrets(record)
        write_json(directory / "events" / f"{len(events):06d}.json", {"previous": previous, "record": record, "sha256": digest(record)})

    def start(self, goal: str, kind: str = "local_engineering", max_iterations: int = 3,
              max_seconds: int = 1800, max_jev_calls: int = 20) -> dict:
        reject_secrets(goal)
        if not goal.strip() or len(goal) > 4000 or kind not in KINDS:
            raise LabError("State a bounded goal and supported local loop kind")
        if type(max_iterations) is not int or not 1 <= max_iterations <= 10 or type(max_seconds) is not int or not 30 <= max_seconds <= 7200 or type(max_jev_calls) is not int or not 0 <= max_jev_calls <= 100:
            raise LabError("Loop limits are outside the supported bounds")
        loop_id = "lp-" + uuid.uuid4().hex
        directory = self.root / "local/jev-loops" / loop_id
        directory.mkdir(parents=True)
        state = {"loop_id": loop_id, "goal": goal, "kind": kind, "status": "active", "stage": "plan",
                 "iteration": 1, "max_iterations": max_iterations, "deadline": time.time()+max_seconds,
                 "max_jev_calls": max_jev_calls, "jev_calls": 0, "policy": policy_snapshot(self.root),
                 "last_execute_fingerprint": None, "stagnant_iterations": 0, "evidence": [],
                 "stop_reason": None, "scientific_gate": "not_evaluated", "launch_authorized": False}
        self.save(directory, state, [], "start", {"goal": goal})
        return self.next(loop_id)

    def guard(self, state: dict) -> str | None:
        if time.time() >= state["deadline"]:
            return "time_budget_exhausted"
        if policy_snapshot(self.root) != state["policy"]:
            return "methodology_changed"
        return None

    def stop_if_needed(self, directory: Path, state: dict, events: list[dict]) -> dict:
        reason = self.guard(state) if state["status"] == "active" else None
        if reason:
            state.update(status="stopped", stop_reason=reason)
            self.save(directory, state, events, "stop", {"reason": reason})
        return state

    def next(self, loop_id: str) -> dict:
        with self.locked(loop_id) as directory:
            state, events = self.load(directory)
            state = self.stop_if_needed(directory, state, events)
            instructions = {
                "plan": "Write the plan and acceptance criteria to a new artifact inside this loop directory. Consult the actual methodology. Record plan with complete and its evidence path.",
                "execute": "Perform the planned local work; save outputs and evidence. For audit/review kinds, write only loop artifacts. Record execute with complete and evidence paths. If any operation needs new authority, record blocked.",
                "review": "Inspect outputs and run the planned meaningful checks. Save actual check output and a review artifact. Record review as pass only when acceptance criteria hold, iterate with specific findings, or blocked. Local pass is not a research arbiter PASS.",
            }
            return {**state, "artifact_directory": str(directory.relative_to(self.root)),
                    "next_instruction": instructions[state["stage"]] if state["status"] == "active" else "Stop and report the recorded status.",
                    "execution_model": "cooperative; no agent or command is started by these tools",
                    "restrictions": ["No training launches or automatic kill/relaunch/resume", "No background monitoring",
                                     "No changes to active or frozen campaign inputs", "No external publishing",
                                     "Honor mandatory reviewers and scientific/human gates"]}

    def record(self, loop_id: str, stage: str, outcome: str, summary: str,
               evidence_paths: list[str], expected_event_sha256: str | None = None) -> dict:
        reject_secrets({"summary": summary, "evidence_paths": evidence_paths})
        if not summary.strip() or len(summary) > 4000 or len(evidence_paths) > 20 or len(set(evidence_paths)) != len(evidence_paths):
            raise LabError("Provide a bounded factual summary and evidence paths")
        with self.locked(loop_id) as directory:
            state, events = self.load(directory)
            if expected_event_sha256 and expected_event_sha256 != events[-1]["sha256"]:
                raise LabError("Loop changed since inspection; refresh before recording")
            reason = self.guard(state)
            if state["status"] != "active" or reason:
                self.stop_if_needed(directory, state, events)
                raise LabError("Loop is stopped or its time/methodology bound changed")
            if stage != state["stage"]:
                raise LabError("Stage does not match the current loop state")
            allowed = {"pass", "iterate", "blocked"} if stage == "review" else {"complete", "blocked"}
            if outcome not in allowed:
                raise LabError("Outcome is invalid for this stage")
            evidence = []
            for path in evidence_paths:
                text = read_text(path, self.root)
                evidence.append({"path": str(local_path(path, self.root).relative_to(self.root)), "sha256": digest(text)})
            if outcome != "blocked" and not evidence:
                raise LabError("A completed step needs durable evidence")
            if stage == "review" and outcome == "pass":
                if len({item["path"] for item in evidence}) < 2:
                    raise LabError("Pass needs both a review artifact and check-output evidence")
                # Earlier evidence must still identify the exact content that was reviewed.
                for item in state["evidence"]:
                    if digest(read_text(item["path"], self.root)) != item["sha256"]:
                        raise LabError("Earlier evidence changed; record iterate and re-review")
            if stage == "execute":
                fingerprint = digest(evidence)
                state["stagnant_iterations"] = state["stagnant_iterations"]+1 if fingerprint == state["last_execute_fingerprint"] else 0
                state["last_execute_fingerprint"] = fingerprint
            state["evidence"].extend(evidence)
            if outcome == "blocked":
                state.update(status="blocked", stop_reason=summary)
            elif stage in STAGES:
                state["stage"] = STAGES[stage]
            elif outcome == "pass":
                state.update(status="complete", stop_reason="local_acceptance_reported")
            elif state["iteration"] >= state["max_iterations"] or state["stagnant_iterations"] >= 1:
                state.update(status="stopped", stop_reason="iteration_budget_exhausted" if state["iteration"] >= state["max_iterations"] else "no_progress")
            else:
                state.update(iteration=state["iteration"]+1, stage="plan", evidence=[])
            self.save(directory, state, events, "record", {"stage": stage, "outcome": outcome, "summary": summary, "evidence": evidence})
        return self.next(loop_id)

    def reserve_call(self, loop_id: str) -> str:
        with self.locked(loop_id) as directory:
            state, events = self.load(directory)
            reason = self.guard(state)
            if state["status"] != "active" or reason:
                self.stop_if_needed(directory, state, events)
                raise LabError("Loop cannot spend another Jev call")
            if state["jev_calls"] >= state["max_jev_calls"]:
                state.update(status="stopped", stop_reason="jev_call_budget_exhausted")
                self.save(directory, state, events, "stop", {"reason": state["stop_reason"]})
                raise LabError("Jev call budget exhausted")
            state["jev_calls"] += 1
            self.save(directory, state, events, "reserve_jev_call", {"attempt": state["jev_calls"]})
            return f"{loop_id}:{state['jev_calls']}"

    def status(self, loop_id: str) -> dict:
        with self.locked(loop_id) as directory:
            state, events = self.load(directory)
            return {**state, "event_count": len(events), "last_event_sha256": events[-1]["sha256"],
                    "deadline_exceeded": time.time() >= state["deadline"],
                    "methodology_unchanged": policy_snapshot(self.root) == state["policy"]}
