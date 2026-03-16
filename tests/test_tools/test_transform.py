"""Tests for transform tools (flatten, pick_fields, group_by, sort_by, sample)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools.transform import flatten, pick_fields, group_by, sort_by, sample


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


# ==================================================================
# Flatten
# ==================================================================


class TestFlatten:
    def test_flat_config(self, loaded_store: JSONStore) -> None:
        result = flatten(loaded_store, "test", path="config")
        assert "theme" in result
        assert "dark" in result
        assert "nested.deep.value" in result
        assert "found_it" in result

    def test_flat_root(self, loaded_store: JSONStore) -> None:
        result = flatten(loaded_store, "test")
        assert "name" in result
        assert "config.theme" in result

    def test_custom_separator(self, loaded_store: JSONStore) -> None:
        result = flatten(loaded_store, "test", path="config", separator="/")
        assert "nested/deep/value" in result

    def test_not_an_object(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError, match="expected an object"):
            flatten(loaded_store, "test", path="tags")

    # --- Edge cases ---

    def test_flatten_empty_object(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = flatten(s, "d")
        # Should return truncated empty dict
        assert "{}" in result

    def test_flatten_deeply_nested(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"b": {"c": {"d": "deep"}}}})
        result = flatten(s, "d")
        assert "a.b.c.d" in result
        assert "deep" in result

    def test_flatten_array_inside_object(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [1, 2, 3]})
        result = flatten(s, "d")
        assert "items[0]" in result
        assert "items[1]" in result
        assert "items[2]" in result

    def test_flatten_nested_array_of_dicts(self, store: JSONStore) -> None:
        s = _load_data(store, {"rows": [{"x": 1}, {"x": 2}]})
        result = flatten(s, "d")
        assert "rows[0].x" in result
        assert "rows[1].x" in result

    def test_flatten_array_root_fails(self, store: JSONStore) -> None:
        s = _load_data(store, [1, 2, 3])
        with pytest.raises(TypeError, match="expected an object"):
            flatten(s, "d")

    def test_flatten_scalar_root_fails(self, store: JSONStore) -> None:
        s = _load_data(store, "just a string")
        with pytest.raises(TypeError, match="expected an object"):
            flatten(s, "d")

    def test_flatten_null_values_preserved(self, store: JSONStore) -> None:
        s = _load_data(store, {"key": None, "other": "val"})
        result = flatten(s, "d")
        assert "key" in result
        assert "null" in result.lower() or "None" in result

    def test_flatten_boolean_values(self, store: JSONStore) -> None:
        s = _load_data(store, {"on": True, "off": False})
        result = flatten(s, "d")
        assert "on" in result
        assert "off" in result

    def test_flatten_unicode_keys(self, store: JSONStore) -> None:
        s = _load_data(store, {"日本語": {"키": "값"}})
        result = flatten(s, "d")
        assert "日本語.키" in result
        assert "값" in result


# ==================================================================
# PickFields
# ==================================================================


class TestPickFields:
    def test_pick_name_price(self, loaded_store: JSONStore) -> None:
        result = pick_fields(loaded_store, "test", "products", ["name", "price"])
        assert "Widget" in result
        assert "9.99" in result
        assert "3 items" in result
        assert "in_stock" not in result

    def test_pick_single_field(self, loaded_store: JSONStore) -> None:
        result = pick_fields(loaded_store, "test", "products", ["name"])
        assert "Widget" in result
        assert "Gadget" in result
        assert "price" not in result

    def test_pick_missing_field(self, loaded_store: JSONStore) -> None:
        result = pick_fields(loaded_store, "test", "products", ["nonexistent"])
        assert "3 items" in result

    def test_not_an_array(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError, match="expected an array"):
            pick_fields(loaded_store, "test", "config", ["theme"])

    # --- Edge cases ---

    def test_pick_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = pick_fields(s, "d", "items", ["x"])
        assert "0 items" in result

    def test_pick_empty_fields_list(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"a": 1}, {"b": 2}]})
        result = pick_fields(s, "d", "items", [])
        # Should produce empty projected objects
        assert "2 items" in result

    def test_pick_mixed_array_skips_non_objects(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"name": "a"}, 42, "text", {"name": "b"}]})
        result = pick_fields(s, "d", "items", ["name"])
        assert "a" in result
        assert "b" in result

    def test_pick_sparse_objects(self, store: JSONStore) -> None:
        """Some objects have the field, some don't."""
        s = _load_data(store, {"items": [
            {"name": "A", "age": 10},
            {"name": "B"},
            {"age": 20},
        ]})
        result = pick_fields(s, "d", "items", ["name", "age"])
        assert "A" in result
        assert "B" in result
        assert "10" in result
        assert "20" in result

    def test_pick_nested_field_not_projected(self, store: JSONStore) -> None:
        """pick_fields only looks at top-level keys, not nested."""
        s = _load_data(store, {"items": [{"alpha": {"beta": 1}, "gamma": 2}]})
        result = pick_fields(s, "d", "items", ["alpha"])
        assert "beta" in result  # nested dict is included as part of "alpha" value
        assert "gamma" not in result


