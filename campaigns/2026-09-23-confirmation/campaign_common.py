"""Shared immutable inputs for the active full-run confirmation campaign."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
SOURCE = LAB / "publication-engram-20260921/code/constituent-study-20260922"
BASE_JOB = json.loads((LAB / "local/constituent-study-20260922/screen-job.json").read_text())
CODE_CONFIGMAP = "kai-n8n64-code-26f3cc40a8"
CODE_SHA256 = "26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45"
