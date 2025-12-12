from flask import Flask, render_template, jsonify, request
import random
from puzzles import sample_puzzle

app = Flask(__name__)

# serve homepage
@app.route("/")
def index():
    return render_template("index.html")

# return a random puzzle
@app.route("/api/puzzle")
def puzzle():
    return jsonify(sample_puzzle)

# check a group
@app.route("/api/check", methods=["POST"])
def check_group():
    data = request.json
    group = data.get("group", [])

    # get correct sets
    correct_sets = sample_puzzle["sets"]
    categories = sample_puzzle["categories"]
    group_sorted = sorted(group)

    set_category = "No category"
    correct = False
    for set, category in zip(correct_sets, categories):
        if sorted(set) == group_sorted:
            correct = True
            set_category = category
            break

    response_dict = {
        "correct": correct,
        "category": set_category,
    }
    return jsonify(response_dict)

    return jsonify({"correct": correct})

if __name__ == "__main__":
    app.run(debug=True)
