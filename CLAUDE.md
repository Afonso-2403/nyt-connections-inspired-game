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

- **`app.py`** — Flask app with three routes: `GET /` (serves HTML), `GET /api/puzzle` (returns current puzzle JSON), `POST /api/check` (validates a group of 4 words against correct sets)
- **`puzzles.py`** — Puzzle definitions as dicts with `words` (16 items), `sets` (4 groups of 4), and `categories` (4 labels). The active puzzle is selected by changing the `game_puzzle` variable in `app.py`
- **`static/main.js`** — Client-side game logic: grid rendering, word selection, group submission via fetch to `/api/check`
- **`templates/index.html`** — Single-page Jinja2 template

## Adding Puzzles

Add a new dict to `puzzles.py` following the existing structure, then update `game_puzzle` in `app.py` to point to it.
