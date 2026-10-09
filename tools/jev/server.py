from __future__ import annotations

from typing import Any
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings
from .service import Service

# In MCP 1.26, Settings references FastMCP before that class is defined.
# Resolve it after import so recent Pydantic settings can inspect the field.
Settings.model_rebuild()
server = FastMCP("BNJetTag Jev Lab", instructions="Jev judgments are advisory. Lab loops are cooperative local workflows, not cluster launchers. Use existing methodology and action-time authorization.", log_level="WARNING")
service = Service()


@server.tool()
def jev_doctor(live: bool = False) -> dict[str, Any]:
    """Check key availability without exposing it; live=True makes one synthetic API call."""
    return service.doctor(live)


@server.tool()
def jev_triage_logs(items: list[dict], loop_id: str | None = None) -> dict[str, Any]:
    """Classify supplied failure excerpts. Items need id and text, or path with optional start_line/end_line. No automatic retry."""
    return service.triage_logs(items, loop_id)


@server.tool()
def jev_rank_snippets(query: str, items: list[dict], loop_id: str | None = None) -> dict[str, Any]:
    """Rank explicit search candidates by relevance. Items need id and text or a lab source path. No repository crawling."""
    return service.rank_snippets(query, items, loop_id)


@server.tool()
def jev_triage_review(items: list[dict], loop_id: str | None = None) -> dict[str, Any]:
    """Classify findings with supporting text; severity A remains mandatory review regardless of Jev's answer."""
    return service.triage_review(items, loop_id)


@server.tool()
def jev_screen_papers(items: list[dict], loop_id: str | None = None) -> dict[str, Any]:
    """Score supplied abstracts independently for binary networks, FPGA deployment, and jet tagging. IDs plus text/path required."""
    return service.screen_papers(items, loop_id)


@server.tool()
def jev_check_claims(items: list[dict], loop_id: str | None = None) -> dict[str, Any]:
    """Check wording against an exact passage: id, claim, and source as text/path. Arithmetic stays in code."""
    return service.check_claims(items, loop_id)


@server.tool()
def jev_route_task(task: str, loop_id: str | None = None) -> dict[str, Any]:
    """Recommend an existing lab workflow owner. Does not spawn agents or change model requirements."""
    return service.route_task(task, loop_id)


@server.tool()
def jev_check_methods(candidate: str, loop_id: str | None = None) -> dict[str, Any]:
    """Audit proposed training method text against actual lab conventions. Advisory only; missing details remain missing."""
    return service.check_methods(candidate, loop_id)


@server.tool()
def lab_check_protocol(path: str, baseline_path: str | None = None) -> dict[str, Any]:
    """Locally validate a structured training protocol and compare with an optional content-addressed snapshot. No API call."""
    return service.call("lab_check_protocol", {"path": path, "baseline_path": baseline_path})


@server.tool()
def lab_freeze_protocol(path: str) -> dict[str, Any]:
    """Snapshot a structurally valid declared method and methodology hashes. Does not freeze training code or approve a run."""
    return service.call("lab_freeze_protocol", {"path": path})


@server.tool()
def lab_loop_start(goal: str, kind: str = "local_engineering", max_iterations: int = 3, max_seconds: int = 1800, max_jev_calls: int = 20) -> dict[str, Any]:
    """Start a bounded cooperative local loop: plan, execute, review. Kinds: local_engineering, methods_audit, literature_review, evidence_review."""
    return service.call("lab_loop_start", dict(goal=goal, kind=kind, max_iterations=max_iterations, max_seconds=max_seconds, max_jev_calls=max_jev_calls))


@server.tool()
def lab_loop_next(loop_id: str) -> dict[str, Any]:
    """Get the next local-loop directive; stops on expired budgets or changed methodology. Does not execute anything."""
    return service.call("lab_loop_next", {"loop_id": loop_id})


@server.tool()
def lab_loop_record(loop_id: str, stage: str, outcome: str, summary: str, evidence_paths: list[str], expected_event_sha256: str | None = None) -> dict[str, Any]:
    """Record durable evidence. plan/execute accept complete or blocked; review accepts pass, iterate, blocked. Pass requires review and check output."""
    return service.call("lab_loop_record", dict(loop_id=loop_id, stage=stage, outcome=outcome, summary=summary, evidence_paths=evidence_paths, expected_event_sha256=expected_event_sha256))


@server.tool()
def lab_loop_status(loop_id: str) -> dict[str, Any]:
    """Read and validate the loop event chain, budget counters, policy hashes, and state."""
    return service.call("lab_loop_status", {"loop_id": loop_id})


def main():
    server.run(transport="stdio")
