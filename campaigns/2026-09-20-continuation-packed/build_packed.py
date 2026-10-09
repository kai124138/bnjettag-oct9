"""Repack the 2026-09-20 continuation: several arms share one GPU pod.

Why: one arm is kernel-launch-bound (~19k params) and holds a GPU at ~30%, under the
NRP 40% floor. Only the Job shape changes; ConfigMap, code sha, configs, PVC run
directories and the per-arm command line are those of build_continuations.py.
Packs group arms with similar remaining epochs so a pod's arms finish together.
"""
import json,copy
from pathlib import Path
out=Path('local/continuation-20260920')
# label -> (job suffix, packs of arm indexes); ordered by completed epochs at 2026-09-21T01:50Z
packs={'arch':[[3,4,7],[9,0,1],[5,2,6],[10,8,11]],
       'attn':[[6,5,0],[1,3,2],[4,14,8],[11,7,10],[9,12,13]],
       'engram':[[2,1,3,0]]}
runner='''pids=()
trap 'kill -TERM "${pids[@]}" 2>/dev/null || true' TERM INT
for a in ${PACKS[$JOB_COMPLETION_INDEX]}; do
  ARMCMD > >(sed -u "s/^/[arm$a] /") 2>&1 &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
wait
exit $rc
'''
for label,groups in packs.items():
 j=json.loads((out/(label+'-job.json')).read_text());name=j['metadata']['name']+'-p'+str(max(map(len,groups)))
 n=j['spec']['completions'];assert sorted(sum(groups,[]))==list(range(n)),label
 j['metadata']['name']=name
 for obj in (j['metadata'],j['spec']['template']['metadata']):obj['labels']['continuation']='full1000-20260920-packed'
 s=j['spec'];s['completions']=s['parallelism']=len(groups)
 c=s['template']['spec']['containers'][0];k=max(map(len,groups))
 for kind in ('requests','limits'):c['resources'][kind].update({'cpu':str(2*k),'memory':f'{6*k}Gi'})
 command=c['args'][0]
 cut='ARM=$(' if label=='engram' else 'timeout --signal'
 head,tail=command[:command.index(cut)],command[command.index(cut):]
 armcmd=tail.strip().splitlines()[-1]
 if label=='engram':
  assert tail.count('$ARM')==2
  head+='arm_name() { printf "engram-e%02d-s1" "$1"; }\n'
  armcmd=armcmd.replace('$ARM','$(arm_name $a)')
 else:
  # helper is unchanged except that the arm index arrives as argv[1]
  assert head.count("i=int(os.environ['JOB_COMPLETION_INDEX'])")==1
  head=head.replace("i=int(os.environ['JOB_COMPLETION_INDEX'])","i=int(sys.argv[1])")
  armcmd+=' $a'
 assert armcmd.startswith('timeout --signal=TERM')
 head+='PACKS=('+' '.join('"'+' '.join(map(str,g))+'"' for g in groups)+')\n'
 c['args']=[head+runner.replace('ARMCMD',armcmd)]
 (out/(label+'-packed-job.json')).write_text(json.dumps(j,indent=2)+'\n')
 print(name,len(groups),'pods',c['resources']['requests'],'|',armcmd)
