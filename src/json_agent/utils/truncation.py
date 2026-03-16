"""
Truncation Utilities — prevent oversized outputs from flooding the LLM context.

MCP tool responses are consumed by the AI model, so we cap their size to keep
things useful and within token budgets.
"""

from __future__ import annotations

import json
from typing import Any

# Default maximum characters for a serialized tool response
DEFAULT_MAX_CHARS = 10_000


def truncate_value(value: Any, *, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """
    Serialize a JSON value to a string, truncating if necessary.

    For dicts/lists, serializes to pretty JSON. If the result exceeds
    *max_chars*, it truncates and appends an indicator.

    Args:
        value: Any JSON-serializable value.
        max_chars: Maximum character length of the output string.

    Returns:
        A string representation, possibly truncated.
    """
    text = _serialize(value)

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + f"\n\n... [truncated — total {len(text)} chars]"


def truncate_list(
    items: list[Any],
    *,
    max_items: int = 50,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Serialize a list, showing at most *max_items* entries.

    If the list is longer than *max_items*, only the first *max_items*
    are shown with a count of remaining items.

    Args:
        items: The list to serialize.
        max_items: Maximum number of items to include.
        max_chars: Maximum total character length.

    Returns:
        A string representation with optional truncation notice.
    """
    total = len(items)

    if total <= max_items:
        return truncate_value(items, max_chars=max_chars)

    sliced = items[:max_items]
    text = _serialize(sliced)
    suffix = f"\n\n... showing {max_items} of {total} items"

    result = text + suffix
    if len(result) > max_chars:
        result = result[:max_chars] + f"\n\n... [truncated — total {len(result)} chars]"

    return result


def _serialize(value: Any) -> str:
    """Serialize a value to a compact-but-readable JSON string."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)
