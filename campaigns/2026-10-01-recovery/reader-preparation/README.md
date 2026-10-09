# Read-only evidence reader preparation

Status: authorized and submitted once; 253 evidence files were transferred with hashes
verified and exported locally. The reader exited zero and the Job completed;
independent transport and metadata/log reviews are complete in this record. [RUN.md](RUN.md)
records the actual approval, object UIDs and current observations. The exact submitted
package and hashes are recorded in `ACTIVE.json`. Earlier `frozen/` directories are immutable superseded preparation drafts;
they are not launch choices. This directory does not modify the training launcher,
global hooks, historical bundles or publication repository.

The finite reader recovers only the recovery manifest's 17 run directories, three
cache identity records, matching arm logs, selected checkpoint generations, five b5
epoch-500 snapshot directories and two named b5 readout JSON files. It never reads
dataset array payloads or loads models, optimizer arrays or training code.
Checkpoint/optimizer files are opaque allowlisted bytes. An actual cache metadata
match does not rehash its arrays or establish historical immutable launch context.

## Authorized recovery-only exception

`docs/infrastructure/run-handoff.md` says: “Do not fabricate it or create a pod just
to fetch it without separate approval.” Its current training adapter requires an
already exported cache identity and adds a provenance init container that writes to
`kai-data`. Those conditions cannot bootstrap this missing evidence through a
read-only PVC mount. There is no compliant existing read-only recovery adapter.

The approved exception covers only the exact hash-bound package in `ACTIVE.json`:

- Create its one immutable ConfigMap and one finite CPU Job in `cms-ml`, using existing
  PVC `kai-data`, UID `c5be55ec-3362-40a9-b283-f8d0750dcf95`, mounted read-only.
- Use this reviewed campaign-local `launch.py` adapter in place of the training
  handoff **for this recovery only**, without its cache prerequisite or writable
  provenance init. Record the exact approval separately; pending scientific gates
  and historical briefs remain unchanged.
- Read the new objects' status/logs, start one `kubectl port-forward` bound to local
  `127.0.0.1`, and receive the allowlisted evidence into a fresh private local directory.

The Job requests 100m CPU and 256 MiB RAM, limits 1 CPU and 512 MiB RAM, and requests
no GPU. It uses the verified digest-pinned official Python image in `image-receipt.json`,
one read-only code mount and one bounded ephemeral scratch volume. Token automount is
off, the container runs without root or added capabilities, and no `fsGroup` or PVC
permission change is used. There is no Service, Deployment, service-account creation,
RBAC change, init container, training, readout computation or persistent monitor.
Backoff is zero. Reader lifetime is 30 minutes; Job deadline is 35 minutes; terminal
Job retention is one hour. The reader exits early after successful transfer.

Kai approved the single recovery workload and adapter under reference
`Kai-20261001-one-recovery-workload`; the dated approval record is linked in [RUN.md](RUN.md).
The reviewed CPU-only package was retained. Frozen pending annotations describe its
preparation state and remain unchanged; the separate approval and submission records
establish actual action-time authorization. The adapter's default invocation is offline.
`--submit` also requires an approval record naming both exceptions, exact operations,
the preparation hash and Kai's actual authorization reference. It checks the named
`nautilus` context and live PVC UID, refuses existing objects, and records a durable
intent before `create`. A prior intent blocks replay. Partial creates are retained;
there is no delete, apply, replace, automatic retry or relaunch. If an approval guard
rejects the adapter, stop and report the rejection; do not alter the command or hook
to get around it. Other training-launch requirements remain in force.

## Local validation and authorized operation sequence

`prepare.py` creates a new content-addressed directory with mode-0444 payloads,
`BUNDLE.json`, full factual brief, Job, ConfigMap and `preparation.json`. Read-only file
mode is a workflow guard; every use rechecks the hashes. No secret or credential is
included. The preparation hash binds code, scope, image receipt, PVC observation,
brief and both Kubernetes manifests.

