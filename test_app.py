import os
import tempfile
import pytest
import db


SAMPLE_PUZZLE = [
    ("Fruits", ["APPLE", "BANANA", "ORANGE", "CHERRY"]),
    ("Vehicles", ["CAR", "TRUCK", "BICYCLE", "BOAT"]),
    ("Animals", ["CAT", "DOG", "FISH", "LION"]),
    ("Furniture", ["SOFA", "BED", "CHAIR", "TABLE"]),
]


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    """Use a temporary database for every test."""
    test_db = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", test_db)
    db.init_db()
    yield test_db


# --- db layer tests ---


class TestDB:
    def test_add_and_get_puzzle_by_id(self):
        pid = db.add_puzzle("test", SAMPLE_PUZZLE)
        puzzle = db.get_puzzle_by_id(pid)

        assert puzzle is not None
        assert sorted(puzzle["words"]) == sorted(
            [w for _, words in SAMPLE_PUZZLE for w in words]
        )
        assert puzzle["sets"] == [words for _, words in SAMPLE_PUZZLE]
        assert puzzle["categories"] == [cat for cat, _ in SAMPLE_PUZZLE]

    def test_get_puzzle_by_name(self):
        db.add_puzzle("fruits_test", SAMPLE_PUZZLE)
        puzzle = db.get_puzzle_by_name("fruits_test")

        assert puzzle is not None
        assert puzzle["categories"] == ["Fruits", "Vehicles", "Animals", "Furniture"]

    def test_get_nonexistent_puzzle_by_name(self):
        assert db.get_puzzle_by_name("does_not_exist") is None

    def test_get_nonexistent_puzzle_by_id(self):
        assert db.get_puzzle_by_id(9999) is None

    def test_list_puzzles(self):
        db.add_puzzle("one", SAMPLE_PUZZLE)
        db.add_puzzle("two", SAMPLE_PUZZLE[:2])
        result = db.list_puzzles()

        assert len(result) == 2
        names = [name for _, name in result]
        assert "one" in names
        assert "two" in names

    def test_duplicate_puzzle_name_raises(self):
        db.add_puzzle("unique", SAMPLE_PUZZLE)
        with pytest.raises(Exception):
            db.add_puzzle("unique", SAMPLE_PUZZLE)

    def test_words_are_shuffled(self):
        """Words list should be shuffled (not always match insertion order)."""
        db.add_puzzle("shuffle_test", SAMPLE_PUZZLE)
        original_order = [w for _, words in SAMPLE_PUZZLE for w in words]
        # Run multiple times — extremely unlikely to match every time if shuffled
        matched = 0
        for _ in range(10):
            puzzle = db.get_puzzle_by_name("shuffle_test")
            assert puzzle

            if puzzle["words"] == original_order:
                matched += 1
        assert matched < 10, "Words were never shuffled across 10 retrievals"

    def test_category_sort_order_preserved(self):
        cats = [
            ("Zebras", ["Z1", "Z2", "Z3", "Z4"]),
            ("Apples", ["A1", "A2", "A3", "A4"]),
            ("Middle", ["M1", "M2", "M3", "M4"]),
            ("Last", ["L1", "L2", "L3", "L4"]),
        ]
        db.add_puzzle("order_test", cats)
        puzzle = db.get_puzzle_by_name("order_test")
        assert puzzle

        assert puzzle["categories"] == ["Zebras", "Apples", "Middle", "Last"]


# --- Flask API tests ---


@pytest.fixture
def client():
    """Create a Flask test client with a seeded puzzle."""
    import app as flask_app

    flask_app.app.config["TESTING"] = True
    # Seed a puzzle matching ACTIVE_PUZZLE
    db.add_puzzle(flask_app.ACTIVE_PUZZLE, SAMPLE_PUZZLE)
    with flask_app.app.test_client() as c:
        yield c


