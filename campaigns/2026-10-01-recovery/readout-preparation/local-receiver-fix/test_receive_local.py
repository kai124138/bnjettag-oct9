import copy,importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('local_readout_receiver',HERE/'receive_local.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CAP=ROOT/'campaigns/2026-10-01-recovery/captures/readout-run-20261001T0625Z'
HANDOFF=HERE.parent/'handoffs/rh-b6ae7a233d366d7b15d5120e'
class Guards(unittest.TestCase):
 def setUp(self):
  self.job=json.loads((CAP/'observation-02/job.json').read_bytes());self.pod=json.loads((CAP/'observation-02/pod.json').read_bytes());self.source=json.loads((CAP/'observation-01/source-configmap.json').read_bytes());self.handoff=json.loads((CAP/'observation-01/handoff-configmap.json').read_bytes())
 def validate(self,job=None,pod=None):return m.validate_objects(HANDOFF,job or self.job,pod or self.pod,self.source,self.handoff,self.job['metadata']['uid'],self.pod['metadata']['uid'])
 def test_actual_capture(self):
  before=copy.deepcopy(self.pod);identity=self.validate();self.assertEqual(identity['job_name'],'kai-chang1001-readoutb5-42abed-r1');self.assertEqual(before,self.pod);self.assertEqual(m.VALIDATION[0]['actual_init_resources']['limits']['ephemeral-storage'],'50Gi')
 def test_wrong_values_or_extra_fields(self):
  for kind,key,value in [('limits','ephemeral-storage','51Gi'),('requests','ephemeral-storage','1'),('limits','cpu','2'),('limits','nvidia.com/gpu','1')]:
   pod=copy.deepcopy(self.pod);pod['spec']['initContainers'][0]['resources'][kind][key]=value
   with self.assertRaises(ValueError):self.validate(pod=pod)
 def test_job_main_and_other_init_still_strict(self):
  job=copy.deepcopy(self.job);job['spec']['template']['spec']['initContainers'][0]['resources']['limits']['ephemeral-storage']='50Gi'
  with self.assertRaises(ValueError):self.validate(job=job)
  pod=copy.deepcopy(self.pod);pod['spec']['containers'][0]['resources']['limits']['ephemeral-storage']='50Gi'
  with self.assertRaises(ValueError):self.validate(pod=pod)
  pod=copy.deepcopy(self.pod);pod['spec']['initContainers'][0]['args']=['unreviewed']
  with self.assertRaises(ValueError):self.validate(pod=pod)
if __name__=='__main__':unittest.main()
