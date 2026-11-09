# Recommend Structure

## Goal
A structure the user can keep up without effort. Prefer targeted changes over a full rebuild: if the current structure mostly works, only fix the outliers.

## How to work
1. Run `scan.py PATH --depth 3` to see where size and file counts are. Without a path, scan `~`.
2. Use `top_types` per folder from scan.py, plus file names where needed, to find which areas the folders belong to.
3. Propose a target tree, then map the largest current folders onto it.
4. List only the moves and renames that matter most (max ~20).

## Principles
- **Keep the OS standard folders.** Documents, Pictures, Downloads … stay where they are; structure goes inside them.
- **Max 2–3 levels.** Deeper and files get lost.
- **5–10 subfolders per folder.** Fewer: merge. More: group.
- **No single-file folders, no `Misc/`.** A catch-all folder becomes the next mess.
- **Finished things go to an archive**, by year: `Archive/2024/`. Don't mix active and finished work.
- **Downloads and Desktop are inboxes.** Nothing lives there permanently.

## Building blocks
Use only what fits the user's files.

```
Documents/
├── Admin/              # IDs, contracts, insurance, housing
├── Finance/
│   └── 2026/           # invoices, payslips, taxes – by year
├── Uni/
│   └── 2026_Spring/    # by semester, then by course
│       └── Linear_Algebra/
├── Work/
│   └── <Employer>/
├── Personal/           # hobbies, travel, health
└── Archive/
    └── 2024/
Pictures/
└── 2026/
    └── 2026-07_Italy/  # by year, then by event
dev/                    # code – outside Documents and outside cloud sync
```

## Developer projects
- All code in one place outside Documents: `~/dev` (Windows: `%USERPROFILE%\dev`).
- Never inside a cloud-synced folder: `node_modules` and `.venv` would sync thousands of files.
- Layout: `dev/<topic-or-org>/<repo>`, not deeper.

## Naming
- Dated documents (invoices, letters, scans): `YYYY-MM-DD_topic_detail.ext`.
- Folders: one style throughout, e.g. `Title_Case_With_Underscores`. No dates in active folder names, except year and semester folders.
- No version suffixes like `_final2`: one current file, old versions go to the archive.
- Suggest renames only for names that say nothing or are inconsistent: `IMG_4432`, `Scan_0042`, `Untitled`, `Document (3)`.

## Leave alone
- App-managed folders (game libraries, VMs, IDE data): never touch what is inside. A whole game or VM unchanged for years may be suggested for removal through its app, with a warning. Say "not updated since", never "not used since".
- The top level of cloud folders: other devices depend on it. Suggest changes there only with a warning.

## Output
- Current and proposed tree, max 2 levels each.
- A short `from → to` table for the largest folders.
- 2–3 sentences of rationale: which areas you found and why the tree fits them.