class TestAPI:
    def test_get_puzzle(self, client):
        resp = client.get("/api/puzzle")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "words" in data
        assert "sets" in data
        assert "categories" in data
        assert len(data["words"]) == 16
        assert len(data["sets"]) == 4

    def test_check_correct_group(self, client):
        resp = client.post(
            "/api/check",
            json={"group": ["APPLE", "BANANA", "ORANGE", "CHERRY"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["correct"] is True
        assert data["category"] == "Fruits"

    def test_check_incorrect_group(self, client):
        resp = client.post(
            "/api/check",
            json={"group": ["APPLE", "BANANA", "CAR", "DOG"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["correct"] is False

    def test_check_correct_regardless_of_order(self, client):
        resp = client.post(
            "/api/check",
            json={"group": ["CHERRY", "ORANGE", "BANANA", "APPLE"]},
        )
        data = resp.get_json()
        assert data["correct"] is True
        assert data["category"] == "Fruits"

    def test_index_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Connections" in resp.data


# --- Create puzzle API tests ---


VALID_CREATE_PAYLOAD = {
    "name": "my-puzzle",
    "categories": [
        {"name": "Fruits", "words": ["APPLE", "BANANA", "ORANGE", "CHERRY"]},
        {"name": "Vehicles", "words": ["CAR", "TRUCK", "BICYCLE", "BOAT"]},
        {"name": "Animals", "words": ["CAT", "DOG", "FISH", "LION"]},
        {"name": "Furniture", "words": ["SOFA", "BED", "CHAIR", "TABLE"]},
    ],
}


class TestCreatePuzzleAPI:
    def test_create_puzzle_success(self, client):
        resp = client.post("/api/puzzle", json=VALID_CREATE_PAYLOAD)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "my-puzzle"
        assert "id" in data

        # Verify it's actually in the database
        puzzle = db.get_puzzle_by_name("my-puzzle")
        assert puzzle is not None
        assert puzzle["categories"] == ["Fruits", "Vehicles", "Animals", "Furniture"]

    def test_create_puzzle_without_name_generates_one(self, client):
        payload = {
            "categories": VALID_CREATE_PAYLOAD["categories"],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"].startswith("puzzle-")
        assert len(data["name"]) > len("puzzle-")

    def test_create_puzzle_with_empty_name_generates_one(self, client):
        payload = {
            "name": "   ",
            "categories": VALID_CREATE_PAYLOAD["categories"],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"].startswith("puzzle-")

    def test_create_puzzle_duplicate_name(self, client):
        client.post("/api/puzzle", json=VALID_CREATE_PAYLOAD)
        resp = client.post("/api/puzzle", json=VALID_CREATE_PAYLOAD)
        assert resp.status_code == 409
        data = resp.get_json()
        assert "error" in data

    def test_create_puzzle_missing_categories(self, client):
        resp = client.post("/api/puzzle", json={"name": "bad"})
        assert resp.status_code == 400

    def test_create_puzzle_wrong_number_of_categories(self, client):
        payload = {
            "name": "short",
            "categories": VALID_CREATE_PAYLOAD["categories"][:2],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 400

    def test_create_puzzle_wrong_number_of_words(self, client):
        payload = {
            "name": "bad-words",
            "categories": [
                {"name": "Fruits", "words": ["APPLE", "BANANA", "ORANGE"]},
                {"name": "Vehicles", "words": ["CAR", "TRUCK", "BICYCLE", "BOAT"]},
                {"name": "Animals", "words": ["CAT", "DOG", "FISH", "LION"]},
                {"name": "Furniture", "words": ["SOFA", "BED", "CHAIR", "TABLE"]},
            ],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 400

    def test_create_puzzle_empty_category_name(self, client):
        payload = {
            "name": "empty-cat",
            "categories": [
                {"name": "", "words": ["A", "B", "C", "D"]},
                {"name": "Two", "words": ["E", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 400

    def test_create_puzzle_empty_word(self, client):
        payload = {
            "name": "empty-word",
            "categories": [
                {"name": "One", "words": ["A", "", "C", "D"]},
                {"name": "Two", "words": ["E", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 400

    def test_create_puzzle_duplicate_words(self, client):
        payload = {
            "name": "dupes",
            "categories": [
                {"name": "One", "words": ["APPLE", "B", "C", "D"]},
                {"name": "Two", "words": ["APPLE", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "duplicate" in data["error"].lower()

    def test_create_puzzle_words_are_uppercased(self, client):
        payload = {
            "name": "casing-test",
            "categories": [
                {"name": "One", "words": ["apple", "Banana", "oRaNgE", "CHERRY"]},
                {"name": "Two", "words": ["car", "truck", "bicycle", "boat"]},
                {"name": "Three", "words": ["cat", "dog", "fish", "lion"]},
                {"name": "Four", "words": ["sofa", "bed", "chair", "table"]},
            ],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 201

        puzzle = db.get_puzzle_by_name("casing-test")
        assert puzzle is not None
        for word in puzzle["words"]:
            assert word == word.upper(), f"Word '{word}' was not uppercased"

    def test_create_puzzle_strips_whitespace(self, client):
        payload = {
            "name": "  strip-test  ",
            "categories": [
                {"name": "  One  ", "words": [" A ", "B", "C", "D"]},
                {"name": "Two", "words": ["E", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        resp = client.post("/api/puzzle", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "strip-test"

        puzzle = db.get_puzzle_by_name("strip-test")
        assert puzzle is not None
        assert puzzle["categories"][0] == "One"
        assert "A" in puzzle["words"]
