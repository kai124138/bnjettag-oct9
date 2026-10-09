#!/usr/bin/env bash
# migrate-resume.sh — finish the 2026-09-26 migration that migrate.sh started.
#
#   tools/migrate-resume.sh plan     # print what remains; touch nothing
#   tools/migrate-resume.sh run      # do it (moves only, nothing deleted)
#
# Why this exists: migrate.sh stopped at its "sessions" step because macOS's filesystem is
# case-insensitive, so `Sessions/` (the old vault folder) and `sessions/` were the same
# directory and `mv` refused to move files onto themselves. Everything up to that step is
# done. This script does the rest, and also moves docs/methodology and docs/conventions,
# which were created after migrate.sh was written. Every step is guarded, so running it
# twice is harmless.
set -euo pipefail
MODE="${1:-plan}"
L="$HOME/Desktop/bnjettag-lab/bnjettag-lab 2"
NEW="$HOME/Desktop/bnjettag"
A="$NEW/archive/2026-09-26-integration"
say() { printf '%s\n' "$*"; }
do_() { if [ "$MODE" = run ]; then "$@"; else say "  would: $*"; fi; }
gmv() { if git -C "$NEW" ls-files --error-unmatch "$1" >/dev/null 2>&1; then do_ git -C "$NEW" mv "$1" "$2"; else do_ mv "$NEW/$1" "$NEW/$2"; fi; }

[ -d "$NEW/.git" ] || { say "$NEW is not the workspace (no .git); refusing"; exit 1; }
do_ mkdir -p "$A"

say "== R1 sessions: case-rename the old vault folder so its name is lowercase"
if [ -d "$NEW/Sessions" ] && ls -d "$NEW"/[S]essions >/dev/null 2>&1; then
  do_ mv "$NEW/Sessions" "$NEW/sessions.tmp"; do_ mv "$NEW/sessions.tmp" "$NEW/sessions"
