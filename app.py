from flask import Flask, render_template, jsonify, request
import db

app = Flask(__name__)

# Initialize database tables on startup
db.init_db()

ACTIVE_PUZZLE = "lena"


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


if __name__ == "__main__":
    app.run(debug=True)
