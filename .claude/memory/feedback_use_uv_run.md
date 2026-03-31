---
name: use uv run for python
description: Always use uv run to invoke Python and pytest instead of bare python/pytest commands
type: feedback
---

## Always use `uv run` for Python commands

**Rule:** Use `uv run python`, `uv run pytest`, `uv run ruff`, `uv run mypy` etc. instead of bare `python`, `pytest`, `ruff`, `mypy` commands.

**Why:** The project uses `uv` as its package manager. Running tools via `uv run` ensures the correct virtual environment and dependencies are used.

**How to apply:**
- `uv run pytest` instead of `pytest`
- `uv run ruff check` instead of `ruff check`
- `uv run mypy` instead of `mypy`
- `uv run python script.py` instead of `python script.py`
