#!/usr/bin/env python3
"""Read-only overview: how full each filesystem is and what really fills it.

Usage: disk_overview.py [PATH] [--full-pct 90] [--min-size BYTES] [--depth 4] [--top 40]
Prints JSON. Never writes, moves or deletes anything.

With PATH it sizes that folder and tells which filesystem it is on. 
Without PATH it sizes the full filesystems, or all of them if none is full.
"""
import argparse
import json
import math
import os
import re
import shutil
import stat
import string
import sys

sys.dont_write_bytecode = True  # read-only promise: no __pycache__ next to the scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python3 -I leaves it out
from common import disk_bytes_to_count, human

# Sized as one unit: what is inside them is not a cleanup target of its own.
WHOLE = {"node_modules", ".venv", "venv", "__pycache__", "target", ".git", ".snapshots", "backintime", "timeshift", "timeshift-btrfs"}

def unescape_mount(path):
    # Decode the octal escapes in a mount path, e.g. /media/usb\040drive -> /media/usb drive
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), path)


def filesystems():
    # Windows Branch
    if os.name == "nt":
        # Loop through alphabet
        drives = [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")]
        # Loop through found drives
        return [{"device": d, "type": None, "mounts": [d]} for d in drives]
    # Linux Branch
    by_device = {}
    try:
        # Opens the mount list
        with open("/proc/self/mounts") as f:
            for line in f:
                device, mount, fstype = line.split()[:3]
                # Only real partitions start with /dev/, not tmpfs, proc, sysfs, etc.
                if device.startswith("/dev/"):
                    # Add entry and save it to fs
                    fs = by_device.setdefault(device, {"device": device, "type": fstype, "mounts": []})
                    fs["mounts"].append(unescape_mount(mount))
    except OSError:
        pass
    return list(by_device.values()) or [{"device": None, "type": None, "mounts": ["/"]}]


def filesystem_usage(fs, full_pct):
    # shutil.disk_usage() returns a total, used, and free space
    du = shutil.disk_usage(fs["mounts"][0])
    # percentage of used space if total space is not zero, otherwise 0
    pct = math.ceil(100 * du.used / (du.used + du.free)) if du.used + du.free else 0
    return {"mounts": fs["mounts"], "device": fs["device"], "type": fs["type"],
            "size": human(du.total), "used": human(du.used), "free": human(du.free),
            "used_pct": pct, "full": pct >= full_pct}


# Checks on which filesystem the given path lives
def filesystem_of(path, rows):
    # Get partition number of path
    dev = os.stat(path).st_dev
    for row in rows:
        if any(os.stat(m).st_dev == dev for m in row["mounts"]):
            return row
    return None


# Measures folder and subfolder size 
def size_tree(path, dev, seen, scan_errors):
    node = {"path": path, "bytes": 0, "children": []}
    try:
        names = os.listdir(path)            # usually needs root
    except OSError:
        scan_errors["unreadable_dirs"] += 1  
        return node
    for name in names:
        folder_path = os.path.join(path, name)
        try:
            st = os.lstat(folder_path)
        except OSError:
            continue
        if not stat.S_ISDIR(st.st_mode):
            node["bytes"] += disk_bytes_to_count(st, seen)
        elif st.st_dev == dev:  # skip folders on another partition, e.g. /home when scanning /
            # Recurse through subfolder
            child = size_tree(folder_path, dev, seen, scan_errors)
            child["bytes"] += disk_bytes_to_count(st, seen)
            # Remove children of selected folder names, they are counted as one unit
            if name in WHOLE:
                child["children"] = []
            node["bytes"] += child["bytes"]
            node["children"].append(child)
    return node


def collect(node, depth, min_size, scanned, rows):
    # Transforms the tree into a flat list of rows for the report, filtering by depth and size.
    def row(size, **extra):
        return {"path": node["path"], "size": human(size), "bytes": size,
                "share": f"{size / scanned:.0%}", **extra}

    # Contains the direct subfolders of the node that are at least min_size
    big = [c for c in node["children"] if c["bytes"] >= min_size]
    if not big or depth == 0:
        if node["bytes"] >= min_size:
            rows.append(row(node["bytes"]))
        return
    for child in big:
        collect(child, depth - 1, min_size, scanned, rows)
    rest = node["bytes"] - sum(c["bytes"] for c in big)
    if rest >= min_size:
        rows.append(row(rest, rest=True))


def main():
    # Parse command-line arguments.
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--full-pct", type=int, default=90)     # At what % of used space is a filesystem "full"?
    ap.add_argument("--min-size", type=int, default=None)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()

    # Initialize tables of filesystems and their usage
    table = [filesystem_usage(fs, a.full_pct) for fs in filesystems()]
    full = [row for row in table if row["full"]]
    result = {"filesystems": table, "full": [row["mounts"][0] for row in full]}

    # If a path argument is given
    if a.path:
        # make relative paths absolute, by replacing envvars and ~, and normalizing separators
        root = os.path.abspath(os.path.expandvars(os.path.expanduser(a.path)))
        # Stops execution if the path is not a folder
        if not os.path.isdir(root):
            ap.error(f"not a folder: {root}")
        
        home = filesystem_of(root, table)
        # New key representing the mount of the given path
        result["target"] = {"path": root, "filesystem": home["mounts"][0] if home else None,
                            "on_full_filesystem": bool(home and home["full"])}
        roots = [root]
    else:
        roots = []
        for row in (full or table):
            for m in row["mounts"]:
                roots.append(m)

    seen_files, scan_errors = set(), {"unreadable_dirs": 0}
    # Size each root into a tree of {path, bytes, children}.
    trees = [size_tree(r, os.stat(r).st_dev, seen_files, scan_errors) for r in roots]
    scanned = sum(t["bytes"] for t in trees)
    # minimum size of reportable folders: 1% of scanned or 1 MB, unless overridden by --min-size
    min_size = a.min_size or max(1 << 20, scanned // 100)


    rows = []
    for tree in trees:
        collect(tree, a.depth, min_size, scanned or 1, rows)
    rows.sort(key=lambda r: r["bytes"], reverse=True)  # biggest first
    for r in rows:
        del r["bytes"]  # only needed for sorting
    # Create a json report
    print(json.dumps({**result, "scanned": human(scanned), **scan_errors,
                      "largest": rows[:a.top]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
