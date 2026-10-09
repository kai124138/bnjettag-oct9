"""Reproduce the six checkpoint-compatible full N8 confirmation configs."""
from __future__ import annotations

import json
from pathlib import Path

from campaign_common import SOURCE

HERE = Path(__file__).resolve().parent


def main():
    config_dir = HERE / "configs"
    config_dir.mkdir(exist_ok=True)
    rows = []
    for seed in (2, 3):
        for arm in ("a00", "a02", "a03"):
            source = SOURCE / "configs" / f"const0922-{arm}-n8-s1-fast50-fp32.json"
            cfg = json.loads(source.read_text())
            name = f"confirm0923-{arm}-s{seed}-e1000"
            cfg["name"] = name
            cfg["experiment"].update(
                arm=name, group="confirmation-20260923-architecture", seed=seed,
                source_arm=arm, selection_metric="val_categorical_accuracy",
            )
            cfg["train"].update(
                epochs=1000, batch=256, val_batch=4096, lr=2e-5,
                warmup_epochs=1, decay_epochs=999,
                wandb_project="BNJetTag-Engram-Experimental",
            )
            cfg["train"]["ebops"]["pid"]["warmup"] = 10
            cfg["train"]["ebops"]["selection"] = "max_accuracy"
            cfg["engram_study"]["question"] = (
                f"Seed confirmation for historical {arm.upper()} at unchanged batch 256"
            )
            filename = name + ".json"
            (config_dir / filename).write_text(json.dumps(cfg, indent=2) + "\n")
            rows.append({"name": name, "file": filename, "seed": seed, "source_arm": arm})

    index = {
        "schema_version": 2,
        "runs": rows,
        "epochs": 1000,
        "execution_policy": (
            "Run every declared arm to 1,000 epochs; checkpoint metrics never stop or gate training."
        ),
    }
    (HERE / "index.json").write_text(json.dumps(index, indent=2) + "\n")


if __name__ == "__main__":
    main()
