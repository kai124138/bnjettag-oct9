"""Constructive v5: is the section-18 label threshold T reproducible? Design arithmetic, not a result.

Runs ../screen_null.py unchanged except (a) the RNG seed and (b) optionally a minimum size for the
conditional set in the threshold rule (the rule as written counts any non-empty set). Prints T per
family for each (seed, min-set) pair.
Usage: uv run --with numpy,scipy python constructive_v5_tstab.py   (about 20 s per run, 12 runs)
"""
import pathlib, re, subprocess, sys, tempfile
SRC = (pathlib.Path(__file__).resolve().parent.parent / "screen_null.py").read_text()
OLD = "if (si <= T).sum() > 0 and h[si <= T].mean() < 0.5]"
assert OLD in SRC and "default_rng(20260927)" in SRC
for minset in (1, 200):
    for seed in (20260927, 1, 2, 3, 4, 5):
        code = SRC.replace("default_rng(20260927)", f"default_rng({seed})").replace(
            OLD, f"if (si <= T).sum() >= {minset} and h[si <= T].mean() < 0.5]")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
        out = subprocess.run([sys.executable, f.name], capture_output=True, text=True).stdout
        ts = re.findall(r"(5M|350k) label threshold T = ([0-9.]+) pt", out)
        print(f"min set {minset:3d}, seed {seed:>8}: " + ", ".join(f"{a} T {b}" for a, b in ts))
