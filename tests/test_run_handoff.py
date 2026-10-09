import argparse
import base64
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('run_handoff', ROOT / 'tools/run_handoff.py')
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)


def archive(entries, link=None):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as tar:
        for name, data in entries:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
        if link:
            member = tarfile.TarInfo(link)
            member.type = tarfile.SYMTYPE
            member.linkname = '/etc/passwd'
            tar.addfile(member)
    return out.getvalue()


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        payload = archive([('code/run.py', b'print("fixture")\n'),
                           ('code/config.json', b'{"seed":1,"epochs":500}\n')])
        self.source = {'apiVersion':'v1', 'kind':'ConfigMap', 'immutable':True,
            'metadata':{'name':'kai-code-fixture', 'namespace':'cms-ml',
                        'annotations':{rh.PREFIX+'bundle-sha256':rh.sha(payload)}},
            'binaryData':{'hgq2.tar.gz':base64.b64encode(payload).decode()}}
        self.job = {'apiVersion':'batch/v1', 'kind':'Job',
            'metadata':{'name':'kai-fixture', 'namespace':'cms-ml', 'labels':{'user':'kai','campaign':'fixture'}},
            'spec':{'template':{'metadata':{'labels':{'user':'kai'}}, 'spec':{
                'automountServiceAccountToken':False, 'restartPolicy':'Never',
                'containers':[{'name':'train','image':'python:3.12','command':['python','run.py'],
                    'resources':{'requests':{'cpu':'1'}},
                    'env':[{'name':'WANDB_API_KEY','valueFrom':{'secretKeyRef':{'name':'kai-wandb','key':'WANDB_API_KEY'}}}],
                    'volumeMounts':[{'name':'persistent','mountPath':'/data'},
                                    {'name':'code','mountPath':'/cmcode','readOnly':True}]}],
                'volumes':[{'name':'persistent','persistentVolumeClaim':{'claimName':'kai-data'}},
                           {'name':'code','configMap':{'name':'kai-code-fixture'}}]}}}}
        self.brief = {'purpose':'Fixture test only','changes':'Uncommitted fixture contents',
            'approval_ref':'TEST ONLY','scientific_gate':{'status':'pending','reference':'K1 pending'},
            'runs':[{'name':'fixture-s1','config_path':'code/config.json'}],
            'expected_metrics':[{'name':'loss','split':'validation','expectation':'finite'}],
            'stop_rules':[{'condition':'nonfinite loss','action':'notify-only','approval_ref':'TEST ONLY'}],
            'outputs':['/data/fixture/runs/fixture-s1']}
        self.info = b'{"array_sha256":{"x_train":"' + b'a'*64 + b'"},"split_seed":1}\n'
        self.data_path = '/data/fixture/data/data_info.json'

    def tearDown(self):
        self.temp.cleanup()

    def record(self):
        return rh.build_record(self.job,self.source,self.brief,self.info,self.data_path)

    def prepare(self):
        for name, value in [('job',self.job),('source',self.source),('brief',self.brief)]:
            (self.root/(name+'.json')).write_bytes(rh.encoded(value))
        (self.root/'info.json').write_bytes(self.info)
        args=argparse.Namespace(job=self.root/'job.json',configmap=self.root/'source.json',
            brief=self.root/'brief.json',data_info=self.root/'info.json',data_path=self.data_path,out=self.root/'records')
        with contextlib.redirect_stdout(io.StringIO()):
            return rh.prepare(args)

    def test_prepare_repeat_same_bytes_and_id(self):
        first=self.prepare(); before=(first/'record.json').read_bytes()
        self.assertEqual(first,self.prepare())
        self.assertEqual(before,(first/'record.json').read_bytes())
        rh.validate_dir(first)

    def test_working_payload_change_changes_run_id(self):
        old=rh.identity(self.record())
        payload=archive([('code/run.py',b'print("uncommitted edit")\n'),('code/config.json',b'{"seed":1}\n')])
        self.source['binaryData']['hgq2.tar.gz']=base64.b64encode(payload).decode()
        self.source['metadata']['annotations'][rh.PREFIX+'bundle-sha256']=rh.sha(payload)
        self.assertNotEqual(old,rh.identity(self.record()))

    def test_required_fields_fail_closed(self):
        for key in ('purpose','changes','approval_ref','runs','outputs','expected_metrics','stop_rules','scientific_gate'):
            with self.subTest(key=key):
                saved=self.brief.pop(key)
                with self.assertRaises((ValueError,KeyError)): self.record()
                self.brief[key]=saved

    def test_bad_config_and_data_identity(self):
        self.brief['runs'][0]['config_path']='code/missing.json'
        with self.assertRaises(ValueError): self.record()
        self.brief['runs'][0]['config_path']='code/config.json'
        self.info=b'{"array_sha256":{}}'
        with self.assertRaises(ValueError): self.record()

    def test_unsafe_paths_links_duplicates_and_secrets(self):
        for name in ('../escape.py','/code/a.py','code/../../a.py','code/.env','code/.ssh/id_rsa',
                     'code/credentials.json','code/key.pem','code/a\\b.py','code/C:/a.py'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                rh.payload_files(archive([(name,b'{}')]))
        with self.assertRaises(ValueError): rh.payload_files(archive([('code/a.py',b'x'),('code/a.py',b'y')]))
        with self.assertRaises(ValueError): rh.payload_files(archive([],link='code/link.py'))
        for data in (b'-----BEGIN PRIVATE KEY-----',b'API_KEY = "test-secret-value"',b'{"api_key":"do-not-copy"}'):
            with self.subTest(data=data),self.assertRaises(ValueError):
                rh.payload_files(archive([('code/config.json',data)]))

    def test_inline_env_credential_rejected_reference_allowed(self):
        self.record()
        self.job['spec']['template']['spec']['containers'][0]['env'][0]={'name':'WANDB_API_KEY','value':'forbidden'}
        with self.assertRaises(ValueError): self.record()

    def test_tampered_payload_record_and_job(self):
        self.source['metadata']['annotations'][rh.PREFIX+'bundle-sha256']='b'*64
        with self.assertRaises(ValueError): self.record()
        self.source['metadata']['annotations'][rh.PREFIX+'bundle-sha256']=rh.sha(base64.b64decode(self.source['binaryData']['hgq2.tar.gz']))
        path=self.prepare()
        job=rh.read_json(path/'job.json');job['spec']['template']['spec']['containers'][0]['command']=['wrong']
        (path/'job.json').write_bytes(rh.encoded(job))
        with self.assertRaises(ValueError):rh.validate_dir(path)
        record=self.record();record['files']['code/run.py']='f'*64
        with self.assertRaises(ValueError):rh.validate_record(record)

    def test_dry_run_never_calls_process_and_missing_record_blocks(self):
        path=self.prepare()
        args=argparse.Namespace(directory=path,submit=False)
        with patch.object(rh.subprocess,'run',side_effect=AssertionError('no subprocess allowed')):
            with contextlib.redirect_stdout(io.StringIO()):rh.launch(args)
            args.directory=self.root/'missing'
            with self.assertRaises(OSError):rh.launch(args)

    def test_pending_gate_and_mismatched_approval_block_before_process(self):
        path=self.prepare()
        args=argparse.Namespace(directory=path,submit=True,approval_ref='TEST ONLY',kubectl='never')
        with patch.object(rh.subprocess,'run',side_effect=AssertionError('must not call')):
            with self.assertRaises(ValueError):rh.launch(args)
        self.brief['scientific_gate']['status']='cleared';path=self.prepare();args.directory=path;args.approval_ref='wrong'
        with patch.object(rh.subprocess,'run',side_effect=AssertionError('must not call')):
            with self.assertRaises(ValueError):rh.launch(args)

    def test_job_stamping_preserves_original_training_spec(self):
        record=self.record();job,cm=rh.manifests(record)
        self.assertEqual(self.job['spec']['template']['spec']['containers'],job['spec']['template']['spec']['containers'])
        self.assertTrue(cm['immutable'])
        self.assertFalse(job['spec']['template']['spec']['automountServiceAccountToken'])
        self.assertEqual(job['metadata']['annotations'][rh.PREFIX+'handoff-sha256'],rh.sha(rh.encoded(record)))

    def test_install_repeat_conflict_and_data_mismatch(self):
        record=self.record();path=self.root/'record.json';path.write_bytes(rh.encoded(record))
        args=argparse.Namespace(record=path,root=self.root/'pvc')
        original=Path.read_bytes
        def fake_read(p):return self.info if str(p)==self.data_path else original(p)
        with patch.object(Path,'read_bytes',fake_read),contextlib.redirect_stdout(io.StringIO()):
            rh.install(args);rh.install(args)
            installed=args.root/rh.identity(record)
            (installed/'source.tar.gz').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):rh.install(args)
        def wrong_read(p):return b'wrong' if str(p)==self.data_path else original(p)
        with patch.object(Path,'read_bytes',wrong_read),self.assertRaises(ValueError):rh.install(args)

    def test_submit_idempotence_with_fake_cluster_only(self):
        self.brief['scientific_gate']['status']='cleared';path=self.prepare()
        args=argparse.Namespace(directory=path,submit=True,approval_ref='TEST ONLY',kubectl='fake-kubectl')
        cluster={};creates=[]
        def fake_run(argv,**kwargs):
            if 'lint' in argv:return subprocess.CompletedProcess(argv,0)
            if 'get' in argv:
                n=argv.index('get');value=cluster.get((argv[n+1],argv[n+2]))
                return subprocess.CompletedProcess(argv,0,json.dumps(value) if value else '', '')
            if 'create' in argv:
                obj=rh.read_json(argv[-1]);key=(obj['kind'],obj['metadata']['name']);cluster[key]=obj;creates.append(key)
                return subprocess.CompletedProcess(argv,0)
            self.fail('unexpected process')
        original=Path.is_file
        def has_doctor(p):return True if str(p).endswith('nrp-lab/nrp_doctor.py') else original(p)
        with patch.object(Path,'is_file',has_doctor),patch.object(rh.subprocess,'run',side_effect=fake_run):
            rh.launch(args);rh.launch(args)
        self.assertEqual(len(creates),3)
        self.assertEqual(len(list((path/'events').glob('*.json'))),3)
        self.assertEqual(rh.read_json(path/'status.json')['status'],'submitted-or-already-present')
        # TTL removal: even with the same run ID and matching surviving ConfigMaps, no replay.
        del cluster[('Job','kai-fixture')]
        with patch.object(Path,'is_file',has_doctor),patch.object(rh.subprocess,'run',side_effect=fake_run):
            with self.assertRaises(ValueError):rh.launch(args)
        self.assertEqual(len(creates),3)
        # A fresh consumer directory without local events is still blocked by the remote marker.
        fresh=self.root/'fresh'/path.name;fresh.mkdir(parents=True)
        for name in ('record.json','job.json','handoff-configmap.json','source-configmap.json'):
            (fresh/name).write_bytes((path/name).read_bytes())
        args.directory=fresh
        with patch.object(Path,'is_file',has_doctor),patch.object(rh.subprocess,'run',side_effect=fake_run):
            with self.assertRaises(ValueError):rh.launch(args)
        self.assertEqual(len(creates),3)
        args.directory=path
        # Removal of remote marker must still not bypass the durable local intent.
        del cluster[('ConfigMap','kai-'+path.name)]
        with patch.object(Path,'is_file',has_doctor),patch.object(rh.subprocess,'run',side_effect=fake_run):
            with self.assertRaises(ValueError):rh.launch(args)
        self.assertEqual(len(creates),3)

    def test_data_subpath_and_overlapping_mounts_rejected(self):
        mounts=self.job['spec']['template']['spec']['containers'][0]['volumeMounts']
        for key in ('subPath','subPathExpr'):
            mounts[0][key]='different-dataset-root'
            with self.assertRaises(ValueError):self.record()
            del mounts[0][key]
        for path in ('/data/other','/','/cmcode/override'):
            mounts.append({'name':'other','mountPath':path})
            with self.assertRaises(ValueError):self.record()
            mounts.pop()

    def test_code_volume_without_actual_mount_rejected(self):
        mounts=self.job['spec']['template']['spec']['containers'][0]['volumeMounts']
        code=mounts.pop()
        with self.assertRaises(ValueError):self.record()
        mounts.append(code);code['subPath']='hgq2.tar.gz'
        with self.assertRaises(ValueError):self.record()
        del code['subPath'];code['mountPath']='/wrong'
        with self.assertRaises(ValueError):self.record()

    def test_hook_blocks_direct_jobs_and_stdin(self):
        path=self.prepare()
        hook=ROOT/'.claude/hooks/pre-kubectl-lint.py'
        for command in ('kubectl create -f '+str(path/'job.json'),'kubectl apply -f -'):
            event={'tool_name':'Bash','cwd':str(ROOT),'tool_input':{'command':command}}
            result=subprocess.run([sys.executable,str(hook)],input=json.dumps(event),text=True,capture_output=True)
            self.assertEqual(result.returncode,2,result.stderr)

    def test_lint_failure_cannot_submit(self):
        self.brief['scientific_gate']['status']='cleared';path=self.prepare()
        args=argparse.Namespace(directory=path,submit=True,approval_ref='TEST ONLY',kubectl='never')
        with patch.object(Path,'is_file',return_value=True),patch.object(rh.subprocess,'run',return_value=subprocess.CompletedProcess([],2)) as runner:
            with self.assertRaises(ValueError):rh.launch(args)
            self.assertEqual(runner.call_count,1)
            self.assertIn('lint',runner.call_args.args[0])

    def test_conflicting_cluster_object_never_created_or_replaced(self):
        self.brief['scientific_gate']['status']='cleared';path=self.prepare()
        args=argparse.Namespace(directory=path,submit=True,approval_ref='TEST ONLY',kubectl='never')
        calls=[]
        def run(argv,**kwargs):
            calls.append(argv)
            if 'lint' in argv:return subprocess.CompletedProcess(argv,0)
            self.assertIn('get',argv)
            return subprocess.CompletedProcess(argv,0,'{"kind":"ConfigMap","immutable":false}','')
        with patch.object(Path,'is_file',return_value=True),patch.object(rh.subprocess,'run',side_effect=run):
            with self.assertRaises(ValueError):rh.launch(args)
        self.assertFalse(any('create' in call or 'apply' in call for call in calls))
        self.assertFalse((path/'.submit.lock').exists())

    def test_consumer_rejects_wrong_job_annotation(self):
        path=self.prepare()
        argv=['run_handoff.py','inspect',str(path),'--expected-sha','0'*64,'--run-id',path.name]
        with patch.object(sys,'argv',argv),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(rh.main(),2)


if __name__=='__main__':unittest.main()
