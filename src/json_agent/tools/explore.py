"""
Explore Tools — MCP tools for inspecting JSON structure and values.

Lets the LLM understand what a JSON document contains without pulling
the entire document into context.
"""

from __future__ import annotations

import json
from typing import Any

from json_agent.store import JSONStore
from json_agent.utils.path_resolver import resolve_path
from json_agent.utils.truncation import truncate_value


def get_keys(store: JSONStore, alias: str, path: str = "") -> str:
    """
    Get all keys at a given path in a loaded JSON document.

    Works on objects (returns key names) and arrays (returns indices).

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot/bracket notation path. Empty string means root.

    Returns:
        A list of keys or indices at the given path.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if isinstance(target, dict):
        keys = list(target.keys())
        return f"Object with {len(keys)} keys:\n" + "\n".join(f"  - {k}" for k in keys)

    if isinstance(target, list):
        length = len(target)
        return f"Array with {length} items (indices 0..{length - 1})"

    return f"Value at '{path}' is a {type(target).__name__}, not an object or array. No keys available."


def get_value(store: JSONStore, alias: str, path: str = "") -> str:
    """
    Retrieve the value at an exact path. Large outputs are auto-truncated.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot/bracket notation path. Empty string means root.

    Returns:
        The serialized value at the path (truncated if large).
    """
    data = store.get(alias)
    target = resolve_path(data, path)
    return truncate_value(target)


def get_type(store: JSONStore, alias: str, path: str = "") -> str:
    """
    Return the JSON type of the value at a given path.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot/bracket notation path. Empty string means root.

    Returns:
        The JSON type name: object, array, string, number, boolean, or null.
    """
    data = store.get(alias)
    target = resolve_path(data, path)
    type_name = _json_type(target)

    # Add count info for containers
    if isinstance(target, dict):
        return f"object ({len(target)} keys)"
    if isinstance(target, list):
        return f"array ({len(target)} items)"
    return type_name


def get_structure(
    store: JSONStore,
    alias: str,
    path: str = "",
    max_depth: int = 3,
) -> str:
    """
    Return a schema-like skeleton showing keys and types up to a max depth.

    Useful for understanding the shape of a deeply nested JSON document
    without viewing all the data.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot/bracket notation path. Empty string means root.
        max_depth: How many levels deep to traverse (default 3).

    Returns:
        An indented tree of keys and types.
    """
    data = store.get(alias)
    target = resolve_path(data, path)
    tree = _build_structure(target, depth=0, max_depth=max_depth)
    return tree


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _json_type(value: Any) -> str:
    """Map a Python value to a JSON type name."""
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


def _build_structure(value: Any, *, depth: int, max_depth: int, indent: int = 0) -> str:
    """
    Recursively build a type-skeleton string.

    Example output:
        object (3 keys)
          name: string
          age: number
          address: object (2 keys)
            street: string
            city: string
    """
    prefix = "  " * indent
    type_name = _json_type(value)

    if isinstance(value, dict):
        header = f"{type_name} ({len(value)} keys)"
        if depth >= max_depth:
            return f"{prefix}{header}  [depth limit reached]"

        lines = [f"{prefix}{header}"]
        for key, val in value.items():
            child = _build_structure(val, depth=depth + 1, max_depth=max_depth, indent=indent + 1)
            # If child is a single-line scalar, inline it
            if "\n" not in child:
                lines.append(f"{prefix}  {key}: {child.strip()}")
            else:
                lines.append(f"{prefix}  {key}:")
                lines.append(child)
        return "\n".join(lines)

    if isinstance(value, list):
        header = f"{type_name} ({len(value)} items)"
        if depth >= max_depth or len(value) == 0:
            return f"{prefix}{header}"

        # Show the structure of the first element as representative
        first = _build_structure(value[0], depth=depth + 1, max_depth=max_depth, indent=indent + 1)
        lines = [f"{prefix}{header}"]
        if "\n" not in first:
            lines.append(f"{prefix}  [0]: {first.strip()}")
        else:
            lines.append(f"{prefix}  [0]:")
            lines.append(first)
        if len(value) > 1:
            lines.append(f"{prefix}  ... ({len(value) - 1} more items)")
        return "\n".join(lines)

    # Scalar
    return f"{prefix}{type_name}"
