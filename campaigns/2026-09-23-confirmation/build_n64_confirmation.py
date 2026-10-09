"""Generate full 1,000-epoch N64 A07/E02/E05 confirmations at 5M eBOPs."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from campaign_common import BASE_JOB, CODE_CONFIGMAP, CODE_SHA256, SOURCE

HERE = Path(__file__).resolve().parent


def main():
    config_dir = HERE / "configs-n64"
    config_dir.mkdir(exist_ok=True)
    rows = []
    for seed in (2, 3):
        for arm in ("a07", "e02", "e05"):
            source = SOURCE / "configs" / f"const0922-{arm}-n64-s1-fast50-fp32.json"
            cfg = json.loads(source.read_text())
            name = f"confirm0924-{arm}-n64-s{seed}-e1000-5m"
            cfg["name"] = name
            cfg["experiment"].update(
                arm=name, group="confirmation-20260924-n64-full", seed=seed,
                source_arm=arm, selection_metric="val_categorical_accuracy",
                checkpoint_every_epochs=1, remote_every_epochs=25,
            )
            cfg["train"].update(
                epochs=1000, batch=256, val_batch=4096, lr=2e-5,
                warmup_epochs=1, decay_epochs=999,
                wandb_project="BNJetTag-Engram-Experimental",
            )
            cfg["train"]["ebops"]["pid"].update(target_ebops=5_000_000, warmup=10)
            cfg["train"]["ebops"]["selection"] = "max_accuracy"
            cfg["engram_study"]["question"] = (
                f"Full 1,000-epoch N64 {arm.upper()} confirmation at a 5,000,000 eBOP budget"
            )
            cfg["constituent_study"]["protocol"] = (
                "full 1000-epoch confirmation; no short screening or intermediate go/no-go rung"
            )
            filename = name + ".json"
            (config_dir / filename).write_text(json.dumps(cfg, indent=2) + "\n")
            rows.append({
                "name": name, "file": filename, "seed": seed, "source_arm": arm,
                "data_cache": "/data/constituent-study-20260922/n64/data",
                "output_root": "/data/confirmation-20260923/n64-5m-full/runs",
            })

    index = {
        "schema_version": 2, "budget_ebops": 5_000_000, "epochs": 1000,
        "runs": rows,
        "execution_policy": "Run every declared arm to 1,000 epochs; checkpoint metrics never stop or gate training.",
    }
    (HERE / "index-n64.json").write_text(json.dumps(index, indent=2) + "\n")
    files = {
        "index-n64.json": (HERE / "index-n64.json").read_text(),
        "preflight_n64.py": (HERE / "preflight_n64.py").read_text(),
    }
    for row in rows:
        files[row["file"]] = (config_dir / row["file"]).read_text()
    content_sha = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    configmap_name = "kai-confirm-n64-full-configs-" + content_sha[:10]
    configmap = {
        "apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
        "metadata": {"name": configmap_name, "namespace": "cms-ml",
                     "labels": {"user": "kai", "campaign": "confirmation-20260923"}},
        "data": files,
    }
    (HERE / "n64-configs-configmap.json").write_text(json.dumps(configmap) + "\n")

    job = copy.deepcopy(BASE_JOB)
    labels = {"user": "kai", "campaign": "confirmation-20260923", "app": "kai-confirm-n64-preflight"}
    job["metadata"] = {"name": f"kai-confirm-n64-preflight-0924-{content_sha[:6]}",
                       "namespace": "cms-ml", "labels": labels}
    spec = job["spec"]
    spec.update(completions=1, parallelism=1, backoffLimitPerIndex=3, maxFailedIndexes=1,
                activeDeadlineSeconds=3600, ttlSecondsAfterFinished=604800)
    spec["template"]["metadata"] = {"labels": labels}
    pod = spec["template"]["spec"]
    container = pod["containers"][0]
    next(v for v in pod["volumes"] if v["name"] == "code")["configMap"]["name"] = CODE_CONFIGMAP
    pod["volumes"].append({"name": "configs", "configMap": {"name": configmap_name}})
    container["volumeMounts"].append({"name": "configs", "mountPath": "/configs", "readOnly": True})
    container.pop("env", None)
    for kind in ("requests", "limits"):
        container["resources"][kind].pop("nvidia.com/gpu", None)
        container["resources"][kind].update(cpu="4", memory="16Gi", **{"ephemeral-storage": "12Gi"})
    container["args"] = [f"""set -euo pipefail
export KERAS_BACKEND=tensorflow WANDB_MODE=disabled CUDA_VISIBLE_DEVICES=-1 NVIDIA_TF32_OVERRIDE=0
export OMP_NUM_THREADS=4 TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2 OPENBLAS_NUM_THREADS=1
mkdir -p /work/code
echo '{CODE_SHA256}  /cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1
export PYTHONPATH=/work/code BNHGQ2_CODE_SHA256={CODE_SHA256}
pip install -q --no-cache-dir -r /work/code/requirements-cpu.txt
python -u /configs/preflight_n64.py
"""]
    (HERE / "n64-preflight-job.json").write_text(json.dumps(job, indent=2) + "\n")
    (HERE / "n64-manifest.json").write_text(json.dumps({
        "configs_sha256": content_sha, "configmap": configmap_name,
        "training_code_configmap": CODE_CONFIGMAP, "training_code_sha256": CODE_SHA256,
        "budget_ebops": 5_000_000, "epochs": 1000, "runs": rows,
        "short_screening": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
