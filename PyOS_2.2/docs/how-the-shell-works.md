# How the shell works

PyShell is a POSIX-flavored shell written in pure Python.

## 1. Terminal widget

pyos.shell.terminal.Terminal is a tk.Text subclass. Enter -> self.on_command(line).

## 2. Expansion pipeline (pysh.PyShell.run)

`` 
line = self._expand_history(line)
line = self._expand_substitutions(line)
line = self._expand_arithmetic(line)
line = self._expand_vars(line)
line = self._expand_aliases(line)
line = self._expand_globs(line)
`` 

## 3. Parsing (pyos.shell.parser)

parse(line) returns list[ChainOp]. Each ChainOp has an operator (None, &&, ||, ;) and a Pipeline of Stage objects. A Stage has cmd, args, redirects.

## 4. Execution (pyos.shell.executor)

Each Stage runs with write/writeln/err/ok/info temporarily replaced by capturing versions. stdout of stage N becomes stdin of stage N+1.

## 5. Commands

Every command is fn(sh, args, line) in pyos/shell/commands/*.py. Each module has a COMMANDS dict. pyos/shell/commands/__init__.py merges them into ALL_COMMANDS.
