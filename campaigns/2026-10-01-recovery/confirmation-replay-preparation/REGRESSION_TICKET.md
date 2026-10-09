# Confirmation diagnostic startup failure — 1 October 2026

Status: open; engineering fix and review required before a distinct new attempt.
This is the cause of the new diagnostic's startup failure, **not** a diagnosis of
historical confirmation metric failures.

The immutable handoff init passed. In final record `rh-a15040ccc47283093ee9c734`,
[probe.py line93](probe.py:93) calls `out.mkdir(exist_ok=False)` for
`/data/confirmation-20260923/diagnostics/replay-a02s3-20261001-r1`.
The `diagnostics` parent did not exist, so Python raised `FileNotFoundError` before
input verification, worker execution, model loading or inference. The main container
exited1 with zero restarts. Job UID `e78483f4-b74c-4fed-b7fa-e4b771e762a3`
failed at06:48:41Z; owned Pod UID `ea50754f-c194-4a9f-9b4f-eeb12a4628bd`.
[The complete log receipt](../captures/confirmation-replay-20261001T0645Z/final-logs/receipt.json)
and [terminal objects](../captures/confirmation-replay-20261001T0645Z/observation-02/receipt.json)
are retained. The reviewed probe hash is
`83f4392833c418627672f0da393c3c9484ade7c4c2876bff0b4c316d78d0dcb1`.

The eight synthetic tests covered inference and transport helpers, but did not
exercise the top-level startup with an absent output parent. Their pass did not
establish a successful end-to-end startup. No result/export envelope was produced
because creation preceded the protected execution block; absence must stay explicit.

The smallest required change is to create the exact authorized diagnostic parent
safely, while retaining exclusive creation of a new output leaf. Preserve source
nonmutation, path restrictions, refusal to overwrite an existing output, all inference
settings and the 30-minute one-GPU bound. Add a meaningful top-level synthetic startup
case with the parent absent and an existing-leaf refusal case. Check how startup
failures are recorded when the durable output cannot yet be created.

After implementation and independent review, prepare a new diagnostic envelope,
Job/output identity and immutable record, validate the final files and perform
fresh action-time lint. Keep this failed record and all its evidence. No automatic
retry, tolerance change, training or resume is authorized by this ticket.

Engineering and independent review agents reached the service usage limit before
this failure was observed. The fix has not been implemented or independently
reviewed. The operator continues evidence collection; this dependency remains open.

## Fix, 2 October 2026

`probe.py` now calls `make_output`, which creates only the immediate `diagnostics`
parent, refuses a symlinked or missing parent chain, and keeps `mkdir(exist_ok=False)`
on the leaf. Any failure before `result.json` can be written, including the handoff
identity check, prints `CONFIRMATION_REPLAY_STARTUP_FAILED <type>: <message>` and exits 1.
Three new top-level tests cover absent parent, existing leaf and symlinked parent or
wrong handoff; 11 of 11 pass ([log](tests-startup-fix.log)). The failed record's probe
bytes remain inside its handoff ConfigMap. Independent review, a new `-r2` Job/output
identity, a new envelope and action-time lint remain pending; nothing was launched.
`prepare.py` now names the next attempt `kai-confirm1001-replay-a02s3-r2` with a matching
`-r2` output; the r1 objects stay. A startup failure leaves an empty leaf and no BNJ export,
so `receive.py` will reject the log; capture that pod log by hand.
Independent review (opus, 2 October): PASS.

Check: top-level absent-parent/existing-leaf startup tests added and passing; review pending.
