# Folder Cleaner

A read-only [Claude Code](https://claude.com/claude-code) skill that looks at a folder tree and recommends a saner structure or analyzes your current disk usage. It never moves, renames or deletes anything.

> **Work in progress.** The first two functions below work today. The third is planned for the first release.

## What it does

The functions follow one idea: organize your folders, see where the space went, then decide what can go.

| Function | Question it answers | What you get | Status |
|---|---|---|---|
| **Recommend structure** | How should I organize my folders? | A target folder tree and a short list of moves and renames. | Available |
| **Disk full** | Where did my space go? | Which partition is full and what fills it, hidden folders included. A warning if the folder you want to clean is on a different partition, because deleting there frees nothing on the full one. | Available |
| **User bloat** | Which of my files can go? | Dead folders, old installers and duplicates. | Planned |

## How it works

- `scripts/scan.py` collects the facts as JSON: folder sizes, file types and last changes.
Claude turns them into recommendations, following the rules in `references/structure.md`.
- `scripts/disk_overview.py` measures how full each partition is and which folders fill it. Claude follows `references/disk-overview.md`.

## Install

```bash
git clone https://github.com/davidpavlic/Filesystem_Cleaner_Skill ~/.claude/skills/folder-cleaner
```

Then ask Claude Code something like *"How should I structure my Documents folder?"* or *"Where did my disk space go?"*

The scripts also run on their own and only need Python 3:

```bash
python3 scripts/scan.py ~/Documents --depth 2
python3 scripts/disk_overview.py
```

## Evals

The scripts are deterministic, Claude is not. `evals/run.py` checks whether Claude actually follows the skill's rules: it runs Claude Code headless on each prompt in `evals/cases.json` and checks the tool calls in the transcript.

| Case | Prompt | Passes when |
|---|---|---|
| `storage_full` | My storage is full | The skill loads and `disk_overview.py` runs without a path. |
| `clear_downloads` | Clear up space in the Downloads folder | `disk_overview.py` runs on Downloads, no other script runs. |
| `aufraeumen_downloads` | Räum meinen Downloads-Ordner auf | `disk_overview.py` runs first, then `scan.py`, both on Downloads. |
| `structure_desktop` | How should I structure my "~/Schreibtisch" folder? | `scan.py` runs on Schreibtisch. `disk_overview.py` may run, but only before it. |
| `skill_miss_easy` | Write me a poem | The skill does not load. |
| `skill_miss_hard` | How do I delete a folder in linux? | The skill does not load, although "delete" is in its description. |

Every case also fails on any write except the report, on commands like `rm`, `mv` or `sudo`, and on a script that is not listed for it.

```bash
python3 evals/run.py                 # all cases
python3 evals/run.py storage_full    # one case
```

- Needs a logged-in Claude Code and uses your plan or API credit, at most $1 per case.
- Claude runs in a fresh temporary project that contains only this skill. It may only read and run the skill's scripts, so nothing on your disk can change.
- The paths in the cases (`~/Downloads`, `~/Schreibtisch`) are from my machine. Adjust them to yours.

**Last run:** 6/6 passed on 2026-11-03 with Claude Code 2.1.300 and Opus 5.5, $0.89 in total.

**What the evals don't test:** the quality of the answers. They check which tools and scripts Claude used and that it changed nothing, not whether its recommendations are any good. A structure case passes as soon as `scan.py` runs on the right folder, even if that folder turns out to be empty.

## How it was built

Built with Claude Code. I review and rework each script by hand before committing it.
