#!/usr/bin/env python3
"""Isolated engineering fixtures; no optimizer steps or scientific evaluation."""
import ast
import contextlib
import copy
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def ah(a):
    import numpy as np
    a = np.ascontiguousarray(a)
    return hashlib.sha256(str(a.dtype).encode() + str(a.shape).encode() + a.tobytes()).hexdigest()


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def normalize(obj):
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items() if k != "shared_object_id"}
    if isinstance(obj, (list, tuple)):
        return [normalize(v) for v in obj]
    return obj


def initialize():
    import tensorflow as tf
    import keras
    import hgq
    tf.config.experimental.enable_tensor_float_32_execution(False)
    assert not tf.config.list_physical_devices("GPU")
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.subln import register_subln
    apply_keras_compat()
    register_subln()
    from bnhgq2 import qat
    return keras, qat


def binary(model, cfg):
    import numpy as np
    from bnhgq2.qat import effective_weight_values
    if cfg["quant"]["weight"] != "binary_absmean":
        return {"status": "NOT_APPLICABLE", "reason": "nonbinary weights"}
    values = effective_weight_values(model)
    good = bool(values) and all(len(v) == 2 and v[0] != 0 and v[1] != 0
                                and np.isclose(v[0], -v[1], atol=0, rtol=0)
                                for v in values.values())
    return {"status": "PASS" if good else "FAIL", "layers": len(values)}


