"""
Filter Operators — shared dispatch table for field-based filtering.

Centralises the operator definitions used by both ``query.filter_objects``
and ``advanced_query.multi_filter`` so they stay in sync.
"""

from __future__ import annotations

import re
from typing import Any, Callable

# Operator dispatch table — maps operator names to comparator lambdas.
# Each comparator takes (field_value, filter_value) and returns bool.
FILTER_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq":       lambda a, b: a == b,
    "neq":      lambda a, b: a != b,
    "gt":       lambda a, b: a > b,
    "gte":      lambda a, b: a >= b,
    "lt":       lambda a, b: a < b,
    "lte":      lambda a, b: a <= b,
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
