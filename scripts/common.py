"""Helpers shared by the read-only scripts. Nothing here writes, moves or deletes."""


def human(n):
    # Byte count to readable string
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            if unit == "B":
                return f"{n:.0f} {unit}"
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def disk_bytes(file_stat):
    blocks = getattr(file_stat, "st_blocks", None)                  # None as default (Windows has no st_blocks)
    return file_stat.st_size if blocks is None else blocks * 512


def disk_bytes_to_count(file_stat, seen):
    # Check links on file_stat
    if file_stat.st_nlink > 1:
        key = (file_stat.st_dev, file_stat.st_ino)  # FS, Inode
        if key in seen:
            return 0
        seen.add(key)
    return disk_bytes(file_stat)