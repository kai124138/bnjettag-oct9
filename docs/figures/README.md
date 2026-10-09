---
title: docs/figures
status: current
date: 2026-09-26
---

# docs/figures

Schematics for the lab repo. The `.tex` is the artifact of record; `.svg`/`.png` are generated.

```
./render.sh <name>      # <name>.tex -> <name>.svg + <name>.png, locally (tectonic + PyMuPDF)
```

Each `.tex` is a standalone document (`\documentclass[tikz,border=4pt]{standalone}`), so it
compiles anywhere with a TeX engine. The upmath MCP server is still fine for equations and
small pictures, but it sends every snippet to i.upmath.me over a length-limited GET URL and
returns HTTP 400 whenever a TikZ library is passed in `packages` (checked 2026-09-26 with a
one-node picture and `positioning`); anything that needs a library renders here instead.

| figure | shows |
| --- | --- |
| `harness-layout` | the proposed shape of the research harness (2026-09-26 review) |

## style/

Candidate `.mplstyle` files and the contact sheet that compares them on one verified panel.

```
uv run --with matplotlib,pandas,pillow python style/contact_sheet.py   # -> style/contact-sheet-auc.png
```

`bnjettag-a-incumbent.mplstyle` is the rcParams block from the publication tree's
`code/analysis/build_figures.py` verbatim, plus that script's per-call defaults lifted into
rc keys. The chosen style is promoted to
`docs/style/bnjettag.mplstyle` once picked (see `SYSTEM.md` §5; the journal variant B was picked on 2026-09-26).
