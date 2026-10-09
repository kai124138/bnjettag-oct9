# Hardware source diagnosis — 2026-10-01

R4 reached a **Vitis compiler crash before RTL generation**. Its root cause is not
established. The unsupported array-partition Tcl directive is a separate observed
compatibility problem, not a demonstrated explanation for the crash. No compiler,
synthesis, model evaluation or remote command was run for this diagnosis.

Paths below are relative to `campaigns/2026-09-17-synthesis-r4-gradual/` unless stated.

## Primary evidence

| Evidence | What it establishes |
| --- | --- |
| `hls-attempt1.log:2–12` | Vitis HLS 2023.2, SW build 4023990, on Mulder, September 17, 2026. |
| `hls-attempt1.log:30–44`; `export/hls_prj_rf1/build_prj.tcl:149` | `ERROR: [HLS 200-642] The 'config_array_partition -maximum_size' command is not supported.` The generated Tcl wraps this command in `catch`, and execution continues through target/clock setup to `csynth_design`. Removing that message has not been shown to cure the later failure. |
| `hls-attempt1.log:83–88` | A TOP-directive warning precedes `ERROR: [HLS 200-1715] Encountered problem during source synthesis` and `Pre-synthesis failed.` This warning also lacks an isolated causal test. |
| `hls-frontend-diagnostics.log:5–6,19–29,68–72` | Stack frames include `llvm::collectPragmaObjects` and `DisaggregatePreprocess::runOnModule`; the active pass is `Disaggregation preprocessing`. The compiler reports `Segmentation fault (core dumped)` and the diagnostic records clang child exit 254. The vendor binary path contains `clang-3.9-csynth`; its banner reports clang 7.0.0. |
| `README.md:136`; `export/verification.json:116–119`; `export/hls_prj_rf1/firmware/myproject.cpp:7–16` | Three failed HLS attempts are reported. Splitting interface pragmas and explicit C linkage did not resolve them. Those two changes are already present in the saved generated source; the export script does not automatically reproduce them. |
| `remote-evidence/license_probe/probe.log:21` | A historical VU13P Vivado device/Synthesis license probe failed with `Common 17-345`. This is a separate Vivado-stage issue, not the HLS frontend crash. The xczu7ev probe passed historically; neither probe establishes current licensing. |

The shorthand in `campaigns/2026-09-26-delta/inventory/tried-already.md:174` calls
the unsupported directive the failure mechanism. The raw log supports the narrower
statement above: caught directive incompatibility followed by a compiler crash.
No historical inventory was rewritten during this audit.

The R4 export targeted `xcvu13p-flga2577-2-e`, 2.5 ns, reuse factor 1, Latency,
`io_parallel`; its contemplated Vivado OOC target was the separately labelled
`xczu7ev-ffvc1156-2-e` proxy. Export metadata records hls4ml 1.3.0, HGQ2 0.1.9,
Keras 3.15.0, TensorFlow 2.21.0 and quantizers 1.2.2. Historical local/Linux
export-to-C fidelity records cover 4,096 internal-validation jets. They establish
neither HLS success nor current-candidate fidelity, II, resources or timing.

## Attempt identity is incomplete locally

The source checkpoint bytes presently hash to
`212c0cf2e41727b5b65548517887b2afedb7806fbc7b38da39422c1c991d72e6`, matching
`source/model_best.keras`, `export/verification.json` and the saved remote status.
However, the attempts cannot be collapsed into one provenance record:

- `remote-evidence/status.json:74–77,112` ends at **17:57:15Z**, with archive
  `4aac36b59641a12ee2abc4f271ff06949dae099406daf5b19696ee0e7f085e93`
  and verification hash `c64181aa…`.
- The current `export/verification.json` hashes to
  `99b32a6a5a2c3a87ac3562652123c5456f8efaa848144f50c96352f32841e668`
  and names project archive `6c411b11…` at line 116.
- `README.md:136` describes a later supervisor ending at **18:05:56Z**. Its final
  status and all three attempts' source/log associations are not present locally.

Both named project archives are absent locally, including the documented
`export/hls_prj_rf1.tar.gz`. Also absent are the raw remote `logs/hls.log`, the
failing LLVM input `a.g.ld.5.gdce.bc`, `kernel.internal.xml`, `top-io-fe.xml`, and
the associated `.clang.reflow.diag.xml/.yml` under the failed solution's
`.autopilot/db`. The local `remote-evidence/attempts/` contains only the earlier
archive-metadata rejection status. These are recovery needs, not proof the remote
artifacts have disappeared. No current-candidate csynth report is established here.

