from flask import request


def json_field(name):
    """Read a string field from the JSON body; anything missing or non-string becomes ""."""
    data = request.get_json(silent=True)
    value = data.get(name) if isinstance(data, dict) else None
    return value if isinstance(value, str) else ""
