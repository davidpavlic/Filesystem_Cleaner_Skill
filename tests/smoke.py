#!/usr/bin/env python3
"""Smoke test: runs both scripts on a small temporary folder and checks known values.

Usage: python3 tests/smoke.py
No Claude, no network. CI runs it on Linux and Windows (.github/workflows/smoke.yml).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
MB = 1024 * 1024


def run(script, *args):
    # Run a script the way Claude Code does (python -I) and return its JSON output
    out = subprocess.run([sys.executable, "-I", str(SCRIPTS / script), *args],
                         capture_output=True, text=True)
    assert out.returncode == 0, f"{script} failed:\n{out.stderr}"
    return json.loads(out.stdout)


def make_fixture(root):
    # 4 MB of real data: one file hard-linked a second time, an installer, a hidden folder
    (root / "docs").mkdir()
    (root / "docs" / "a.bin").write_bytes(os.urandom(2 * MB))
    os.link(root / "docs" / "a.bin", root / "docs" / "a-link.bin")
    (root / "setup.exe").write_bytes(os.urandom(MB))
    (root / ".cache").mkdir()
    (root / ".cache" / "c.bin").write_bytes(os.urandom(MB))


def main():
    pycache_before = (SCRIPTS / "__pycache__").exists()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Setup folder structure with known sizes and types
        make_fixture(root)

        # scan.py skips hidden folders unless asked; the hard link counts as a file but not as space
        scan = run("scan.py", str(root))
        assert scan["total"] == {"files": 3, "size": "3.0 MB"}, scan["total"]
        assert [Path(i["path"]).name for i in scan["installers"]] == ["setup.exe"], scan["installers"]
        hidden = run("scan.py", str(root), "--include-hidden")
        assert hidden["total"] == {"files": 4, "size": "4.0 MB"}, hidden["total"]

        # disk_overview.py always includes hidden folders and also counts the hard link once
        disk = run("disk_overview.py", str(root))
        assert disk["filesystems"], "no filesystem found"
        assert disk["scanned"] == "4.0 MB", disk["scanned"]
        assert disk["unreadable_dirs"] == 0, disk["unreadable_dirs"]
        names = {Path(r["path"]).name for r in disk["largest"]}
        assert {"docs", ".cache"} <= names, names

    # Read-only promise: running the scripts must not leave bytecode next to them
    assert (SCRIPTS / "__pycache__").exists() == pycache_before, "scripts wrote __pycache__"
    print("smoke test passed")


if __name__ == "__main__":
    main()