def probes(cfg):
    import numpy as np
    n, f = cfg["arch"]["n_part"], cfg["arch"]["n_feat"]
    rng = np.random.default_rng(20261001)
    x = rng.normal(0, 0.75, (24, n, f)).astype("float32")
    x[0] = 0; x[1] = 1; x[2] = -1
    x[3] = np.resize(np.array([-1, 1], dtype="float32"), (n, f))
    for i, occupancy in enumerate([1, max(1, n // 2), n], 4):
        x[i, occupancy:] = 0
    boundaries = np.array([-1, -0.5, -2**-8, 0, 2**-8, 0.5, 1], dtype="float32")
    for i, b in enumerate(boundaries, 7):
        x[i] = np.resize([np.nextafter(b, np.float32(-np.inf)), b,
                          np.nextafter(b, np.float32(np.inf))], (n, f))
    return x, {"seed": 20261001, "shape": list(x.shape), "dtype": str(x.dtype),
               "padding_occupancy": [1, max(1, n // 2), n],
               "boundaries": boundaries.tolist(), "raw_sha256": ah(x)}


def model_checks(task, source, out):
    import numpy as np
    keras, qat = initialize()
    from bnhgq2.config import load_config
    from bnhgq2.ebops_target import width_snapshot
    rows = []
    for item in task["items"]:
        keras.backend.clear_session()
        row = {"id": item["id"], "status": "PASS"}
        try:
            config_path=source/item['config_relative']
            assert digest(json.loads(config_path.read_text()))==item['config_sha256'],'config identity changed'
            cfg = load_config(config_path)
            if task['phase']=='reload':
                assert file_sha(item['checkpoint'])==item['checkpoint_sha256'],'checkpoint identity changed'
                assert file_sha(item['preprocessing'])==item['preprocessing_sha256'],'preprocessing identity changed'
            if task["phase"] == "build":
                model, _ = qat.build_qat_model(cfg, seed=1)
            else:
                model = keras.models.load_model(item["checkpoint"], compile=False)
            row.update(parameters=model.count_params(), input_shape=list(model.input_shape),
                       output_shape=list(model.output_shape),
                       graph_sha256=digest(normalize(model.get_config())),
                       binary=binary(model, cfg), width_state_sha256=digest(width_snapshot(model)))
            row["normalization"] = "Remove serialization shared_object_id only"
            if row["binary"]["status"] == "FAIL":
                row["status"] = "FAIL"
            if task["phase"] == "reload":
                x, probe = probes(cfg)
                if cfg["arch"].get("input_std"):
                    from bnhgq2.data import apply_input_std
                    std = json.loads(Path(item["preprocessing"]).read_text())
                    x = apply_input_std(x, std["mu"], std["sigma"])
                y = np.asarray(model(x, training=False))
                assert np.isfinite(y).all()
                arrays_dir = out.parent / (out.stem + "-arrays")
                arrays_dir.mkdir(exist_ok=True)
                output_path = arrays_dir / (item["id"] + ".npy")
                np.save(output_path, y, allow_pickle=False)
                row.update(probe=probe, processed_probe_sha256=ah(x), output_sha256=ah(y),
                           output_file=str(output_path), output_file_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
                           max_abs_output=float(np.max(np.abs(y))))
                # State evidence only; this does not trace or remeasure widths.
                row["remeasured_widths"] = {"status": "PENDING", "reason": "original calibration/selected-width reference not established"}
                assert file_sha(item['checkpoint'])==item['checkpoint_sha256'],'checkpoint changed during reload'
                assert file_sha(item['preprocessing'])==item['preprocessing_sha256'],'preprocessing changed during reload'
            assert digest(json.loads(config_path.read_text()))==item['config_sha256'],'config changed during execution'
            del model
        except Exception as exc:
            row.update(status="FAIL", error=f"{type(exc).__name__}: {exc}")
            traceback.print_exc()
        rows.append(row)
    return rows


def core_contracts(source,task):
    import numpy as np
    import builtins
    import bnhgq2.config as config
    import bnhgq2.wandb_util as tracking
    import bnhgq2.store as store
    import run_stage
    expected_root = str(source.parents[1])
    assert config.PROJECT_ROOT == expected_root
    assert store.STORE == str(Path(expected_root) / "results/hgq2")
    for mode in [None, "disabled", "offline"]:
        env = dict(os.environ); env.pop("WANDB_MODE", None)
        if mode is not None: env["WANDB_MODE"] = mode
        with patch.dict(os.environ, env, clear=True), patch.object(builtins, "open", side_effect=AssertionError("credential read")):
            assert not tracking.wandb_enabled()
    with patch.dict(os.environ, {"WANDB_MODE": "online", "WANDB_API_KEY": "synthetic-fixture-never-a-real-key"}):
        assert tracking.wandb_enabled()
    cfgpath = source / "configs/pre_conference-n8-w1a8.json"
    calls = []
    with patch.object(sys, "argv", ["run_stage", "train", "--config", str(cfgpath), "--out-dir", "/fixture/explicit", "--seed", "7"]), patch.object(run_stage, "stage_train", side_effect=lambda cfg,h,ctx,**kw: calls.append((ctx,kw))):
        run_stage.main()
    assert calls == [({"out_dir": "/fixture/explicit"}, {"seed": 7, "smoke": False})]
    calls = []
    with patch.object(sys, "argv", ["run_stage", "all", "--config", str(cfgpath), "--skip-convert"]), patch.dict(run_stage.STAGES, {k: (lambda *a,k=k,**kw: calls.append(k)) for k in run_stage.STAGES}):
        run_stage.main()
    assert calls == [x for x in run_stage.ORDER if x != "convert"]
    from bnhgq2 import train as trainer
    c = config.load_config(cfgpath)
    with patch.object(trainer, "train", side_effect=lambda *a,**kw: {"path":kw["out_dir"]}), patch.object(store, "write_stage"):
        result = run_stage.stage_train(c, config.cfg_hash(c), {}, seed=7)
        # The dispatcher stores the result in the context; validate the actual call too.
    calls = []
    with patch.object(trainer, "train", side_effect=lambda *a,**kw: calls.append(kw) or {}), patch.object(store, "write_stage"), patch.dict(os.environ, {"BNHGQ2_OUT_ROOT":"/fixture/env"}):
        run_stage.stage_train(c, config.cfg_hash(c), {}, seed=3)
    assert calls[0]["out_dir"] == "/fixture/env/w1a8-s3"
    import bnhgq2.convert as convert
    if task.get('is_candidate'):assert hasattr(convert,'pack_for_mulder')
    if hasattr(convert,"pack_for_mulder"):
        assert convert.pack_for_mulder is convert.package_hls_project
        assert list(inspect.signature(convert.pack_for_mulder).parameters) == ["out_dir","tar_path"]
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"project";d.mkdir();(d/"fixture.txt").write_text("fixture")
            target=str(Path(tmp)/"project.tar.gz")
            assert convert.pack_for_mulder(str(d),target) == target
    aliases={"convert_final":"convert_binary","roc_final":"evaluate_roc","fold_r14n8":"fold_binary_transformer","ebops_r14":"measure_pre_conference_ebops","uncertainty_r14":"estimate_auc_uncertainty","log_hls_wandb":"record_synthesis_metrics"}
    for old,new in aliases.items():
        if task.get('is_candidate'):assert (source/(old+'.py')).is_file(),old
        if (source/(old+".py")).exists():
            a,b=importlib.import_module(old),importlib.import_module(new)
            assert a.main is b.main
            for name,v in vars(b).items():
                if inspect.isfunction(v): assert getattr(a,name) is v
            if old=="convert_final":assert a.run_convert_final is b.run_convert_binary
    return {"public_cli":"PASS","paths":"PASS","tracking":"PASS","aliases":"PASS"}


def generators(source, task):
    result = {}
    for relative in task["generators"]:
        filename=source/relative
        with tempfile.TemporaryDirectory() as tmp:
            namespace={"__name__":"fixture_generator","__file__":str(Path(tmp)/filename.name)}
            # Execute definitions from captured/candidate bytes; the __main__ block is run
            # separately with output __file__/HERE redirected to a temporary directory.
            old_path=sys.path[:];sys.path.insert(0,str(filename.parent))
            for key in ["gen_r14","gen_ebops_n8","gen_ebops_ablation","generate_pre_conference"]:sys.modules.pop(key,None)
            try:
                with patch.object(sys,"argv",[str(filename)]):
                    namespace["__name__"]="__main__"
                    # gen_ptw reads HEADLINE beside __file__; provide only that fixture input.
                    headline=source/"configs/r14-l1x3-n8-w1a8.json"
                    if filename.name=="gen_ptw.py":(Path(tmp)/headline.name).write_bytes(headline.read_bytes())
                    exec(compile(filename.read_text(),str(filename),"exec"),namespace)
                made={p.name:json.loads(p.read_text()) for p in Path(tmp).glob("*.json")}
                if filename.name=="gen_ptw.py":made.pop(headline.name)
                assert made
                result[relative]={name:digest(obj) for name,obj in sorted(made.items())}
                for name,obj in made.items():
                    expected=source/"configs"/name
                    assert expected.exists(), name
                    assert obj==json.loads(expected.read_text()), name
                if filename.name=="gen_ebops_n8.py":
                    for method in ["make_cost_first","make_long_budget"]:
                        obj=namespace[method]();expected=source/"configs"/(obj["name"]+".json")
                        assert obj==json.loads(expected.read_text())
                        result[relative][expected.name]=digest(obj)
            finally:sys.path[:]=old_path
    return result


def training_contracts(source, task):
    import numpy as np
    keras,qat=initialize()
    from bnhgq2 import train as trainer,wandb_util
    from bnhgq2.data import input_std_stats,apply_input_std
    ptwm=importlib.import_module("bnhgq2.pt_weights") if (source/"bnhgq2/pt_weights.py").exists() else None
    cfg=json.loads((source/task["config_relative"]).read_text())
    x=np.arange(60*8*3,dtype="float32").reshape(60,8,3)/100
    y=np.eye(5,dtype="float32")[np.arange(60)%5]
    pts=np.full(60,1000.,dtype='float64');pts[np.arange(60)%5==0]=10.
    train_idx=np.random.default_rng(3).permutation(60)[12:]
    special=next(int(i) for i in train_idx if i%5==0);pts[special]=1000.
    rows={}
    class StopBeforeFit(Exception):pass
    class FakeModel:
        trainable_variables=[]
        def count_params(self):return 1
        def compile(self,**kwargs):self.compiled=kwargs
        def fit(self,X,Y,**kwargs):
            captured.update(x=ah(X),y=ah(Y),sample_weight=None if "sample_weight" not in kwargs else ah(kwargs["sample_weight"]),
                            fit_keys=sorted(kwargs),epochs=kwargs["epochs"],batch=kwargs["batch_size"])
            raise StopBeforeFit()
    cases=["absent","disabled"]+(["uncapped","capped","label_mismatch"] if ptwm else [])
    for case in cases:
        captured={}; c=copy.deepcopy(cfg);c["train"].pop("pt_weights",None)
        if case!="absent":c["train"]["pt_weights"]={"enable":case!="disabled","n_bins":8,"cap":5 if case=="capped" else None,"plot":False}
        def callbacks(Xval,Yval,*args,**kwargs):
            captured.update(xval=ah(Xval),yval=ah(Yval),callback_kwargs=kwargs)
            return []
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            for target,attr,replacement in [(trainer,"load_train_data",lambda *a,**k:(x.copy(),y.copy(),1)),(qat,"build_qat_model",lambda *a,**k:(FakeModel(),[])),(qat,"calibrate_activations",lambda *a,**k:{}),(qat,"act_grid_params",lambda *a,**k:{}),(qat,"effective_weight_values",lambda *a,**k:{"fixture":np.array([-1.,1.])}),(trainer,"make_callbacks",callbacks),(trainer,"ebops_callbacks",lambda *a,**k:([],None)),(wandb_util,"wandb_enabled",lambda *a,**k:False)]:
                stack.enter_context(patch.object(target,attr,replacement))
            pt_calls=[]
            if ptwm:
                def loadpt(*a,**kw):
                    pt_calls.append(True)
                    return pts.copy(),np.roll(y,1,axis=0) if case=="label_mismatch" else y.copy()
                stack.enter_context(patch.object(ptwm,"load_train_pt",loadpt))
            try:trainer.train(c,seed=3,out_dir=tmp)
            except StopBeforeFit:assert case!="label_mismatch"
            except SystemExit as exc:
                assert case=="label_mismatch" and "not aligned" in str(exc)
                rows[case]={"rejected":True};continue
            else:raise AssertionError("stub fit not reached")
            idx=np.random.default_rng(3).permutation(60);nv=12
            mu,sigma=input_std_stats(x[idx[nv:]])
            assert captured["x"]==ah(apply_input_std(x[idx[nv:]],mu,sigma))
            assert captured["xval"]==ah(apply_input_std(x[idx[:nv]],mu,sigma))
            assert captured["yval"]==ah(y[idx[:nv]])
            assert captured["y"]==ah(y[idx[nv:]])
            if case in ["absent","disabled"]:assert not pt_calls and captured["sample_weight"] is None
            else:
                expected,_=ptwm.compute_pt_weights(pts[idx[nv:]],y[idx[nv:]].argmax(1),n_bins=8,cap=5 if case=="capped" else None)
                assert captured["sample_weight"]==ah(expected)
            rows[case]=captured
    assert rows["absent"]==rows["disabled"]
    if ptwm:
        assert rows['uncapped']['sample_weight']!=rows['capped']['sample_weight'],'cap fixture did not exercise clipping'
        p=pts[train_idx];lab=y[train_idx].argmax(1)
        bins=np.linspace(np.log(p).min(),np.log(p).max(),9)
        all_counts=np.histogram(np.log(p),bins)[0];class_counts=np.histogram(np.log(p[lab==0]),bins)[0]
        raw=((all_counts+.5)/len(p))/((class_counts+.5)/(lab==0).sum())
        assert raw[-1]>5 and class_counts[-1]>0,'no observed training jet activates cap'
    return rows


def selection_contracts(source):
    import numpy as np
    keras,qat=initialize()
    from bnhgq2 import train as trainer,ebops_target as ebt,ablation
    cfg=json.loads((source/"configs"/("r14-l1x3-n8-w1a8.json" if (source/"configs/r14-l1x3-n8-w1a8.json").exists() else "pre_conference-n8-w1a8.json")).read_text())
    result={}
    for schedule in ["poly","cosine_restarts"]:
        callbacks=trainer.make_callbacks(np.zeros((5,8,3)),np.eye(5),"fixture",0,.01,2,10,1,False,{"best_auc":-1,"best_epoch":-1},lr_schedule=schedule,lr_cycle_epochs=5,lr_min_frac=.001)
        cb=next(x for x in callbacks if isinstance(x,keras.callbacks.LearningRateScheduler))
        result[schedule]=[float(cb.schedule(i,0)) for i in [0,1,2,4,6,7,11,12,20]]
    target_cfg={'train':{'ebops':{'pid':{'target_ebops':350000}}},'experiment':{'target_schedule':[[0,1000000],[250,750000],[500,500000],[750,350000]]}}
    result['target_boundaries']=[ablation.training_target(target_cfg,e) for e in [0,249,250,499,500,749,750,999]]
    assert result['target_boundaries']==[1000000,1000000,750000,750000,500000,500000,350000,350000]
    front=[{"epoch":1,"auc":.8,"ebops":100},{"epoch":2,"auc":.8,"ebops":90},{"epoch":0,"auc":.8,"ebops":90}]
    # Match the actual bookkeeping field name.
    front=[{**r,"val_macro_auc":r["auc"]} for r in front]
    result["front"]=trainer.select_front_point(front)
    assert result["front"]["epoch"]==0 and trainer.select_front_point([]) is None
    widths={"fixture":{"bits":8.,"width_trainable":True}}
    class Fake:
        stop_training=False
        def save(self,path):pass
    for selection in ["max_auc","min_ebops"]:
        with tempfile.TemporaryDirectory() as tmp, patch.object(ebt,"width_snapshot",return_value=widths):
            monitor=object.__new__(ebt.BudgetMonitor)
            keras.callbacks.Callback.__init__(monitor);monitor.set_model(Fake())
            monitor.sample=np.zeros((1,));monitor.out_dir=Path(tmp);monitor.initial={"total":200};monitor.initial_widths=widths
            monitor.target=100;monitor.selection=selection;monitor.stop_on_target=False
            monitor.lowest=monitor.best=monitor.last=None;monitor.history=Path(tmp)/"widths.jsonl"
            states=[]
            for epoch,(cost,auc) in enumerate([(101,.99),(100,.7),(90,.6),(100,.8),(100,.8)]):
                with patch.object(ebt,"compute_ebops",return_value={"total":cost,"per_layer":{}}):monitor.on_epoch_end(epoch,{"val_macro_auc":auc})
                states.append(copy.deepcopy(monitor.best))
            assert states[0] is None and states[1]["epoch"]==1
            assert states[-1]["epoch"]==(3 if selection=="max_auc" else 2)
            result[selection]=states
    return result


def evaluation_contracts(source):
    import numpy as np
    from bnhgq2.data import apply_input_std
    evaluator=importlib.import_module("evaluate_roc" if (source/"evaluate_roc.py").exists() else "roc_final")
    logits=np.arange(60,dtype="float32").reshape(12,5)/17
    p=evaluator.softmax64(logits)
    assert p.dtype==np.float64 and np.allclose(p.sum(1),1)
    class Fake:
        def __call__(self,x,training=False):return x
    assert np.array_equal(evaluator.predict_in_batches(Fake(),logits,batch=5),logits)
    x=np.arange(72,dtype="float32").reshape(3,8,3)
    standard=apply_input_std(x,[1,2,3],[2,3,4])
    result={"softmax":ah(p),"dtype":str(p.dtype),"standard":ah(standard),"batched_rows":ah(logits)}
    import h5py
    from bnhgq2.data import load_eval_set, CLASS_LABELS
    from bnhgq2.train import load_train_data
    with tempfile.TemporaryDirectory() as tmp:
        for file_id in [1,0]:
            const=np.zeros((5,4,3),dtype="float32")
            const[:,:,0]=[2,4,4,1]
            const[:,:,1]=np.arange(5)[:,None]+10*file_id
            const[:,:,2]=np.arange(4)
            labels=np.eye(5,dtype="float32")
            jets=np.column_stack([np.arange(5)+100+10*file_id,labels])
            with h5py.File(Path(tmp)/f'{file_id}.h5','w') as hf:
                hf['jetConstituentList']=const;hf['jets']=jets
                hf['jetFeatureNames']=np.asarray(['j_pt',*CLASS_LABELS],dtype='S')
                hf['particleFeatureNames']=np.asarray(['p_pt','p_etarel','p_phirel'],dtype='S')
        xx,yy,n=load_train_data(tmp,3,features=['pt','etarel','phirel'])
        xe,ye=load_eval_set(tmp,3,features=['pt','etarel','phirel'])
        assert n==2 and np.array_equal(xx,xe) and np.array_equal(yy,ye)
        assert np.array_equal(xx[0,:,2],[1,2,0]) # stable ties at equal pT
        assert np.array_equal(xx[:,0,1],np.r_[np.arange(5),np.arange(5)+10])
        result['loader_rows']=ah(xx);result['loader_labels']=ah(yy)
    path=source/"sample_weighting/eval_ptw_n8.py"
    if path.exists():
        spec=importlib.util.spec_from_file_location("ptw_eval",path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        score=module.scores_for(Fake(),logits)
        assert score.dtype==np.float32 and np.array_equal(score,p.astype("float32"))
        result["ptw_score"]=ah(score)
        try:module.scores_for(Fake(),p)
        except AssertionError:result["simplex_rejected"]=True
        else:raise AssertionError("already-softmaxed input accepted")
    return result


def generator_order(source):
    sys.path.insert(0,str(source/'configs'))
    result={}
    for order in ['public_first','legacy_first']:
        for name in list(sys.modules):
            if name in ['gen_ebops_n8','gen_ebops_ablation','generate_pre_conference'] or name.startswith('configs.'):
                sys.modules.pop(name,None)
        names=['gen_ebops_ablation','configs.legacy.gen_ebops_ablation']
        if order=='legacy_first':names.reverse()
        modules=[importlib.import_module(n) for n in names]
        hashes={}
        for module in modules:
            for arm in module.ARMS:
                obj=module.make_ablation(arm)
                assert obj==json.loads((source/'configs'/(obj['name']+'.json')).read_text())
                hashes[obj['name']]=digest(obj)
        result[order]=hashes
    assert result['public_first']==result['legacy_first']
    return result


def teacher_contracts(source):
    import types
    import numpy as np
    keras,qat=initialize()
    import tensorflow as tf
    import run_ablation as runner
    result={}
    for case in ['plain','track','missing','bad_basename','local','artifact']:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=root/'data';data.mkdir()
            x=np.arange(60,dtype='float32').reshape(4,5,3);y=np.eye(5,dtype='float32')[:4]
            xv=x+100
            for name,a in [('x_train',x),('y_train',y),('x_val',xv),('y_val',y)]:np.save(data/(name+'.npy'),a)
            info={'train_sha256':runner.array_hash(x),'val_sha256':runner.array_hash(xv),'input_std':{'mu':[0,0,0],'sigma':[1,1,1]}}
            (data/'data_info.json').write_text(json.dumps(info));(data/'READY.json').write_text('{}')
            cfg={'experiment':{'arm':'fixture'}}
            if case not in ['plain','track']:cfg['experiment']['distillation']={'teacher_artifact':'fixture/project/model:v0' if case=='artifact' else ''}
            cfgfile=root/'fixture.json';cfgfile.write_text(json.dumps(cfg))
            teacher=root/'teacher';teacher.mkdir();(teacher/'input_std.json').write_text(json.dumps(info['input_std']))
            args=['run_ablation','train','--config',str(cfgfile),'--root',str(root)]
            if case=='track':args+=['--track']
            if case in ['local','bad_basename']:args+=['--teacher-checkpoint',str(teacher/('model_best.keras' if case=='local' else 'other.keras'))]
            calls=[];artifact_calls=[]
            class Artifact:
                def download(self,root):
                    p=Path(root);p.mkdir();(p/'input_std.json').write_text(json.dumps(info['input_std']))
            class Api:
                def artifact(self,name):artifact_calls.append(name);return Artifact()
            fakewandb=types.SimpleNamespace(Api=Api)
            def predict(X,**kw):
                assert np.array_equal(X,x) and kw=={'batch_size':1024,'verbose':0}
                return np.zeros((len(X),5),dtype='float32')
            fake_model=types.SimpleNamespace(trainable=True,predict=predict)
            def load_model(path,**kw):
                expected=teacher/'model_best.keras' if case=='local' else root/'runs/fixture/teacher/model_best.keras'
                assert Path(path)==expected and kw=={'compile':False}
                return fake_model
            def train_stub(cfg,arrays,metadata,out,**kw):
                assert np.array_equal(arrays[0],x) and np.array_equal(arrays[2],xv)
                assert out==root/'runs/fixture';calls.append(kw)
            with patch.object(sys,'argv',args),patch.object(tf.config,'list_physical_devices',return_value=['fixture_GPU']),patch.object(runner,'run_training',side_effect=train_stub),patch.object(keras.models,'load_model',side_effect=load_model),patch.dict(sys.modules,{'wandb':fakewandb}):
                try:runner.main()
                except ValueError as exc:
                    assert case in ['missing','bad_basename'];result[case]={'rejected':str(exc)};continue
            assert len(calls)==1 and calls[0]['remote']==(case=='track')
            assert bool(artifact_calls)==(case=='artifact')
            result[case]={'tracking':calls[0]['remote'],'artifact_requested':artifact_calls,'teacher_used':calls[0]['teacher_logits'] is not None}
    return result


def delivered_contracts(source):
    import types
    import numpy as np
    keras,qat=initialize()
    from bnhgq2 import train as trainer,wandb_util,ebops_target,ebops_calc
    cfg=json.loads((source/'configs/pre_conference-n8-w1a8.json').read_text())
    cfg['train']['ebops']={'enable':True,'monitor_widths':True}
    x=np.arange(60*8*3,dtype='float32').reshape(60,8,3)/100;y=np.eye(5,dtype='float32')[np.arange(60)%5]
    result={}
    class Fake:
        trainable_variables=[];history=types.SimpleNamespace(epoch=[0]);jit_compile=False
        def count_params(self):return 1
        def compile(self,**kw):pass
        def fit(self,*a,**kw):pass # deliberately no optimizer or callback execution
    for case in ['at_cap','over_cap_rejected','no_feasible','minimum_cost']:
        with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
            point={'epoch':2,'val_macro_auc':.7,'ebops':100}
            monitor=types.SimpleNamespace(runtime_cfg=cfg,initial={'total':200},target=100,info={},sample=x[:2],
                    best=point if case in ['at_cap','over_cap_rejected'] else None,
                    lowest={'epoch':3,'val_macro_auc':.6,'ebops':110} if case=='minimum_cost' else None,
                    selection='min_ebops' if case=='minimum_cost' else 'max_auc',out_dir=Path(tmp))
            measured=100 if case=='at_cap' else 101 if case=='over_cap_rejected' else 110
            loaded=[]
            def callbacks(*args,**kw):args[9].update(best_auc=.9,best_epoch=4);return []
            replacements=[(trainer,'load_train_data',lambda *a,**kw:(x,y,1)),(qat,'build_qat_model',lambda *a,**kw:(Fake(),[])),
                (qat,'calibrate_activations',lambda *a,**kw:{}),(qat,'act_grid_params',lambda *a,**kw:{}),
                (qat,'effective_weight_values',lambda *a,**kw:{'fixture':np.array([-1.,1.])}),
                (trainer,'make_callbacks',callbacks),(trainer,'ebops_callbacks',lambda *a,**kw:([],None)),
                (wandb_util,'wandb_enabled',lambda *a,**kw:False),(ebops_target,'BudgetMonitor',lambda *a,**kw:monitor),
                (ebops_target,'width_snapshot',lambda *a,**kw:{}),(ebops_calc,'compute_ebops',lambda *a,**kw:{'total':measured}),
                (keras.models,'load_model',lambda path,**kw:loaded.append(Path(path).name) or Fake())]
            for obj,key,value in replacements:stack.enter_context(patch.object(obj,key,value))
            try:meta=trainer.train(copy.deepcopy(cfg),seed=3,out_dir=tmp)
            except RuntimeError as exc:
                assert case=='over_cap_rejected' and 'exceeds' in str(exc);result[case]={'rejected':True};continue
            expected='model_best.keras' if case=='at_cap' else 'model_min_ebops.keras' if case=='minimum_cost' else 'model_unconstrained.keras'
            assert loaded==[expected] and meta['ebops_budget']['checkpoint']==expected
            assert meta['ebops_budget']['budget_met']==(case=='at_cap')
            result[case]={'checkpoint':expected,'budget_met':meta['ebops_budget']['budget_met'],'best_epoch':meta['best_epoch']}
    return result


def final_target_contract(source):
    import types
    import numpy as np
    keras,qat=initialize()
    from bnhgq2 import ablation
    cfg=json.loads((source/'configs/post_conference_budget350k-gradual_budget-w1a8.json').read_text())
    cfg['train']['epochs']=2
    arrays=(np.zeros((10,8,3),dtype='float32'),np.eye(5,dtype='float32')[np.arange(10)%5],
            np.ones((5,8,3),dtype='float32'),np.eye(5,dtype='float32'))
    result={}
    class FakeModel:
        def count_params(self):return 1
        def predict(self,x,**kw):return np.zeros((len(x),5),dtype='float32')
        def save(self,path):saved_names.append(Path(path).name)
    class FakePID:
        beta=0.;_ebops=0.
        def __init__(self,**kw):self.pid=types.SimpleNamespace(integral=0.,prev_error=0.)
        def set_model(self,*a):pass
        def on_train_begin(self,*a):pass
        def on_epoch_begin(self,*a):pass
        def on_epoch_end(self,*a):pass
    for cost in [750000,350000]:
        saved_names=[]
        with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
            fake=FakeModel();optimizer=types.SimpleNamespace(learning_rate=types.SimpleNamespace(assign=lambda value:None))
            widths={'fixture':{'bits':8.,'width_trainable':True}}
            replacements=[(ablation,'restore_checkpoint',lambda *a:None),(ablation,'matching_initialization',lambda *a:(fake,{})),
                (ablation,'optimizer_for',lambda *a:optimizer),(ablation,'binary_gate',lambda *a:None),
                (ablation,'BetaPID',FakePID),(ablation,'width_snapshot',lambda *a:widths),
                (ablation,'make_epoch_step',lambda *a,**kw:lambda *a:types.SimpleNamespace(numpy=lambda:np.array([1.,1.,0.,.5]))),
                (ablation,'macro_ovr_auc',lambda *a:(.9,[.9]*5)),(ablation,'save_checkpoint',lambda *a:Path('fixture-checkpoint'))]
            for obj,key,value in replacements:stack.enter_context(patch.object(obj,key,value))
            stack.enter_context(patch.object(ablation,'compute_ebops',side_effect=[{'total':1000000,'per_layer':{}},{'total':cost,'per_layer':{}}]))
            state=ablation.run_training(copy.deepcopy(cfg),arrays,{'input_std':{'mu':[0,0,0],'sigma':[1,1,1]}},tmp,stop_after=1)
            log=json.loads((Path(tmp)/'activation_widths.jsonl').read_text())
            assert log['training_target_ebops']==1000000 and log['target_ebops']==350000
            assert (state['best_feasible'] is not None)==(cost<=350000)
            assert ('model_best.keras' in saved_names)==(cost<=350000)
            result[str(cost)]={'admitted':state['best_feasible'] is not None,'saved_names':saved_names,
                               'metric_execution':'STUBBED','optimizer_steps':0}
    return result


def ptw_entry_contract(source):
    from unittest.mock import MagicMock
    import numpy as np
    path=source/'sample_weighting/eval_ptw_n8.py'
    spec=importlib.util.spec_from_file_location('ptw_entry',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    # The fixed production split-size check receives metadata mocks. All backing
    # data, scores and writes below are twelve-row fixtures; metric calculation is stubbed.
    x=MagicMock();x.__len__.return_value=260000
    labels=np.eye(5,dtype='float32')[np.arange(12)%5]
    y=MagicMock();y.shape=(260000,5);y.__len__.return_value=260000;y.astype.return_value=labels
    scores=np.arange(60,dtype='float32').reshape(12,5)/100;pt=np.arange(12,dtype='float32')+100
    standard=np.ones((12,8,3),dtype='float32');saved=[];calls=[]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);ckpt=root/'explicit-checkpoints/base-s3';ckpt.mkdir(parents=True)
        meta={'seed':3,'config':'ptw-n8-20260925-base-w1a8','config_hash':'fixture','params':1,'best_epoch':0,'best_val_macro_auc':.5}
        (ckpt/'train_meta.json').write_text(json.dumps(meta));(ckpt/'input_std.json').write_text(json.dumps({'mu':[1,2,3],'sigma':[2,3,4]}))
        def load_data(path,**kw):assert path==str(root/'val') and kw=={'n_part':8,'features':['pt','etarel','phirel']};return x,y
        def load_pt(path):assert path==str(root/'val');return pt,y
        def apply(data,mu,sigma):assert data is x and mu==[1,2,3] and sigma==[2,3,4];calls.append('preprocess');return standard
        def score(model,data):assert data is standard;calls.append('score');return scores
        def load_model(path):assert Path(path)==ckpt/'model_best.keras';calls.append('checkpoint');return object()
        def save(path,**kwargs):saved.append((path,kwargs))
        argv=['eval_ptw','--out',str(root/'out'),'--ckpt',str(root/'explicit-checkpoints'),'--val-dir',str(root/'val'),'--train-dir',str(root/'train'),'--skip-val']
        with patch.object(sys,'argv',argv),patch.object(mod,'SEEDS',[3]),patch.object(mod,'ARMS',{'base':'BASE'}),patch.object(mod,'load_eval_set',load_data),patch.object(mod,'load_jet_pt',load_pt),patch.object(mod,'apply_input_std',apply),patch.object(mod,'scores_for',score),patch.object(mod,'load_final_model',load_model),patch.object(mod,'macro_ovr_auc',return_value=(.5,[.5]*5)),patch.object(mod.np,'savez_compressed',save):mod.main()
        assert calls==['checkpoint','preprocess','score'] and len(saved)==1
        assert Path(saved[0][0])==root/'out/BASE-s3.npz'
        arrays=saved[0][1];assert np.array_equal(arrays['y'],labels) and np.array_equal(arrays['score'],scores) and np.array_equal(arrays['j_pt'],pt)
    return {'explicit_paths':'PASS','preprocessing_forwarding':'PASS','label_score_pt_association':'PASS','fixture_rows':12,'metric_execution':'STUBBED'}


def main():
    task=json.loads(Path(sys.argv[1]).read_text());source=Path(task["source"]);out=Path(task["output"])
    sys.path.insert(0,str(source))
    def no_network(*a,**kw):raise AssertionError("network forbidden in merge preflight")
    socket.socket.connect=no_network;socket.create_connection=no_network
    try:
        phase=task["phase"]
        if phase in ["build","reload"]:result=model_checks(task,source,out)
        elif phase=="core":result=core_contracts(source,task)
        elif phase=="generators":result=generators(source,task)
        elif phase=="training":result=training_contracts(source,task)
        elif phase=="selection":result=selection_contracts(source)
        elif phase=="evaluation":result=evaluation_contracts(source)
        elif phase=="generator_order":result=generator_order(source)
        elif phase=="teacher":result=teacher_contracts(source)
        elif phase=="delivered":result=delivered_contracts(source)
        elif phase=="final_filter":result=final_target_contract(source)
        elif phase=="ptw_entry":result=ptw_entry_contract(source)
        else:raise ValueError(phase)
        out.write_text(json.dumps({"status":"PASS","result":result},sort_keys=True,indent=2)+"\n")
    except BaseException as exc:
        out.write_text(json.dumps({"status":"FAIL","error":f"{type(exc).__name__}: {exc}"},indent=2)+"\n")
        traceback.print_exc();raise


if __name__=="__main__":main()
