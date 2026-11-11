# User Bloat

`scan.py` skips hidden folders.

## Which call
- Path given: `scan.py PATH --files`.
- No path (never scan the whole home):
    - About space, after `disk_overview.py` ran: scan up to three of the biggest folders in `largest` that hold the user's own files, in one `scan.py --files` call. If there are none, say that deleting own files frees little there.
    - Otherwise: ask which folder.

## Read the result in this order
1. `skipped_paths`: say they were not found, never call them empty.
2. `installers` older than 3 months can usually go.
3. `extracted_archives`: archive and folder hold the same files, one of the two can usually go.
4. `duplicates`: same content, checked by hash. One per group is enough, keep the one in the most fitting place.
5. `stale_folders`: old is not useless, photos and documents are kept on purpose. Suggest one only if its name or `top_types` point to a leftover.
6. `files`: the biggest files. If name and type do not tell what a file is, say so, never guess. `files_not_listed` above 0: say how many smaller files were left out.

## Never recommend deleting
- Files inside game libraries, VMs or other app-managed folders. A whole game or VM is removed through its app.
- Cloud-synced folders (Dropbox, OneDrive, Nextcloud): deleting there deletes on every device. Mention only, with a warning.

## Report
Group the files by what they are, e.g. installers, documents, photos. Per file: what it is, keep / can go / ask, a short reason and the size. In a report, use the Folder Overview table, and the Duplicates table for `duplicates`.
