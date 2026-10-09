'Optional Weights & Biases experiment tracking and versioned artifact utilities.\n\nSet WANDB_ENTITY and WANDB_PROJECT for your account. Tracking is disabled\nunless WANDB_MODE is explicitly set to online and credentials are available.'
from __future__ import annotations

import hashlib
import os

DEFAULT_ENTITY = os.environ.get("WANDB_ENTITY", "")
DEFAULT_PROJECT = "binary-transformer"


def resolve_entity() -> str:
    return os.environ.get("WANDB_ENTITY") or DEFAULT_ENTITY


def resolve_project(cfg_project: str | None = None) -> str:
    return os.environ.get("WANDB_PROJECT") or cfg_project or DEFAULT_PROJECT


def wandb_enabled(cfg_project: str | None = None) -> bool:
    """A credential present (env key, or local ~/.netrc as on the laptop) and a
    project resolvable. Pods always come through the env-key path (k8s secret)."""
    if os.environ.get("WANDB_MODE", "disabled").lower() != "online":
        return False
    if not resolve_project(cfg_project):
        return False
    if os.environ.get("WANDB_API_KEY"):
        return True
    try:
        netrc = os.path.expanduser("~/.netrc")
        return os.path.isfile(netrc) and "api.wandb.ai" in open(netrc).read()
    except Exception:
        return False


def _env_tags() -> list:
    return [t.strip() for t in os.environ.get("WANDB_TAGS", "").split(",") if t.strip()]


def init_kwargs(*, name: str, job_type: str, config: dict | None = None,
                cfg_project: str | None = None, group: str | None = None,
                tags: list | None = None) -> dict:
    """Standard wandb.init kwargs. Group/tags come from the job YAML env
    (WANDB_GROUP / WANDB_TAGS) unless given explicitly; absent env keeps the
    pre-overhaul behaviour (no group, no tags) so old YAMLs stay valid."""
    kw = dict(entity=resolve_entity(), project=resolve_project(cfg_project),
              name=name, job_type=job_type)
    group = group or os.environ.get("WANDB_GROUP")
    if group:
        kw["group"] = group
    all_tags = list(dict.fromkeys(_env_tags() + list(tags or [])))
    if all_tags:
        kw["tags"] = all_tags
    if config is not None:
        kw["config"] = config
    return kw


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log_files_artifact(run, *, name: str, type: str, files: list,
                       metadata: dict | None = None, aliases: list | None = None):
    """Log `files` as one versioned artifact and BLOCK until the server commits it.

    Replaces the hand-rolled durability gate: `.wait()` returns only after the
    commit (server-verified checksums); we additionally assert every file made it
    into the manifest. Raises on any failure — callers decide whether that is
    fatal (training pods: yes, the pod is emptyDir-only).
    """
    import wandb
    art = wandb.Artifact(name=name, type=type, metadata=metadata or {})
    names = []
    for f in files:
        if os.path.isdir(f):
            art.add_dir(f, name=os.path.basename(f))
        else:
            art.add_file(f)
            names.append(os.path.basename(f))
    run.log_artifact(art, aliases=aliases or ["latest"])
    if os.environ.get("WANDB_MODE", "").lower().startswith(("off", "dis")):
        # offline: no server to commit against; the artifact is staged for `wandb sync`
        print(f"[wandb] artifact {name} staged (offline mode — no commit check)",
              flush=True)
        return art
    art.wait()
    entries = set(art.manifest.entries)
    missing = [n for n in names if n not in entries]
    if missing:
        raise RuntimeError(f"artifact {name}: files missing from committed "
                           f"manifest: {missing}")
    print(f"[wandb] artifact {name}:{art.version} committed "
          f"({len(art.manifest.entries)} files)", flush=True)
    return art


def fetch_checkpoint(run_name: str, dest: str, *, project: str | None = None,
                     entity: str | None = None,
                     want=("model_best.keras",)) -> str | None:
    """Artifact-first checkpoint fetch with run-files fallback.

    1. artifact <entity>/<project>/model-<run_name>:latest  (2026-08+ runs)
    2. run files <run_name>/<file> on the run itself        (pre-overhaul runs)
    Returns the directory containing the files, or None. Duplicate runs (job
    retries) are ranked finished > has best_val_macro_auc > newest, matching the
    earlier evaluation fetch."""
    import wandb
    entity = entity or resolve_entity()
    project = project or resolve_project()
    api = wandb.Api(timeout=120)
    os.makedirs(dest, exist_ok=True)
    try:
        art = api.artifact(f"{entity}/{project}/model-{run_name}:latest")
        d = art.download(root=dest)
        if all(os.path.isfile(os.path.join(d, w)) for w in want):
            print(f"[wandb] fetched artifact model-{run_name}:{art.version} -> {d}",
                  flush=True)
            return d
    except Exception:
        pass  # no artifact — pre-overhaul run; fall through to run files
    try:
        runs = [r for r in api.runs(f"{entity}/{project}",
                                    filters={"display_name": run_name})]
    except Exception as e:
        print(f"[wandb] run query failed for {run_name}: {e!r}", flush=True)
        return None

    def rank(r):
        return (r.state == "finished",
                r.summary.get("best_val_macro_auc") is not None, str(r.created_at))

    # Run files live under the OUT-DIR leaf, which is the run name for reference experiment+
    # but drops the campaign prefix for final/reference experiment (run final-w1a8-s1 stores
    # w1a8-s1/model_best.keras) — so match by basename, exactly like the old
    # evaluate_roc fetch, and return the directory holding the first wanted file.
    for r in sorted(runs, key=rank, reverse=True):
        by_base = {}
        for f in r.files():
            b = os.path.basename(f.name)
            if b in want:
                by_base.setdefault(b, []).append(f)
        if not all(len(by_base.get(w, [])) == 1 for w in want):
            continue
        for w in want:
            by_base[w][0].download(root=dest, replace=True)
        d = os.path.join(dest, os.path.dirname(by_base[list(want)[0]][0].name))
        print(f"[wandb] fetched run files {run_name} ({r.state} {r.id}) -> {d}",
              flush=True)
        return d
    return None
