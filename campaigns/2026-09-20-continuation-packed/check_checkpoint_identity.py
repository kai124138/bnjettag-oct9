import json, pathlib, hashlib, tarfile, time
P=pathlib.Path
records=[]
for label,campaign in [('arch','batch20260917'),('attn','batch20260918'),('engram','engram')]:
    bundle=P('/bundles')/label/'hgq2.tar.gz'
    digest=hashlib.sha256(bundle.read_bytes()).hexdigest()
    target=P('/work')/label; target.mkdir(parents=True,exist_ok=True)
    with tarfile.open(bundle) as t: t.extractall(target,filter='data')
    code=target/'hgq2'
    for cfgp in sorted((code/'configs'/campaign).glob('*.json')):
        cfg=json.loads(cfgp.read_text())
        if 'experiment' not in cfg: continue
        arm=cfg['experiment']['arm']
        if label=='engram' and arm not in [f'engram-e{i:02d}-s1' for i in range(4)]: continue
        root=P('/data/engram-study-20260918') if label=='engram' else P('/data/batch20260917')/('n'+str(cfg['arch']['n_part']))
        run=root/'runs'/arm
        latest=json.loads((run/'latest.json').read_text())
        state=json.loads((run/'checkpoints'/latest['checkpoint']/'state.json').read_text())
        cfgsha=hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
        assert cfg['train']['epochs']==1000,(arm,'configured schedule')
        assert state['config_sha256']==cfgsha,(arm,'config mismatch')
        if label=='engram':
            manifest=json.loads((run/'source_manifest.json').read_text())
            assert state['code_sha256']==manifest['sha256'],(arm,'engram source mismatch')
            for name,sha in manifest['files'].items(): assert hashlib.sha256((code/name).read_bytes()).hexdigest()==sha,(arm,name)
        else: assert state['code_sha256']==digest,(arm,'code mismatch')
        assert not (run/'COMPLETE.json').exists(),(arm,'COMPLETE exists')
        row=dict(label=label,arm=arm,run=str(run),bundle_sha256=digest,latest=latest,state=state,config_sha256=cfgsha,files=[p.name for p in run.iterdir()])
        if label=='engram': row['source_manifest']=manifest
        records.append(row)
assert len(records)==31,len(records)
P('/work/pvc-state.json').write_text(json.dumps(records,indent=2))
print('PREFLIGHT_ALL_PASS '+json.dumps([{'arm':r['arm'],'epoch':r['state']['completed_epochs']} for r in records]),flush=True)
time.sleep(3600)
