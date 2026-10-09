# Results notebook, 2026-09-29

`results_summary.ipynb` rebuilds the project's results summary from data already saved in
this repository. It scores the saved prediction arrays again, parses the synthesis reports
and the saved pod logs again, and types in no number by hand. It is laid out for screenshots
onto slides, and every figure is also written to `figures/` as a 300 dpi PNG and an SVG. The
figures use the talk variant of the house style (`docs/figures/style/bnjettag-c-poster.mplstyle`)
and are sized so that their smallest text stays at 12 pt or more when fitted to a 16:9 slide
under a title.

## Rerun

From the repository root:

```
.venv-hgq2/bin/python -m nbconvert --to notebook --execute --inplace messages/2026-09-29-results-notebook/results_summary.ipynb
```

The run takes well under a minute on the laptop. The usual `jupyter nbconvert …` fails here:
there is no `jupyter` on the PATH, and the console scripts in `.venv-hgq2/bin/` still point at
the interpreter of an older checkout (`bnjettag-lab/research/.venv-hgq2`). Calling nbconvert
as a module goes through the working interpreter. The default `python3` on the PATH
(`.venv-chang`) has no nbformat, so the command names the `.venv-hgq2` interpreter
explicitly. Run All in Jupyter gives the same result when the kernel is `.venv-hgq2`.

## What is here

The notebook holds the prose and the tables. `nbhelpers.py` holds every loader, recompute
and figure function, and it is the file `tools/plot_check.py` checks. `figures/` is
rewritten on each run. The last cell of the notebook lists every file the run read, with its
size and modification time.

## How to read it

Each number names its metric, its split and n, and carries one of four statuses. *Verified*
means recomputed here from saved arrays. *Reported* means quoted from a saved evaluation
record whose arrays are not on this machine. *Telemetry* comes from logs of runs still in
progress and is not a result. *Archived* is Round 14, the pre-conference study without an
EBOP target, kept in its own labelled sections. Held-out (ROC-test) and validation numbers
never share a column.

## Known limits

The best reported number under the N = 8 target, the confirmation campaign's A02 checkpoint,
is quoted from a JSON record and not recomputed, because its prediction arrays were never
copied here. No current-era model has been synthesized, so the FPGA section shows Round 14
only. The pilot and benchmark sections read the newest saved log copies, so a rerun after new
copies land will show later epochs and more benchmark phases. Section 8 of the notebook lists
what it leaves out for lack of a saved, checkable source, and two inconsistencies between the
ablation records that it reports without resolving.
