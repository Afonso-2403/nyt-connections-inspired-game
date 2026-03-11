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


@app.route("/api/puzzle", methods=["POST"])
def create_puzzle():
    data = request.json or {}

    # Parse and strip name; generate if missing/blank
    name = (data.get("name") or "").strip()
    if not name:
        name = f"puzzle-{uuid.uuid4().hex[:6]}"

    # Validate categories structure
    categories = data.get("categories")
    if not categories or not isinstance(categories, list) or len(categories) != 4:
        return jsonify({"error": "Exactly 4 categories required"}), 400

    all_words = []
    categories_with_words = []
    for cat in categories:
        cat_name = (cat.get("name") or "").strip()
        if not cat_name:
            return jsonify({"error": "Category name must not be empty"}), 400

        words = cat.get("words")
        if not words or not isinstance(words, list) or len(words) != 4:
            return jsonify({"error": f"Category '{cat_name}' must have exactly 4 words"}), 400

        cleaned_words = []
        for w in words:
            word = (w or "").strip().upper()
            if not word:
                return jsonify({"error": "Words must not be empty"}), 400
            cleaned_words.append(word)

        all_words.extend(cleaned_words)
        categories_with_words.append((cat_name, cleaned_words))

    # Check for duplicate words across all categories
    if len(all_words) != len(set(all_words)):
        return jsonify({"error": "Duplicate words found across categories"}), 400

    try:
        puzzle_id = db.add_puzzle(name, categories_with_words)
    except Exception:
        return jsonify({"error": f"Puzzle name '{name}' already exists"}), 409

    return jsonify({"id": puzzle_id, "name": name}), 201


if __name__ == "__main__":
    app.run(debug=True)
