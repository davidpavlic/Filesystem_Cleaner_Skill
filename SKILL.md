---
name: folder-cleaner
description: Recommends a folder structure and shows which partition is full and what fills it. Read-only, never changes files. Use for "clean up", "free up space", "storage full", "where did my space go", "what can I delete", "aufräumen".
---

# Folder Cleaner

## Rules
- Never move, rename or delete files. The only file you may create is the report.
- Always get facts (sizes, dates, hashes) from the scripts, never estimate them.
- Output: up to ~50 files > answer in chat. More > report using `assets/report-template.md`.
- Any request about space or cleaning up: run `disk_overview.py` first and follow references/disk-overview.md. Deleting only frees space on the filesystem a file lives on.

## Functions
| Request | First read | Script |
|---|---|---|
| recommend structure, tidy up, aufräumen | references/structure.md | scripts/scan.py |
| disk full, storage full, what can I delete, free up space | references/disk-overview.md | scripts/disk_overview.py |
