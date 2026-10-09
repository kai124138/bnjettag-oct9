# Recovery collector remediation — 2026-10-01

Status: fixes implemented; independent re-review pending. No live collector run,
remote access, training, synthesis or historical-record change occurred.

| Review finding | Change | Synthetic evidence |
| --- | --- | --- |
| A1: ordinary credential forms survive redaction | Authorization scheme/value redaction precedes generic rules. Parsed JSON is sanitized recursively before serialization; recognized credential-bearing JSON is refused for byte-for-byte export. Source and derivative hashes remain. | Bearer/Basic headers, quoted/nested API keys and Kubernetes status messages contain no fixture tokens after sanitization and remain valid serialized JSON. A credential-bearing pointer is refused and never followed. |
| A2: failed Job read downgrades UID binding | Job responses require a valid listing and nonempty observed UID. Failed/malformed/UID-less reads skip that Job's pod/log requests. Successfully observed absence is a different receipt state and also skips logs; no implicit orphan fallback exists. | Failed process, malformed JSON/object, missing UID and empty listing issue no pod/log calls. Different owner UID yields no logs; positive UID match permits current/previous logs. |
| A3: pointer and generation can disagree | Copy the exact bytes that passed JSON/credential checks; select the generation only from the accepted exported pointer. Record pointer SHA and generation. Compare source file/directory identity before and after reads/copies. Retain missing/changed state and write a partial receipt in `finally` on interruption. | Advancing `latest.json` still exports its captured earlier generation. Removing the pointer/old generation cannot substitute the new one. Source modification/deletion is detected; interrupted export retains a receipt. |
| B1: terminal/source/preprocessing artifacts omitted | Add `source_manifest.json`, `input_std.json`, `COMPLETE.json`, `TRAINING_COMPLETE.json`, `VERIFIED_COMPLETE.json`, `screen_result.json` to the exact seventeen run paths. | Temporary fixture verifies all six records copy byte-for-byte with per-file receipts; missing records remain explicit. |

Validation command:

```sh
python3 -m unittest discover -s campaigns/2026-10-01-recovery -p 'test_recover.py' -v
```

Result: **21 tests passed**. Tests use local historical manifests, temporary fabricated
files and mocked subprocesses; no synthetic credential value is printed. No scientific
metric or model array is evaluated.

Limits retained: redaction is not a universal secret detector; filesystem path checks
do not protect against a concurrent adversary; source-stability checks are observations,
not an atomic snapshot. Raw export records require review before checkpoint use or
publication. Unavailable Job UIDs deliberately prevent orphan-log recovery in this tool.

Chang K1 **has fired**. Its (c)/(d) decision and complete b5 readout remain pending.
The review's closing shorthand does not change that scientific status. Terminal markers
and engineering fixes provide no new launch or resume authority.
