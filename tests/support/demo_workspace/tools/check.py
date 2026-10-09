"""Repair test: the config must give a positive batch size and a dry run must succeed."""
import json
import subprocess
import sys
from pathlib import Path

ws = Path(__file__).resolve().parents[1]
cfg = json.loads((ws / 'code/config.json').read_text())
if not isinstance(cfg.get('batch_size'), int) or cfg['batch_size'] <= 0:
    sys.exit('batch_size must be a positive integer')
sys.exit(subprocess.run([sys.executable, str(ws / 'code/run.py'), '--dry-run']).returncode)
