#!/usr/bin/env bash
# migrate.sh — fold every BNJetTag folder into one workspace at ~/Desktop/bnjettag.
#
#   tools/migrate.sh plan     # print what would move; touch nothing
#   tools/migrate.sh run      # do it (moves only, nothing deleted; same volume, so renames)
#
# Written 2026-09-26. The Claude Code session that designed this was not permitted to run a
# bulk move of ~20 GB of trees, so it is a script for Kai to read and run (or to tell Claude to
# run). Every step is a rename or a copy; the only removals are of directories left empty.
#
# Before:                                        After:
#   ~/Downloads/bnjettag-training-results          ~/Desktop/bnjettag            (the same git repo, moved)
#   ~/Desktop/bnjettag-lab/bnjettag-lab 2          ~/Desktop/bnjettag/{.claude,tools,docs/style,docs/figures,nrp-lab,local,campaigns,sessions,SYSTEM.md,INDEX.md}
#   … /publication-engram-20260921                 ~/Desktop/bnjettag/publication          (GitHub working copy, nested git)
#   … /publication, publication-status-*           ~/Desktop/bnjettag/archive/2026-09-26-integration/publication-clones/
#   ~/Desktop/bnjettag_results, -code, -methodology  ~/Desktop/bnjettag/published/          (nested git repos)
#   ~/Downloads/bnjettag fake, bnjettag-restart,     ~/Desktop/bnjettag-archive/            (10 GB of stale snapshots, kept OUTSIDE the tree)
#     bnjettag-training-results copy, ~/bnjettag-*
#   docs/literature, docs/reports (in the repo)      literature/, messages/                  (git mv, history kept)
set -euo pipefail
MODE="${1:-plan}"
R="$HOME/Downloads/bnjettag-training-results"
L="$HOME/Desktop/bnjettag-lab/bnjettag-lab 2"
NEW="$HOME/Desktop/bnjettag"
BIG="$HOME/Desktop/bnjettag-archive"
A="$NEW/archive/2026-09-26-integration"

say() { printf '%s\n' "$*"; }
do_() { if [ "$MODE" = run ]; then "$@"; else say "  would: $*"; fi; }
# git mv when tracked, plain mv otherwise (run from $NEW)
gmv() { if git -C "$NEW" ls-files --error-unmatch "$1" >/dev/null 2>&1; then do_ git -C "$NEW" mv "$1" "$2"; else do_ mv "$NEW/$1" "$NEW/$2"; fi; }
cnt() { find "$1" -type f -not -path '*/.git/*' -not -path '*/data/*' -not -path '*/_attic/*' 2>/dev/null | wc -l | tr -d ' '; }

[ -d "$R" ] || { say "science tree not at $R (already moved?)"; exit 1; }
[ -d "$L" ] || { say "lab repo not at $L (already moved?)"; exit 1; }
[ ! -e "$NEW" ] || { say "$NEW already exists; refusing"; exit 1; }
say "== files before: root $(cnt "$R"), lab $(cnt "$L") (excluding .git, data, _attic)"

say "== A1 science tree -> Desktop (rename on the same volume)"
do_ mv "$R" "$NEW"
do_ mkdir -p "$A" "$BIG"

say "== A3 stale 5 GB snapshots and home duplicates -> $BIG (beside the workspace, not in it)"
do_ mv "$HOME/Downloads/bnjettag fake" "$BIG/bnjettag-fake-2026-07"
do_ mv "$HOME/Downloads/bnjettag-restart" "$BIG/bnjettag-restart-2026-09-05"
do_ mv "$HOME/Downloads/bnjettag-training-results copy" "$BIG/bnjettag-training-results-copy-2026-07"
do_ mv "$HOME/bnjettag-code" "$BIG/bnjettag-code-home-clone-1-dirty"
do_ mv "$HOME/bnjettag-methodology" "$BIG/bnjettag-methodology-home-clone"

say "== A4 agent layer: old root .claude -> archive (its memory is merged in B); lab .claude -> root"
do_ mv "$NEW/.claude" "$A/research-claude"
do_ mv "$L/.claude" "$NEW/.claude"

