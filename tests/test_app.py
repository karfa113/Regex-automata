import pytest

from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize("endpoint", ["/api/convert", "/api/test"])
def test_invalid_tests_payload_returns_bad_request(client, endpoint):
    response = client.post(endpoint, json={"regex": "a", "tests": None})

    assert response.status_code == 400
    assert response.json == {"error": "'tests' must be a list of strings."}


def test_missing_tests_defaults_to_empty_list(client):
    response = client.post("/api/test", json={"regex": "a"})

    assert response.status_code == 200
    assert response.json["results"] == []


@pytest.mark.parametrize("endpoint", ["/api/convert", "/api/test"])
def test_oversized_tests_payload_returns_bad_request(client, endpoint):
    response = client.post(endpoint, json={"regex": "a", "tests": ["a"] * 51})

    assert response.status_code == 400
    assert response.json == {"error": "You may submit at most 50 test strings."}
