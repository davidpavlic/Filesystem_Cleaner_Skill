# Disk Overview

`disk_overview.py` shows how full each filesystem is and which folders take up the space. Unlike the other scripts it includes hidden folders.

## Which call
- Path given: `disk_overview.py PATH` sizes that folder and tells which filesystem it is on.
- No path, or "storage full": `disk_overview.py` sizes the full filesystems, or all of them if none is full.
- Filesystems count as full from 90% (`--full-pct`). The list starts at 1% of the scanned size (`--min-size`).

## Read the result in this order
1. `full`: filesystems at 90%+. Name them first.
2. `target.on_full_filesystem`: if it is false while `full` is not empty, say first that cleaning this path frees nothing on the full filesystem. Then ask the user whether you should run `disk_overview.py` without a path to check the full filesystem, and wait for the answer.
3. `largest`: biggest folders first. 
   - `share` is this folder's percentage of everything scanned in this run, not of the whole filesystem.
   - `rest: true`: what is left in that folder besides the larger subfolders listed. It is not the size of the whole folder.
4. `unreadable_dirs` above 0, or without a path `scanned` clearly below `used`: part of it needs root. Say so and give the user `sudo du -xh -d2 <mount> | sort -rh | head -30` to run.

## Never recommend deleting
`/usr`, `/etc`, `/boot`, `/opt` or anything else from the installed system: never suggest removing these folders by hand. If a row clearly belongs to one program, e.g. `/usr/lib/libreoffice`, you may suggest uninstalling it through its package manager or app if the user no longer needs it.
Snapshots and backups: mention the size only, they may be the only backup.

## Report
Start with the filesystem table (mount, type, size, used, free), then the largest folders.
