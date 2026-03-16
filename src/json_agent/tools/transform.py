"""
Transform Tools — MCP tools for reshaping and sampling JSON data.

These tools let the LLM restructure data (flatten, project, group, sort)
before presenting results, making answers more focused and readable.
"""

from __future__ import annotations

import random
from typing import Any

from json_agent.store import JSONStore
from json_agent.utils.path_resolver import resolve_path
from json_agent.utils.truncation import truncate_list, truncate_value


def flatten(store: JSONStore, alias: str, path: str = "", separator: str = ".") -> str:
    """
    Flatten a nested JSON object into dot-notation key-value pairs.

    Only works on objects (dicts). Nested objects and arrays are recursively
    flattened into "parent.child" keys.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the object to flatten. Empty means root.
        separator: The separator for flattened keys (default ".").

    Returns:
        A flat mapping of dotted paths → values.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, dict):
        raise TypeError(
            f"Value at path '{path or '$'}' is {type(target).__name__}, "
            f"expected an object. Only objects can be flattened."
        )

    flat: dict[str, Any] = {}
    _flatten_recursive(target, prefix="", separator=separator, result=flat)
    return truncate_value(flat)


def pick_fields(
    store: JSONStore,
    alias: str,
    path: str,
    fields: list[str],
) -> str:
    """
    Extract specific fields from each object in an array (projection).

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array of objects.
        fields: List of field names to include in each projected object.

    Returns:
        The projected array with only the requested fields.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(
            f"Value at path '{path}' is {type(target).__name__}, expected an array."
        )

    projected = []
    for item in target:
        if isinstance(item, dict):
            row = {f: item[f] for f in fields if f in item}
            projected.append(row)

    header = f"Projected {len(projected)} items with fields: {', '.join(fields)}"
    return header + "\n" + truncate_list(projected)


def group_by(store: JSONStore, alias: str, path: str, field: str) -> str:
    """
    Group an array of objects by a field value.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array of objects.
        field: The field to group by.

    Returns:
        A grouped mapping of field_value → list of objects.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(
            f"Value at path '{path}' is {type(target).__name__}, expected an array."
        )

    groups: dict[str, list[Any]] = {}
    ungrouped = 0

    for item in target:
        if not isinstance(item, dict) or field not in item:
            ungrouped += 1
            continue
        key = str(item[field])
        groups.setdefault(key, []).append(item)

    # Build summary
    lines = [f"Grouped {len(target)} items into {len(groups)} group(s) by '{field}'"]
    if ungrouped:
        lines.append(f"  ({ungrouped} items skipped — missing '{field}' field)")
    lines.append("")

    for key, items in groups.items():
        lines.append(f"  {key}: {len(items)} item(s)")

    summary = "\n".join(lines)

    # Also include the full grouped data, truncated
    return summary + "\n\n" + truncate_value(groups)


def sort_by(
    store: JSONStore,
    alias: str,
    path: str,
    field: str,
    descending: bool = False,
) -> str:
    """
    Sort an array of objects by a field.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array of objects.
        field: The field to sort by.
        descending: Sort in descending order (default False = ascending).

    Returns:
        The sorted array, truncated.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(
            f"Value at path '{path}' is {type(target).__name__}, expected an array."
        )

    # Separate items that have the field from those that don't
    sortable = [item for item in target if isinstance(item, dict) and field in item]
    unsortable = [item for item in target if not isinstance(item, dict) or field not in item]

    try:
        sorted_items = sorted(sortable, key=lambda x: x[field], reverse=descending)
    except TypeError:
        # Mixed types — fall back to string comparison
        sorted_items = sorted(sortable, key=lambda x: str(x[field]), reverse=descending)

    direction = "descending" if descending else "ascending"
    header = f"Sorted {len(sorted_items)} items by '{field}' ({direction})"
    if unsortable:
        header += f"  ({len(unsortable)} items without '{field}' appended at end)"
        sorted_items.extend(unsortable)

    return header + "\n" + truncate_list(sorted_items)


def sample(
    store: JSONStore,
    alias: str,
    path: str = "",
    n: int = 5,
    seed: int | None = None,
) -> str:
    """
    Return N random items from an array.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array. Empty means root.
        n: Number of items to sample (default 5).
        seed: Optional random seed for reproducibility.

    Returns:
        N randomly chosen items from the array.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(
            f"Value at path '{path or '$'}' is {type(target).__name__}, expected an array."
        )

    total = len(target)
    n = min(n, total)  # Don't sample more than available

    if seed is not None:
        rng = random.Random(seed)
        sampled = rng.sample(target, n)
    else:
        sampled = random.sample(target, n)

    header = f"Random sample of {n} item(s) from {total} total"
    return header + "\n" + truncate_list(sampled)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _flatten_recursive(
    obj: dict[str, Any],
    prefix: str,
    separator: str,
    result: dict[str, Any],
) -> None:
    """Recursively flatten a nested dict into *result*."""
    for key, value in obj.items():
        full_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            _flatten_recursive(value, full_key, separator, result)
        elif isinstance(value, list):
            # Flatten list items with index notation
            for idx, item in enumerate(value):
                item_key = f"{full_key}[{idx}]"
                if isinstance(item, dict):
                    _flatten_recursive(item, item_key, separator, result)
                else:
                    result[item_key] = item
        else:
            result[full_key] = value
