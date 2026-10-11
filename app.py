"""Flask server. Routes only; all logic lives in the automata/ package."""

from flask import Flask, jsonify, render_template, request

from automata import convert
from flask import send_from_directory

app = Flask(__name__)

MAX_TESTS = 50
MAX_TEST_LENGTH = 200


def _read_request():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    regex = str(data.get("regex", ""))
    raw_tests = data.get("tests", [])
    if not isinstance(raw_tests, list):
        raise ValueError("'tests' must be a list of strings.")
    if len(raw_tests) > MAX_TESTS:
        raise ValueError(f"You may submit at most {MAX_TESTS} test strings.")
    tests = [str(t) for t in raw_tests]
    dead_state = data.get("dead_state", True)
    if not isinstance(dead_state, bool):
        raise ValueError("'dead_state' must be a boolean.")
    if any(len(t) > MAX_TEST_LENGTH for t in tests):
        raise ValueError(f"Test strings may be at most {MAX_TEST_LENGTH} characters.")
    return regex, tests, dead_state


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/convert")
def api_convert():
    """Full conversion: tables, diagrams, construction steps (+ optional test strings)."""
    try:
        regex, tests, dead_state = _read_request()
        return jsonify(convert(regex, tests, dead_state))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/test")
def api_test():
    """Fast path for running strings: no diagrams are generated."""
    try:
        regex, tests, dead_state = _read_request()
        out = convert(regex, tests, dead_state, render=False)
        return jsonify(results=out["results"])
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


if __name__ == "__main__":
    app.run()

@app.route('/google3892eb5cb3819e7e.html')
def google_site_verification():
    return send_from_directory(
        app.root_path,
        'google3892eb5cb3819e7e.html'
    )