After critical PASS and the explicit exception, the operator records the actual
authorization in a new private JSON file with `approval_status: approved` and these fields: `approval_ref`,
`user_authorization_reference`, `authorized_at_utc`, `preparation_sha256`,
`context: nautilus`, `namespace: cms-ml`; `exceptions` must be exactly
`read_only_bootstrap_without_training_handoff_init` and
`reviewed_campaign_recovery_adapter`; `operations` must be exactly
`create_immutable_reader_configmap`, `create_finite_readonly_reader_job`,
`loopback_port_forward`, `read_reader_status_logs` and `download_allowlisted_evidence`.
The timestamp must parse as explicit UTC; pending or placeholder references are
rejected. These are operator-record guards, not cryptographic proof of approval.
No example approval record is pre-filled as though approval existed.

1. Run the frozen `launch.py` with `--preparation` pointing to the exact
   `frozen/<bundle-sha>/preparation.json` file, not its directory,
   `--expected-preparation-sha256` and `--doctor nrp-lab/nrp_doctor.py`. This performs
   only local package validation and existing offline CPU-shape lint.
2. For the authorized action, add `--submit`, `--approval-record`, exact
   `--approval-ref`, and `--events reader-preparation/submissions/<preparation-sha>`
   using the full campaign path. This is the sole reviewed create adapter.
3. Capture raw JSON for this exact Job, immutable ConfigMap, current `kai-data` PVC,
   and its running Pod. Verify Job UID / Pod owner UID and read the `reader_ready`
   log. Raw responses for this new controlled workload remain private.
4. Forward only that verified Pod: `kubectl --context nautilus -n cms-ml port-forward
   --address 127.0.0.1 pod/<verified-pod-name> 18765:8765`. The Pod listener itself
   binds `127.0.0.1`; no Service or pod-IP listener is created.
5. Run frozen `receive.py` with `--preparation` pointing to the same
   `preparation.json` file,
   `--expected-preparation-sha256`, `--job-json`, `--pod-json`, `--pvc-json`,
   `--configmap-json`, `--port 18765` and a fresh `--out` path. It validates captured
   object UIDs/ownership, exact image/command/mount/security/resource settings and
   immutable code bytes. It accepts only a fixed manifest endpoint and content-hash
   blobs; no client-provided filesystem path reaches the reader.
6. Feed the verified mirror to the existing exporter:
   `python3 campaigns/2026-10-01-recovery/recover.py export-pvc
   --pvc-root <transfer-out>/pvc --out <new-export-directory> --checkpoints`.
   Keep both transport and exporter receipts: logs are already sanitized derivatives,
   so the original PVC log hash comes from the transport receipt, not the mirror.
7. Collect terminal reader status/logs, end the local port-forward, and review the
   evidence. A missing generation, mismatch or incomplete read remains unresolved;
   no resume or scientific gate follows automatically.

## Integrity boundaries and limits

Every path component is opened relative to the PVC directory descriptor with
`O_NOFOLLOW`; traversal, symlinks and nonregular final objects are refused. The exact
accepted `latest.json` bytes select a bounded generation name. Generation directories
and each file are checked for changes, without claiming a cross-directory atomic
snapshot. Recognized credential-bearing JSON is refused; logs are sanitized using
the current exporter's pure filters. These are limited heuristics, not universal
secret detection. Source and stored hashes remain distinct.

The reader accounts every byte read, including rejected sources, against 2 GiB.
It allows at most 640 files, 128 matching logs per log directory, 2 MiB per JSON,
16 MiB per log and 128 MiB per checkpoint file. Limit exhaustion writes an incomplete
receipt. Scratch is bounded to 2304 MiB with a 3 GiB ephemeral-storage container limit.
Permission denial or a source exceeding the reviewed bounds stays explicit; the
reader never changes permissions or increases limits automatically.

The receiver validates hashes and lengths before installing each local file, refuses
an existing output directory, and records partial transfer failures. It cannot
cryptographically attest runtime execution: the operational identity rests on the
captured Kubernetes objects, immutable ConfigMap and authorized port-forward to their
UID-bound Pod. The server is reachable only within the Pod's loopback namespace or
through a separately authorized Kubernetes forwarding/exec route; it supplies no
Kubernetes credential. Existing cluster RBAC is unchanged.

Successful transport provides evidence for later review. It cannot restore missing
historical pod logs, fabricate original launch records, certify a checkpoint, clear
Chang K1, select option (c)/(d), or substitute earlier hardware results for successful
synthesis of current constrained candidates.
