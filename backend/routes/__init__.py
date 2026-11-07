from flask import request

POP_UNAVAILABLE = {"error": "POP not found or not available."}


def json_body():
    """The JSON body as a dict; {} when missing, invalid or not an object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def json_field(name):
    """Read a string field from the JSON body; anything missing or non-string becomes ""."""
    value = json_body().get(name)
    if not isinstance(value, str):
        return ""
    try:
        value.encode("utf-8")  # lone surrogates can't be hashed or stored
    except UnicodeEncodeError:
        return ""
    return value


def json_int(name):
    """Read a whole-number field that fits SQLite's INTEGER; None otherwise (bools don't count)."""
    value = json_body().get(name)
    if isinstance(value, bool) or not isinstance(value, int) or not -2**63 <= value < 2**63:
        return None
    return value


def json_bool(name):
    """Read a true/false field; None when it is anything else."""
    value = json_body().get(name)
    return value if isinstance(value, bool) else None


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
