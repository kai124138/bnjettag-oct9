from __future__ import annotations

import json
import math
import os
import time
import uuid
from pathlib import Path

from .common import ROOT, MAX_BYTES, LabError, canonical, credential, digest, reject_secrets, utc_now, write_json

CATALOG = json.loads((Path(__file__).with_name("catalog.json")).read_text())


def validate_answers(questions: dict, response: dict) -> dict:
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise LabError("Jev returned an incomplete or unexpected answer set")
    def number(value: object, low: float, high: float) -> bool:
        return type(value) in (int, float) and math.isfinite(value) and low <= value <= high
    for qid, question in questions.items():
        answer = answers[qid]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise LabError("Jev answer type does not match its question")
        kind = question["type"]
        if kind == "noul":
            if not number(answer.get("noul"), 0, 1):
                raise LabError("Invalid yes/no probability")
            continue
        criteria = question["criteria"]
        labels = set(criteria) if kind == "choice" else {str(i) for i in range(len(criteria))}
        probabilities = answer.get("probabilities")
        if (not isinstance(probabilities, dict) or set(probabilities) != labels
                or any(not number(v, 0, 1) for v in probabilities.values())
                or abs(sum(probabilities.values()) - 1) > 0.005
                or not number(answer.get("confidence"), 0, 1)):
            raise LabError("Invalid decision probabilities or confidence")
        if kind == "choice":
            if answer.get("choice") not in labels or probabilities[answer["choice"]] < max(probabilities.values()):
                raise LabError("Invalid selected option")
        elif not number(answer.get("score"), 0, len(criteria)-1):
            raise LabError("Invalid rubric score")
    return answers


class Engine:
    def __init__(self, root: Path = ROOT, transport=None):
        self.root = root
        self.transport = transport

    def ask(self, state: object, questions: dict, loop_id: str | None = None) -> dict:
        reject_secrets({"state": state, "questions": questions})
        if not questions or len(questions) > 60 or len(canonical({"state": state, "questions": questions})) > MAX_BYTES:
            raise LabError("Request exceeds the bounded question or excerpt limit")
        reservation = None
        if loop_id:
            from .loops import LoopStore
            reservation = LoopStore(self.root).reserve_call(loop_id)
        started = time.monotonic()
        model = os.environ.get("JEV_MODEL", "jev-latest")
        try:
            if self.transport:
                response = self.transport(state, questions)
            else:
                key, _ = credential()
                if not key:
                    raise LabError("No TypeSafe key found in the environment or ~/.typesafe.env")
                from typesafe_sdk import TypeSafeClient, RetryPolicy
                with TypeSafeClient(api_key=key, model=model, base_url="https://api.typesafe.ai",
                                    timeout=20, retry=RetryPolicy(max_retries=0)) as client:
                    response = client.system_one(state=state, questions=questions).model_dump(mode="json")
            answers = validate_answers(questions, response)
        except LabError:
            raise
        except Exception as error:
            status = getattr(error, "status_code", None)
            raise LabError(f"Jev request failed ({type(error).__name__}, HTTP {status or 'unavailable'}); no automatic action") from None
        audit_id = "jv-" + uuid.uuid4().hex
        result = {
            "audit_id": audit_id, "model": response.get("model", model), "answers": answers,
            "usage": response.get("usage", {}), "latency_seconds": round(time.monotonic()-started, 3),
            "catalog_sha256": digest(CATALOG), "advisory_only": True,
        }
        reject_secrets(result)
        write_json(self.root / "local/jev-audit" / f"{audit_id}.json", {
            **result, "created_at": utc_now(), "request_sha256": digest({"state": state, "questions": questions}),
            "questions": questions, "loop_id": loop_id, "reservation": reservation,
            "raw_state_saved": False,
        })
        return result


def question(preset: str, kind: str = "choice", extra: str = "") -> dict:
    item = CATALOG[preset]
    return {"type": kind, "instructions": item["instructions"] + extra, "criteria": item["criteria"]}


def decision(answer: dict) -> str:
    threshold = CATALOG["thresholds"]
    if answer["type"] == "choice":
        probabilities = sorted(answer["probabilities"].values(), reverse=True)
        if answer["choice"] in {"unknown", "unclear", "insufficient_evidence", "missing"}:
            return "review"
        return "suggestion" if answer["confidence"] >= threshold["confidence"] and probabilities[0]-probabilities[1] >= threshold["margin"] else "review"
    return "suggestion" if answer.get("confidence", 0) >= threshold["confidence"] else "review"
