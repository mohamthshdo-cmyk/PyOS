"""PyChrome - embedded browser with REAL downloads to Virtual Disk."""
import os
import time
import tkinter as tk
from tkinter import simpledialog

from pyos.apps.base import BaseApp
from pyos.kernel import downloads as dlmgr

try:
    from tkinterweb import HtmlFrame
    ENGINE_OK = True
except ImportError:
    ENGINE_OK = False


WORKING_SITES = [
    ("Wikipedia",         "https://en.wikipedia.org/wiki/Main_Page"),
    ("DuckDuckGo (HTML)", "https://html.duckduckgo.com/html/"),
    ("Python Docs",       "https://docs.python.org/3/"),
    ("PyPI",              "https://pypi.org/"),
    ("GitHub",            "https://github.com/"),
    ("Stack Overflow",    "https://stackoverflow.com/"),
    ("Hacker News",       "https://news.ycombinator.com/"),
    ("Arch Wiki",         "https://wiki.archlinux.org/"),
    ("MDN Web Docs",      "https://developer.mozilla.org/en-US/"),
    ("Project Gutenberg", "https://www.gutenberg.org/"),
    ("XKCD",              "https://xkcd.com/"),
    ("Text NPR",          "https://text.npr.org/"),
    ("CNN Lite",          "https://lite.cnn.com/"),
    ("Internet Archive",  "https://archive.org/"),
    ("OpenStreetMap",     "https://www.openstreetmap.org/"),
]

HOME_URL = "about:home"


