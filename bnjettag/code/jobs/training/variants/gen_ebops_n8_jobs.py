#!/usr/bin/env python3
"""Generate four pilot jobs, a CPU preflight job, and an immutable code ConfigMap.

No cluster mutation. Reuses the established R14 container/dependency/data recipe.
Only source .py/.sh and this pilot's configs are packaged (no credentials/results).
"""
from __future__ import annotations

import argparse
import base64
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import yaml
from gen_r14_jobs import TEMPLATE

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[2] / "hgq2"
sys.path.insert(0, str(CODE / "configs"))
from gen_ebops_n8 import ARMS, PREFIX, PROJECT, make_pilot, make_cost_first, make_long_budget


def package_code():
    paths = list((CODE / "bnhgq2").rglob("*.py"))
    paths += list((CODE / "hls_templates").glob("*.h"))
    paths += [CODE / n for n in ("run_stage.py", "preflight_final.sh", "check_ebops_target.py", "check_ebops_costfirst.py", "check_ebops_long.py")]
    paths += list((CODE / "configs").glob("ebops-n8-*.json"))
    paths += [CODE / "configs" / n for n in ("gen_r14.py", "gen_ebops_n8.py")]
    raw = io.BytesIO()
    records = {}
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for p in sorted(set(paths)):
            data = p.read_bytes()
            relative = str(p.relative_to(CODE))
            records[relative] = hashlib.sha256(data).hexdigest()
            info = tarfile.TarInfo("hgq2/" + relative)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    payload = gzip.compress(raw.getvalue(), mtime=0)
    assert len(payload) < 900_000, "ConfigMap payload is too large"
    digest = hashlib.sha256(payload).hexdigest()
    cm = f"kai-ebops-n8-code-{digest[:10]}"
    return payload, digest, cm, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cost-first", action="store_true", help="One cost-priority b50 retry")
    mode.add_argument("--long-budget", action="store_true", help="One 1000-epoch, 350k-EBOPs run")
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    configs = ({"e1000-b350k": make_long_budget()} if args.long_budget else
               {"costfirst-b50": make_cost_first()} if args.cost_first else {arm: make_pilot(arm) for arm in ARMS})
    group = ("ebops-n8-20260911-long-budget" if args.long_budget else
             f"{PREFIX}-costfirst" if args.cost_first else PREFIX)
    for arm, expected in configs.items():
        actual = json.loads((CODE / "configs" / f"{expected['name']}.json").read_text())
        assert actual == expected, "Regenerate pilot configs first"
    payload, digest, cm, records = package_code()
    (out / "hgq2.tar.gz").write_bytes(payload)
    (out / "configmap.json").write_text(json.dumps({
        "apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
        "metadata": {"name": cm, "namespace": "cms-ml", "labels": {"app": "kai-ebops-n8"}},
        "binaryData": {"hgq2.tar.gz": base64.b64encode(payload).decode()},
    }, indent=2) + "\n")
    jobs = []
    for arm, cfg in configs.items():
        config = cfg["name"]
        leaf = f"{config}-s1"
        day = "0911" if args.long_budget else "0910"
        name = f"kai-ebops-n8-{day}-{arm}-s1"
        job = yaml.safe_load(TEMPLATE.format(job=name, leaf=leaf, stage="pilot", config=config,
                                             seed=1, npart=8, variant="w1a8"))
        job["metadata"] = {"name": name, "namespace": "cms-ml",
                           "labels": {"app": "kai-ebops-n8", "arm": arm}}
        job["spec"]["backoffLimit"] = 0
        if args.long_budget:
            job["spec"]["activeDeadlineSeconds"] = 172800
        pod = job["spec"]["template"]
        pod["metadata"]["labels"] = {"app": "kai-ebops-n8", "arm": arm}
        pod["spec"]["volumes"][0]["configMap"]["name"] = cm
        container = pod["spec"]["containers"][0]
        script = container["args"][0]
        script = script.replace("kai-bn14-code", cm).replace("BNJetTagAug", PROJECT)
        script = script.replace("export WANDB_GROUP=r14-n8", f"export WANDB_GROUP={group}")
        script = script.replace("export WANDB_TAGS=r14,l1x3,pilot,n8,w1a8",
                                f"export WANDB_TAGS=ebops-pilot,l1x3,n8,w1,free-width,{arm}")
        # Auth/project are checked before spending time on the dataset download.
        auth = (f"export WANDB_PROJECT={PROJECT}\n"
                "export WANDB_ENTITY=kayamaguchi-uc-san-diego\n"
                "export WANDB_MODE=online\n"
                "python -c \"import wandb; wandb.Api().viewer; print('[wandb] authentication OK')\"\n")
        script = script.replace('echo "[data] $(date) fetch', auth + 'echo "[data] $(date) fetch', 1)
        script = script.replace('export PYTHONPATH="$CODE:$PYTHONPATH"',
                                'export PYTHONPATH="$CODE:${PYTHONPATH:-}"\n'
                                f'export BNHGQ2_CODE_SHA256={digest}\n'
                                f'echo "{digest}  /cmcode/hgq2.tar.gz" | sha256sum -c -\n'
                                'test -f "$CODE/bnhgq2/ebops_target.py"')
        if args.cost_first or args.long_budget:
            # Exercise the actual non-XLA GPU training/checkpoint path before downloading data.
            script = script.replace('echo "[data] $(date) fetch',
                                    'WANDB_MODE=disabled python -u "$CODE/check_ebops_costfirst.py" --gpu --integration\n'
                                    'echo "[data] $(date) fetch', 1)
        if args.long_budget:
            script = script.replace("check_ebops_costfirst.py\" --gpu --integration", "check_ebops_long.py\" --gpu")
        container["args"] = [script]
        # No quota for H100/H200; avoid these and unvalidated Blackwell wheels.
        exprs = pod["spec"]["affinity"]["nodeAffinity"]["requiredDuringSchedulingIgnoredDuringExecution"]["nodeSelectorTerms"][0]["matchExpressions"]
        for expr in exprs:
            if expr["key"] == "nvidia.com/gpu.product":
                expr["values"] = [v for v in expr["values"] if not any(s in v for s in ("H100", "H200", "Blackwell"))]
        (out / f"{name}.yaml").write_text(yaml.safe_dump(job, sort_keys=False))
        jobs.append(job)
    (out / "training-jobs.yaml").write_text(yaml.safe_dump_all(jobs, sort_keys=False))
    preflight = copy.deepcopy(jobs[0])
    name = f"kai-ebops-n8-preflight-{digest[:8]}"
    preflight["metadata"] = {"name": name, "namespace": "cms-ml",
                             "labels": {"app": "kai-ebops-n8-preflight"}}
    preflight["spec"]["activeDeadlineSeconds"] = 1800
    pod = preflight["spec"]["template"]
    pod["metadata"]["labels"] = {"app": "kai-ebops-n8-preflight"}
    pod["spec"].pop("affinity")
    pod["spec"]["nodeSelector"] = {"kubernetes.io/arch": "amd64"}
    container = pod["spec"]["containers"][0]
    container["name"] = "preflight"
    container.pop("env")  # CPU preflight has no W&B credential.
    container["resources"] = {side: {"cpu": "2", "memory": "4Gi", "ephemeral-storage": "8Gi"}
                              for side in ("requests", "limits")}
    container["args"] = [f'''set -euo pipefail
export KERAS_BACKEND=tensorflow CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled
export BNF_CODE=/work/code BNF_CONFIG_GLOB='ebops-n8-*.json' BNF_SKIP_INSTALL=1
mkdir -p "$BNF_CODE"
echo '{digest}  /cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C "$BNF_CODE" --strip-components=1
export PYTHONPATH="$BNF_CODE"
pip install -q --no-cache-dir tensorflow==2.21.0 keras==3.15.0 hgq2==0.1.9 quantizers==1.2.2 scikit-learn==1.9.0 h5py==3.14.0 wandb==0.28.0 hls4ml==1.3.0 numpy==2.5.0
bash "$BNF_CODE/preflight_final.sh"
python -u "$BNF_CODE/check_ebops_target.py" --integration
python -u "$BNF_CODE/check_ebops_costfirst.py" --integration
{'python -u "$BNF_CODE/check_ebops_long.py"' if args.long_budget else ''}
''']
    (out / "preflight.yaml").write_text(yaml.safe_dump(preflight, sort_keys=False))
    manifest = {"project": PROJECT, "entity": "kayamaguchi-uc-san-diego", "group": group,
                "configmap": cm, "code_sha256": digest, "files": records,
                "preflight_job": name, "jobs": [j["metadata"]["name"] for j in jobs],
                "seeds": [1], "arms": ({"e1000-b350k": 350000} if args.long_budget else
                                          {"costfirst-b50": 869591} if args.cost_first else ARMS),
                "cost_first": args.cost_first, "long_budget": args.long_budget, "initial_activation_bits": 8,
                "epochs": next(iter(configs.values()))["train"]["epochs"], "data": "full train split; 20% internal validation"}
    (out / "launch_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ("project", "code_sha256", "configmap", "jobs")}, indent=2))


if __name__ == "__main__":
    main()
