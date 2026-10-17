"""
Real download manager for PyOS.

All downloads land in the virtual disk's Downloads folder.
Each download runs on a background thread, reports progress to a
listener callback, and is recorded in a small in-memory history.
"""
import os
import threading
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse, unquote

from pyos.kernel import disk as vdisk


# ==================================================================
# In-memory history (latest N downloads)
# ==================================================================
class Download:
    def __init__(self, url, filename, dest_logical):
        self.url = url
        self.filename = filename
        self.dest_logical = dest_logical
        self.total = 0
        self.got = 0
        self.state = "Pending"     # Pending, Downloading, Done, Failed, Cancelled
        self.error = ""
        self.started = time.time()
        self.finished = 0.0

    def percent(self):
        if self.total <= 0:
            return 0
        return min(100, int(self.got * 100 / self.total))

    def human_size(self, n=None):
        if n is None:
            n = self.total or self.got
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return "%.1f %s" % (n, unit)
            n /= 1024.0
        return "%.1f TB" % n


_history = []
_history_lock = threading.Lock()
MAX_HISTORY = 50


def get_history():
    with _history_lock:
        return list(reversed(_history))


def clear_history():
    with _history_lock:
        _history.clear()


def _record(dl):
    with _history_lock:
        _history.append(dl)
        if len(_history) > MAX_HISTORY:
            del _history[0:len(_history) - MAX_HISTORY]


# ==================================================================
# Public API
# ==================================================================
def default_dest_logical(filename):
    """Downloads always go to /Downloads/<filename>."""
    return "/Downloads/" + filename


def filename_from_url(url):
    try:
        path = urlparse(url).path
        name = unquote(os.path.basename(path))
    except Exception:
        name = ""
    if not name:
        name = "download_" + str(int(time.time()))
    # sanitize
    bad = '<>:"/\\|?*'
    for c in bad:
        name = name.replace(c, "_")
    return name


def start(url, listener=None, filename=None):
    """
    Start a download in the background. Returns the Download object
    immediately. `listener(dl)` is called on progress updates.
    """
    if not filename:
        filename = filename_from_url(url)
    dest_logical = default_dest_logical(filename)
    dl = Download(url, filename, dest_logical)
    _record(dl)

    thread = threading.Thread(
        target=_run_download,
        args=(dl, listener),
        daemon=True,
    )
    thread.start()
    return dl


def _run_download(dl, listener):
    dl.state = "Downloading"
    _notify(listener, dl)

    try:
        # Reserve space check — need at least 1 byte free to start
        if not vdisk.has_space_for(1):
            raise OSError("No space left on device")

        req = urllib.request.Request(
            dl.url,
            headers={"User-Agent": "PyOS-PyChrome/2.0"},
        )

        real_dest = vdisk.disk_path(dl.dest_logical)
        os.makedirs(os.path.dirname(real_dest), exist_ok=True)

        with urllib.request.urlopen(req, timeout=30) as resp:
            length = resp.getheader("Content-Length")
            try:
                dl.total = int(length) if length else 0
            except Exception:
                dl.total = 0

            # capacity check against declared size
            if dl.total > 0 and not vdisk.has_space_for(dl.total):
                raise OSError("No space left on device")

            # write in chunks
            with open(real_dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    dl.got += len(chunk)
                    # live disk space check every 256 KB
                    if dl.got % (256 * 1024) < 65536:
                        if not vdisk.has_space_for(len(chunk) + 1):
                            raise OSError("No space left on device")
                    f.write(chunk)
                    _notify(listener, dl)

        dl.state = "Done"
        dl.finished = time.time()
        _notify(listener, dl)

    except urllib.error.HTTPError as e:
        dl.state = "Failed"
        dl.error = "HTTP " + str(e.code) + " " + str(e.reason)
    except urllib.error.URLError as e:
        dl.state = "Failed"
        dl.error = "URL error: " + str(e.reason)
    except Exception as e:
        dl.state = "Failed"
        dl.error = str(e)
    finally:
        if dl.state != "Done":
            dl.finished = time.time()
        _notify(listener, dl)


def _notify(listener, dl):
    if listener is None:
        return
    try:
        listener(dl)
    except Exception:
        pass
