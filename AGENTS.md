# Agent Guidelines

- Commits must follow the Conventional Commits specification (for example, `fix: pause countdown when menu open`).
- Target Python 3.13; do not introduce compatibility shims for older versions.
- Always run `python -m pytest` in the project virtualenv before handing work back; headless SDL environment is configured automatically via `tests/conftest.py`.
