"""Materialize the proposed batch; does not start training or contact services."""
import copy
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "publication/code/hgq2/configs/post_conference_budget350k-channel_quantization-w1a8.json"
# id, constituents, embedding, FFN, layers, heads, granularity, budget, control, question
ROWS = [
    ("A00", 8, 32, 64, 2, 4, "channel", 350000, "historical R1", "Accuracy-selected reference"),
    ("A01", 8, 32, 64, 2, 4, "tensor", 350000, "A00", "Activation granularity"),
    ("A02", 8, 32, 32, 2, 4, "channel", 350000, "A00", "Smaller FFN with channel widths"),
    ("A03", 8, 32, 32, 2, 4, "tensor", 350000, "A01; A02", "Complete granularity-by-FFN comparison"),
    ("A04", 16, 32, 32, 2, 4, "channel", 350000, "A02", "More constituents at matched budget"),
    ("A05", 32, 32, 32, 2, 4, "channel", 350000, "A04", "Input information versus quadratic attention cost"),
    ("A06", 16, 16, 32, 2, 4, "channel", 350000, "A04", "Narrower embedding"),
    ("A07", 16, 32, 32, 1, 4, "channel", 350000, "A04", "Shallower transformer"),
    ("A08", 16, 32, 32, 2, 2, "channel", 350000, "A04", "Fewer heads at fixed embedding"),
    ("A09", 16, 32, 32, 2, 4, "channel", 500000, "A04", "Relieve quantization pressure"),
    ("A10", 16, 32, 32, 2, 4, "channel", 250000, "A04", "Tighter resource target"),
    ("A11", 8, 32, 32, 2, 4, "channel", 500000, "A02; A09", "Complete constituents-by-budget comparison"),
]


def main():
    base = json.loads(SOURCE.read_text())
    configs = HERE / "proposed_configs"
    configs.mkdir(exist_ok=True)
    runs = []
    for rid, n, d, f, layers, heads, granularity, budget, control, question in ROWS:
        cfg = copy.deepcopy(base)
        name = f"batch20260917-{rid.lower()}-s1"
        cfg.update(name=name)
        cfg["arch"].update(n_part=n, d_model=d, ffn_dim=f, n_layers=layers, n_heads=heads)
        cfg["quant"]["act_granularity"] = granularity
        cfg["train"]["ebops"]["pid"]["target_ebops"] = budget
        # run_training uses experiment.selection_metric, not the legacy selection string.
        cfg["experiment"].update(arm=name, group="batch20260917", seed=1,
                                 selection_metric="val_categorical_accuracy")
        cfg["hls"]["rf"] = 1
        cfg["train"]["wandb_project"] = "BNJetTag-Batch20260917"
        serialized = json.dumps(cfg, indent=2) + "\n"
        target = configs / f"{name}.json"
        target.write_text(serialized)
        blockers = ["common data/export/resume preflight"]
        if granularity == "channel" and f != 64:
            blockers.append("generalize matching_initialization forward-equivalence check")
        if layers != 2:
            blockers.append("derive binary gate and initialization expectations from architecture")
        runs.append(dict(id=rid, seed=1, constituents=n, d_model=d, ffn_dim=f,
                         layers=layers, heads=heads, head_dim=d // heads,
                         activation_granularity=granularity, target_ebops=budget,
                         method="full-model binary-weight QAT; learned activation widths",
                         control=control, question=question,
                         config=str(target.relative_to(HERE)),
                         config_sha256=hashlib.sha256(serialized.encode()).hexdigest(),
                         status="planned; not launched", prerequisites="; ".join(blockers)))
    with (HERE / "training_runs.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(runs[0]))
        writer.writeheader()
        writer.writerows(runs)
    manifest = dict(status="planning artifact, not an executable scheduler",
                    baseline_config=str(SOURCE.relative_to(REPO)),
                    baseline_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    immutable_training_horizon=1000,
                    screening=[dict(cumulative_epochs=100, runs=12),
                               dict(cumulative_epochs=200, runs=8),
                               dict(cumulative_epochs=400, runs=4)],
                    screening_epoch_passes=2800, max_concurrent_gpu_jobs=2,
                    primary_selection="validation accuracy subject to native EBOP target",
                    runs=runs)
    (HERE / "training_plan.json").write_text(json.dumps(manifest, indent=2) + "\n")
    assert len(runs) == 12 and len({r["id"] for r in runs}) == 12
    for run in runs:
        cfg = json.loads((HERE / run["config"]).read_text())
        assert cfg["arch"]["d_model"] % cfg["arch"]["n_heads"] == 0
        assert cfg["train"]["epochs"] == 1000 and cfg["train"]["decay_epochs"] == 999
        assert cfg["experiment"]["selection_metric"] == "val_categorical_accuracy"
        assert cfg["experiment"]["arm"].endswith("-s1")
        assert cfg["hls"]["rf"] == 1
    print(f"Wrote and structurally checked {len(runs)} proposed configurations; no training launched.")


if __name__ == "__main__":
    main()
