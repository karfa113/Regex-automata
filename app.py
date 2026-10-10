"""Flask server. Routes only; all logic lives in the automata/ package."""

from flask import Flask, jsonify, render_template, request

from automata import convert

app = Flask(__name__)

MAX_TESTS = 50
MAX_TEST_LENGTH = 200


def _read_request():
    data = request.get_json(silent=True) or {}
    regex = str(data.get("regex", ""))
    tests = [str(t) for t in data.get("tests", [])][:MAX_TESTS]
    dead_state = bool(data.get("dead_state", True))
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