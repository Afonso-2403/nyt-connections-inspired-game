**Connections App**

**Description:** 

A small prototype that mimics the New York Times "Connections" game. 
Pick the correct groups of four related words.

**Deployment**

This web app is deployed in [python anywhere](https://www.pythonanywhere.com) and can be accessed through [this url](https://connectionsstylegame.pythonanywhere.com/).

**Files & Components**
- **`app.py`:** Flask application and API endpoints
- **`puzzles.py`:** Example puzzles and their correct sets.
- **`templates/index.html`:** Minimal UI markup and placeholders for the grid and completed groups.
- **`static/main.js`:** Client-side logic for rendering the grid, selecting words, submitting checks, and showing completed groups.
- **`static/style.css`:** Styles for the grid, selection state, and completed group layout.
- **`pyproject.toml`:** Project metadata and dependencies.

**Run locally**

This project is managed with `uv`, for local development you should have it installed and from the project directory run:
```
uv run python ./app.py
```

**Add or edit puzzles**
- Edit `puzzles.py` and add puzzles to the same structure: a `words` list and `sets` (arrays of correct 4-word groups).


**License & Credits**
- This is a small prototype and not affiliated with the New York Times.
