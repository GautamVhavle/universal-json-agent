"""
Filter Operators — shared dispatch table for field-based filtering.

Centralises the operator definitions used by both ``query.filter_objects``
and ``advanced_query.multi_filter`` so they stay in sync.
"""

from __future__ import annotations

import math
import re
from typing import Any, Callable


def _parse_number(value: str) -> int | float | None:
    """Parse a numeric string. Reject blanks, non-numbers, and non-finite floats."""
    text = value.strip()
    if not text:
        return None
    try:
        number: int | float = float(text) if any(c in text for c in ".eE") else int(text)
    except ValueError:
        return None
    if isinstance(number, float) and not math.isfinite(number):
        return None
    return number


def align_numbers(left: Any, right: Any) -> tuple[Any, Any]:
    """Coerce a numeric string when the other side is a real number.

    Booleans are left alone so True is never treated as 1. Two strings stay
    strings so ids like "01234" are not rewritten.
    """
    if isinstance(left, bool) or isinstance(right, bool):
        return left, right
    if isinstance(left, (int, float)) and isinstance(right, str):
        parsed = _parse_number(right)
        if parsed is not None:
            return left, parsed
    elif isinstance(right, (int, float)) and isinstance(left, str):
        parsed = _parse_number(left)
        if parsed is not None:
            return parsed, right
    return left, right


def _numeric(compare: Callable[[Any, Any], bool]) -> Callable[[Any, Any], bool]:
    def wrapped(left: Any, right: Any) -> bool:
        left, right = align_numbers(left, right)
        return compare(left, right)

    return wrapped


def skip_note(*, type_skipped: int = 0, regex_skipped: int = 0) -> str:
    """Suffix for filter headers when some comparisons could not run."""
    notes: list[str] = []
    if type_skipped:
        notes.append(f"{type_skipped} skipped — value type does not match")
    if regex_skipped:
        notes.append(f"{regex_skipped} skipped — invalid regex")
    if not notes:
        return ""
    return "  (" + "; ".join(notes) + ")"


# Operator dispatch table — maps operator names to comparator lambdas.
# Each comparator takes (field_value, filter_value) and returns bool.
FILTER_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq":       _numeric(lambda a, b: a == b),
    "neq":      _numeric(lambda a, b: a != b),
    "gt":       _numeric(lambda a, b: a > b),
    "gte":      _numeric(lambda a, b: a >= b),
    "lt":       _numeric(lambda a, b: a < b),
    "lte":      _numeric(lambda a, b: a <= b),
    "contains": lambda a, b: isinstance(a, str) and isinstance(b, str) and b in a,
    "regex":    lambda a, b: isinstance(a, str) and isinstance(b, str) and bool(re.search(b, a)),
}

VALID_OPERATOR_NAMES = frozenset(FILTER_OPERATORS.keys())


def validate_operator(operator: str) -> None:
    """
    Raise ``ValueError`` if *operator* is not a recognised filter operator.

    Args:
        operator: The operator string to validate.

    Raises:
        ValueError: With a message listing all valid operators.
    """
    if operator not in FILTER_OPERATORS:
        raise ValueError(
            f"Unknown operator '{operator}'. "
            f"Valid operators: {', '.join(sorted(VALID_OPERATOR_NAMES))}"
        )
