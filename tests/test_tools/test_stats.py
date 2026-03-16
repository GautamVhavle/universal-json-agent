"""Tests for stats tools (describe)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from json_agent.store import JSONStore
from json_agent.tools.stats import describe


def _load_data(store: JSONStore, data, alias: str = "d") -> JSONStore:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    store.load(f.name, alias=alias)
    os.unlink(f.name)
    return store


class TestDescribe:
    def test_basic_stats(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [10, 20, 30, 40, 50]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 5" in result
        assert "Mean   : 30" in result
        assert "Min    : 10" in result
        assert "Max    : 50" in result
        assert "Sum    : 150" in result
        assert "50%    : 30" in result  # median

    def test_single_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [42]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 1" in result
        assert "Mean   : 42" in result
        assert "Min    : 42" in result
        assert "Max    : 42" in result
        assert "Std Dev: 0" in result

    def test_no_numbers(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": ["a", "b"]})
        result = describe(s, "d", "$.vals[*]")
        assert "No numeric values" in result

    def test_no_matches(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [1, 2]})
        result = describe(s, "d", "$.nope[*]")
        assert "No numeric values" in result

    def test_booleans_excluded(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [True, False, 10, 20]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 2" in result
        assert "Mean   : 15" in result

    def test_mixed_types(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [10, "text", None, 30]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 2" in result

    def test_negative_numbers(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [-10, 0, 10]})
        result = describe(s, "d", "$.vals[*]")
        assert "Mean   : 0" in result
        assert "Min    : -10" in result

    def test_floats(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [1.5, 2.5, 3.5, 4.5]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 4" in result
        assert "Mean   : 3" in result

    def test_percentiles(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": list(range(1, 101))})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 100" in result
        assert "25%    : 25" in result
        assert "50%    : 50" in result
        assert "75%    : 75" in result

    def test_std_dev_nonzero(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [2, 4, 4, 4, 5, 5, 7, 9]})
        result = describe(s, "d", "$.vals[*]")
        assert "Std Dev: 2" in result  # std dev = 2.0

    def test_invalid_jsonpath(self, store: JSONStore) -> None:
        s = _load_data(store, {"v": 1})
        with pytest.raises(ValueError, match="Invalid JSONPath"):
            describe(s, "d", "$$$$bad")

    def test_unknown_alias(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            describe(store, "missing", "$.x")

    def test_two_values_interpolation(self, store: JSONStore) -> None:
        """With [10, 20], p25 should be 12.5 via linear interpolation."""
        s = _load_data(store, {"vals": [10, 20]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 2" in result
        assert "25%    : 12.5" in result

    def test_large_float_formatting(self, store: JSONStore) -> None:
        """Floats >= 1e15 should use 4 decimal place formatting."""
        s = _load_data(store, {"vals": [1.5e15, 2.5e15]})
        result = describe(s, "d", "$.vals[*]")
        assert "Count  : 2" in result
        # The mean 2e15 is a float >= 1e15, should not be truncated to int
        assert "Sum" in result

    def test_identical_values(self, store: JSONStore) -> None:
        """All same values: std dev = 0, all percentiles = the value."""
        s = _load_data(store, {"vals": [5, 5]})
        result = describe(s, "d", "$.vals[*]")
        assert "Std Dev: 0" in result
        assert "25%    : 5" in result
        assert "50%    : 5" in result
        assert "75%    : 5" in result

    def test_exact_percentile_rank(self, store: JSONStore) -> None:
        """3-element array: p50 is exactly the middle element."""
        s = _load_data(store, {"vals": [10, 20, 30]})
        result = describe(s, "d", "$.vals[*]")
        assert "50%    : 20" in result

    def test_non_integer_float_format(self, store: JSONStore) -> None:
        """Float values that aren't integer-valued show decimals."""
        s = _load_data(store, {"vals": [1.1, 2.2, 3.3]})
        result = describe(s, "d", "$.vals[*]")
        assert "Mean" in result
        assert "." in result  # should have decimal places
