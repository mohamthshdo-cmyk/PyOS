# How to add an app

Every app is a BaseApp subclass, registered in pyos/apps/__init__.py.

## 1. Write the app

`` 
import tkinter as tk
from pyos.apps.base import BaseApp

class HelloApp(BaseApp):
    NAME = "Hello"
    ICON = "H"
    WIDTH = 400
    HEIGHT = 300
    def build(self, parent):
        tk.Label(parent, text="Hello from PyOS!",
                 bg="#1a1b26", fg="#c0caf5").pack(expand=True)
`` 

## 2. Register it

Inside pyos/apps/__init__.py _build():

`` 
try:
    from pyos.apps import hello
    reg["hello"] = {"name": "Hello", "icon": "H", "class": hello.HelloApp}
except Exception as e:
    print("[apps] hello not loaded: " + str(e))
`` 

## 3. Restart PyOS

Sidebar gets a new icon, launcher shows it, apps lists it, launch hello opens it.

## Conventions

NAME — window title. ICON — single character. WIDTH/HEIGHT — initial size. build(parent) — build UI inside parent.
Colors: #1a1b26 bg, #c0caf5 fg, #7aa2f7 accent.
