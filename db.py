import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "connections.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id INTEGER NOT NULL REFERENCES puzzles(id),
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            text TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def add_puzzle(name, categories_with_words):
    """Insert a puzzle. categories_with_words is a list of (category_name, [words])."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO puzzles (name) VALUES (?)", (name,))
    puzzle_id = cur.lastrowid
    for i, (cat_name, words) in enumerate(categories_with_words):
        cur.execute(
            "INSERT INTO categories (puzzle_id, name, sort_order) VALUES (?, ?, ?)",
            (puzzle_id, cat_name, i),
        )
        cat_id = cur.lastrowid
        for word in words:
            cur.execute(
                "INSERT INTO words (category_id, text) VALUES (?, ?)",
                (cat_id, word),
            )
    conn.commit()
    conn.close()
    return puzzle_id


def get_puzzle_by_id(puzzle_id):
    """Return a puzzle dict: {name, words, sets, categories}."""
    conn = get_db()
    puzzle_row = conn.execute(
        "SELECT name FROM puzzles WHERE id = ?", (puzzle_id,)
    ).fetchone()
    if not puzzle_row:
        conn.close()
        return None

    cats = conn.execute(
        "SELECT id, name FROM categories WHERE puzzle_id = ? ORDER BY sort_order",
        (puzzle_id,),
    ).fetchall()
    if not cats:
        conn.close()
        return None

    sets = []
    categories = []
    all_words = []
    for cat in cats:
        categories.append(cat["name"])
        words = conn.execute(
            "SELECT text FROM words WHERE category_id = ?", (cat["id"],)
        ).fetchall()
        group = [w["text"] for w in words]
        sets.append(group)
        all_words.extend(group)
    conn.close()

    random.shuffle(all_words)
    return {
        "name": puzzle_row["name"],
        "words": all_words,
        "sets": sets,
        "categories": categories,
    }


def get_puzzle_by_name(name):
    """Look up a puzzle by name and return its formatted dict."""
    conn = get_db()
    row = conn.execute("SELECT id FROM puzzles WHERE name = ?", (name,)).fetchone()
    conn.close()
    if not row:
        return None
    return get_puzzle_by_id(row["id"])


def get_random_puzzle():
    """Return a random puzzle from the database, or None if empty."""
    conn = get_db()
    row = conn.execute("SELECT id FROM puzzles ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    if not row:
        return None
    return get_puzzle_by_id(row["id"])


def list_puzzles():
    """Return all puzzles as [(id, name), ...]."""
    conn = get_db()
    rows = conn.execute("SELECT id, name FROM puzzles ORDER BY id").fetchall()
    conn.close()
    return [(r["id"], r["name"]) for r in rows]
