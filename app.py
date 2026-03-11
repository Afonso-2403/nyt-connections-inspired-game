import uuid
from flask import Flask, render_template, jsonify, request
import db

app = Flask(__name__)

# Initialize database tables on startup
db.init_db()

ACTIVE_PUZZLE = "puzzle-b44e"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/puzzle")
def puzzle():
    game_puzzle = db.get_puzzle_by_name(ACTIVE_PUZZLE)
    if not game_puzzle:
        return jsonify({"error": "Puzzle not found"}), 404
    return jsonify(game_puzzle)


@app.route("/api/check", methods=["POST"])
def check_group():
    data = request.json
    group = data.get("group", [])

    game_puzzle = db.get_puzzle_by_name(ACTIVE_PUZZLE)
    if not game_puzzle:
        return jsonify({"error": "Puzzle not found"}), 404

    correct_sets = game_puzzle["sets"]
    categories = game_puzzle["categories"]
    group_sorted = sorted(group)

    set_category = "No category"
    correct = False
    for s, category in zip(correct_sets, categories):
        if sorted(s) == group_sorted:
            correct = True
            set_category = category
            break

    return jsonify({"correct": correct, "category": set_category})


def validate_and_clean_puzzle(data):
    """Validate and clean puzzle input data.

    Returns (name, categories_with_words) on success.
    Raises ValueError with a descriptive message on invalid input.
    """
    name = (data.get("name") or "").strip()
    if not name:
        name = f"puzzle-{uuid.uuid4().hex[:6]}"

    categories = data.get("categories")
    if not categories or not isinstance(categories, list) or len(categories) != 4:
        raise ValueError("Exactly 4 categories required")

    all_words = []
    categories_with_words = []
    for cat in categories:
        cat_name = (cat.get("name") or "").strip()
        if not cat_name:
            raise ValueError("Category name must not be empty")

        words = cat.get("words")
        if not words or not isinstance(words, list) or len(words) != 4:
            raise ValueError(f"Category '{cat_name}' must have exactly 4 words")

        cleaned_words = []
        for w in words:
            word = (w or "").strip().upper()
            if not word:
                raise ValueError("Words must not be empty")
            cleaned_words.append(word)

        all_words.extend(cleaned_words)
        categories_with_words.append((cat_name, cleaned_words))

    if len(all_words) != len(set(all_words)):
        raise ValueError("Duplicate words found across categories")

    return name, categories_with_words


@app.route("/api/puzzle", methods=["POST"])
def create_puzzle():
    data = request.json or {}
    try:
        name, categories_with_words = validate_and_clean_puzzle(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        puzzle_id = db.add_puzzle(name, categories_with_words)
    except Exception:
        return jsonify({"error": f"Puzzle name '{name}' already exists"}), 409

    return jsonify({"id": puzzle_id, "name": name}), 201


if __name__ == "__main__":
    app.run(debug=True)
