"""
JSON Type Mapping — shared utility for mapping Python values to JSON type names.

Used by the store, explore tools, and any module that needs consistent
type-name strings for JSON values.
"""

from __future__ import annotations

from typing import Any


def json_type_name(value: Any) -> str:
    """
    Map a Python value to its JSON type name.

    Returns one of: "object", "array", "string", "boolean", "number", "null".
    Falls back to "unknown" for non-JSON types.

    Note: bool check MUST precede int check because ``bool`` is a subclass
    of ``int`` in Python.
    """
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "null"
    return "unknown"
