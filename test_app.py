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
    db.add_puzzle("test-puzzle", SAMPLE_PUZZLE)
    with flask_app.app.test_client() as c:
        yield c


class TestGetRandomPuzzle:
    def test_returns_a_puzzle(self):
        db.add_puzzle("one", SAMPLE_PUZZLE)
        db.add_puzzle("two", SAMPLE_PUZZLE)
        result = db.get_random_puzzle()
        assert result is not None
        assert "name" in result
        assert result["name"] in ("one", "two")

    def test_returns_none_when_empty(self):
        assert db.get_random_puzzle() is None


class TestAPI:
    def test_get_puzzle_by_name(self, client):
        resp = client.get("/api/puzzle?name=test-puzzle")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "words" in data
        assert "sets" in data
        assert "categories" in data
        assert len(data["words"]) == 16
        assert len(data["sets"]) == 4
        assert data["name"] == "test-puzzle"

    def test_get_puzzle_default_returns_random(self, client):
        resp = client.get("/api/puzzle")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "name" in data
        assert "words" in data

    def test_get_puzzle_not_found(self, client):
        resp = client.get("/api/puzzle?name=nonexistent")
        assert resp.status_code == 404

    def test_check_correct_group(self, client):
        resp = client.post(
            "/api/check?name=test-puzzle",
            json={"group": ["APPLE", "BANANA", "ORANGE", "CHERRY"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["correct"] is True
        assert data["category"] == "Fruits"

    def test_check_incorrect_group(self, client):
        resp = client.post(
            "/api/check?name=test-puzzle",
            json={"group": ["APPLE", "BANANA", "CAR", "DOG"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["correct"] is False

    def test_check_correct_regardless_of_order(self, client):
        resp = client.post(
            "/api/check?name=test-puzzle",
            json={"group": ["CHERRY", "ORANGE", "BANANA", "APPLE"]},
        )
        data = resp.get_json()
        assert data["correct"] is True
        assert data["category"] == "Fruits"

    def test_check_missing_name_returns_400(self, client):
        resp = client.post(
            "/api/check",
            json={"group": ["APPLE", "BANANA", "ORANGE", "CHERRY"]},
        )
        assert resp.status_code == 400

    def test_index_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Connections" in resp.data


# --- Validation unit tests ---

from app import validate_and_clean_puzzle

VALID_INPUT = {
    "name": "my-puzzle",
    "categories": [
        {"name": "Fruits", "words": ["APPLE", "BANANA", "ORANGE", "CHERRY"]},
        {"name": "Vehicles", "words": ["CAR", "TRUCK", "BICYCLE", "BOAT"]},
        {"name": "Animals", "words": ["CAT", "DOG", "FISH", "LION"]},
        {"name": "Furniture", "words": ["SOFA", "BED", "CHAIR", "TABLE"]},
    ],
}


class TestValidateAndCleanPuzzle:
    def test_valid_input(self):
        name, cats = validate_and_clean_puzzle(VALID_INPUT)
        assert name == "my-puzzle"
        assert len(cats) == 4
        assert cats[0] == ("Fruits", ["APPLE", "BANANA", "ORANGE", "CHERRY"])

    def test_missing_name_generates_one(self):
        data = {"categories": VALID_INPUT["categories"]}
        name, _ = validate_and_clean_puzzle(data)
        assert name.startswith("puzzle-")
        assert len(name) > len("puzzle-")

    def test_blank_name_generates_one(self):
        data = {"name": "   ", "categories": VALID_INPUT["categories"]}
        name, _ = validate_and_clean_puzzle(data)
        assert name.startswith("puzzle-")

    def test_strips_whitespace_from_name(self):
        data = {"name": "  my-puzzle  ", "categories": VALID_INPUT["categories"]}
        name, _ = validate_and_clean_puzzle(data)
        assert name == "my-puzzle"

    def test_strips_whitespace_from_category_and_words(self):
        data = {
            "name": "test",
            "categories": [
                {"name": "  One  ", "words": [" A ", "B", "C", "D"]},
                {"name": "Two", "words": ["E", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        _, cats = validate_and_clean_puzzle(data)
        assert cats[0][0] == "One"
        assert cats[0][1][0] == "A"

    def test_uppercases_words(self):
        data = {
            "name": "test",
            "categories": [
                {"name": "One", "words": ["apple", "Banana", "oRaNgE", "CHERRY"]},
                {"name": "Two", "words": ["car", "truck", "bicycle", "boat"]},
                {"name": "Three", "words": ["cat", "dog", "fish", "lion"]},
                {"name": "Four", "words": ["sofa", "bed", "chair", "table"]},
            ],
        }
        _, cats = validate_and_clean_puzzle(data)
        for _, words in cats:
            for word in words:
                assert word == word.upper()

    def test_missing_categories_raises(self):
        with pytest.raises(ValueError):
            validate_and_clean_puzzle({"name": "bad"})

    def test_wrong_number_of_categories_raises(self):
        data = {"name": "short", "categories": VALID_INPUT["categories"][:2]}
        with pytest.raises(ValueError):
            validate_and_clean_puzzle(data)

    def test_wrong_number_of_words_raises(self):
        data = {
            "name": "bad",
            "categories": [
                {"name": "Fruits", "words": ["APPLE", "BANANA", "ORANGE"]},
                {"name": "Vehicles", "words": ["CAR", "TRUCK", "BICYCLE", "BOAT"]},
                {"name": "Animals", "words": ["CAT", "DOG", "FISH", "LION"]},
                {"name": "Furniture", "words": ["SOFA", "BED", "CHAIR", "TABLE"]},
            ],
        }
        with pytest.raises(ValueError):
            validate_and_clean_puzzle(data)

    def test_empty_category_name_raises(self):
        data = {
            "name": "bad",
            "categories": [
                {"name": "", "words": ["A", "B", "C", "D"]},
                {"name": "Two", "words": ["E", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        with pytest.raises(ValueError):
            validate_and_clean_puzzle(data)

    def test_empty_word_raises(self):
        data = {
            "name": "bad",
            "categories": [
                {"name": "One", "words": ["A", "", "C", "D"]},
                {"name": "Two", "words": ["E", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        with pytest.raises(ValueError):
            validate_and_clean_puzzle(data)

    def test_duplicate_words_raises(self):
        data = {
            "name": "bad",
            "categories": [
                {"name": "One", "words": ["APPLE", "B", "C", "D"]},
                {"name": "Two", "words": ["APPLE", "F", "G", "H"]},
                {"name": "Three", "words": ["I", "J", "K", "L"]},
                {"name": "Four", "words": ["M", "N", "O", "P"]},
            ],
        }
        with pytest.raises(ValueError, match="(?i)duplicate"):
            validate_and_clean_puzzle(data)


# --- Create puzzle API tests ---


class TestCreatePuzzleAPI:
    def test_create_puzzle_success(self, client):
        resp = client.post("/api/puzzle", json=VALID_INPUT)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "my-puzzle"
        assert "id" in data

        puzzle = db.get_puzzle_by_name("my-puzzle")
        assert puzzle is not None
        assert puzzle["categories"] == ["Fruits", "Vehicles", "Animals", "Furniture"]

    def test_create_puzzle_duplicate_name(self, client):
        client.post("/api/puzzle", json=VALID_INPUT)
        resp = client.post("/api/puzzle", json=VALID_INPUT)
        assert resp.status_code == 409
        assert "error" in resp.get_json()

    def test_create_puzzle_validation_error_returns_400(self, client):
        resp = client.post("/api/puzzle", json={"name": "bad"})
        assert resp.status_code == 400
        assert "error" in resp.get_json()