# ==================================================================
# GroupBy
# ==================================================================


class TestGroupBy:
    def test_group_by_status(self, loaded_array_store: JSONStore) -> None:
        result = group_by(loaded_array_store, "arr", "", "status")
        assert "3 group(s)" in result
        assert "active: 3" in result
        assert "inactive: 1" in result
        assert "pending: 1" in result

    def test_group_by_in_stock(self, loaded_store: JSONStore) -> None:
        result = group_by(loaded_store, "test", "products", "in_stock")
        assert "2 group(s)" in result

    def test_not_an_array(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError, match="expected an array"):
            group_by(loaded_store, "test", "config", "theme")

    # --- Edge cases ---

    def test_group_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = group_by(s, "d", "items", "cat")
        assert "0 group(s)" in result

    def test_group_missing_field_skipped(self, store: JSONStore) -> None:
        s = _load_data(store, [
            {"cat": "A", "v": 1},
            {"v": 2},              # missing "cat"
            {"cat": "B", "v": 3},
        ])
        result = group_by(s, "d", "", "cat")
        assert "2 group(s)" in result
        assert "1 items skipped" in result

    def test_group_all_missing_field(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": 1}, {"x": 2}])
        result = group_by(s, "d", "", "cat")
        assert "0 group(s)" in result
        assert "2 items skipped" in result

    def test_group_non_dict_items_skipped(self, store: JSONStore) -> None:
        s = _load_data(store, [42, "text", {"cat": "A"}])
        result = group_by(s, "d", "", "cat")
        assert "1 group(s)" in result
        assert "2 items skipped" in result

    def test_group_single_group(self, store: JSONStore) -> None:
        s = _load_data(store, [
            {"cat": "A", "v": 1},
            {"cat": "A", "v": 2},
            {"cat": "A", "v": 3},
        ])
        result = group_by(s, "d", "", "cat")
        assert "1 group(s)" in result
        assert "A: 3 item" in result

    def test_group_by_boolean_field(self, store: JSONStore) -> None:
        s = _load_data(store, [
            {"active": True, "n": "a"},
            {"active": False, "n": "b"},
            {"active": True, "n": "c"},
        ])
        result = group_by(s, "d", "", "active")
        assert "2 group(s)" in result

    def test_group_by_numeric_field(self, store: JSONStore) -> None:
        s = _load_data(store, [{"code": 1}, {"code": 2}, {"code": 1}])
        result = group_by(s, "d", "", "code")
        assert "2 group(s)" in result


# ==================================================================
# SortBy
# ==================================================================


class TestSortBy:
    def test_sort_ascending(self, loaded_store: JSONStore) -> None:
        result = sort_by(loaded_store, "test", "products", "price")
        assert "ascending" in result
        lines = result.split("\n")
        price_positions = [i for i, l in enumerate(lines) if "4.75" in l]
        gadget_positions = [i for i, l in enumerate(lines) if "24.5" in l]
        assert price_positions[0] < gadget_positions[0]

    def test_sort_descending(self, loaded_store: JSONStore) -> None:
        result = sort_by(loaded_store, "test", "products", "price", descending=True)
        assert "descending" in result
        lines = result.split("\n")
        gadget_positions = [i for i, l in enumerate(lines) if "24.5" in l]
        cheap_positions = [i for i, l in enumerate(lines) if "4.75" in l]
        assert gadget_positions[0] < cheap_positions[0]

    def test_sort_by_string(self, loaded_store: JSONStore) -> None:
        result = sort_by(loaded_store, "test", "products", "name")
        assert "ascending" in result

    def test_not_an_array(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError, match="expected an array"):
            sort_by(loaded_store, "test", "config", "theme")

    # --- Edge cases ---

    def test_sort_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = sort_by(s, "d", "items", "x")
        assert "Sorted 0 items" in result

    def test_sort_single_item(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"x": 10}]})
        result = sort_by(s, "d", "items", "x")
        assert "Sorted 1 items" in result

    def test_sort_missing_field_appended(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"x": 3},
            {"y": 1},   # missing x — unsortable
            {"x": 1},
        ]})
        result = sort_by(s, "d", "items", "x")
        assert "1 items without 'x'" in result

    def test_sort_mixed_types_fallback(self, store: JSONStore) -> None:
        """When numeric and string values are mixed, falls back to str comparison."""
        s = _load_data(store, {"items": [
            {"v": "banana"},
            {"v": 42},
            {"v": "apple"},
        ]})
        result = sort_by(s, "d", "items", "v")
        assert "Sorted 3 items" in result

    def test_sort_descending_numbers(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"n": 1}, {"n": 5}, {"n": 3},
        ]})
        result = sort_by(s, "d", "items", "n", descending=True)
        lines = result.split("\n")
        five_pos = next(i for i, l in enumerate(lines) if "5" in l)
        one_pos = next(i for i, l in enumerate(lines) if '"n": 1' in l or "'n': 1" in l)
        assert five_pos < one_pos

    def test_sort_all_items_missing_field(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"a": 1}, {"b": 2}]})
        result = sort_by(s, "d", "items", "x")
        assert "Sorted 0 items" in result
        assert "2 items without 'x'" in result

    def test_sort_non_dict_items_unsortable(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [42, {"x": 1}, "text"]})
        result = sort_by(s, "d", "items", "x")
        assert "Sorted 1 items" in result
        assert "2 items without 'x'" in result


