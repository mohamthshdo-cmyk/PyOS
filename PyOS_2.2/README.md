# PyOS

A Linux-style desktop environment written entirely in Python + Tkinter.

**This is a simulation, not a real OS.** It doesn't touch hardware, doesn't have a real kernel, and isn't a Linux replacement. It's a self-contained desktop environment that boots, logs in, and runs apps — all in Python.

![screenshot](docs/screenshot.png)

## Features

- Boot sequence + login (user accounts, password hashing, first-boot setup)
- Window manager (draggable, resizable, minimizable managed windows)
- Sidebar + launcher (every app reachable in one click)
- PyShell — POSIX-flavored shell with pipes, redirects, variables, globs, command substitution, aliases, history, job control
- Bundled apps: Terminal, Calculator, Notepad, File Explorer, PyChrome
- Virtual disk — sandboxed storage at ~/.pyos/disk/
- Real download manager — HTTP(S) to virtual disk /Downloads

## Install

Requirements: Python 3.9+ and tkinter.

### Windows
Install Python from python.org with "tcl/tk and IDLE" checked. Then:
`` 
pip install -r requirements.txt
python main.pyw
`` 

### Linux
`` 
sudo apt install python3-tk   # Debian/Ubuntu
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk   # Arch
pip install -r requirements.txt
python3 main.pyw
`` 

### macOS
`` 
brew install python-tk
pip install -r requirements.txt
python3 main.pyw
`` 

## First boot

1. Boot lines scroll
2. New username: type name, Enter
3. New password: type password, Enter
4. Desktop appears

Subsequent boots: pyos login: then password.

## Shell quick reference

`` 
help            list all commands
apps            list installed apps
launch <name>   open an app
echo hi | wc    pipe
ls -la > out    redirect
echo $HOME      variable expansion
cd /tmp         change directory
`` 

## Optional dependencies

- tkinterweb — PyChrome's embedded browser
- psutil — makes free show real memory numbers

## Documentation

- docs/architecture.md
- docs/how-the-shell-works.md
- docs/how-the-window-manager-works.md
- docs/how-apps-register.md

## License

MIT — see LICENSE.