class PyChromeApp(BaseApp):
    NAME = "PyChrome"
    ICON = "C"
    WIDTH = 1100
    HEIGHT = 700

    def build(self, parent):
        self.parent = parent
        self.history = []
        self.hist_idx = -1
        self.download_popups = {}   # Download -> Toplevel

        if not ENGINE_OK:
            self._show_missing_engine(parent)
            return

        self._build_toolbar(parent)
        self._build_bookmarks(parent)
        self._build_page(parent)
        self._build_status(parent)

        self._go(HOME_URL, push=False)

    def _show_missing_engine(self, parent):
        f = tk.Frame(parent, bg="#1a1b26"); f.pack(expand=True, fill="both")
        tk.Label(f, text="tkinterweb is not installed",
                 font=("Segoe UI", 16, "bold"),
                 bg="#1a1b26", fg="#7aa2f7").pack(pady=(80, 12))
        tk.Label(f, text="pip install tkinterweb",
                 font=("Consolas", 11),
                 bg="#1a1b26", fg="#9ece6a").pack()

    # ==================== toolbar ====================
    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg="#1f2335")
        bar.pack(fill="x")

        def btn(glyph, cmd):
            tk.Button(bar, text=glyph, bg="#2a2e3f", fg="#c0caf5",
                      bd=0, activebackground="#7aa2f7",
                      activeforeground="#16161e",
                      font=("Segoe UI Symbol", 12),
                      command=cmd).pack(side="left", padx=2, pady=4, ipadx=6)

        btn("\u2190", self._back)
        btn("\u2192", self._forward)
        btn("\u21bb", self._reload)
        btn("\u2302", self._home)

        self.url_var = tk.StringVar(value=HOME_URL)
        entry = tk.Entry(bar, textvariable=self.url_var,
                         bg="#1a1b26", fg="#c0caf5", bd=0,
                         insertbackground="#7aa2f7",
                         font=("Consolas", 10))
        entry.pack(side="left", fill="x", expand=True,
                   padx=6, pady=4, ipady=4)
        entry.bind("<Return>", lambda e: self._go(self.url_var.get()))

        tk.Button(bar, text="Go", bg="#7aa2f7", fg="#16161e",
                  bd=0, activebackground="#bb9af7",
                  activeforeground="#16161e",
                  font=("Segoe UI", 10, "bold"),
                  command=lambda: self._go(self.url_var.get())
                  ).pack(side="left", padx=(0, 4), pady=4, ipadx=12)

        btn("\u2b07", self._download_current)     # download icon
        btn("\U0001f4c2", self._show_downloads)  # folder

    # ==================== bookmarks ====================
    def _build_bookmarks(self, parent):
        bar = tk.Frame(parent, bg="#16161e")
        bar.pack(fill="x")

        favorites = [
            ("Wikipedia", "https://en.wikipedia.org/wiki/Main_Page"),
            ("DDG",       "https://html.duckduckgo.com/html/"),
            ("HN",        "https://news.ycombinator.com/"),
            ("PyDocs",    "https://docs.python.org/3/"),
            ("XKCD",      "https://xkcd.com/"),
            ("Start",     HOME_URL),
        ]
        for label, url in favorites:
            tk.Button(bar, text=label, bg="#16161e", fg="#7aa2f7",
                      bd=0, activebackground="#2a2e3f",
                      activeforeground="#bb9af7",
                      font=("Segoe UI", 9),
                      command=lambda u=url: self._go(u)
                      ).pack(side="left", padx=4, pady=3)

    # ==================== page ====================
    def _build_page(self, parent):
        self.page_holder = tk.Frame(parent, bg="#0c0c0c")
        self.page_holder.pack(fill="both", expand=True)
        self.html = HtmlFrame(self.page_holder, messages_enabled=False)
        self.html.pack(fill="both", expand=True)
        try:
            self.html.add_link_handler(self._on_link)
        except Exception:
            pass

    def _build_status(self, parent):
        self.status = tk.Label(parent, text="", bg="#1f2335", fg="#565f89",
                               anchor="w", font=("Segoe UI", 8))
        self.status.pack(fill="x", side="bottom")

    # ==================== nav ====================
    def _go(self, url, push=True):
        url = self._normalize(url)
        if url == HOME_URL:
            self._show_start_page()
        else:
            try:
                self.html.load_url(url)
            except Exception as e:
                self.status.config(text="Error: " + str(e), fg="#f7768e")
                return
        self.url_var.set(url)
        self.status.config(text="Loaded: " + url, fg="#565f89")
        if push:
            self.history = self.history[:self.hist_idx + 1]
            self.history.append(url)
            self.hist_idx = len(self.history) - 1

    def _normalize(self, url):
        url = (url or "").strip()
        if not url:
            return HOME_URL
        if url == HOME_URL:
            return url
        first = url.split(" ")[0]
        if "." not in first and not url.startswith(("http://", "https://")):
            q = url.replace(" ", "+")
            return "https://html.duckduckgo.com/html/?q=" + q
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    def _on_link(self, url):
        if url:
            self._go(url)

    def _back(self):
        if self.hist_idx > 0:
            self.hist_idx -= 1
            self._go(self.history[self.hist_idx], push=False)

    def _forward(self):
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self._go(self.history[self.hist_idx], push=False)

    def _reload(self):
        if self.hist_idx >= 0:
            self._go(self.history[self.hist_idx], push=False)

    def _home(self):
        self._go(HOME_URL)

    # ==================== downloads ====================
    def _download_current(self):
        """Ask for a URL, then start the real download into /Downloads."""
        default = self.url_var.get()
        if default in ("", HOME_URL):
            return self.status.config(
                text="Nothing to download (no URL in bar)", fg="#f7768e")
        url = simpledialog.askstring("Download",
                                     "URL to download:",
                                     initialvalue=default)
        if not url:
            return
        self._start_download(url)

    def _start_download(self, url):
        try:
            dl = dlmgr.start(url, listener=self._on_download_progress)
        except Exception as e:
            self.status.config(text="Download failed to start: " + str(e),
                               fg="#f7768e")
            return
        self._open_download_popup(dl)
        self.status.config(
            text="Downloading: " + dl.filename, fg="#7dcfff")

    def _open_download_popup(self, dl):
        win = tk.Toplevel(self.parent)
        win.title("Downloading " + dl.filename)
        win.geometry("460x160")
        win.configure(bg="#1a1b26")
        win.transient(self.parent)

        tk.Label(win, text=dl.filename, bg="#1a1b26", fg="#c0caf5",
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=12, pady=(12, 2))
        tk.Label(win, text=dl.url, bg="#1a1b26", fg="#565f89",
                 font=("Consolas", 8), anchor="w",
                 wraplength=440, justify="left").pack(fill="x", padx=12)

        bar = tk.Canvas(win, bg="#1f2335", height=18,
                        highlightthickness=0)
        bar.pack(fill="x", padx=12, pady=10)
        fill = bar.create_rectangle(0, 0, 0, 18, fill="#7aa2f7")

        info = tk.Label(win, text="Starting...", bg="#1a1b26",
                        fg="#c0caf5", font=("Consolas", 9))
        info.pack(pady=(0, 12))

        self.download_popups[dl] = {
            "win": win, "bar": bar, "fill": fill, "info": info,
            "_dirty": True,
        }
        self._poll_downloads()

    def _poll_downloads(self):
        """Tk-side poller: refreshes dirty download popups every 250 ms."""
        for dl, popup in list(self.download_popups.items()):
            if popup.get("_dirty"):
                popup["_dirty"] = False
                try:
                    self._update_download_ui(dl)
                except Exception:
                    pass
        try:
            self.parent.after(250, self._poll_downloads)
        except Exception:
            pass

    def _on_download_progress(self, dl):
        # called from the worker thread — do NOT touch Tk here.
        # Instead mark the popup dirty; a Tk-side poller reads the flag.
        popup = self.download_popups.get(dl)
        if popup is not None:
            popup["_dirty"] = True

    def _update_download_ui(self, dl):
        popup = self.download_popups.get(dl)
        if not popup:
            return
        try:
            pct = dl.percent()
            popup["bar"].coords(
                popup["fill"], 0, 0,
                pct * popup["bar"].winfo_width() // 100, 18)
            if dl.state == "Downloading":
                popup["info"].config(
                    text="%d%% (%s / %s)" % (
                        pct, dl.human_size(dl.got), dl.human_size(dl.total)),
                    fg="#c0caf5")
            elif dl.state == "Done":
                popup["info"].config(
                    text="Done: " + dl.human_size(dl.got) +
                         "  ->  " + dl.dest_logical,
                    fg="#9ece6a")
                self.status.config(
                    text="Downloaded " + dl.filename + " to " +
                         dl.dest_logical, fg="#9ece6a")
                # auto-close after a moment
                popup["win"].after(2500, popup["win"].destroy)
                self.download_popups.pop(dl, None)
            elif dl.state == "Failed":
                popup["info"].config(
                    text="Failed: " + (dl.error or "unknown error"),
                    fg="#f7768e")
                self.status.config(
                    text="Download failed: " + dl.filename, fg="#f7768e")
                popup["win"].after(4000, popup["win"].destroy)
                self.download_popups.pop(dl, None)
        except Exception:
            pass

    def _show_downloads(self):
        """A small window listing download history."""
        win = tk.Toplevel(self.parent)
        win.title("Downloads")
        win.geometry("640x400")
        win.configure(bg="#1a1b26")

        tk.Label(win, text="Downloads", bg="#1a1b26", fg="#7aa2f7",
                 font=("Segoe UI", 14, "bold")).pack(pady=(12, 4))

        lb = tk.Listbox(win, bg="#0c0c0c", fg="#c0caf5",
                        bd=0, font=("Consolas", 10),
                        selectbackground="#7aa2f7",
                        selectforeground="#16161e")
        lb.pack(fill="both", expand=True, padx=12, pady=8)

        items = dlmgr.get_history()
        if not items:
            lb.insert("end", "(no downloads yet)")
        for dl in items:
            when = time.strftime("%H:%M:%S", time.localtime(dl.started))
            status = dl.state
            size = dl.human_size(dl.got if dl.state != "Done" else dl.got)
            lb.insert("end", "%s  %-10s  %-10s  %s  ->  %s" % (
                when, status, size, dl.filename, dl.dest_logical))

    # ==================== start page ====================
    def _show_start_page(self):
        rows = []
        for name, url in WORKING_SITES:
            rows.append(
                '<tr>'
                '<td style="padding:6px 10px;">'
                '<a href="' + url + '" style="color:#7aa2f7;text-decoration:none;">' + name + '</a>'
                '</td>'
                '<td style="padding:6px 10px;color:#565f89;font-size:11px;">' + url + '</td>'
                '</tr>'
            )
        html = (
            '<html><head><meta charset="utf-8"></head>'
            '<body style="background:#1a1b26;color:#c0caf5;'
            'font-family:Segoe UI,Arial,sans-serif;padding:24px;">'
            '<h1 style="color:#7aa2f7;margin:0 0 4px 0;">PyChrome</h1>'
            '<p style="color:#565f89;margin:0 0 20px 0;">'
            'Downloads land in <b>/Downloads</b> on the Virtual Disk.'
            '</p>'
            '<table style="border-collapse:collapse;">'
            + "".join(rows) +
            '</table>'
            '<p style="color:#565f89;margin-top:24px;font-size:12px;">'
            'Tip: paste any direct file URL (ending in .pdf, .zip, .txt) '
            'into the URL bar and press Enter, then click the '
            '\u2b07 button to download it.</p>'
            '</body></html>'
        )
        try:
            self.html.load_html(html)
        except Exception as e:
            self.status.config(text="Start page error: " + str(e),
                               fg="#f7768e")
