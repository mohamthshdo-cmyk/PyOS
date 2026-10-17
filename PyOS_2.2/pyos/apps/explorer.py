"""File Explorer for PyOS - virtual disk + optional host browse."""
import os
import datetime
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk

from pyos.apps.base import BaseApp
from pyos.kernel import disk as vdisk


def _fmt_time(ts):
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


class ExplorerApp(BaseApp):
    NAME = "File Explorer"
    ICON = "F"
    WIDTH = 1000
    HEIGHT = 620

    def build(self, parent):
        vdisk.ensure()

        self.parent = parent
        self.mode = "disk"           # "disk" or "host"
        self.disk_cwd = "/"          # logical path inside virtual disk
        self.host_cwd = os.path.expanduser("~")

        self._build_toolbar(parent)
        self._build_main(parent)
        self._build_status(parent)

        self._refresh()

    # ==================== toolbar ====================
    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg="#1f2335")
        bar.pack(fill="x")

        def btn(glyph, cmd):
            tk.Button(bar, text=glyph, bg="#2a2e3f", fg="#c0caf5",
                      bd=0, activebackground="#7aa2f7",
                      activeforeground="#16161e",
                      font=("Segoe UI Symbol", 11),
                      command=cmd).pack(side="left", padx=2, pady=4, ipadx=6)

        btn("\u2191", self._up)
        btn("\u2302", self._home)
        btn("\u21bb", self._refresh)

        self.path_var = tk.StringVar()
        entry = tk.Entry(bar, textvariable=self.path_var,
                         bg="#1a1b26", fg="#c0caf5",
                         insertbackground="#7aa2f7", bd=0,
                         font=("Consolas", 10))
        entry.pack(side="left", fill="x", expand=True,
                   padx=6, pady=4, ipady=4)
        entry.bind("<Return>", lambda e: self._navigate(self.path_var.get()))

        btn("\U0001f4c1+", self._new_folder)
        btn("\U0001f4c4+", self._new_file)
        btn("\u270f", self._rename_selected)
        btn("\U0001f5d1", self._delete_selected)

    # ==================== main area ====================
    def _build_main(self, parent):
        wrap = tk.Frame(parent, bg="#1a1b26")
        wrap.pack(fill="both", expand=True)

        # --- sidebar ---
        left = tk.Frame(wrap, bg="#1f2335", width=210)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Storage", bg="#1f2335", fg="#7aa2f7",
                 font=("Segoe UI", 10, "bold"), anchor="w"
                 ).pack(fill="x", padx=12, pady=(12, 4))

        self._side_btn(left, "\U0001f4be  Virtual Disk", self._go_disk_root)

        tk.Frame(left, bg="#2a2e3f", height=1).pack(fill="x", padx=10, pady=8)

        tk.Label(left, text="Disk Folders", bg="#1f2335", fg="#7aa2f7",
                 font=("Segoe UI", 10, "bold"), anchor="w"
                 ).pack(fill="x", padx=12, pady=(0, 4))
        for name in ("Documents", "Downloads", "Pictures", "Music", "Videos", "Temp"):
            self._side_btn(left, "\U0001f4c1  " + name,
                           (lambda n=name: self._go_disk("/" + n)))

        tk.Frame(left, bg="#2a2e3f", height=1).pack(fill="x", padx=10, pady=8)

        tk.Label(left, text="Host", bg="#1f2335", fg="#7aa2f7",
                 font=("Segoe UI", 10, "bold"), anchor="w"
                 ).pack(fill="x", padx=12, pady=(0, 4))
        self._side_btn(left, "\U0001f310  Host Home", self._go_host_home)
        self._side_btn(left, "\U0001f4c2  PyOS Install", self._go_host_pyos)

        # --- file table ---
        right = tk.Frame(wrap, bg="#1a1b26")
        right.pack(side="left", fill="both", expand=True)

        cols = ("name", "size", "modified", "type")
        self.tree = ttk.Treeview(right, columns=cols, show="headings",
                                     selectmode="browse")
        self.tree.heading("name", text="Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")
        self.tree.heading("type", text="Type")
        self.tree.column("name", width=360)
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("modified", width=150)
        self.tree.column("type", width=110)
        self.tree.tag_configure("dir", foreground="#7aa2f7")
        self.tree.tag_configure("file", foreground="#c0caf5")

        vsb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Double-Button-1>", self._on_double)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _side_btn(self, parent, label, cmd):
        b = tk.Button(parent, text=label, anchor="w",
                      bg="#1f2335", fg="#c0caf5", bd=0,
                      activebackground="#2a2e3f",
                      activeforeground="#7aa2f7",
                      font=("Segoe UI", 10), padx=12, pady=5,
                      command=cmd)
        b.pack(fill="x")

    # ==================== status bar ====================
    def _build_status(self, parent):
        bar = tk.Frame(parent, bg="#1f2335", height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status = tk.Label(bar, text="", bg="#1f2335", fg="#565f89",
                               anchor="w", font=("Segoe UI", 9))
        self.status.pack(side="left", padx=10)

        self.disk_label = tk.Label(bar, text="", bg="#1f2335",
                                   fg="#7aa2f7", anchor="e",
                                   font=("Segoe UI", 9))
        self.disk_label.pack(side="right", padx=10)

    def _set_status(self, text):
        self.status.config(text=text)

    def _update_disk_label(self):
        info = vdisk.info()
        self.disk_label.config(
            text="Disk: " + vdisk.format_human(info["used"]) +
                 " / " + vdisk.format_human(info["total"]) +
                 " (" + str(info["percent"]) + "%)")

    # ==================== navigation ====================
    def _go_disk_root(self):
        self.mode = "disk"
        self.disk_cwd = "/"
        self._refresh()

    def _go_disk(self, path):
        self.mode = "disk"
        self.disk_cwd = path
        self._refresh()

    def _go_host_home(self):
        self.mode = "host"
        self.host_cwd = os.path.expanduser("~")
        self._refresh()

    def _go_host_pyos(self):
        self.mode = "host"
        self.host_cwd = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".."))
        self._refresh()

    def _up(self):
        if self.mode == "disk":
            if self.disk_cwd in ("/", ""):
                return
            parent = "/" + "/".join(self.disk_cwd.strip("/").split("/")[:-1])
            if parent == "/":
                parent = "/"
            self.disk_cwd = parent
        else:
            parent = os.path.dirname(self.host_cwd)
            if parent and parent != self.host_cwd:
                self.host_cwd = parent
        self._refresh()

    def _home(self):
        if self.mode == "disk":
            self._go_disk_root()
        else:
            self._go_host_home()

    def _navigate(self, path):
        if self.mode == "disk":
            self.disk_cwd = path if path.startswith("/") else "/" + path
        else:
            self.host_cwd = os.path.expanduser(path)
        self._refresh()

    # ==================== refresh ====================
    def _refresh(self):
        self.tree.delete(*self.tree.get_children())

        try:
            if self.mode == "disk":
                self.path_var.set(self.disk_cwd)
                entries = vdisk.listdir(self.disk_cwd)
                for name, is_dir, size, mtime in entries:
                    icon = "\U0001f4c1 " if is_dir else "\U0001f4c4 "
                    sz = "" if is_dir else vdisk.format_human(size)
                    tp = "Folder" if is_dir else (
                        os.path.splitext(name)[1] or "File")
                    self.tree.insert("", "end",
                                     values=(icon + name, sz,
                                             _fmt_time(mtime), tp),
                                     tags=("dir" if is_dir else "file",))
                self._set_status(
                    str(len(entries)) + " item(s) on Virtual Disk")
            else:
                self.path_var.set(self.host_cwd)
                names = sorted(os.listdir(self.host_cwd),
                               key=lambda n: (not os.path.isdir(
                                   os.path.join(self.host_cwd, n)),
                                   n.lower()))
                for name in names:
                    full = os.path.join(self.host_cwd, name)
                    is_dir = os.path.isdir(full)
                    try:
                        size = 0 if is_dir else os.path.getsize(full)
                        mtime = os.path.getmtime(full)
                    except Exception:
                        size, mtime = 0, 0
                    icon = "\U0001f4c1 " if is_dir else "\U0001f4c4 "
                    sz = "" if is_dir else vdisk.format_human(size)
                    tp = "Folder" if is_dir else (
                        os.path.splitext(name)[1] or "File")
                    self.tree.insert("", "end",
                                     values=(icon + name, sz,
                                             _fmt_time(mtime), tp),
                                     tags=("dir" if is_dir else "file",))
                self._set_status(
                    str(len(names)) + " item(s) on Host")
        except Exception as e:
            self._set_status("Error: " + str(e))

        self._update_disk_label()

    # ==================== helpers ====================
    def _selected_name(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return None
        return vals[0].split(" ", 1)[1] if " " in vals[0] else vals[0]

    def _selected_logical(self):
        name = self._selected_name()
        if not name:
            return None
        if self.mode == "disk":
            base = self.disk_cwd.rstrip("/")
            return (base + "/" + name) if base else ("/" + name)
        else:
            return os.path.join(self.host_cwd, name)

    def _on_select(self, e=None):
        full = self._selected_logical()
        if full:
            self._set_status("Selected: " + full)

    def _on_double(self, e=None):
        name = self._selected_name()
        if not name:
            return
        if self.mode == "disk":
            full = self._selected_logical()
            try:
                real = vdisk.disk_path(full)
                if os.path.isdir(real):
                    self.disk_cwd = full
                    self._refresh()
                else:
                    self._open_file_real(real)
            except Exception as ex:
                messagebox.showerror("Open", str(ex))
        else:
            full = os.path.join(self.host_cwd, name)
            if os.path.isdir(full):
                self.host_cwd = full
                self._refresh()
            else:
                self._open_file_real(full)

    def _open_file_real(self, real_path):
        try:
            os.startfile(real_path)
        except Exception:
            try:
                import subprocess
                subprocess.Popen(["xdg-open", real_path])
            except Exception as e:
                messagebox.showerror("Open", "Cannot open:\n" + str(e))

    # ==================== file operations ====================
    def _new_folder(self):
        name = simpledialog.askstring("New folder", "Folder name:",
                                      initialvalue="New Folder")
        if not name:
            return
        try:
            if self.mode == "disk":
                base = self.disk_cwd.rstrip("/")
                vdisk.mkdir((base + "/" + name) if base else ("/" + name))
            else:
                os.makedirs(os.path.join(self.host_cwd, name), exist_ok=True)
            self._refresh()
        except Exception as e:
            messagebox.showerror("New folder", str(e))

    def _new_file(self):
        name = simpledialog.askstring("New file", "File name:",
                                      initialvalue="untitled.txt")
        if not name:
            return
        try:
            if self.mode == "disk":
                base = self.disk_cwd.rstrip("/")
                vdisk.create_file((base + "/" + name) if base else ("/" + name))
            else:
                open(os.path.join(self.host_cwd, name), "a").close()
            self._refresh()
        except Exception as e:
            messagebox.showerror("New file", str(e))

    def _rename_selected(self):
        old = self._selected_name()
        if not old:
            return
        new = simpledialog.askstring("Rename", "New name:", initialvalue=old)
        if not new or new == old:
            return
        try:
            if self.mode == "disk":
                full = self._selected_logical()
                vdisk.rename(full, new)
            else:
                os.rename(os.path.join(self.host_cwd, old),
                          os.path.join(self.host_cwd, new))
            self._refresh()
        except Exception as e:
            messagebox.showerror("Rename", str(e))

    def _delete_selected(self):
        name = self._selected_name()
        if not name:
            return
        if not messagebox.askyesno("Delete", "Delete " + name + "?"):
            return
        try:
            if self.mode == "disk":
                vdisk.delete(self._selected_logical())
            else:
                full = os.path.join(self.host_cwd, name)
                if os.path.isdir(full):
                    import shutil
                    shutil.rmtree(full)
                else:
                    os.remove(full)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Delete", str(e))

    def _import_from_host(self):
        """Copy a host file into the virtual disk."""
        path = filedialog.askopenfilename(title="Import into Virtual Disk")
        if not path:
            return
        dest_name = os.path.basename(path)
        base = self.disk_cwd.rstrip("/")
        dest_logical = (base + "/" + dest_name) if base else ("/" + dest_name)
        try:
            vdisk.import_from_host(path, dest_logical)
            self._set_status("Imported " + dest_name)
            self._refresh()
        except OSError as e:
            messagebox.showerror("Import failed", str(e))

    def _on_right_click(self, e):
        row = self.tree.identify_row(e.y)
        if row:
            self.tree.selection_set(row)
        m = tk.Menu(self.parent, tearoff=0, bg="#1f2335", fg="#c0caf5",
                    activebackground="#7aa2f7", activeforeground="#16161e")
        m.add_command(label="  Open", command=self._on_double)
        m.add_command(label="  Rename", command=self._rename_selected)
        m.add_command(label="  Delete", command=self._delete_selected)
        m.add_separator()
        m.add_command(label="  New Folder", command=self._new_folder)
        m.add_command(label="  New File", command=self._new_file)
        m.add_separator()
        if self.mode == "host":
            m.add_command(label="  Copy into Disk",
                          command=self._import_from_host)
        m.add_command(label="  Copy Path", command=self._copy_path)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def _copy_path(self):
        p = self._selected_logical() or self.path_var.get()
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(p)
            self._set_status("Copied: " + p)
        except Exception:
            pass
