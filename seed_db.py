"""Seed the database with puzzles from puzzles.py."""
import db
import puzzles


def seed():
    db.init_db()

    existing = {name for _, name in db.list_puzzles()}

    puzzle_map = {
        "sample": puzzles.sample_puzzle,
        "lena": puzzles.lena_puzzle,
        "alvaro": puzzles.alvaro_puzzle,
    }

    for name, puzzle in puzzle_map.items():
        if name in existing:
            print(f"Skipping '{name}' (already exists)")
            continue
        categories_with_words = list(zip(puzzle["categories"], puzzle["sets"]))
        db.add_puzzle(name, categories_with_words)
        print(f"Added puzzle '{name}'")


if __name__ == "__main__":
    seed()
