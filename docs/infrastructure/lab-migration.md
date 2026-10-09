# Lab migration to the home PC

## Authority and preserved baseline

Canonical writable workspace: `/home/kaimoe/lab/bnjettag` in existing Ubuntu WSL.
Open that folder through the independently configured VS Code Remote SSH connection.
Windows path: `\\wsl.localhost\Ubuntu\home\kaimoe\lab\bnjettag`.
Do not keep editing the old Mac tree after switching. Preserve it as a recovery source until
all selected lab files are verified; do not delete it as part of migration.

The initial import is only 12,842 reviewed text/code/config files, verified against
`TRANSFER_MANIFEST.json`. The untouched baseline and Library archive are at
`/home/kaimoe/bnjettag-pc-20260930-zst01u_o`. Its archive SHA-256 is
`cde07983587857f2ecd3bb6f3c31ff1625ceb8d6bc1f3a5db726ffb402117120`.
No datasets, model binaries, Git history, credentials or quarantined files came with it.
The PC tools do not access the Mac or unrelated personal directories.

## Missing artifact inventory: known references, not verified Mac contents

The reviewed `DATASET.md` describes a validation archive and 26 HDF5 files under `data/val`.
Those are historical references, not proof of current presence, size or integrity on the Mac.
Other likely missing classes are `.npy/.npz` arrays, Keras/ONNX/PyTorch checkpoints,
ROC result arrays, generated PDF/PNG figures and synthesis binaries. Only an inventory run
by Kai on the Mac can establish which files remain. Review lab subdirectories before choosing
them; don't inventory the whole home directory.

Existing NRP locations include PVC `kai-data`, `/data/chang-n64-20260926/pilot-b/runs`,
its epoch-0500 snapshots, `/data/delta-20260927`, and W&B project references in campaign records.
Do not copy large artifacts merely because the code references them. First record their
authoritative location, run/seed, artifact version and available SHA-256. b3 certification
records are already imported; live checkpoint bytes have not been freshly rehashed. All
relevant pilot pods are completed, so a new PVC reader workload would require separate approval.
W&B and PVC references do not prove every excluded local artifact has a remote equivalent.

## User-run Mac export

Copy just `tools/lab_transfer.py` and `tools/run_handoff.py` from the canonical lab to a
temporary helper directory on the Mac using the already configured remote connection.
The helper has no networking, remote execution, credential reads or source deletion commands.
It reads only the lab root and explicitly selected relative paths.

Run these on the Mac yourself, replacing `RELATIVE_LAB_DIRECTORY` with an existing lab-only
directory you selected. Add repeated `--include` arguments for other lab directories:

```sh
python3 /path/to/helpers/lab_transfer.py inventory \
  --root /Users/kaiyamaguchi/Desktop/bnjettag \
  --include RELATIVE_LAB_DIRECTORY \
  --out /path/to/new/lab-inventory.json
```

Inventory records path, byte size and SHA-256; it excludes symlinks, credential paths,
`.env*`, SSH/kube/AWS metadata, recognized secrets and opaque archives/unsupported types.
The root filename `LAB_TRANSFER_MANIFEST.json` (case-insensitive) is reserved on export and
import so provenance metadata cannot overwrite a selected user file.
Review `files` and `excluded`. Archive files are deliberately not unpacked or silently copied:
prefer selected HDF5/array files over an opaque tarball. Unsupported items need explicit
review before expanding the allowlist. A filename/content scanner cannot guarantee every
arbitrary lab file is secret-free; the user's selection and review are still required.

Create `selection.json` as a JSON list of the exact reviewed relative paths from `files`.
Select only missing files that should live on the PC; existing verified files need no resend.

```sh
python3 /path/to/helpers/lab_transfer.py pack \
  --root /Users/kaiyamaguchi/Desktop/bnjettag \
  --inventory /path/to/new/lab-inventory.json \
  --selection /path/to/new/selection.json \
  --out /path/to/new/lab-selected.tar.gz
```

Files changed since inventory block packaging. The helper verifies the resulting archive and
prints its SHA-256. Retain that value independently. No existing output archive is overwritten.
For large data, make several selections/archives rather than retrying one giant export.

Transfer only these selected archives and their inventories over the separately approved SSH
connection into a new PC directory such as `~/lab/incoming/2026-09-30/`. Use the established
host-key trust and connection details supplied by the networking task; do not disable host
verification, install keys, or copy Mac configuration directories to make a transfer work.
No new transport or synchronization daemon is provided here.

## Verify on the PC before integration

```sh
python3 ~/lab/bnjettag/tools/lab_transfer.py verify \
  --archive ~/lab/incoming/2026-09-30/lab-selected.tar.gz \
  --sha256 SHA256_PRINTED_ON_MAC \
  --out ~/lab/incoming/2026-09-30/verified-batch-1
```

The destination must not exist. Every path, size and file hash must pass before a verified
directory is published. Nothing is executed. The helper does not merge into the canonical
tree or delete source files. Compare the verified manifest against the canonical tree:
identical files can be skipped; conflicting paths require review, never blind overwrite.
Only after that review should selected missing lab artifacts be copied to their final paths.
Keep the Mac copy until final counts/hashes and representative workflow checks pass.

Git metadata is a separate unresolved migration item. Do not copy `.git` wholesale: local
Git config/remotes/hooks can contain credentials or machine-specific settings. This import is
not a clone and has no verified remote. If history is needed, Kai can review/export a Git
bundle from the Mac in a separately authorized step; first scan its reachable history for
secrets. No new repository/remote is invented by these tools.
