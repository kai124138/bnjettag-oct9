import concurrent.futures
import json
from pathlib import Path
import re
import subprocess

OUT=Path(__file__).resolve().parent
items=json.loads((OUT/'cluster.json').read_text())['items']
pods=[x for x in items if x['kind']=='Pod' and x['metadata']['name'].startswith((
 'kai-batch0917-screen-e100-r3-', 'kai-batch0918-', 'kai-ebops-abl-', 'kai-engram-screen-'))]
def fetch(p):
 name=p['metadata']['name']
 result=subprocess.run(['kubectl','logs','-n','cms-ml',name,'--tail=160','--timestamps=true','--request-timeout=20s'],capture_output=True,text=True,timeout=35)
 text=result.stdout+result.stderr
 (OUT/(name+'.log')).write_text(text)
 matches=[line for line in text.splitlines() if re.search(r'epoch \d+/|paused_for_promotion|AssertionError|allclose|SCREEN|completed_epochs|unable to retrieve',line)]
 return name,matches[-3:]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for name,lines in pool.map(fetch,pods): print(name,'\n'+'\n'.join(lines))
