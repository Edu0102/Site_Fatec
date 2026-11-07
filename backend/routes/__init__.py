from flask import request


def json_field(name):
    """Read a string field from the JSON body; anything missing or non-string becomes ""."""
    data = request.get_json(silent=True)
    value = data.get(name) if isinstance(data, dict) else None
    return value if isinstance(value, str) else ""


def to_http(result, ok_message, not_found_message, conflict_message="Conflict."):
    """Turn a repository write result into the JSON response C#'s ToHttp gave."""
    if result == "ok":
        return {"message": ok_message}, 200
    if result == "not_found":
        return {"error": not_found_message}, 404
    if result == "conflict":
        return {"error": conflict_message}, 409
    if result == "forbidden":
        return {"error": "Forbidden."}, 403
    raise ValueError(f"unknown write result: {result}")
