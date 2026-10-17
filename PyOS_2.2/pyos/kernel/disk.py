"""
PyOS Virtual Disk.

A sandboxed storage area at ~/.pyos/disk/ with a configurable capacity.
All File Explorer writes go through this module so we can enforce
disk-full behaviour and keep a manifest.
"""
import os
import json
import shutil

from pyos.kernel.state import PYOS_HOME


DISK_ROOT = os.path.join(PYOS_HOME, "disk")
META_FILE = os.path.join(DISK_ROOT, ".diskmeta.json")

DEFAULT_CAPACITY_MB = 256


# ==================================================================
# Metadata
# ==================================================================
def _load_meta():
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"capacity_mb": DEFAULT_CAPACITY_MB}


def _save_meta(meta):
    os.makedirs(DISK_ROOT, exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def ensure():
    """Create the disk folder structure on first use."""
    os.makedirs(DISK_ROOT, exist_ok=True)
    for sub in ("Documents", "Downloads", "Pictures", "Music", "Videos", "Temp"):
        os.makedirs(os.path.join(DISK_ROOT, sub), exist_ok=True)
    if not os.path.isfile(META_FILE):
        _save_meta({"capacity_mb": DEFAULT_CAPACITY_MB})


# ==================================================================
# Capacity
# ==================================================================
def capacity_bytes():
    return _load_meta().get("capacity_mb", DEFAULT_CAPACITY_MB) * 1024 * 1024


def set_capacity_mb(mb):
    meta = _load_meta()
    meta["capacity_mb"] = int(mb)
    _save_meta(meta)


def used_bytes():
    """Sum of all file sizes under DISK_ROOT."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(DISK_ROOT):
        for name in filenames:
            if name == ".diskmeta.json":
                continue
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except Exception:
                pass
    return total


def free_bytes():
    return max(0, capacity_bytes() - used_bytes())


def usage_percent():
    cap = capacity_bytes()
    if cap <= 0:
        return 0
    return int(used_bytes() * 100 / cap)


def has_space_for(n_bytes):
    return free_bytes() >= n_bytes


# ==================================================================
# Path helpers
# ==================================================================
def disk_path(logical_path):
    """
    Convert a logical path like "/Documents/notes.txt" to a real
    on-disk path under DISK_ROOT. Refuses to escape DISK_ROOT.
    """
    p = (logical_path or "/").strip()
    p = p.replace("\\", "/")
    parts = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    real = os.path.join(DISK_ROOT, *parts)
    # safety: ensure real is under DISK_ROOT
    real_abs = os.path.abspath(real)
    if not real_abs.startswith(os.path.abspath(DISK_ROOT)):
        raise ValueError("path escapes disk root")
    return real_abs


def is_within_disk(real_path):
    try:
        return os.path.abspath(real_path).startswith(os.path.abspath(DISK_ROOT))
    except Exception:
        return False


# ==================================================================
# Operations
# ==================================================================
def listdir(logical_path):
    """Return list of (name, is_dir, size, mtime) for a logical path."""
    real = disk_path(logical_path)
    out = []
    if not os.path.isdir(real):
        raise NotADirectoryError(logical_path)
    for name in sorted(os.listdir(real)):
        if name == ".diskmeta.json":
            continue
        full = os.path.join(real, name)
        is_dir = os.path.isdir(full)
        try:
            size = 0 if is_dir else os.path.getsize(full)
            mtime = os.path.getmtime(full)
        except Exception:
            size = 0
            mtime = 0
        out.append((name, is_dir, size, mtime))
    return out


def mkdir(logical_path):
    real = disk_path(logical_path)
    os.makedirs(real, exist_ok=True)


def create_file(logical_path):
    real = disk_path(logical_path)
    if not has_space_for(1):
        raise OSError("No space left on device")
    with open(real, "a", encoding="utf-8"):
        pass


def read_file(logical_path):
    real = disk_path(logical_path)
    with open(real, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(logical_path, data):
    real = disk_path(logical_path)
    data_bytes = len(data.encode("utf-8"))
    # how much would this add?
    existing = 0
    if os.path.isfile(real):
        existing = os.path.getsize(real)
    delta = data_bytes - existing
    if delta > 0 and not has_space_for(delta):
        raise OSError("No space left on device")
    with open(real, "w", encoding="utf-8") as f:
        f.write(data)


def delete(logical_path):
    real = disk_path(logical_path)
    if os.path.isdir(real):
        shutil.rmtree(real)
    else:
        os.remove(real)


def rename(logical_path, new_name):
    real = disk_path(logical_path)
    # reject traversal / separators in the *new* name
    if not new_name or "/" in new_name or "\\" in new_name or new_name in (".", ".."):
        raise ValueError("invalid name: " + repr(new_name))
    parent = os.path.dirname(real)
    new_real = os.path.join(parent, new_name)
    # ensure destination is still inside DISK_ROOT
    if not is_within_disk(new_real):
        raise ValueError("path escapes disk root")
    os.rename(real, new_real)


def copy_file(logical_path, dest_logical):
    src = disk_path(logical_path)
    dst = disk_path(dest_logical)
    size = os.path.getsize(src) if os.path.isfile(src) else 0
    if not has_space_for(size):
        raise OSError("No space left on device")
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def import_from_host(host_path, dest_logical):
    """Copy a real host file into the disk, enforcing capacity."""
    size = os.path.getsize(host_path) if os.path.isfile(host_path) else 0
    if not has_space_for(size):
        raise OSError("No space left on device")
    dst = disk_path(dest_logical)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(host_path):
        shutil.copytree(host_path, dst)
    else:
        shutil.copy2(host_path, dst)


def info():
    return {
        "used": used_bytes(),
        "free": free_bytes(),
        "total": capacity_bytes(),
        "percent": usage_percent(),
    }


def format_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return ("%.1f %s" % (n, unit)) if unit != "B" else ("%d B" % n)
        n /= 1024.0
    return "%.1f PB" % n
