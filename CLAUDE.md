# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A NYT "Connections"-style word puzzle game built with Flask (Python backend) and vanilla JS frontend. Deployed on PythonAnywhere at connectionsstylegame.pythonanywhere.com.

## Running Locally

```bash
uv run python ./app.py
```

Requires `uv` for dependency management. Python 3.13+, Flask is the only dependency.

## Architecture

- **`app.py`** — Flask app with three routes: `GET /` (serves HTML), `GET /api/puzzle` (returns current puzzle JSON), `POST /api/check` (validates a group of 4 words against correct sets). The `ACTIVE_PUZZLE` variable controls which puzzle is served.
- **`db.py`** — SQLite database layer. Tables: `puzzles`, `categories`, `words`. Provides `get_puzzle_by_name()`, `add_puzzle()`, `list_puzzles()`. DB file is `connections.db` in the project root.
- **`seed_db.py`** — Migrates puzzles from the legacy `puzzles.py` into the database. Run with `uv run python seed_db.py`. Safe to re-run (skips existing puzzles).
- **`puzzles.py`** — Legacy puzzle definitions (kept for reference/seeding)
- **`static/main.js`** — Client-side game logic: grid rendering, word selection, group submission via fetch to `/api/check`
- **`templates/index.html`** — Single-page Jinja2 template

## Adding Puzzles

Use `db.add_puzzle()` to insert new puzzles programmatically, then set `ACTIVE_PUZZLE` in `app.py` to the puzzle name.
