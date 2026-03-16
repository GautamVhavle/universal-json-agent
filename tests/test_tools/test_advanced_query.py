"""Tests for advanced query tools (multi_filter, compare)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from json_agent.store import JSONStore
from json_agent.tools.advanced_query import multi_filter, compare


def _load_data(store: JSONStore, data, alias: str = "d") -> JSONStore:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    store.load(f.name, alias=alias)
    os.unlink(f.name)
    return store


# ==================================================================
# multi_filter
# ==================================================================


class TestMultiFilter:
    def test_and_mode(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"status": "active", "score": 90},
            {"status": "active", "score": 40},
            {"status": "inactive", "score": 85},
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "status", "operator": "eq", "value": "active"},
            {"field": "score", "operator": "gt", "value": 50},
        ], mode="and")
        assert "Matched 1 of 3" in result
        assert "90" in result

    def test_or_mode(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"status": "active", "score": 90},
            {"status": "active", "score": 40},
            {"status": "inactive", "score": 85},
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "status", "operator": "eq", "value": "inactive"},
            {"field": "score", "operator": "gt", "value": 80},
        ], mode="or")
        assert "Matched 2 of 3" in result

    def test_single_condition(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}, {"x": 2}]})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "eq", "value": 1},
        ])
        assert "Matched 1 of 2" in result

    def test_no_matches(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}, {"x": 2}]})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "gt", "value": 100},
        ])
        assert "Matched 0 of 2" in result

    def test_empty_conditions_raises(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}]})
        with pytest.raises(ValueError, match="At least one condition"):
            multi_filter(s, "d", "items", [])

    def test_invalid_mode_raises(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}]})
        with pytest.raises(ValueError, match="Invalid mode"):
            multi_filter(s, "d", "items", [
                {"field": "x", "operator": "eq", "value": 1},
            ], mode="xor")

    def test_invalid_operator_raises(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}]})
        with pytest.raises(ValueError, match="unknown operator"):
            multi_filter(s, "d", "items", [
                {"field": "x", "operator": "nope", "value": 1},
            ])

    def test_missing_condition_key_raises(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}]})
        with pytest.raises(ValueError, match="missing required key"):
            multi_filter(s, "d", "items", [
                {"field": "x", "operator": "eq"},  # missing "value"
            ])

    def test_not_array_raises(self, store: JSONStore) -> None:
        s = _load_data(store, {"obj": {"x": 1}})
        with pytest.raises(TypeError, match="expected an array"):
            multi_filter(s, "d", "obj", [
                {"field": "x", "operator": "eq", "value": 1},
            ])

    def test_contains_and_gt(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"name": "Alpha Widget", "price": 30},
            {"name": "Beta Widget", "price": 10},
            {"name": "Alpha Gadget", "price": 50},
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "name", "operator": "contains", "value": "Alpha"},
            {"field": "price", "operator": "gte", "value": 30},
        ], mode="and")
        assert "Matched 2 of 3" in result

    def test_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "eq", "value": 1},
        ])
        assert "Matched 0 of 0" in result

    def test_missing_field_no_match(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"x": 1, "y": 2},
            {"x": 3},  # missing y
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "gt", "value": 0},
            {"field": "y", "operator": "gt", "value": 0},
        ], mode="and")
        assert "Matched 1 of 2" in result

    def test_regex_condition(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"code": "AB-123"},
            {"code": "CD-456"},
            {"code": "AB-789"},
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "code", "operator": "regex", "value": "^AB-"},
        ])
        assert "Matched 2 of 3" in result


# ==================================================================
# compare
# ==================================================================


class TestCompare:
    def test_identical_values(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"x": 1}, "b": {"x": 1}})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "No differences" in result

    def test_value_change(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"x": 1}, "b": {"x": 2}})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "CHANGED" in result
        assert "1" in result and "2" in result

    def test_added_key(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"x": 1}, "b": {"x": 1, "y": 2}})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "ADDED" in result
        assert "y" in result

    def test_removed_key(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"x": 1, "y": 2}, "b": {"x": 1}})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "REMOVED" in result
        assert "y" in result

    def test_type_change(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"v": 42}, "b": {"v": "forty-two"}})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "TYPE" in result or "CHANGED" in result

    def test_array_length_diff(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": [1, 2, 3], "b": [1, 2]})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "LENGTH" in result

    def test_nested_diff(self, store: JSONStore) -> None:
        s = _load_data(store, {
            "a": {"deep": {"val": "old"}},
            "b": {"deep": {"val": "new"}},
        })
        result = compare(s, "d", path_a="a", path_b="b")
        assert "CHANGED" in result
        assert "deep" in result

    def test_cross_document_compare(self, store: JSONStore) -> None:
        _load_data(store, {"x": 1}, alias="doc1")
        _load_data(store, {"x": 2}, alias="doc2")
        result = compare(store, "doc1", alias_b="doc2")
        assert "CHANGED" in result

    def test_compare_root_to_root(self, store: JSONStore) -> None:
        _load_data(store, {"a": 1, "b": 2}, alias="r1")
        _load_data(store, {"a": 1, "b": 2}, alias="r2")
        result = compare(store, "r1", alias_b="r2")
        assert "No differences" in result

    def test_compare_scalar_diff(self, store: JSONStore) -> None:
        s = _load_data(store, {"v1": "hello", "v2": "world"})
        result = compare(s, "d", path_a="v1", path_b="v2")
        assert "CHANGED" in result

    def test_compare_different_types(self, store: JSONStore) -> None:
        s = _load_data(store, {"arr": [1, 2], "obj": {"a": 1}})
        result = compare(s, "d", path_a="arr", path_b="obj")
        assert "TYPE" in result

    def test_unknown_alias(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            compare(store, "missing")

    def test_non_dict_condition_raises(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 1}]})
        with pytest.raises(ValueError, match="must be a dict"):
            multi_filter(s, "d", "items", ["not a dict"])

    def test_uppercase_mode(self, store: JSONStore) -> None:
        """Mode is case-insensitive: 'AND' should work like 'and'."""
        s = _load_data(store, {"items": [{"x": 1, "y": 2}]})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "eq", "value": 1},
            {"field": "y", "operator": "eq", "value": 2},
        ], mode="AND")
        assert "Matched 1 of 1" in result

    def test_multi_filter_type_mismatch_skipped(self, store: JSONStore) -> None:
        """Comparing string > int triggers TypeError; should be skipped (False)."""
        s = _load_data(store, {"items": [
            {"val": "text"},
            {"val": 100},
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "val", "operator": "gt", "value": 50},
        ])
        assert "Matched 1 of 2" in result

    def test_multi_filter_regex_error_skipped(self, store: JSONStore) -> None:
        """Invalid regex in value triggers re.error; should be skipped (False)."""
        s = _load_data(store, {"items": [
            {"code": "ABC"},
        ]})
        result = multi_filter(s, "d", "items", [
            {"field": "code", "operator": "regex", "value": "[invalid("},
        ])
        assert "Matched 0 of 1" in result

    def test_multi_filter_non_dict_items_skipped(self, store: JSONStore) -> None:
        """Non-dict items in array are silently skipped."""
        s = _load_data(store, {"items": [42, {"x": 1}, "text"]})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "eq", "value": 1},
        ])
        assert "Matched 1 of 3" in result

    def test_multi_filter_header_condition_description(self, store: JSONStore) -> None:
        """Output header should contain the condition descriptions."""
        s = _load_data(store, {"items": [{"x": 1}]})
        result = multi_filter(s, "d", "items", [
            {"field": "x", "operator": "eq", "value": 1},
        ])
        assert "x eq 1" in result

    def test_compare_diffs_capped_at_100(self, store: JSONStore) -> None:
        """More than 100 differences should be capped."""
        obj_a = {f"k{i}": i for i in range(150)}
        obj_b = {f"k{i}": i + 1 for i in range(150)}
        _load_data(store, {"a": obj_a, "b": obj_b})
        result = compare(store, "d", path_a="a", path_b="b")
        assert "capped at 100" in result

    def test_compare_long_scalar_truncated(self, store: JSONStore) -> None:
        """Very long string diffs should be truncated with '...'."""
        long_a = "a" * 200
        long_b = "b" * 200
        s = _load_data(store, {"a": long_a, "b": long_b})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "..." in result

    def test_compare_arrays_same_length_diff_values(self, store: JSONStore) -> None:
        """Arrays of same length but different elements show CHANGED."""
        s = _load_data(store, {"a": [1, 2, 3], "b": [1, 99, 3]})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "CHANGED" in result
        assert "[1]" in result

    def test_compare_string_scalars_repr(self, store: JSONStore) -> None:
        """String diffs use repr() notation."""
        s = _load_data(store, {"a": "hello", "b": "world"})
        result = compare(s, "d", path_a="a", path_b="b")
        assert "CHANGED" in result
        assert "'hello'" in result
        assert "'world'" in result
