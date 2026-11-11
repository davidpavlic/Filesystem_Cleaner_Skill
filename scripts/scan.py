#!/usr/bin/env python3
"""Read-only inventory: folder sizes and types, stale folders, installers,
archives that were already extracted and, with --files, the biggest files and
files with the same content.

Usage: scan.py PATH [PATH ...] [--depth 3] [--stale-days 365] [--include-hidden] [--files]
Prints JSON. Never writes, moves or deletes anything.
"""
import argparse
import hashlib
import json
import os
import stat
import time
import sys
from collections import Counter, defaultdict
from datetime import date

sys.dont_write_bytecode = True  # read-only promise: no __pycache__ next to the scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python3 -I leaves it out
from common import disk_bytes, disk_bytes_to_count, human

# Extensions we treat as installers: usually deletable once the app is installed.
INSTALLERS = {".exe", ".msi", ".msix", ".dmg", ".pkg", ".deb", ".rpm", ".run"}
# Archive extensions; flagged only if a same-named folder sits next to them (already unpacked).
ARCHIVES = (".tar.gz", ".tgz", ".tar", ".zip", ".7z", ".rar")
# --files lists at most this many files, biggest first; the rest is only counted.
MAX_FILES = 100


def day(ts):
    # Format a Unix timestamp as a plain YYYY-MM-DD date.
    return date.fromtimestamp(ts).isoformat()


def files(root, include_hidden):
    for dirpath, dirsubdirs, dirfiles in os.walk(root):
        # Editing the dirsubdirs list before os.walk() recurses into hidden folders.
        dirsubdirs[:] = [
            d for d in dirsubdirs
            if (include_hidden or not d.startswith("."))
        ]
        for name in dirfiles:
            path = os.path.join(dirpath, name)
            try:
                file_stat = os.lstat(path)          # lstat() to get symlink data, not the target's
            except OSError:                         # because of permissions or deletions
                continue                    
            if stat.S_ISREG(file_stat.st_mode):     # regular files only (skip symlinks, devices, …)
                yield path, file_stat


def group(root, path, depth):
    # Returns the parent folder of path relative to root at given depth.
    rel = os.path.relpath(os.path.dirname(path), root)
    parts = [] if rel == "." else rel.split(os.sep) # . for root, otherwise split path
    return os.path.join(root, *parts[:depth])       # * unpacks the list


# Checks if an archive has a same-named folder next to it
def extracted_folder(path):
    name = os.path.basename(path)
    for ext in ARCHIVES:
        # If file is identified as an archive
        if name.lower().endswith(ext):
            # Get the folder name
            folder = os.path.join(os.path.dirname(path), name[: -len(ext)])
            # Check if the folder exists and is a directory
            return folder if os.path.isdir(folder) else None
    return None


def file_hash(path):
    # SHA-256 of the content, read in 1 MB chunks so big files do not fill the memory
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def duplicates(by_size):
    # Groups of files with the same content; only files of the same size are hashed
    groups = []
    for size, by_inode in by_size.items():
        if len(by_inode) < 2:
            continue
        by_hash = defaultdict(list)
        for path in by_inode.values():
            try:
                by_hash[file_hash(path)].append(path)
            except OSError:  # because of permissions or deletions
                continue
        groups += [(size, sorted(paths)) for paths in by_hash.values() if len(paths) > 1]
    return sorted(groups, reverse=True)  # biggest first


def main():
    # Parse command-line arguments.
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--depth", type=int, default=3)          # how finely to group folders
    ap.add_argument("--stale-days", type=int, default=365)   # "stale" files threshold
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--files", action="store_true")          # also list the biggest files
    a = ap.parse_args()

    # Var & Data Initialization
    cutoff = time.time() - a.stale_days * 86400 # current - var * seconds a day
    # Map for each folder
    folders = defaultdict(lambda: {"files": 0, "bytes": 0, "newest": 0, "types": Counter()})
    # extracted: list of archives that have a same-named folder next to them
    installers, extracted, types = [], [], Counter()
    all_files = []  # only with --files: (size, path, mtime, type) of every file
    by_size = defaultdict(dict)  # only with --files: exact size -> {inode: path}, for the duplicate check
    total_files = total_bytes = 0
    seen = set()  # hard-linked files already counted
    skipped = []  # paths that are missing or not a folder

    for p in a.paths:
        # make relative paths absolute, by replacing envvars and ~, and normalizing separators
        root = os.path.abspath(os.path.expandvars(os.path.expanduser(p)))
        if not os.path.isdir(root):
            skipped.append(root)  # reported, so a missing path does not look like an empty folder
            continue
        for path, file_stat in files(root, a.include_hidden):
            size = disk_bytes_to_count(file_stat, seen)
            total_files += 1
            total_bytes += size
            # Saves the files extension
            ext = os.path.splitext(path)[1].lower() or "(none)"

            # Gets folders map entry in g and updates its values based on path by depth
            g = folders[group(root, path, a.depth)]
            g["files"] += 1
            g["bytes"] += size
            g["newest"] = max(g["newest"], file_stat.st_mtime)
            g["types"][ext] += 1
            types[ext] += 1

            # Check if installer
            if ext in INSTALLERS:
                installers.append({"path": path, "size": human(disk_bytes(file_stat)),
                                   "modified": day(file_stat.st_mtime)})

            # Check if archive
            folder = extracted_folder(path)
            if folder:
                extracted.append({"path": path, "size": human(disk_bytes(file_stat)),
                                  "extracted_to": folder})

            # Remember every file for the --files list and the duplicate check
            if a.files:
                all_files.append((disk_bytes(file_stat), path, file_stat.st_mtime, ext))
                if file_stat.st_size:  # empty files are all equal, not worth listing
                    # keyed by inode, so the hard links of one file are no duplicates
                    by_size[file_stat.st_size][(file_stat.st_dev, file_stat.st_ino)] = path

    # Biggest folders first by bytes (B, KB, GB is not in the attribute, only in extracted & installers)
    rows = sorted(folders.items(), key=lambda kv: kv[1]["bytes"], reverse=True)

    def row(path, folder_stats):
        return {"path": path, "files": folder_stats["files"], "size": human(folder_stats["bytes"]),
                "newest_change": day(folder_stats["newest"]),
                "top_types": dict(folder_stats["types"].most_common(3))} # most common 3 file types

    # Cap the folder lists at 50 entries so the output stays readable.
    out = {
        "total": {"files": total_files, "size": human(total_bytes)},
        "skipped_paths": skipped,
        "folders": [row(path, folder_stats) for path, folder_stats in rows[:50]],
        "stale_folders": [row(path, folder_stats) for path, folder_stats in rows if folder_stats["newest"] < cutoff][:50],
        "installers": installers,
        "extracted_archives": extracted,
        "types": dict(types.most_common(15)),
    }
    # --files: the biggest files first, capped at MAX_FILES
    if a.files:
        biggest = sorted(all_files, reverse=True)[:MAX_FILES]
        out["files"] = [{"path": path, "size": human(size), "modified": day(mtime), "type": ext}
                        for size, path, mtime, ext in biggest]
        out["files_not_listed"] = len(all_files) - len(biggest)
        out["duplicates"] = [{"size": human(size), "paths": paths}
                             for size, paths in duplicates(by_size)[:50]]
    # Compact, without indentation: Claude Code moves long outputs to a file, which costs extra steps
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
