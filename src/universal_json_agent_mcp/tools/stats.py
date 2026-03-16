"""
Stats Tools — MCP tools for statistical summaries of numeric JSON data.

Goes beyond min/max and sum to provide mean, median, standard deviation,
and percentiles — the kind of quick analysis that avoids pulling large
datasets into the context window.
"""

from __future__ import annotations

import math
from typing import Any

from jsonpath_ng.ext import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

from universal_json_agent_mcp.store import JSONStore


def describe(store: JSONStore, alias: str, expression: str) -> str:
    """
    Return a statistical summary (count, mean, min, max, median, std dev,
    25th/75th percentiles) for numeric values matched by a JSONPath expression.

    Non-numeric values (strings, booleans, nulls) are silently skipped.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        expression: A JSONPath expression resolving to numbers
                    (e.g. "$.orders[*].total").

    Returns:
        A formatted statistical summary.
    """
    nums = _extract_numbers(store, alias, expression)

    if not nums:
        return f"No numeric values found for: {expression}"

    nums_sorted = sorted(nums)
    n = len(nums_sorted)
    total = sum(nums_sorted)
    mean = total / n
    minimum = nums_sorted[0]
    maximum = nums_sorted[-1]
    median = _percentile(nums_sorted, 50)
    p25 = _percentile(nums_sorted, 25)
    p75 = _percentile(nums_sorted, 75)

    # Population standard deviation
    variance = sum((x - mean) ** 2 for x in nums_sorted) / n
    std_dev = math.sqrt(variance)

    lines = [
        f"Statistical summary for: {expression}",
        f"  Count  : {n}",
        f"  Mean   : {_fmt(mean)}",
        f"  Std Dev: {_fmt(std_dev)}",
        f"  Min    : {_fmt(minimum)}",
        f"  25%    : {_fmt(p25)}",
        f"  50%    : {_fmt(median)}",
        f"  75%    : {_fmt(p75)}",
        f"  Max    : {_fmt(maximum)}",
        f"  Sum    : {_fmt(total)}",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _extract_numbers(store: JSONStore, alias: str, expression: str) -> list[int | float]:
    """Run a JSONPath query and return only int/float values (booleans excluded)."""
    try:
        parsed = jsonpath_parse(expression)
    except (JsonPathParserError, Exception) as exc:
        raise ValueError(f"Invalid JSONPath expression: {expression!r} — {exc}") from exc

    data = store.get(alias)
    matches = parsed.find(data)

    return [
        m.value for m in matches
        if isinstance(m.value, (int, float)) and not isinstance(m.value, bool)
    ]


def _percentile(sorted_data: list[int | float], p: float) -> float:
    """Compute the p-th percentile using linear interpolation."""
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]

    # Rank (0-indexed continuous)
    rank = (p / 100) * (n - 1)
    low = int(math.floor(rank))
    high = int(math.ceil(rank))

    if low == high:
        return sorted_data[low]

    # Linear interpolation
    fraction = rank - low
    return sorted_data[low] + fraction * (sorted_data[high] - sorted_data[low])


def _fmt(value: int | float) -> str:
    """Format a number: drop decimal if integer-valued, else 4 decimal places."""
    if isinstance(value, float) and value == int(value) and abs(value) < 1e15:
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
