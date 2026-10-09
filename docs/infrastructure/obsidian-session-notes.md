---
title: Session notes
status: current
date: 2026-09-26
---

# Session notes

Every Claude Code session opened in this repo becomes a markdown note under `sessions/`
(gitignored), created when the session starts and kept current as the conversation grows.
The point is retrieval: what was decided in a session, which files it touched, which study
it belongs to, searchable next to the documents it produced. It is **agent context, not
evidence**: a number is still only quotable from a `VERIFY.md` or a recomputation.

Until 2026-09-26 the notes went into an Obsidian vault in the research tree. Obsidian is a
desktop app that reads a folder of markdown as a vault with search, backlinks and a graph;
it was not being opened, and the lab repo was never inside a vault, so seventeen sessions
went unrecorded. The destination is now fixed by an environment variable and needs no vault.

## Moving parts

| Item | Path |
| --- | --- |
| Script | `~/.claude/hooks/claude_to_obsidian.py` (name kept; it writes plain markdown) |
| Hook registration | `~/.claude/settings.json`: `SessionStart`, `Stop`, `SessionEnd` |
| Destination | `.claude/settings.local.json` → `env.CLAUDE_OBSIDIAN_DIR` = `<this repo>/sessions` |
| Notes | `sessions/YYYY-MM-DD-<project>-<8-char session id>.md` |
| Index | `INDEX.md` lists the count and the newest note (`python3 tools/index.py build`) |
| Parse cache | `~/.claude/hooks/.cache/obsidian/<session-id>.json` |

## What lands in a note

Prose only. Tool calls, tool results, thinking blocks, subagent transcripts and system
reminders are stripped. What the tools *did* survives as a collapsible summary at the top:
turn and tool-call counts, session span, tools by frequency, which agents and skills ran,
and every file written or edited. Frontmatter: `title`, `date`, `updated`, `project`, `cwd`,
`model`, `git_branch`, `session_id`, `turns`, `tool_calls`, `status` (`active` while open,
`done` once ended), `tags`.

## Behaviour worth knowing

- Filenames never change; the name is fixed at creation and remembered in the cache.
- Incremental: each `Stop` reads only the bytes appended since the last one.
- Silent when idle; self-healing if the transcript is replaced (compaction, resume).
- Never breaks a session: always exits 0 and never writes to stdout.

## Operations

Backfill this repo's past sessions (safe to re-run; filenames are stable):

```bash
for t in ~/.claude/projects/-Users-kaiyamaguchi-Desktop-bnjettag-lab/*.jsonl; do
  CLAUDE_OBSIDIAN_DIR="$PWD/sessions" python3 ~/.claude/hooks/claude_to_obsidian.py --file "$t"
done
```

Do not use `--backfill` with the override set: it would write every project on this machine
into `sessions/`. To turn the notes off, delete the three `claude_to_obsidian` entries from
`~/.claude/settings.json`.
