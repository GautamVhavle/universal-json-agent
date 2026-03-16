"""
Path Resolver — navigate nested JSON structures using dot-notation paths.

Supports:
    - Dot notation:         "users.0.name"
    - Bracket notation:     "users[0].name"
    - Root access:          "" or "." returns the root document
    - Mixed:                "data.items[2].tags.0"
"""

from __future__ import annotations

from functools import lru_cache
import re
from typing import Any


# Matches bracket indices like [0], [12]
_BRACKET_INDEX_RE = re.compile(r"\[(\d+)\]")


def resolve_path(data: Any, path: str) -> Any:
    """
    Traverse *data* following *path* and return the value found.

    Args:
        data: The root JSON value (dict, list, or scalar).
        path: Dot/bracket notation path. Empty string means root.

    Returns:
        The value at the given path.

    Raises:
        KeyError: If an object key is not found.
        IndexError: If an array index is out of range.
        TypeError: If traversal hits a scalar before the path is exhausted.
    """
    if not path or path == ".":
        return data

    segments = _tokenize(path)
    current = data

    for segment in segments:
        if isinstance(current, dict):
            if segment not in current:
                raise KeyError(f"Key '{segment}' not found. Available keys: {list(current.keys())[:20]}")
            current = current[segment]
        elif isinstance(current, list):
            try:
                index = int(segment)
            except ValueError:
                raise TypeError(
                    f"Cannot index a JSON array with non-integer key '{segment}'. "
                    f"Array has {len(current)} items."
                )
            if index < 0 or index >= len(current):
                raise IndexError(f"Index {index} out of range for array of length {len(current)}")
            current = current[index]
        else:
            raise TypeError(
                f"Cannot traverse into {type(current).__name__} value with key '{segment}'. "
                f"Path resolution stopped."
            )

    return current


def _tokenize(path: str) -> tuple[str, ...]:
    """
    Split a path string into individual segments.

    "users[0].name"  → ["users", "0", "name"]
    "data.items.2"   → ["data", "items", "2"]
    """
    return list(_tokenize_cached(path))


@lru_cache(maxsize=1024)
def _tokenize_cached(path: str) -> tuple[str, ...]:
    """
    Split a path string into individual segments.

    "users[0].name"  → ["users", "0", "name"]
    "data.items.2"   → ["data", "items", "2"]
    """
    # Replace bracket notation with dot notation: "a[0].b" → "a.0.b"
    normalized = _BRACKET_INDEX_RE.sub(r".\1", path)
    # Strip leading/trailing dots, split, and drop empties
    return tuple(seg for seg in normalized.strip(".").split(".") if seg)
