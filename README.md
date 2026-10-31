# Folder Cleaner

A read-only [Claude Code](https://claude.com/claude-code) skill that looks at a folder tree and recommends a saner structure. It never moves, renames or deletes anything.

> **Work in progress.** Recommending a structure works today. Finding what fills a full disk, dead folders and duplicates are planned for the first release.

## How it works

`scripts/scan.py` collects the facts as JSON: folder sizes, file types and last changes.
Claude turns them into recommendations, following the rules in `references/structure.md`.

## Install

```bash
git clone https://github.com/davidpavlic/Filesystem_Cleaner_Skill ~/.claude/skills/folder-cleaner
```

Then ask Claude Code something like *"How should I structure my Documents folder?"*

The script also runs on its own and only needs Python 3:

```bash
python3 scripts/scan.py ~/Documents --depth 2
```

## How it was built

Built with Claude Code. I review and rework each script by hand before committing it.
