import json
import os


_TEXT_CACHE = {}


def load_texts(path: str = "locales/fa.json") -> dict:
    """Load and cache texts from JSON."""
    global _TEXT_CACHE
    if path in _TEXT_CACHE:
        return _TEXT_CACHE[path]

    if not os.path.exists(path):
        raise FileNotFoundError(f"Texts file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _TEXT_CACHE[path] = data
    return data


def t(key: str, texts: dict, default: str = "") -> str:
    """
    Read nested key like: 'start.buttons.help'
    """
    cur = texts
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur if isinstance(cur, str) else default