## Minimal next diagnostics: reads only

The following local commands recheck the evidence without regenerating it:

```sh
sha256sum campaigns/2026-09-17-synthesis-r4-gradual/source/model_best.keras campaigns/2026-09-17-synthesis-r4-gradual/export/verification.json
rg -n '200-642|200-1715|TOP directive|csynth_design' campaigns/2026-09-17-synthesis-r4-gradual/hls-attempt1.log
rg -n 'collectPragmaObjects|Disaggregation preprocessing|Segmentation fault|code 254' campaigns/2026-09-17-synthesis-r4-gradual/hls-frontend-diagnostics.log
```

After the existing approved Mulder SSH route is available, this inspects only the
known work directory and current resource/tool-file state. It does not source
setup scripts, request licenses, invoke vendor executables, or start work:

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes kayamaguchi@mulder.t2.ucsd.edu 'bash -s' <<'REMOTE'
set -eu
R4_WORKROOT=/home/users/kayamaguchi/bnjet_ebops_r4_20260917
df -h / /tmp "$R4_WORKROOT"
df -i / /tmp "$R4_WORKROOT"
free -m
ps -eo pid,pcpu,rss,etime,comm --sort=-pcpu | head -n 20
stat /data/software/xilinx/Vitis/2023.2/settings64.sh /data/software/xilinx/Vitis_HLS/2023.2/bin/vitis_hls /data/software/xilinx/Vitis_HLS/2023.2/lnx64/tools/clang-3.9-csynth/bin/clang
python3 - "$R4_WORKROOT" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = root / 'status.json'
if status.is_file():
    obj = json.loads(status.read_text())
    print(json.dumps({k: obj.get(k) for k in ('phase','started_utc','completed_utc','input_archive_sha256','verification_sha256','checkpoint_sha256')}, sort_keys=True))
else:
    print('MISSING status.json')
patterns = ('attempts/**/status.json', 'attempts/**/*.tar.gz', 'attempts/**/hls*.log',
            'logs/hls.log', '*.tar.gz', 'export/*.tar.gz',
            '**/.autopilot/db/a.g.ld.5.gdce.bc', '**/.autopilot/db/kernel.internal.xml',
            '**/.autopilot/db/top-io-fe.xml', '**/.autopilot/db/*.clang.reflow.diag.*')
for pattern in patterns:
    paths = sorted(p for p in root.glob(pattern) if p.is_file() and not p.is_symlink())
    if not paths:
        print('MISSING', pattern)
    for path in paths:
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
        print(path.relative_to(root), path.stat().st_size, digest.hexdigest())
PY
REMOTE
```

Recover the identified attempt records and compiler inputs through that authorized
route into a new evidence directory, preserving checksums and original paths.
Do not overwrite R4 archives or rerun its supervisor to fill missing evidence.

## What can be prepared locally, and what requires Mulder

Local work can reconcile archive/verification/source hashes, compare each generated
Tcl/top-function diff, and prepare a reviewed version-specific directive change.
The existing evidence supports investigating the disaggregation/pragma path; it
does not identify a particular pragma or model layer as the cause. A compiler
reproducer or controlled one-change comparison requires the matching Mulder
toolchain, fresh separately recorded diagnostic output, and explicit execution
scope. Repeating the two already failed interface/linkage edits is not a new test.

Current-candidate hardware work remains gated on its own selected certified
checkpoint SHA from VERIFY, frozen converter/config/runtime, sample identity,
learned-width/binary checks, export-to-checkpoint fidelity and fresh C simulation.
See `SCIENTIFIC_GATES.md:70` and `docs/conventions/fpga-synthesis.md`. R4's artifacts
cannot satisfy these requirements for A02/A11, Chang, Delta, or a merged pipeline.

Only after those gates should a fresh authorized synthesis chain use the full
Vitis 2023.2 setup, isolated TMPDIR, and the established serialized limits:
64 GiB process-group RSS, six hours HLS, eight hours Vivado and 50 GiB directory
growth. Recover raw report XML/RPT and parsed JSON; report clock, reuse, measured
top-level II, latency and per-layer/whole-model DSP use. RF=1 does not prove II=1.
Vivado license availability must be checked for its actual target before that
stage, and proxy-device results cannot establish VU13P fit or timing closure.
