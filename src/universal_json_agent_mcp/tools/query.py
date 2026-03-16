"""
Query Tools — MCP tools for searching and filtering JSON data.

Provides JSONPath queries, field-based filtering, and recursive text search
so the LLM can locate specific data without loading everything into context.
"""

from __future__ import annotations

import re
from typing import Any

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.utils.jsonpath_helpers import parse_jsonpath
from universal_json_agent_mcp.utils.operators import FILTER_OPERATORS, validate_operator
from universal_json_agent_mcp.utils.path_resolver import resolve_path
from universal_json_agent_mcp.utils.truncation import truncate_list, truncate_value


def jsonpath_query(store: JSONStore, alias: str, expression: str) -> str:
    """
    Execute a JSONPath expression against a loaded document.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        expression: A JSONPath expression (e.g. "$.users[*].email").

    Returns:
        The matched values serialized as a list, or an error message.
    """
    data = store.get(alias)

    jp = parse_jsonpath(expression)

    matches = jp.find(data)

    if not matches:
        return f"No matches found for JSONPath: {expression}"

    values = [match.value for match in matches]

    if len(values) == 1:
        return truncate_value(values[0])

    return truncate_list(values)


def filter_objects(
    store: JSONStore,
    alias: str,
    path: str,
    field: str,
    operator: str,
    value: str | int | float | bool | None,
) -> str:
    """
    Filter an array of objects by a field condition.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array to filter (e.g. "orders", "data.users").
        field: The field name to compare on each object.
        operator: Comparison operator. One of:
                  "eq"       — equals
                  "neq"      — not equals
                  "gt"       — greater than
                  "gte"      — greater than or equal
                  "lt"       — less than
                  "lte"      — less than or equal
                  "contains" — substring match (strings only)
                  "regex"    — regex match (strings only)
        value: The value to compare against.

    Returns:
        The filtered list of objects, serialized and truncated.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(f"Value at path '{path}' is {type(target).__name__}, expected an array.")

    _validate_operator(operator)
    comparator = FILTER_OPERATORS[operator]
    results = []

    for item in target:
        if not isinstance(item, dict):
            continue
        if field not in item:
            continue
        try:
            if comparator(item[field], value):
                results.append(item)
        except (TypeError, re.error):
            # Skip items where comparison doesn't make sense (e.g. comparing str > int)
            continue

    header = f"Matched {len(results)} of {len(target)} items"
    if not results:
        return header

    return header + "\n" + truncate_list(results)


def search_text(
    store: JSONStore,
    alias: str,
    pattern: str,
    path: str = "",
    case_sensitive: bool = False,
) -> str:
    """
    Recursively search all string values for a substring or regex pattern.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        pattern: A substring or regex pattern to search for.
        path: Optional starting path to narrow the search scope.
        case_sensitive: Whether matching is case-sensitive (default False).

    Returns:
        A list of matching paths and their values.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern '{pattern}': {exc}")

    hits: list[dict[str, str]] = []
    _search_recursive(target, compiled, current_path=path or "$", hits=hits, max_hits=100)

    if not hits:
        return f"No matches found for pattern: {pattern}"

    header = f"Found {len(hits)} match(es) for '{pattern}'"
    if len(hits) >= 100:
        header += " (results capped at 100)"

    return header + "\n" + truncate_list(hits)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _search_recursive(
    value: Any,
    pattern: re.Pattern[str],
    current_path: str,
    hits: list[dict[str, str]],
    max_hits: int,
) -> None:
    """DFS through the JSON tree, collecting string values that match *pattern*."""
    if len(hits) >= max_hits:
        return

    if isinstance(value, str):
        if pattern.search(value):
            hits.append({"path": current_path, "value": value})
    elif isinstance(value, dict):
        for key, val in value.items():
            _search_recursive(val, pattern, f"{current_path}.{key}", hits, max_hits)
    elif isinstance(value, list):
        for idx, val in enumerate(value):
            _search_recursive(val, pattern, f"{current_path}[{idx}]", hits, max_hits)


def _validate_operator(op: str) -> None:
    """Raise ValueError if the operator is not recognised."""
    validate_operator(op)

