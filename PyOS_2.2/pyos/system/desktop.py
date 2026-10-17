"""PyOS desktop environment - flat background, sidebar, launcher."""
import tkinter as tk

from pyos.kernel.state import STATE
from pyos.system.wm import WindowManager
from pyos.system.sidebar import Sidebar


DESKTOP_BG = "#1a1b26"


class Desktop:
    def __init__(self):
        STATE.desktop = self

        self.launcher_visible = False
        self._shutting_down = False

        self.root = tk.Tk()
        self.root.title(
            "PyOS - " + str(STATE.current_user) +
            "@" + str(STATE.data["hostname"])
        )
        self.root.geometry("900x600")
        self.root.minsize(600, 400)
        self.root.configure(bg="#1a1b26")

        from pyos.apps import REGISTRY as APP_REGISTRY
        self.sidebar = Sidebar(self, self.toggle_launcher, APP_REGISTRY)
        self.wm = WindowManager(self.root, self.sidebar)

        self.area = tk.Canvas(self.root, bg=DESKTOP_BG,
                              highlightthickness=0)
        self.area.pack(side="left", fill="both", expand=True)

        self._build_launcher()

        self.root.bind("<Button-3>", self._ctx)
        self.root.after(600, self._auto_launch_terminal)
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

    # ==================================================================
    # LAUNCHER PANEL
    # ==================================================================
    def _build_launcher(self):
        self.launcher = tk.Frame(self.root, bg="#16161e", width=340)
        self.launcher.place(x=Sidebar.WIDTH, y=0, relheight=1)
        self.launcher.pack_propagate(False)

        tk.Label(self.launcher, text="Applications", bg="#16161e",
                 fg="#7aa2f7", font=("Segoe UI", 14, "bold")
                 ).pack(anchor="w", padx=16, pady=(18, 4))

        tk.Frame(self.launcher, bg="#2a2e3f", height=1
                 ).pack(fill="x", padx=16, pady=10)

        self._launcher_btn("T", "Terminal", self.open_terminal, accent=True)

        try:
            from pyos.apps import REGISTRY as APP_REGISTRY
            for key in sorted(APP_REGISTRY.keys(),
                              key=lambda k: APP_REGISTRY[k].get("name", k)):
                if key == "terminal":
                    continue
                meta = APP_REGISTRY[key]
                self._launcher_btn(
                    meta.get("icon", "?"),
                    meta.get("name", key.title()),
                    self._make_launcher(key),
                )
        except Exception as ex:
            print("[launcher] " + str(ex))

        foot = tk.Frame(self.launcher, bg="#16161e")
        foot.pack(side="bottom", fill="x", pady=10)
        tk.Frame(foot, bg="#2a2e3f", height=1
                 ).pack(fill="x", padx=16, pady=(0, 8))

        row = tk.Frame(foot, bg="#16161e")
        row.pack()
        tk.Button(row, text="Log out", bg="#16161e", fg="#c0caf5",
                  bd=0, activebackground="#1f2335",
                  activeforeground="#7aa2f7",
                  font=("Segoe UI", 9), padx=10,
                  command=self.logout).pack(side="left")
        tk.Button(row, text="Shutdown", bg="#16161e", fg="#f7768e",
                  bd=0, activebackground="#1f2335",
                  activeforeground="#f7768e",
                  font=("Segoe UI", 9), padx=10,
                  command=self.shutdown).pack(side="left")

        self.launcher.place_forget()

    def _launcher_btn(self, icon, label, cmd, accent=False):
        bg = "#1f2335" if accent else "#16161e"
        fg = "#7aa2f7" if accent else "#c0caf5"

        def _click():
            try:
                cmd()
            except Exception as ex:
                print("[launcher] " + str(ex))
            self._close_launcher()

        b = tk.Button(self.launcher,
                      text="   " + icon + "    " + label,
                      anchor="w", bg=bg, fg=fg, bd=0,
                      activebackground="#2a2e3f",
                      activeforeground="#7aa2f7",
                      font=("Segoe UI", 11), padx=16, pady=8,
                      command=_click)
        b.pack(fill="x", padx=8, pady=2)

    def _make_launcher(self, key):
        def _launch():
            self.open_app(key)
        return _launch

    def toggle_launcher(self):
        if self.launcher_visible:
            self._close_launcher()
        else:
            self.launcher.place(x=Sidebar.WIDTH, y=0, relheight=1)
            self.launcher.lift()
            self.launcher_visible = True

    def _close_launcher(self):
        if self.launcher_visible:
            self.launcher.place_forget()
            self.launcher_visible = False

    # ==================================================================
    # APP LAUNCHING
    # ==================================================================
    def _auto_launch_terminal(self):
        try:
            self.open_terminal()
        except Exception as ex:
            print("[desktop] auto-launch terminal failed: " + str(ex))

    def open_terminal(self):
        try:
            from pyos.apps.terminal_app import TerminalApp
            TerminalApp().launch(self.wm)
        except Exception as ex:
            print("[desktop] terminal failed: " + str(ex))

    def open_app(self, key):
        try:
            from pyos.apps import REGISTRY as APP_REGISTRY
            if key not in APP_REGISTRY:
                print("[desktop] unknown app: " + str(key))
                return
            cls = APP_REGISTRY[key]["class"]
            cls().launch(self.wm)
        except Exception as ex:
            print("[desktop] open_app(" + str(key) + ") failed: " + str(ex))

    # ==================================================================
    # CONTEXT MENU
    # ==================================================================
    def _ctx(self, e):
        m = tk.Menu(self.root, tearoff=0,
                    bg="#1f2335", fg="#c0caf5",
                    activebackground="#7aa2f7",
                    activeforeground="#16161e")
        m.add_command(label="  Terminal", command=self.open_terminal)
        m.add_separator()
        m.add_command(label="  Log out", command=self.logout)
        m.add_command(label="  Shutdown", command=self.shutdown)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    # ==================================================================
    # POWER
    # ==================================================================
    def shutdown(self):
        if self._shutting_down:
            return
        self._shutting_down = True
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        import sys
        sys.exit(0)

    def logout(self):
        self._shutting_down = True
        STATE.current_user = None
        STATE.save()
        try:
            self.root.destroy()
        except Exception:
            pass
        from pyos.system.boot import BootSequence
        BootSequence().start()

    # ==================================================================
    # MAIN LOOP
    # ==================================================================
    def run(self):
        self.root.mainloop()