fi
[ -d "$L/sessions" ] && { for f in "$L"/sessions/*; do [ -e "$f" ] && do_ mv "$f" "$NEW/sessions/"; done; do_ rmdir "$L/sessions"; }

say "== R2 docs/methodology and docs/conventions (added after migrate.sh was written)"
for d in methodology conventions; do [ -d "$L/docs/$d" ] && do_ mv "$L/docs/$d" "$NEW/docs/$d"; done
[ -d "$L/docs" ] && do_ mv "$L/docs" "$A/lab-docs-remainder"

say "== R3 setup.sh and caches -> archive"
[ -e "$L/setup.sh" ] && do_ mv "$L/setup.sh" "$A/setup.sh"
do_ mkdir -p "$A/caches"; for c in .uv-cache .mpl-cache; do [ -e "$L/$c" ] && do_ mv "$L/$c" "$A/caches/"; done

say "== R4 publication clones"
[ -d "$L/publication-engram-20260921" ] && do_ mv "$L/publication-engram-20260921" "$NEW/publication"
do_ mkdir -p "$A/publication-clones"
[ -d "$L/publication" ] && do_ mv "$L/publication" "$A/publication-clones/publication-20260917-20-uncommitted"
for c in publication-status-20260921 publication-status-20260920; do [ -d "$L/$c" ] && do_ mv "$L/$c" "$A/publication-clones/"; done

say "== R5 published repos"
do_ mkdir -p "$NEW/published"
for d in bnjettag_results bnjettag-code bnjettag-methodology; do [ -d "$HOME/Desktop/$d" ] && do_ mv "$HOME/Desktop/$d" "$NEW/published/"; done

say "== R6 lab repo history -> archive; retire the old shell"
[ -d "$L/.git" ] && do_ mv "$L/.git" "$A/lab-repo.git"
[ -e "$L/.gitignore" ] && do_ mv "$L/.gitignore" "$A/lab-repo.gitignore"
[ -L "$L/research" ] && do_ mv "$L/research" "$A/research-symlink-retired"
[ -d "$L" ] && do_ mv "$L" "$A/lab-repo-remainder"
do_ mkdir -p "$A/outer-shell"
[ -d "$HOME/Desktop/bnjettag-lab/local" ] && do_ mv "$HOME/Desktop/bnjettag-lab/local" "$A/outer-shell/local-duplicate-runbook"
if [ "$MODE" = run ]; then printf '# Moved\n\nThe BNJetTag workspace is now one folder: `~/Desktop/bnjettag/` (moved 2026-09-26).\nOpen Claude Code there. This folder is empty on purpose and can be deleted.\n' > "$HOME/Desktop/bnjettag-lab/MOVED.md"; fi

say "== R7 root clutter -> archive; dated notes -> messages/"
do_ mkdir -p "$A/root-clutter"
for f in output.txt terminal-output.txt model-summary.txt practice.py solutions.md Untitled.base Untitled.canvas "files (2)" ByMaurizio.png bitnet-arch.png "Alternate Plans for Department of Physics.pdf"; do
  [ -e "$NEW/$f" ] && gmv "$f" "archive/2026-09-26-integration/root-clutter/$f"; done
for f in STATUS-2026-08-08.md notes-2026-08-13.md; do [ -e "$NEW/$f" ] && gmv "$f" "messages/$f"; done

say "== R8 memory logs: merge research (primary) + lab (secondary); nothing dropped"
if [ -d "$A/research-claude/memory" ] && [ ! -e "$A/research-claude/memory/.merged" ]; then
  for f in experiment-log decisions research-log; do
    do_ python3 "$NEW/tools/merge_logs.py" "$A/research-claude/memory/$f.md" "$NEW/.claude/memory/$f.md" "$NEW/.claude/memory/$f.md"
  done
  for f in newton-reports job-beta-brief job-gamma-brief; do [ -e "$A/research-claude/memory/$f.md" ] && do_ cp -n "$A/research-claude/memory/$f.md" "$NEW/.claude/memory/$f.md"; done
  [ -e "$A/research-claude/memory/newton-reports.md" ] && [ -e "$NEW/.claude/memory/newton-reports.md" ] && do_ python3 "$NEW/tools/merge_logs.py" "$NEW/.claude/memory/newton-reports.md" "$A/research-claude/memory/newton-reports.md" "$NEW/.claude/memory/newton-reports.md"
  do_ cp "$A/research-claude/memory/project-context.md" "$A/root-versions/project-context.md"
  [ "$MODE" = run ] && touch "$A/research-claude/memory/.merged"
fi

say "== R9 .gitignore additions"
if [ "$MODE" = run ]; then grep -q "2026-09-26 unified workspace" "$NEW/.gitignore" || cat >> "$NEW/.gitignore" <<'EOF'

# 2026-09-26 unified workspace
publication/
published/
archive/
sessions/
local/outputs/
local/store/
local/wandb/
campaigns/*/outputs/
.claude/settings.local.json
.ipynb_checkpoints/
*.pyc
EOF
else say "  would: append the unified-workspace block to $NEW/.gitignore"; fi

say "== R10 machine-local paths"
if [ "$MODE" = run ]; then
  python3 - "$NEW" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1]); p = root / ".claude/settings.local.json"
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault("env", {})["CLAUDE_OBSIDIAN_DIR"] = str(root / "sessions")
p.write_text(json.dumps(d, indent=2) + "\n")
PY
  for s in nrp-nautilus vitis-mulder; do ln -sfn "$NEW/.claude/skills/$s" "$HOME/.claude/skills/$s"; done
  M="$HOME/.claude/projects/-Users-kaiyamaguchi-Desktop-bnjettag/memory"; mkdir -p "$M"
  cp -n "$HOME/.claude/projects/-Users-kaiyamaguchi-Desktop-bnjettag-lab/memory/"*.md "$M/" 2>/dev/null || true
  sed -i '' "s#bnjettag-lab 2/#~/Desktop/bnjettag/#g; s#~/Desktop/bnjettag-lab/bnjettag-lab 2#~/Desktop/bnjettag#g" "$M"/*.md 2>/dev/null || true
else say "  would: set CLAUDE_OBSIDIAN_DIR, repoint ~/.claude/skills symlinks, copy project memory to the new project dir"; fi

say "== R11 checks"
if [ "$MODE" = run ]; then
  cd "$NEW"
  python3 tools/index.py init && python3 tools/index.py build
  python3 tools/brief.py | head -6
  (cd docs/style && tectonic -X compile report-template.tex >/dev/null 2>&1 && rm -f report-template.pdf && echo "report template compiles from the new path")
  echo "{\"tool_name\":\"Bash\",\"cwd\":\"$NEW\",\"tool_input\":{\"command\":\"kubectl apply -f nrp-lab/kai-lab.yaml\"}}" | CLAUDE_PROJECT_DIR="$NEW" python3 .claude/hooks/pre-kubectl-lint.py >/dev/null 2>&1 && echo "hook passes the lab manifest from the new path"
  say "== done. Open Claude Code in $NEW, accept the trust dialog, then: git add -A && git commit"
fi
