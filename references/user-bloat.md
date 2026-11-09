# User Bloat

`scan.py` skips hidden folders.

## Which call
- Path given: `scan.py PATH`.
- No path (never scan the whole home):
    - About space, after `disk_overview.py` ran: scan up to three of the biggest folders in `largest` that hold the user's own files, in one call. If there are none, say that deleting own files frees little there.
    - Otherwise: ask which folder.

## Read the result in this order
1. `skipped_paths`: say they were not found, never call them empty.
2. `installers` older than 3 months can usually go.
3. `extracted_archives`: archive and folder hold the same files, one of the two can usually go.
4. `stale_folders`: old is not useless, photos and documents are kept on purpose. Suggest one only if its name or `top_types` point to a leftover.

## Never recommend deleting
- Files inside game libraries, VMs or other app-managed folders. A whole game or VM is removed through its app.
- Cloud-synced folders (Dropbox, OneDrive, Nextcloud): deleting there deletes on every device. Mention only, with a warning.

## Report
Group the files by what they are, e.g. installers, documents, photos. Per group: what it is, keep / can go / ask, a short reason and the size. In a report, use the Dead Folders & Installers table.
