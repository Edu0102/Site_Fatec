from datetime import datetime, timezone


def utc_now():
    """Current UTC time as ISO text, close to C#'s DateTime.UtcNow.ToString("o")."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
