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

## How it was built

Built with Claude Code. I review and rework each script by hand before committing it.
