# How the window manager works

pyos.system.wm.WindowManager creates and manages windows for apps.

## Creating a window

BaseApp.launch calls wm.open(NAME, build, w, h, icon). WM creates a ManagedWindow (tk.Toplevel with overrideredirect(True)).

## Dragging

Title bar binds ButtonPress-1 and B1-Motion. _move recomputes x/y and calls _clamp_xy, which keeps the window inside wm.bounds.

## Bounds

wm.bounds = {x, y, w, h} of the desktop area. Refreshed on every open() and on every root <Configure> event.
