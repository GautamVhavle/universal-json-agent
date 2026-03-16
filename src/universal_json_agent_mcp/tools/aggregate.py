"""
Aggregate Tools — MCP tools for counting, summing, and summarising JSON data.

These tools let the LLM answer quantitative questions ("how many?", "total?",
"min/max?") without pulling the full dataset into context.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.utils.jsonpath_helpers import extract_numbers, extract_values
from universal_json_agent_mcp.utils.path_resolver import resolve_path
from universal_json_agent_mcp.utils.truncation import truncate_value, truncate_list


def count(store: JSONStore, alias: str, path: str = "") -> str:
    """
    Count items in an array or keys in an object at a given path.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot/bracket notation path. Empty means root.

    Returns:
        A string with the count information.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if isinstance(target, list):
        return f"Array at '{path or '$'}' contains {len(target)} items"
    if isinstance(target, dict):
        return f"Object at '{path or '$'}' contains {len(target)} keys"
    return f"Value at '{path or '$'}' is a scalar ({type(target).__name__}), not countable"


def sum_values(store: JSONStore, alias: str, expression: str) -> str:
    """
    Sum numeric values matched by a JSONPath expression.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        expression: A JSONPath expression that resolves to numeric values
                    (e.g. "$.orders[*].total").

    Returns:
        The sum and count of matched numeric values.
    """
    nums = extract_numbers(store, alias, expression)

    if not nums:
        return f"No numeric values found for: {expression}"

    total = sum(nums)
    return f"Sum: {total}  (from {len(nums)} values)"


def min_max(store: JSONStore, alias: str, expression: str) -> str:
    """
    Get the minimum and maximum of numeric values matched by a JSONPath expression.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        expression: A JSONPath expression that resolves to numeric values.

    Returns:
        The min, max, and count of matched numeric values.
    """
    nums = extract_numbers(store, alias, expression)

    if not nums:
        return f"No numeric values found for: {expression}"

    return f"Min: {min(nums)}  Max: {max(nums)}  (from {len(nums)} values)"


def unique_values(store: JSONStore, alias: str, expression: str) -> str:
    """
    Get distinct values matched by a JSONPath expression.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        expression: A JSONPath expression (e.g. "$.users[*].role").

    Returns:
        A list of distinct values and their count.
    """
    values = extract_values(store, alias, expression)

    if not values:
        return f"No values found for: {expression}"

    # Only hashable values can be de-duped
    try:
        unique = list(dict.fromkeys(values))  # preserves order
    except TypeError:
        # Fallback for unhashable types (dicts, lists)
        unique = []
        seen: list[Any] = []
        for v in values:
            if v not in seen:
                seen.append(v)
                unique.append(v)

    header = f"{len(unique)} unique value(s) from {len(values)} total"
    return header + "\n" + truncate_list(unique)


def value_counts(store: JSONStore, alias: str, expression: str) -> str:
    """
    Count occurrences of each distinct value matched by a JSONPath expression.

    Like pandas value_counts() — great for "how many orders per status?".

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        expression: A JSONPath expression (e.g. "$.orders[*].status").

    Returns:
        A frequency table showing each value and its count, sorted descending.
    """
    values = extract_values(store, alias, expression)

    if not values:
        return f"No values found for: {expression}"

    # Convert unhashable types to their JSON representation for counting
    hashable = []
    for v in values:
        if isinstance(v, (dict, list)):
            hashable.append(json.dumps(v, sort_keys=True, ensure_ascii=False))
        else:
            hashable.append(v)

    counter = Counter(hashable)
    lines = [f"{'Value':<40} Count"]
    lines.append("-" * 50)
    for val, cnt in counter.most_common():
        display = str(val) if len(str(val)) <= 38 else str(val)[:35] + "..."
        lines.append(f"{display:<40} {cnt}")

    lines.append(f"\nTotal: {len(values)} values, {len(counter)} unique")
    return "\n".join(lines)
