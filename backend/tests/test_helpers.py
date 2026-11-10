import pytest

from routes import json_bool, json_int


@pytest.mark.parametrize("body,expected", [
    ({"n": 3}, 3), ({"n": 0}, 0), ({"n": -2}, -2),
    ({"n": True}, None), ({"n": "3"}, None), ({"n": 1.5}, None), ({"n": None}, None), ({}, None),
    ({"n": 2**63}, None), ([1], None),
])
def test_json_int(app, body, expected):
    with app.test_request_context(json=body):
        assert json_int("n") == expected


@pytest.mark.parametrize("body,expected", [
    ({"b": True}, True), ({"b": False}, False), ({"b": 1}, None), ({"b": "true"}, None), ({}, None),
])
def test_json_bool(app, body, expected):
    with app.test_request_context(json=body):
        assert json_bool("b") is expected
