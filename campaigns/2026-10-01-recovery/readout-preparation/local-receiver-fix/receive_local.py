#!/usr/bin/env python3
"""Local-only reader for exactly observed admission-added init ephemeral storage."""
import copy,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ORIGINAL=HERE.parent/'receive.py'
ORIGINAL_SHA256='29421107d2a9507e701d76561eed4620a65979fd8bb3bc34f83f424eb85ae1c5'
OBSERVED={'requests':{'cpu':'100m','memory':'128Mi','ephemeral-storage':'0'},'limits':{'cpu':'1','memory':'256Mi','ephemeral-storage':'50Gi'}}
VALIDATION=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def load_original():
 if sha(ORIGINAL.read_bytes())!=ORIGINAL_SHA256:raise ValueError('original reviewed receiver changed')
 spec=importlib.util.spec_from_file_location('reviewed_readout_receiver',ORIGINAL);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
original=load_original();original_validate=original.validate_objects;original_decode=original.decode
def validate_objects(directory,job,pod,source,handoff,job_uid,pod_uid):
 normalized=copy.deepcopy(pod);containers=normalized['spec'].get('initContainers',[])
 if len(containers)!=1 or containers[0].get('name')!='record-run-handoff' or containers[0].get('resources')!=OBSERVED:raise ValueError('init resources differ from exact observed admission defaults')
 for kind in ('requests','limits'):containers[0]['resources'][kind].pop('ephemeral-storage')
 # Original validator still rejects changes in Job template, main resources, every
 # other init field, volumes/mounts/commands/security/identity and immutable CMs.
 identity=original_validate(directory,job,normalized,source,handoff,job_uid,pod_uid)
 VALIDATION[:] = [{'scope':'Pod initContainer record-run-handoff only','actual_init_resources':OBSERVED,'normalized_fields':{'requests.ephemeral-storage':'0','limits.ephemeral-storage':'50Gi'},'effect':'Admission added a50Gi init ephemeral-storage limit; not requested and not claimed resource-neutral. Main remains12Gi.','original_pod_canonical_sha256':sha(original.encoded(pod)),'validation_pod_canonical_sha256':sha(original.encoded(normalized)),'original_receiver_sha256':ORIGINAL_SHA256,'local_wrapper_sha256':sha(Path(__file__).read_bytes())}]
 return identity
def decode(log,identity):
 files,receipt=original_decode(log,identity)
 if not VALIDATION:raise ValueError('object validation must precede decoding')
 receipt['local_admission_compatibility']=VALIDATION[0]
 return files,receipt
def main():
 original.validate_objects=validate_objects;original.decode=decode;original.main()
if __name__=='__main__':main()
