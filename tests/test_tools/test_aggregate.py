"""Tests for aggregate tools (count, sum_values, min_max, unique_values, value_counts)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools.aggregate import count, sum_values, min_max, unique_values, value_counts


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def _load_data(store: JSONStore, data, alias: str = "d") -> JSONStore:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    store.load(f.name, alias=alias)
    os.unlink(f.name)
    return store


class TestCount:
    def test_count_array(self, loaded_store: JSONStore) -> None:
        result = count(loaded_store, "test", "products")
        assert "3 items" in result

    def test_count_object(self, loaded_store: JSONStore) -> None:
        result = count(loaded_store, "test")
        assert "7 keys" in result

    def test_count_scalar(self, loaded_store: JSONStore) -> None:
        result = count(loaded_store, "test", "name")
        assert "scalar" in result

    def test_count_root_array(self, loaded_array_store: JSONStore) -> None:
        result = count(loaded_array_store, "arr")
        assert "5 items" in result

    # --- Edge cases ---

    def test_count_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = count(s, "d", "items")
        assert "0 items" in result

    def test_count_empty_object(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = count(s, "d")
        assert "0 keys" in result

    def test_count_null(self, store: JSONStore) -> None:
        s = _load_data(store, {"val": None})
        result = count(s, "d", "val")
        assert "scalar" in result

    def test_count_boolean(self, store: JSONStore) -> None:
        s = _load_data(store, {"flag": True})
        result = count(s, "d", "flag")
        assert "scalar" in result

    def test_count_number(self, store: JSONStore) -> None:
        s = _load_data(store, {"n": 42})
        result = count(s, "d", "n")
        assert "scalar" in result

    def test_count_nested_array(self, loaded_store: JSONStore) -> None:
        result = count(loaded_store, "test", "tags")
        assert "3 items" in result

    def test_count_unknown_alias(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            count(store, "missing")


class TestSumValues:
    def test_sum_prices(self, loaded_store: JSONStore) -> None:
        result = sum_values(loaded_store, "test", "$.products[*].price")
        assert "39.24" in result
        assert "3 values" in result

    def test_sum_no_numbers(self, loaded_store: JSONStore) -> None:
        result = sum_values(loaded_store, "test", "$.products[*].name")
        assert "No numeric values" in result

    def test_sum_no_matches(self, loaded_store: JSONStore) -> None:
        result = sum_values(loaded_store, "test", "$.nonexistent[*].x")
        assert "No numeric values" in result

    def test_sum_scores(self, loaded_array_store: JSONStore) -> None:
        result = sum_values(loaded_array_store, "arr", "$[*].score")
        assert "358" in result

    # --- Edge cases ---

    def test_sum_with_zero(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [0, 0, 0]})
        result = sum_values(s, "d", "$.vals[*]")
        assert "Sum: 0" in result
        assert "3 values" in result

    def test_sum_negative_numbers(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [-10, -20, 30]})
        result = sum_values(s, "d", "$.vals[*]")
        assert "Sum: 0" in result

    def test_sum_single_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [42]})
        result = sum_values(s, "d", "$.vals[*]")
        assert "Sum: 42" in result
        assert "1 values" in result

    def test_sum_mixed_types_ignores_non_numeric(self, store: JSONStore) -> None:
        """Boolean True/False should NOT be summed as 1/0."""
        s = _load_data(store, {"vals": [10, "text", True, None, 20]})
        result = sum_values(s, "d", "$.vals[*]")
        assert "Sum: 30" in result
        assert "2 values" in result

    def test_sum_floats_precision(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [0.1, 0.2]})
        result = sum_values(s, "d", "$.vals[*]")
        assert "Sum:" in result
        # Result should contain a float close to 0.3
        assert "0.3" in result

    def test_sum_invalid_jsonpath(self, loaded_store: JSONStore) -> None:
        with pytest.raises(ValueError, match="Invalid JSONPath"):
            sum_values(loaded_store, "test", "$$$$bad")


class TestMinMax:
    def test_prices(self, loaded_store: JSONStore) -> None:
        result = min_max(loaded_store, "test", "$.products[*].price")
        assert "4.75" in result
        assert "24.5" in result
        assert "3 values" in result

    def test_no_numbers(self, loaded_store: JSONStore) -> None:
        result = min_max(loaded_store, "test", "$.products[*].name")
        assert "No numeric values" in result

    def test_scores(self, loaded_array_store: JSONStore) -> None:
        result = min_max(loaded_array_store, "arr", "$[*].score")
        assert "42" in result
        assert "93" in result

    # --- Edge cases ---

    def test_single_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [7]})
        result = min_max(s, "d", "$.vals[*]")
        assert "Min: 7" in result
        assert "Max: 7" in result

    def test_negative_values(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [-100, -1, 0, 50]})
        result = min_max(s, "d", "$.vals[*]")
        assert "Min: -100" in result
        assert "Max: 50" in result

    def test_all_same_values(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [5, 5, 5, 5]})
        result = min_max(s, "d", "$.vals[*]")
        assert "Min: 5" in result
        assert "Max: 5" in result

    def test_booleans_excluded(self, store: JSONStore) -> None:
        s = _load_data(store, {"vals": [True, False, 10]})
        result = min_max(s, "d", "$.vals[*]")
        assert "Min: 10" in result
        assert "1 values" in result


class TestUniqueValues:
    def test_unique_statuses(self, loaded_array_store: JSONStore) -> None:
        result = unique_values(loaded_array_store, "arr", "$[*].status")
        assert "active" in result
        assert "inactive" in result
        assert "pending" in result
        assert "3 unique" in result

    def test_unique_booleans(self, loaded_store: JSONStore) -> None:
        result = unique_values(loaded_store, "test", "$.products[*].in_stock")
        assert "2 unique" in result

    def test_no_matches(self, loaded_store: JSONStore) -> None:
        result = unique_values(loaded_store, "test", "$.nonexistent")
        assert "No values" in result

    # --- Edge cases ---

    def test_all_same_value(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": "same"}, {"x": "same"}, {"x": "same"}])
        result = unique_values(s, "d", "$[*].x")
        assert "1 unique" in result
        assert "3 total" in result

    def test_unique_with_null(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": None}, {"x": "a"}, {"x": None}])
        result = unique_values(s, "d", "$[*].x")
        assert "2 unique" in result

    def test_unique_numbers(self, store: JSONStore) -> None:
        s = _load_data(store, [{"n": 1}, {"n": 2}, {"n": 1}, {"n": 3}])
        result = unique_values(s, "d", "$[*].n")
        assert "3 unique" in result
        assert "4 total" in result

    def test_unique_preserves_order(self, store: JSONStore) -> None:
        s = _load_data(store, [{"v": "cat"}, {"v": "ant"}, {"v": "bat"}, {"v": "ant"}])
        result = unique_values(s, "d", "$[*].v")
        # Order should be cat, ant, bat (first appearance order)
        cat_pos = result.index("cat")
        ant_pos = result.index("ant")
        bat_pos = result.index("bat")
        assert cat_pos < ant_pos < bat_pos

    def test_unique_with_dicts(self, store: JSONStore) -> None:
        """Unhashable types (dicts) should still be de-duped."""
        s = _load_data(store, [
            {"meta": {"type": "A"}},
            {"meta": {"type": "B"}},
            {"meta": {"type": "A"}},
        ])
        result = unique_values(s, "d", "$[*].meta")
        assert "2 unique" in result


class TestValueCounts:
    def test_status_counts(self, loaded_array_store: JSONStore) -> None:
        result = value_counts(loaded_array_store, "arr", "$[*].status")
        assert "active" in result
        assert "3" in result
        assert "inactive" in result
        assert "pending" in result
        assert "5 values" in result
        assert "3 unique" in result

    def test_boolean_counts(self, loaded_store: JSONStore) -> None:
        result = value_counts(loaded_store, "test", "$.products[*].in_stock")
        assert "True" in result
        assert "False" in result

    def test_no_matches(self, loaded_store: JSONStore) -> None:
        result = value_counts(loaded_store, "test", "$.nonexistent")
        assert "No values" in result

    # --- Edge cases ---

    def test_all_unique(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": "a"}, {"x": "b"}, {"x": "c"}])
        result = value_counts(s, "d", "$[*].x")
        assert "3 unique" in result
        # Each should have count 1
        for val in ["a", "b", "c"]:
            assert val in result

    def test_all_same(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": "same"} for _ in range(5)])
        result = value_counts(s, "d", "$[*].x")
        assert "1 unique" in result
        assert "5" in result  # count

    def test_value_counts_sorted_descending(self, store: JSONStore) -> None:
        s = _load_data(store, [
            {"cat": "B"}, {"cat": "A"}, {"cat": "A"},
            {"cat": "A"}, {"cat": "B"},
        ])
        result = value_counts(s, "d", "$[*].cat")
        # A (3) should appear before B (2)
        a_pos = result.index("A")
        b_pos = result.index("B")
        assert a_pos < b_pos

    def test_value_counts_with_numbers(self, store: JSONStore) -> None:
        s = _load_data(store, [{"n": 1}, {"n": 2}, {"n": 1}, {"n": 1}])
        result = value_counts(s, "d", "$[*].n")
        assert "2 unique" in result

    def test_value_counts_with_null(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": None}, {"x": "a"}, {"x": None}])
        result = value_counts(s, "d", "$[*].x")
        assert "2 unique" in result

    def test_value_counts_long_value_truncated(self, store: JSONStore) -> None:
        long_val = "x" * 100
        s = _load_data(store, [{"v": long_val}])
        result = value_counts(s, "d", "$[*].v")
        assert "..." in result  # long value should be truncated in display

    def test_unique_values_with_list_values(self, store: JSONStore) -> None:
        """Unhashable list values trigger the fallback dedup path."""
        s = _load_data(store, [
            {"tags": [1, 2]},
            {"tags": [3, 4]},
            {"tags": [1, 2]},
        ])
        result = unique_values(s, "d", "$[*].tags")
        assert "2 unique" in result

    def test_value_counts_with_dict_values(self, store: JSONStore) -> None:
        """Dict values are JSON-serialized for counting."""
        s = _load_data(store, [
            {"meta": {"a": 1}},
            {"meta": {"a": 1}},
            {"meta": {"b": 2}},
        ])
        result = value_counts(s, "d", "$[*].meta")
        assert "2 unique" in result

    def test_value_counts_with_list_values(self, store: JSONStore) -> None:
        """List values are JSON-serialized for counting."""
        s = _load_data(store, [
            {"tags": [1, 2]},
            {"tags": [1, 2]},
            {"tags": [3]},
        ])
        result = value_counts(s, "d", "$[*].tags")
        assert "2 unique" in result

    def test_count_root_path_label(self, store: JSONStore) -> None:
        """When path is empty, message should use '$' as label."""
        s = _load_data(store, {"a": 1, "b": 2})
        result = count(s, "d")
        assert "'$'" in result
