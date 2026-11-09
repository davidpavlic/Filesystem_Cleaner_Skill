---
name: folder-cleaner
description: Recommends a folder structure, shows partition usage and what fills it, explains what's in a folder and what can go. Read-only, never changes files. Use for "clean up", "free up space", "storage full", "where did my space go", "what can I delete", "lost track of my files", "aufräumen".
---

# Folder Cleaner

## Rules
- Never move, rename or delete files. The only file you may create is the report.
- Always get facts (sizes, dates, hashes) from the scripts, never estimate them.
- Output: up to ~50 files > answer in chat. More > report using `assets/report-template.md`.

## Functions
| Request | First read | Script |
|---|---|---|
| recommend structure, sort, organize | references/structure.md | scripts/scan.py |
| disk full, storage full, free up space | references/disk-overview.md | scripts/disk_overview.py |
| lost track of a folder, what can I safely delete | references/user-bloat.md | scripts/scan.py |

- A request can match several functions. Run each that matches, in this order: disk overview, user bloat, structure.
- "aufräumen" or "clean up" a folder without more detail: user bloat, then structure.
