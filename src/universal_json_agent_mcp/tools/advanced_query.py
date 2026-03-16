"""
Advanced Query Tools — multi-condition filtering and cross-path comparisons.

Extends the basic single-field filter_objects with AND/OR logic, and adds
a compare tool for diffing two paths or documents.
"""

from __future__ import annotations

import json
import re
from typing import Any

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.utils.path_resolver import resolve_path
from universal_json_agent_mcp.utils.truncation import truncate_list, truncate_value


# ------------------------------------------------------------------
# Operator dispatch (reused from query.py pattern)
# ------------------------------------------------------------------

_OPERATORS: dict[str, Any] = {
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "contains": lambda a, b: isinstance(a, str) and isinstance(b, str) and b in a,
    "regex": lambda a, b: isinstance(a, str) and isinstance(b, str) and bool(re.search(b, a)),
}

_VALID_OPS = set(_OPERATORS.keys())
_VALID_MODES = {"and", "or"}


# ==================================================================
# multi_filter
# ==================================================================

def multi_filter(
    store: JSONStore,
    alias: str,
    path: str,
    conditions: list[dict[str, Any]],
    mode: str = "and",
) -> str:
    """
    Filter an array of objects with multiple conditions combined by AND / OR.

    Each condition is a dict with keys: field, operator, value.
    Supported operators: eq, neq, gt, gte, lt, lte, contains, regex.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array to filter.
        conditions: List of {"field": str, "operator": str, "value": ...} dicts.
        mode: "and" (all conditions must match) or "or" (any condition matches).

    Returns:
        The filtered list of objects with a match count header.
    """
    if not conditions:
        raise ValueError("At least one condition is required.")

    mode_lower = mode.lower()
    if mode_lower not in _VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'and' or 'or'.")

    # Validate all conditions up front
    parsed_conditions = []
    for i, cond in enumerate(conditions):
        if not isinstance(cond, dict):
            raise ValueError(f"Condition {i} must be a dict, got {type(cond).__name__}.")
        for key in ("field", "operator", "value"):
            if key not in cond:
                raise ValueError(f"Condition {i} missing required key '{key}'.")
        op = cond["operator"]
        if op not in _VALID_OPS:
            raise ValueError(
                f"Condition {i}: unknown operator '{op}'. "
                f"Valid: {', '.join(sorted(_VALID_OPS))}"
            )
        parsed_conditions.append((cond["field"], _OPERATORS[op], cond["value"]))

    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(
            f"Value at path '{path}' is {type(target).__name__}, expected an array."
        )

    results = []
    for item in target:
        if not isinstance(item, dict):
            continue
        matches = []
        for field, comparator, value in parsed_conditions:
            if field not in item:
                matches.append(False)
                continue
            try:
                matches.append(bool(comparator(item[field], value)))
            except (TypeError, re.error):
                matches.append(False)

        if mode_lower == "and" and all(matches):
            results.append(item)
        elif mode_lower == "or" and any(matches):
            results.append(item)

    cond_desc = f" {mode.upper()} ".join(
        f"{c['field']} {c['operator']} {c['value']!r}" for c in conditions
    )
    header = f"Matched {len(results)} of {len(target)} items  ({cond_desc})"
    if not results:
        return header
    return header + "\n" + truncate_list(results)


# ==================================================================
# compare
# ==================================================================

def compare(
    store: JSONStore,
    alias_a: str,
    alias_b: str | None = None,
    path_a: str = "",
    path_b: str = "",
) -> str:
    """
    Compare two JSON values and report their differences.

    Can compare two paths within the same document (alias_a == alias_b)
    or values from two different loaded documents.

    Reports: added keys, removed keys, type changes, and value changes.

    Args:
        store: The shared JSONStore instance.
        alias_a: The alias of the first (or only) document.
        alias_b: The alias of the second document. Defaults to alias_a
                 (compare within same document).
        path_a: Dot-notation path for the first value.
        path_b: Dot-notation path for the second value.

    Returns:
        A structured diff report.
    """
    alias_b = alias_b or alias_a

    data_a = store.get(alias_a)
    data_b = store.get(alias_b)
    val_a = resolve_path(data_a, path_a)
    val_b = resolve_path(data_b, path_b)

    diffs: list[str] = []
    _diff_recursive(val_a, val_b, path="$", diffs=diffs, max_diffs=100)

    if not diffs:
        return "No differences found."

    header = f"Found {len(diffs)} difference(s)"
    if len(diffs) >= 100:
        header += " (capped at 100)"
    return header + "\n" + "\n".join(diffs)


# ==================================================================
# Private helpers — compare
# ==================================================================


def _diff_recursive(
    a: Any,
    b: Any,
    path: str,
    diffs: list[str],
    max_diffs: int,
) -> None:
    """Walk two values and record differences into *diffs*."""
    if len(diffs) >= max_diffs:
        return

    type_a = type(a).__name__
    type_b = type(b).__name__

    # Different types
    if type_a != type_b:
        diffs.append(f"  TYPE  {path}: {type_a} → {type_b}")
        return

    # Both dicts
    if isinstance(a, dict) and isinstance(b, dict):
        keys_a = set(a.keys())
        keys_b = set(b.keys())
        for key in sorted(keys_a - keys_b):
            if len(diffs) >= max_diffs:
                return
            diffs.append(f"  REMOVED {path}.{key}")
        for key in sorted(keys_b - keys_a):
            if len(diffs) >= max_diffs:
                return
            diffs.append(f"  ADDED   {path}.{key}")
        for key in sorted(keys_a & keys_b):
            _diff_recursive(a[key], b[key], f"{path}.{key}", diffs, max_diffs)
        return

    # Both lists
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"  LENGTH {path}: {len(a)} → {len(b)}")
        for i in range(min(len(a), len(b))):
            _diff_recursive(a[i], b[i], f"{path}[{i}]", diffs, max_diffs)
        return

    # Scalars
    if a != b:
        repr_a = json.dumps(a, default=str) if not isinstance(a, str) else repr(a)
        repr_b = json.dumps(b, default=str) if not isinstance(b, str) else repr(b)
        # Truncate very long values
        if len(repr_a) > 80:
            repr_a = repr_a[:77] + "..."
        if len(repr_b) > 80:
            repr_b = repr_b[:77] + "..."
        diffs.append(f"  CHANGED {path}: {repr_a} → {repr_b}")
