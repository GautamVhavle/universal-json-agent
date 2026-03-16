"""
Introspection Tools — deep structure discovery for unknown JSON documents.

When you encounter a JSON file you've never seen before, these tools help
you understand its shape before querying it.
"""

from __future__ import annotations

from typing import Any

from json_agent.store import JSONStore
from json_agent.utils.path_resolver import resolve_path


def distinct_paths(
    store: JSONStore,
    alias: str,
    path: str = "",
    max_depth: int = 10,
    sample_array_items: int = 5,
) -> str:
    """
    List every unique leaf path in a JSON document.

    For arrays, the first *sample_array_items* elements are inspected so
    that paths like ``items[*].name`` are discovered without scanning
    thousands of identical objects.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to start from. Empty means root.
        max_depth: Maximum recursion depth (default 10).
        sample_array_items: How many array elements to inspect (default 5).

    Returns:
        A newline-separated list of all discovered paths with their types.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    prefix = path or "$"
    found: dict[str, str] = {}  # path → type
    _walk(target, prefix, found, depth=0, max_depth=max_depth,
          sample_n=sample_array_items)

    if not found:
        type_name = _json_type(target)
        return f"Single {type_name} value at '{prefix}' — no nested paths."

    lines = [f"Discovered {len(found)} unique path(s) from '{prefix}'", ""]
    for p, t in found.items():
        lines.append(f"  {p}  →  {t}")

    return "\n".join(lines)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _walk(
    value: Any,
    path: str,
    found: dict[str, str],
    depth: int,
    max_depth: int,
    sample_n: int,
) -> None:
    """Recursively collect leaf paths."""
    if depth > max_depth:
        found[path] = "... (max depth reached)"
        return

    if isinstance(value, dict):
        if not value:
            found[path] = "object (empty)"
            return
        for key in value:
            child_path = f"{path}.{key}"
            _walk(value[key], child_path, found, depth + 1, max_depth, sample_n)

    elif isinstance(value, list):
        if not value:
            found[path] = "array (empty)"
            return
        # Sample first N items to find unique sub-paths
        for i, item in enumerate(value[:sample_n]):
            _walk(item, f"{path}[*]", found, depth + 1, max_depth, sample_n)

    else:
        # Leaf node
        found[path] = _json_type(value)


def _json_type(value: Any) -> str:
    """Return the JSON type name for a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return f"array ({len(value)} items)"
    if isinstance(value, dict):
        return f"object ({len(value)} keys)"
    return type(value).__name__
