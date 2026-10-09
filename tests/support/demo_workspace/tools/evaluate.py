"""Print the path of the metrics file the job wrote."""
import os
import sys
from pathlib import Path

p = Path(os.environ['LOCAL_KUBE_DIR']) / 'data' / 'outputs' / sys.argv[1] / 'metrics.json'
if not p.is_file():
    sys.exit(f'no metrics for {sys.argv[1]}')
print(p)
