# PyOS Architecture

A Linux-shaped desktop, running as a single Tkinter process.

## Boot flow

`` 
main.pyw
  -> pyos.kernel.core.Kernel().boot()
       -> pyos.system.boot.BootSequence().start()
            -> renders boot lines
            -> login
            -> pyos.system.desktop.Desktop().run()
                 -> Sidebar
                 -> WindowManager
                 -> Canvas
                 -> Launcher panel
`` 

## Module map

`` 
pyos/
  kernel/    state, users, disk, downloads
  apps/      BaseApp + every app
  shell/     PyShell (pysh, parser, executor, terminal, commands/)
  system/    boot, desktop, sidebar, wm
`` 

The kernel is not a real kernel — it's a package holding global state.
The shell is real: parse, expand, pipe, redirect.
