# Model artifacts

This directory holds trained checkpoints and the local cache the export pipeline downloads
into. Everything in it is **gitignored** except this file, so a fresh clone starts empty.

## Where Round-14 checkpoints actually live

They are **not in this repository.** All 60 Round-14 checkpoints are versioned W&B
artifacts — `model-<leaf>` in project `BNJetTagAug`, entity `kayamaguchi-uc-san-diego`. W&B
is the durability contract; see `docs/infrastructure/wandb-layout.md`.

`code/hgq2/convert_final.py` fetches what it needs on demand and caches it under

```
bnjettag/models/cache/
```

which is created on first use. Deleting the cache is safe — the next export re-downloads.

## Earlier checkpoints

The trained checkpoints from every round before Round 14 — the FINAL campaign's nine
`large` articles, plus r5, r8, r10, r11, the Chang reproduction, and the early KD run,
about 1.5 GB in total — moved to

```
_attic/pre-r14/models/
```

on 2026-08-13. They were never in git (this directory has always been gitignored), so that
move is a disk operation only and `_attic/RESTORE.sh` reverses it.
