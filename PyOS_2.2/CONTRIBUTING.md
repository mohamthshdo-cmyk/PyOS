# Contributing to PyOS

- Add an app — see docs/how-apps-register.md
- Add a shell command — see docs/how-the-shell-works.md
- Fix a bug — open an issue first
- Improve docs — welcome

Code style: Python 3.9+, stdlib only, match colors (#1a1b26 bg, #c0caf5 fg, #7aa2f7 accent).

Test before pushing:
`` 
python -m py_compile pyos/**/*.py
python main.pyw
`` 