# ==================================================================
# Sample
# ==================================================================


class TestSample:
    def test_sample_default(self, loaded_array_store: JSONStore) -> None:
        result = sample(loaded_array_store, "arr")
        assert "5 item(s) from 5 total" in result

    def test_sample_fewer_than_n(self, loaded_store: JSONStore) -> None:
        result = sample(loaded_store, "test", path="products", n=10)
        assert "3 item(s) from 3 total" in result

    def test_sample_with_seed(self, loaded_array_store: JSONStore) -> None:
        r1 = sample(loaded_array_store, "arr", n=3, seed=42)
        r2 = sample(loaded_array_store, "arr", n=3, seed=42)
        assert r1 == r2

    def test_sample_small_n(self, loaded_array_store: JSONStore) -> None:
        result = sample(loaded_array_store, "arr", n=2, seed=1)
        assert "2 item(s) from 5 total" in result

    def test_not_an_array(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError, match="expected an array"):
            sample(loaded_store, "test", path="config")

    # --- Edge cases ---

    def test_sample_n_equals_length(self, store: JSONStore) -> None:
        s = _load_data(store, [1, 2, 3])
        result = sample(s, "d", n=3, seed=0)
        assert "3 item(s) from 3 total" in result

    def test_sample_n_greater_than_length(self, store: JSONStore) -> None:
        s = _load_data(store, [1, 2])
        result = sample(s, "d", n=100)
        assert "2 item(s) from 2 total" in result

    def test_sample_n_one(self, store: JSONStore) -> None:
        s = _load_data(store, [10, 20, 30])
        result = sample(s, "d", n=1, seed=7)
        assert "1 item(s) from 3 total" in result

    def test_sample_single_item_array(self, store: JSONStore) -> None:
        s = _load_data(store, [99])
        result = sample(s, "d", n=5)
        assert "1 item(s) from 1 total" in result
        assert "99" in result

    def test_sample_different_seeds_differ(self, store: JSONStore) -> None:
        big = list(range(100))
        s = _load_data(store, big)
        r1 = sample(s, "d", n=5, seed=1)
        r2 = sample(s, "d", n=5, seed=999)
        assert r1 != r2

    def test_sample_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, [])
        result = sample(s, "d", n=5)
        assert "0 item(s) from 0 total" in result

    def test_sample_from_object_fails(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": 1})
        with pytest.raises(TypeError, match="expected an array"):
            sample(s, "d")

    def test_sample_from_scalar_fails(self, store: JSONStore) -> None:
        s = _load_data(store, 42)
        with pytest.raises(TypeError, match="expected an array"):
            sample(s, "d")

    def test_sample_n_zero(self, store: JSONStore) -> None:
        s = _load_data(store, [1, 2, 3])
        result = sample(s, "d", n=0)
        assert "0 item(s) from 3 total" in result


class TestFlattenListMixed:
    def test_flatten_list_mixed_dict_and_scalar(self, store: JSONStore) -> None:
        """Dicts in list recurse, non-dicts stored directly."""
        s = _load_data(store, {"items": [{"a": 1}, 2, {"b": 3}]})
        result = flatten(s, "d")
        assert "items[0].a" in result
        assert "items[1]" in result
        assert "items[2].b" in result


class TestSortMixedDescending:
    def test_sort_mixed_types_descending_fallback(self, store: JSONStore) -> None:
        """Mixed string/int triggers fallback to string comparison in descending."""
        s = _load_data(store, {"items": [
            {"val": "b"},
            {"val": 1},
            {"val": "a"},
        ]})
        result = sort_by(s, "d", "items", "val", descending=True)
        assert "descending" in result


class TestPickFieldsRootArray:
    def test_pick_fields_root_array(self, store: JSONStore) -> None:
        """pick_fields on a root array (empty path)."""
        s = _load_data(store, [{"name": "A", "extra": 1}, {"name": "B", "extra": 2}])
        result = pick_fields(s, "d", "", ["name"])
        assert "Projected 2 items" in result
        assert "A" in result
        assert "extra" not in result
