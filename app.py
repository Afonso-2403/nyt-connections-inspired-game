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
    group_sorted = sorted(group)

    correct = False
    for s in correct_sets:
        if sorted(s) == group_sorted:
            correct = True
            break

    return jsonify({"correct": correct})

if __name__ == "__main__":
    app.run(debug=True)
