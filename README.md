# Folder Cleaner

A read-only [Claude Code](https://claude.com/claude-code) skill that looks at a folder tree and recommends a saner structure, analyzes your current disk usage or explains what's in a folder and what can go. It never moves, renames or deletes anything.

> **Work in progress.** Structure, disk full and user bloat work today. Software and system bloat come next.

## What it does

The functions follow one idea: organize your folders, see where the space went, then decide what can go.

| Function | Question it answers | What you get | Status |
|---|---|---|---|
| **Recommend structure** | How should I organize my folders? | A target folder tree and a short list of moves and renames. | Available |
| **Disk full** | Where did my space go? | Which partition is full and what fills it, hidden folders included. A warning if the folder you want to clean is on a different partition, because deleting there frees nothing on the full one. | Available |
| **User bloat** | I lost track of a folder: what is all this, and what can go? | What the files are, which of them still matter and which can safely go, e.g. old installers, unpacked archives and duplicates. | Available |
| **Software bloat** | Which programs can go? | Large installed programs and games with the date they last changed, and old versions of tools like Python or Node next to the current one. Removing them always goes through the package manager or the app. | Planned |
| **System bloat** | What does the system itself pile up? | Package caches, old logs, crash dumps, unused app runtimes and the size of your snapshots. | Planned |

## How it works

- `scripts/scan.py` collects the facts as JSON: folder sizes, file types and last changes.
Claude turns them into recommendations, following the rules in `references/structure.md`.
- `scripts/disk_overview.py` measures how full each partition is and which folders fill it. Claude follows `references/disk-overview.md`.
- For a folder you lost track of, `scripts/scan.py` also lists installers, archives that were already extracted and folders nothing changed in for a year, and with `--files` the biggest files and duplicates. Claude explains what they are and which can go, following `references/user-bloat.md`.

## Design decisions

- **Scripts collect the facts, Claude interprets them.** Sizes, dates and file types come from `scripts/` as JSON, so Claude never has to estimate a number. How to read them is in one reference per function in `references/`.
- **Read-only.** The skill recommends, you decide. You run every move, rename or delete yourself, so a wrong recommendation costs a second look, not your data.
- **The partition comes first.** Deleting a file only frees space on the filesystem it lives on. On my machine `/` and `/home` are separate partitions, so clearing `~/Downloads` does nothing for a full `/`. That is why every request about space starts with `disk_overview.py`.
- **Functions combine instead of overlapping.** A mixed request like "my disk is full, clean up Downloads" runs the matching functions in a fixed order. So each rule lives in one reference, and each function can be tested on its own.
- **Claude loads the skill on its own.** Its description sits in every chat and already colors answers: in `skill_miss_easy` the skill did not load, yet 5 of 6 runs wrote a poem about folders or clutter. The eval project is called `folder-cleaner-evals`, so that name may play a part too. User-invoked only would avoid that, but the partition rule would then only reach people who already know the problem, and the evals could no longer test when the skill loads.
- **Real disk usage, not file size.** The scripts count allocated blocks and each hard link only once, the same way `du` does. Backup tools like Timeshift store snapshots as hard links, so adding up file sizes would report far more than the disk actually holds.
- **Standard library only.** The scripts need nothing but Python 3.

## Install

```bash
git clone https://github.com/davidpavlic/Filesystem_Cleaner_Skill ~/.claude/skills/folder-cleaner
```

Then ask Claude Code something like *"How should I structure my Documents folder?"*, *"Where did my disk space go?"* or *"I lost track of my Downloads folder, what can go?"*

The scripts also run on their own and only need Python 3:

```bash
python3 scripts/scan.py ~/Documents --depth 2
python3 scripts/disk_overview.py
```

## Tests

`tests/smoke.py` runs both scripts on a small temporary folder and checks values known in advance, e.g. that a hard-linked file counts once and a missing path is reported. It needs no Claude and runs on every push on Linux and Windows.

```bash
python3 tests/smoke.py
```

## Evals

The scripts are deterministic, Claude is not. `evals/run.py` runs Claude Code headless on the prompts in `evals/cases.json` and checks in the transcript which scripts it used, and that it changed nothing.

```bash
python3 evals/run.py
```

**Last run:** 9/9 passed on 2026-11-11 with Claude Code 2.1.300 and Opus 5.5, $1.87 in total.

## Does it help?

The evals only check which scripts Claude calls, not whether its answers are good. So I compared blind: five prompts, each answered once with and once without the skill, with the same read-only rights. A fresh Claude session judged the pairs without knowing which was which, and checked the facts against `df` and `du` from my machine.

Plain Claude gave the better answer in 4 of 5 prompts. Scored from 1 to 5 on accuracy, safety, usefulness, clarity and honesty, both ended almost level at 107 and 109 of 125 points: the skill led on honesty and safety, plain Claude on usefulness. The skill also cost more, $1.45 against $0.83.

- Plain Opus 5.5 already runs `df` and noticed on its own that `/` was the full partition.
- Two rules cost most of the usefulness. "Snapshots: mention the size only" kept Claude from the biggest win, 22 GB of backups on the full `/`, which plain Claude suggested moving to `/home`. "Ask and wait" stops halfway, which a headless run punishes more than a real chat.
- Three more eval runs gave 9/9, 9/9 and 7/9. Both failures came from the eval setup, not the skill: a denied call counted as a run, and a blocked `ls` made Claude give up.
- Limits: five prompts, one run each, one machine, and the judge is the same model family.

## How it was built

Built with Claude Code. I review and rework each script by hand before committing it.

## License

MIT, see [LICENSE](LICENSE).
