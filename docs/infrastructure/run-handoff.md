# Immutable run handoff

The PC/WSL directory `~/lab/bnjettag` is the canonical editor and launcher workspace.
Mac VS Code is a remote editor of those same files. The monitor does not need a synchronized
checkout: every supported run carries its exact launch payload and factual brief to NRP once.

## Supported integration

Keep the existing freeze scripts unchanged:

- Chang: `campaigns/2026-09-26-training-batch/manifests/freeze.py`
- Delta: `campaigns/2026-09-27-delta-screen/bundle/freeze_delta.py`

The adapter consumes their immutable `configmap.json` (`binaryData.hgq2.tar.gz`, payload
root `code/`) and generated `batch/v1` JSON Job. It supports namespace `cms-ml`, `user=kai`,
one `kai-data` volume mounted at `/data`, an actual read-only code mount at `/cmcode` in every
container, no subPath/subPathExpr or overlapping mounts at either root, no existing init
containers and token automount off. Unmounted or remapped source ConfigMaps are rejected.
It preserves original commands/resources and adds only provenance annotations, an immutable
handoff ConfigMap, and a small init container using the Job's existing Python-capable image.
Image digests are preferred; mutable historical tags are recorded but are not reproducibility
guarantees. Fingerprint ConfigMaps or other existing prerequisites are not recreated by this tool.
CronJobs, YAML conversion, other PVC layouts and existing init containers require reviewed adapters.

The actual frozen bytes include uncommitted changes in the executed tree. They do not include
arbitrary unexecuted files elsewhere in the repository. Re-freeze after changes; never use
`--jobs-only` to pretend changed source has been captured. The adapter does not decide which
campaign patches or configs should be generated. That remains the scientific workflow.

## Prepare (offline)

Create a JSON brief with these required fields. Replace every illustrative value with reviewed
facts; do not use this example to clear Chang K1:

```json
{
  "purpose": "Question this run answers",
  "changes": "Factual changes relative to a named earlier run or baseline",
  "approval_ref": "Dated Kai authorization or decision document reference",
  "scientific_gate": {"status": "pending", "reference": "STUDY.md pending gate"},
  "runs": [{"name": "actual-arm-name", "config_path": "code/campaigns/example/configs/arm.json"}],
  "expected_metrics": [{"name": "validation AUC", "split": "validation; n from data_info", "expectation": "Approved expected behavior; uncertainty stated"}],
  "stop_rules": [{"condition": "Registered runner guard or alert criterion", "action": "notify-only", "approval_ref": "Dated approved rule"}],
  "outputs": ["/data/campaign/stage/runs/actual-arm-name", "wandb://entity/project/run-id"]
}
```

Use `existing-runner-guard` only for a guard already implemented in the frozen runner.
The adapter does not implement new stop rules. The brief's selected runs are declarations:
review them against the preserved pack/index and exact Job command. It does not infer arbitrary
shell semantics. Literal JSON configs, runtime environment and arguments are preserved;
runtime defaults are defined by the frozen code, not reinterpreted by the adapter.

Export the existing cache's `data_info.json` through an already authorized read path; no
dataset/model download is necessary. It must include `array_sha256`. Do not fabricate it or
create a pod just to fetch it without separate approval. Record its actual `/data/...` path.

```sh
python3 tools/run_handoff.py prepare \
  --job path/to/generated-job.json --configmap path/to/configmap.json \
  --brief path/to/brief.json --data-info path/to/exported-data_info.json \
  --data-path /data/campaign/n64/data/data_info.json --out local/run-handoffs
python3 tools/run_handoff.py validate local/run-handoffs/rh-RETURNED_ID
python3 tools/run_handoff.py launch local/run-handoffs/rh-RETURNED_ID
```

The final command is strictly offline: no kubectl, login or submission. Missing fields,
unsafe archive paths, links, credential filenames, recognized credential signatures, inline
credential environment values, altered checksums and generated-file changes fail closed.
These checks are not a universal secret detector. Review the explicit payload and brief;
never include credentials in code/config files or use the tool on an unreviewed whole home directory.