say "== A5 docs/infrastructure, CLAUDE.md, README.md: identical -> keep root's; differ -> lab wins, root copy archived"
do_ mkdir -p "$A/root-versions/docs-infrastructure"
for f in "$L"/docs/infrastructure/*.md; do b=$(basename "$f")
  if cmp -s "$f" "$NEW/docs/infrastructure/$b" 2>/dev/null || cmp -s "$f" "$R/docs/infrastructure/$b" 2>/dev/null; then say "  identical: $b"
  else say "  differs: $b"; do_ mv "$NEW/docs/infrastructure/$b" "$A/root-versions/docs-infrastructure/$b"; do_ mv "$f" "$NEW/docs/infrastructure/$b"; fi
done
do_ mv "$NEW/CLAUDE.md" "$A/root-versions/CLAUDE.md";  do_ mv "$L/CLAUDE.md" "$NEW/CLAUDE.md"
do_ mv "$NEW/README.md" "$A/root-versions/README.md";  do_ mv "$L/README.md" "$NEW/README.md"

say "== A6 literature/ and messages/ (git mv keeps history)"
gmv docs/literature literature
gmv docs/reports messages

say "== A7 docs/figures, docs/style, proposed CLAUDE"
do_ mv "$NEW/docs/figures/README.md" "$A/root-versions/docs-figures-README.md"
for f in "$L"/docs/figures/*; do do_ mv "$f" "$NEW/docs/figures/"; done
do_ mv "$L/docs/style" "$NEW/docs/style"
do_ mv "$L/docs/proposed-user-CLAUDE.md" "$NEW/docs/"

say "== A9 studies -> campaigns/<date>-<type>; lab dirs -> root"
do_ mkdir -p "$NEW/campaigns"
while read -r src dst; do do_ mv "$L/local/$src" "$NEW/campaigns/$dst"; done <<'MAP'
accuracy-investigation 2026-09-16-accuracy-investigation
training-batch-20260917 2026-09-17-training-batch
synthesis-r4-gradual-20260917 2026-09-17-synthesis-r4-gradual
training-batch-20260918 2026-09-18-training-batch
engram-study 2026-09-18-engram-study
ops-incident-20260919-r6-hang 2026-09-19-ops-incident-r6-hang
continuation-20260920 2026-09-20-continuation-packed
performance-index-20260920 2026-09-20-performance-index
status-20260920 2026-09-20-status
results-status-20260921 2026-09-21-results-status
engram-publication-20260921 2026-09-21-engram-publication
constituent-study-20260922 2026-09-22-constituent-screen
confirmation-20260923 2026-09-23-confirmation
2026-09-25-pt-weighting 2026-09-25-pt-weighting
2026-09-26-code-line-merge 2026-09-26-code-line-merge
MAP
do_ mv "$L/artifacts" "$NEW/campaigns/2026-09-15-ebops-accuracy-eval"
do_ mv "$L/local" "$NEW/local"
do_ mv "$L/nrp-lab" "$NEW/nrp-lab"
do_ mv "$L/tools" "$NEW/tools"
do_ mv "$L/SYSTEM.md" "$NEW/SYSTEM.md"
do_ mv "$L/INDEX.md" "$NEW/INDEX.md"
do_ mkdir -p "$NEW/sessions"
for f in "$L"/sessions/* "$NEW"/Sessions/*; do [ -e "$f" ] && do_ mv "$f" "$NEW/sessions/"; done
for d in "$NEW/Sessions" "$L/sessions"; do [ -d "$d" ] && do_ rmdir "$d"; done
do_ mv "$L/setup.sh" "$A/setup.sh"
do_ mkdir -p "$A/caches"; for c in .uv-cache .mpl-cache; do [ -e "$L/$c" ] && do_ mv "$L/$c" "$A/caches/"; done

say "== A10 publication clones"
do_ mv "$L/publication-engram-20260921" "$NEW/publication"
do_ mkdir -p "$A/publication-clones"
do_ mv "$L/publication" "$A/publication-clones/publication-20260917-20-uncommitted"
do_ mv "$L/publication-status-20260921" "$L/publication-status-20260920" "$A/publication-clones/"

say "== A11 published repos"
do_ mkdir -p "$NEW/published"
for d in bnjettag_results bnjettag-code bnjettag-methodology; do do_ mv "$HOME/Desktop/$d" "$NEW/published/"; done

say "== A12 lab repo history -> archive; retire the old shell"
do_ mv "$L/.git" "$A/lab-repo.git"
do_ mv "$L/.gitignore" "$A/lab-repo.gitignore"
[ -L "$L/research" ] && do_ mv "$L/research" "$A/research-symlink-retired"
# whatever is left in the lab repo (identical docs, caches, .DS_Store) goes to the archive whole
do_ mv "$L" "$A/lab-repo-remainder"
do_ mkdir -p "$A/outer-shell"
[ -d "$HOME/Desktop/bnjettag-lab/local" ] && do_ mv "$HOME/Desktop/bnjettag-lab/local" "$A/outer-shell/local-duplicate-runbook"
if [ "$MODE" = run ]; then printf '# Moved\n\nThe BNJetTag workspace is now one folder: `~/Desktop/bnjettag/` (moved 2026-09-26).\nOpen Claude Code there. This folder is empty on purpose and can be deleted.\n' > "$HOME/Desktop/bnjettag-lab/MOVED.md"; fi

say "== A13 root clutter -> archive; dated notes -> messages/"
do_ mkdir -p "$A/root-clutter"
for f in output.txt terminal-output.txt model-summary.txt practice.py solutions.md Untitled.base Untitled.canvas "files (2)" ByMaurizio.png bitnet-arch.png "Alternate Plans for Department of Physics.pdf"; do
  [ -e "$NEW/$f" ] && gmv "$f" "archive/2026-09-26-integration/root-clutter/$f"; done
for f in STATUS-2026-08-08.md notes-2026-08-13.md; do [ -e "$NEW/$f" ] && gmv "$f" "messages/$f"; done

say "== B1 memory logs: merge research (primary) + lab (secondary), nothing dropped"
for f in experiment-log decisions research-log; do
  do_ python3 "$NEW/tools/merge_logs.py" "$A/research-claude/memory/$f.md" "$NEW/.claude/memory/$f.md" "$NEW/.claude/memory/$f.md"
done
for f in newton-reports job-beta-brief job-gamma-brief; do [ -e "$A/research-claude/memory/$f.md" ] && do_ cp -n "$A/research-claude/memory/$f.md" "$NEW/.claude/memory/$f.md"; done
do_ cp "$A/research-claude/memory/project-context.md" "$A/root-versions/project-context.md"

say "== B2 .gitignore additions"
if [ "$MODE" = run ]; then cat >> "$NEW/.gitignore" <<'EOF'

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
else say "  would: append unified-workspace block to $NEW/.gitignore"; fi

say "== B3 machine-local paths"
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

say "== C checks"
if [ "$MODE" = run ]; then
  cd "$NEW"
  python3 tools/index.py init && python3 tools/index.py build
  python3 tools/brief.py | head -8
  (cd docs/style && tectonic -X compile report-template.tex >/dev/null 2>&1 && rm -f report-template.pdf && echo "report template compiles from the new path")
  echo "{\"tool_name\":\"Bash\",\"cwd\":\"$NEW\",\"tool_input\":{\"command\":\"kubectl apply -f nrp-lab/kai-lab.yaml\"}}" | CLAUDE_PROJECT_DIR="$NEW" python3 .claude/hooks/pre-kubectl-lint.py >/dev/null 2>&1 && echo "hook passes the lab manifest from the new path"
  say "== files after: $(cnt "$NEW") in the workspace"
  say "== done. Open Claude Code in $NEW. Then: git add -A && git commit  (publication/, published/, archive/, sessions/ are ignored)"
fi
