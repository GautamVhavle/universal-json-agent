"""
JSONPath Helpers — shared utilities for extracting values via JSONPath.

Centralises the parse → find → filter pattern used by the aggregate
and stats tool modules, eliminating duplicated JSONPath boilerplate.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from jsonpath_ng.ext import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

from universal_json_agent_mcp.store import JSONStore


@lru_cache(maxsize=256)
def parse_jsonpath(expression: str):
    """
    Parse and cache JSONPath expressions for reuse.

    Repeated JSONPath strings are common across tool calls, and parsing is
    relatively expensive compared with evaluating a pre-parsed expression.
    """
    try:
        return jsonpath_parse(expression)
    except (JsonPathParserError, Exception) as exc:
        raise ValueError(f"Invalid JSONPath expression '{expression}': {exc}") from exc


def extract_values(store: JSONStore, alias: str, expression: str) -> list[Any]:
    """
    Run a JSONPath expression against a loaded document and return all matches.

    Args:
        store: The shared JSONStore instance.
        alias: Alias of the loaded document.
        expression: A JSONPath expression (e.g. ``$.users[*].role``).

    Returns:
        A list of matched values (may be empty).

    Raises:
        ValueError: If the JSONPath expression is syntactically invalid.
        KeyError: If no document is loaded under *alias*.
    """
    data = store.get(alias)
    parsed = parse_jsonpath(expression)

    return [match.value for match in parsed.find(data)]


def extract_numbers(store: JSONStore, alias: str, expression: str) -> list[int | float]:
    """
    Run a JSONPath expression and return only numeric (int/float) matches.

    Booleans are explicitly excluded — ``True``/``False`` should never be
    treated as ``1``/``0`` in numeric aggregations.

    Args:
        store: The shared JSONStore instance.
        alias: Alias of the loaded document.
        expression: A JSONPath expression resolving to numbers.

    Returns:
        A list of int/float values (booleans excluded).

    Raises:
        ValueError: If the JSONPath expression is syntactically invalid.
        KeyError: If no document is loaded under *alias*.
    """
    values = extract_values(store, alias, expression)
    return [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
