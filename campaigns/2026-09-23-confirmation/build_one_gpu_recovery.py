"""Build an immutable one-GPU queue for all N8 and N64 confirmations."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from campaign_common import BASE_JOB, CODE_CONFIGMAP, CODE_SHA256

HERE = Path(__file__).resolve().parent


def main():
    original = json.loads((HERE / "index.json").read_text())
    n8_rows = [{**row,
                "data_cache": "/data/constituent-study-20260922/n8/data",
                "output_root": "/data/confirmation-20260923/architecture/runs"}
               for row in original["runs"]]
    n64_rows = json.loads((HERE / "index-n64.json").read_text())["runs"]
    index = {"schema_version": 2, "runs": n8_rows + n64_rows,
             "execution": "all declared runs target 1,000 epochs; three processes at a time share one GPU and restart in 20-epoch memory-management chunks",
             "decision_rungs": []}
    files = {
        "index-one-gpu.json": json.dumps(index, indent=2) + "\n",
        "pack_runner_one_gpu.py": (HERE / "pack_runner_one_gpu.py").read_text(),
    }
    for row in n8_rows:
        files[row["file"]] = (HERE / "configs" / row["file"]).read_text()
    for row in n64_rows:
        files[row["file"]] = (HERE / "configs-n64" / row["file"]).read_text()
    content_sha = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    configmap_name = "kai-confirm-onegpu-configs-" + content_sha[:10]
    configmap = {
        "apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
        "metadata": {"name": configmap_name, "namespace": "cms-ml",
                     "labels": {"user": "kai", "campaign": "confirmation-20260923"}},
        "data": files,
    }
    (HERE / "one-gpu-configmap.json").write_text(json.dumps(configmap) + "\n")

    result = copy.deepcopy(BASE_JOB)
    labels = {"user": "kai", "campaign": "confirmation-20260923", "app": "kai-confirm-onegpu"}
    result["metadata"] = {"name": f"kai-confirm-onegpu-0924-{content_sha[:6]}-r2",
                          "namespace": "cms-ml", "labels": labels}
    spec = result["spec"]
    spec.update(completions=1, parallelism=1, backoffLimitPerIndex=4, maxFailedIndexes=1,
                activeDeadlineSeconds=604800, ttlSecondsAfterFinished=604800)
    spec["template"]["metadata"] = {"labels": labels}
    pod = spec["template"]["spec"]
    container = pod["containers"][0]
    next(v for v in pod["volumes"] if v["name"] == "code")["configMap"]["name"] = CODE_CONFIGMAP
    pod["volumes"].append({"name": "configs", "configMap": {"name": configmap_name}})
    container["volumeMounts"].append({"name": "configs", "mountPath": "/configs", "readOnly": True})
    container["resources"]["requests"].update(cpu="12", memory="36Gi",
                                                  **{"ephemeral-storage": "24Gi", "nvidia.com/gpu": "1"})
    container["resources"]["limits"].update(cpu="12", memory="36Gi",
                                                **{"ephemeral-storage": "24Gi", "nvidia.com/gpu": "1"})
    container["env"].extend([
        {"name": "CHUNK_EPOCHS", "value": "20"},
        {"name": "STALL_SECONDS", "value": "7200"},
        {"name": "MAX_CONCURRENT", "value": "3"},
    ])
    container["args"] = [f"""set -euo pipefail
export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_FORCE_GPU_ALLOW_GROWTH=true TF_CPP_MIN_LOG_LEVEL=2
export NVIDIA_TF32_OVERRIDE=0 OMP_NUM_THREADS=4 TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2 OPENBLAS_NUM_THREADS=1
mkdir -p /work/code
echo '{CODE_SHA256}  /cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1
export PYTHONPATH=/work/code BNHGQ2_CODE_SHA256={CODE_SHA256}
export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_PROJECT=BNJetTag-Engram-Experimental
export WANDB_GROUP=confirmation-20260924-full1000 WANDB_MODE=online WANDB_TAGS=confirmation,seeds,n8,n64,one-gpu,full1000
export WANDB_DIR=/work WANDB_CACHE_DIR=/work/wandb-cache WANDB_DATA_DIR=/work/wandb-data WANDB_DISABLE_CODE=true WANDB_QUIET=true
pip install -q --no-cache-dir -r /work/code/requirements-training.txt
NVLIBS=$(python -c "import glob; print(':'.join(sorted(glob.glob('/usr/local/lib/python*/site-packages/nvidia/*/lib'))))")
export LD_LIBRARY_PATH="$NVLIBS${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"
python -c "import tensorflow as tf; devices=tf.config.list_physical_devices('GPU'); assert len(devices)==1; print('ONE_GPU_GATE_PASS', devices)"
python -u /configs/pack_runner_one_gpu.py
"""]
    (HERE / "one-gpu-job.json").write_text(json.dumps(result, indent=2) + "\n")
    manifest = {"configmap": configmap_name, "configs_sha256": content_sha,
                "training_code_sha256": CODE_SHA256, "gpu_count": 1,
                "concurrent_runs": 3, "total_runs": len(index["runs"]), "chunk_epochs": 20,
                "memory_per_pod": "36Gi", "stall_seconds": 7200,
                "target_epochs_per_run": 1000, "intermediate_decision_gates": 0,
                "chunk_purpose": "release TensorFlow memory and resume exact state"}
    (HERE / "one-gpu-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
