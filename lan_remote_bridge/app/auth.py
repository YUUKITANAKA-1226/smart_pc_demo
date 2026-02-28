import os

CONTROL_TOKEN = os.getenv("CONTROL_TOKEN", "change-me")


def is_authorized(token: str | None) -> bool:
    return bool(token) and token == CONTROL_TOKEN
