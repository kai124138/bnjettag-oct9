# Arbiter v5: writes sn_m{1,200}_s{seed}.py variants of ../screen_null.py (RNG seed and minimum conditional-set size only).
# Run each with: uv run --with numpy,scipy python sn_m..._s....py ; design arithmetic, not a result.
import pathlib
SRC = pathlib.Path("/Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-27-delta-screen/screen_null.py").read_text()
OLD = "if (si <= T).sum() > 0 and h[si <= T].mean() < 0.5]"
assert OLD in SRC and "default_rng(20260927)" in SRC
for minset in (1, 200):
    for seed in (20260927, 1, 2, 3, 4, 5, 6, 7, 8, 9):
        code = SRC.replace("default_rng(20260927)", f"default_rng({seed})").replace(
            OLD, f"if (si <= T).sum() >= {minset} and h[si <= T].mean() < 0.5]")
        pathlib.Path(f"sn_m{minset}_s{seed}.py").write_text(code)