Only after a cleared scientific gate and explicit current launch authorization:

```sh
python3 tools/run_handoff.py launch local/run-handoffs/rh-RETURNED_ID \
  --submit --approval-ref 'EXACT brief approval_ref'
```

This runs existing `nrp_doctor lint` (warnings allowed; errors block), checks cluster object
identity, then uses `create`, never apply/replace/delete. An existing matching Job and its
provenance objects are reused; conflicts stop without adopting them. If the Job has disappeared
after TTL cleanup/deletion, a surviving handoff ConfigMap or local submission intent/receipt
blocks resubmission under that identity. The handoff ConfigMap has no Job owner reference or TTL.
An intent event is durably written before any create. Interrupted/ambiguous submissions also
fail closed: inspect manually, and use a separately approved new Job name and new run identity
for an intentional new attempt. Never delete provenance markers to force a replay. If an operator
removes both all local history and the remote marker, no local tool can prove that history;
retain those records. Repeating preparation is content-idempotent. A same-ID
submission lock prevents local concurrent submits; after a crash, inspect cluster state before
manually removing a stale `.submit.lock`. Kubernetes object names provide the final create-race
guard. Partial failure may leave immutable ConfigMaps; no automatic cleanup or relaunch occurs.
The tool uses the caller's existing kubeconfig/context. It neither creates nor copies credentials.

The Claude Bash hook rejects direct JSON Job submissions (including Lists), YAML Job declarations
and stdin manifests; it keeps the existing ConfigMap lint route. This is not admission control
and cannot enforce unrelated shells, clients or complex shell indirection.

## Storage, monitoring and status

The init container checks the live `data_info.json` hash, validates the exact payload and
copies `record.json`, `source.tar.gz`, `job-original.json`, and `data_info.json` into
the versioned validator `run_handoff.py` into `/data/run-handoffs/<run-id>` via a temporary
sibling directory and rename. It never overwrites
a conflicting record. It uses no Kubernetes token or API calls. Existing training code still
owns full array validation, checkpoint certification and runtime metrics. This handoff only
checks the data identity file, not every dataset byte on each startup.

Job and pod annotations carry `bnjettag.io/handoff-sha256`, `handoff-configmap`, and
`handoff-path`; the `bnjettag.io/run-id` label identifies the immutable record. Full original
Job command/resources, all payload file hashes, exact configs and data hashes are in the record.
`rh-...` identifies a launch/pack; the brief maps its arm names and W&B output IDs. It does
not rename or merge existing W&B runs. A deliberate new attempt needs a reviewed distinct Job
name/brief; replaying an unchanged record never creates a second named Job.

A consumer must compare the record SHA-256 against the Job annotation and run ID, then verify
the payload and inventory before analysis. Keep the exact version of `run_handoff.py` from
the immutable handoff ConfigMap: validation binds its SHA-256. Do not execute archived training
code merely to inspect it. If context is absent, damaged or inconsistent, report that explicitly.
Legacy Jobs are not silently annotated or retroactively declared reproducible.

For an approved local export or PVC-mounted reader, use the saved validator without running
any training code:

```sh
python3 /path/to/exported-run/run_handoff.py inspect /path/to/exported-run \
  --expected-sha FULL_HASH_FROM_JOB_ANNOTATION --run-id RUN_ID_FROM_JOB_LABEL
```

Launcher events are append-only JSON files under the local handoff's `events/`; `status.json`
is an atomic derived view. Future monitor events belong in their own namespace/directory,
not inside `record.json`. No daemon, CronJob, alert subscription or background poller is installed.
PVC access is independent of Job TTL; access from a PC still requires an approved mounted
workload or a reviewed export route. This implementation does not solve that transport by
deploying a hidden reader pod. No Mac connection or synchronization is required for running jobs.
