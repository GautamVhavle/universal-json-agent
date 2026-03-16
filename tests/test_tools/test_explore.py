"""Tests for explore tools (get_keys, get_value, get_type, get_structure)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from json_agent.store import JSONStore
from json_agent.tools.explore import get_keys, get_value, get_type, get_structure


# ------------------------------------------------------------------
# Helper to load arbitrary data into a store
# ------------------------------------------------------------------

def _load_data(store: JSONStore, data, alias: str = "d") -> JSONStore:
    """Write data to temp file, load into store, return store."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    store.load(f.name, alias=alias)
    os.unlink(f.name)
    return store


class TestGetKeys:
    def test_root_object_keys(self, loaded_store: JSONStore) -> None:
        result = get_keys(loaded_store, "test")
        assert "7 keys" in result
        assert "name" in result
        assert "products" in result

    def test_nested_object_keys(self, loaded_store: JSONStore) -> None:
        result = get_keys(loaded_store, "test", "config")
        assert "theme" in result
        assert "max_items" in result
        assert "nested" in result

    def test_array_keys(self, loaded_store: JSONStore) -> None:
        result = get_keys(loaded_store, "test", "tags")
        assert "3 items" in result

    def test_scalar_path(self, loaded_store: JSONStore) -> None:
        result = get_keys(loaded_store, "test", "name")
        assert "not an object or array" in result

    def test_unknown_alias(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            get_keys(store, "missing")

    # --- Edge cases ---

    def test_empty_object_keys(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = get_keys(s, "d")
        assert "0 keys" in result

    def test_empty_array_keys(self, store: JSONStore) -> None:
        s = _load_data(store, [])
        result = get_keys(s, "d")
        assert "0 items" in result

    def test_boolean_scalar(self, store: JSONStore) -> None:
        s = _load_data(store, {"flag": True})
        result = get_keys(s, "d", "flag")
        assert "not an object or array" in result

    def test_null_scalar(self, store: JSONStore) -> None:
        s = _load_data(store, {"val": None})
        result = get_keys(s, "d", "val")
        assert "not an object or array" in result

    def test_deeply_nested_keys(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"b": {"c": {"d": 1}}}})
        result = get_keys(s, "d", "a.b.c")
        assert "1 keys" in result
        assert "d" in result

    def test_array_of_arrays_keys(self, store: JSONStore) -> None:
        s = _load_data(store, [[1, 2], [3, 4]])
        result = get_keys(s, "d", "0")
        assert "2 items" in result

    def test_bad_path_raises(self, loaded_store: JSONStore) -> None:
        with pytest.raises(KeyError):
            get_keys(loaded_store, "test", "nonexistent_key")


class TestGetValue:
    def test_root(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test")
        assert "Test Store" in result

    def test_scalar_value(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test", "name")
        assert result == "Test Store"

    def test_nested_value(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test", "config.nested.deep.value")
        assert result == "found_it"

    def test_array_element(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test", "products[0].name")
        assert result == "Widget"

    def test_number_value(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test", "version")
        assert "2" in result

    def test_boolean_value(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test", "active")
        assert "true" in result

    def test_null_value(self, loaded_store: JSONStore) -> None:
        result = get_value(loaded_store, "test", "metadata")
        assert "null" in result

    def test_bad_path(self, loaded_store: JSONStore) -> None:
        with pytest.raises(KeyError):
            get_value(loaded_store, "test", "nonexistent.path")

    # --- Edge cases ---

    def test_empty_object_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"empty": {}})
        result = get_value(s, "d", "empty")
        assert "{}" in result

    def test_empty_array_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = get_value(s, "d", "items")
        assert "[]" in result

    def test_empty_string_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"s": ""})
        result = get_value(s, "d", "s")
        assert result == ""

    def test_zero_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"z": 0})
        result = get_value(s, "d", "z")
        assert "0" in result

    def test_false_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"f": False})
        result = get_value(s, "d", "f")
        assert "false" in result

    def test_large_output_truncated(self, store: JSONStore) -> None:
        big = {"data": list(range(5000))}
        s = _load_data(store, big)
        result = get_value(s, "d", "data")
        assert "truncated" in result

    def test_unicode_value(self, store: JSONStore) -> None:
        s = _load_data(store, {"text": "日本語テスト 🎯"})
        result = get_value(s, "d", "text")
        assert "日本語テスト" in result
        assert "🎯" in result

    def test_index_out_of_range(self, loaded_store: JSONStore) -> None:
        with pytest.raises(IndexError):
            get_value(loaded_store, "test", "products[99]")

    def test_traverse_into_string_raises(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError):
            get_value(loaded_store, "test", "name.length")


class TestGetType:
    def test_object(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test")
        assert "object" in result
        assert "7 keys" in result

    def test_array(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test", "products")
        assert "array" in result
        assert "3 items" in result

    def test_string(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test", "name")
        assert result == "string"

    def test_number(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test", "version")
        assert result == "number"

    def test_boolean(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test", "active")
        assert result == "boolean"

    def test_null(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test", "metadata")
        assert result == "null"

    # --- Edge cases ---

    def test_empty_object_type(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = get_type(s, "d")
        assert "object (0 keys)" == result

    def test_empty_array_type(self, store: JSONStore) -> None:
        s = _load_data(store, [])
        result = get_type(s, "d")
        assert "array (0 items)" == result

    def test_float_type(self, store: JSONStore) -> None:
        s = _load_data(store, {"pi": 3.14})
        result = get_type(s, "d", "pi")
        assert result == "number"

    def test_nested_array_type(self, loaded_store: JSONStore) -> None:
        result = get_type(loaded_store, "test", "products[0]")
        assert "object" in result

    def test_scalar_root_type(self, store: JSONStore) -> None:
        s = _load_data(store, 42)
        result = get_type(s, "d")
        assert result == "number"


class TestGetStructure:
    def test_basic_structure(self, loaded_store: JSONStore) -> None:
        result = get_structure(loaded_store, "test")
        assert "object" in result
        assert "name:" in result
        assert "string" in result

    def test_shows_nested_types(self, loaded_store: JSONStore) -> None:
        result = get_structure(loaded_store, "test")
        assert "products:" in result
        assert "array" in result
        assert "config:" in result

    def test_depth_limit(self, loaded_store: JSONStore) -> None:
        result = get_structure(loaded_store, "test", max_depth=1)
        assert "depth limit reached" in result

    def test_sub_path(self, loaded_store: JSONStore) -> None:
        result = get_structure(loaded_store, "test", path="config")
        assert "theme:" in result
        assert "string" in result

    def test_array_structure(self, loaded_array_store: JSONStore) -> None:
        result = get_structure(loaded_array_store, "arr")
        assert "array" in result
        assert "5 items" in result

    # --- Edge cases ---

    def test_empty_object_structure(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = get_structure(s, "d")
        assert "object (0 keys)" in result

    def test_empty_array_structure(self, store: JSONStore) -> None:
        s = _load_data(store, [])
        result = get_structure(s, "d")
        assert "array (0 items)" in result

    def test_depth_zero(self, loaded_store: JSONStore) -> None:
        result = get_structure(loaded_store, "test", max_depth=0)
        assert "depth limit reached" in result

    def test_scalar_root_structure(self, store: JSONStore) -> None:
        s = _load_data(store, "just a string")
        result = get_structure(s, "d")
        assert "string" in result

    def test_deeply_nested_structure(self, store: JSONStore) -> None:
        deep = {"a": {"b": {"c": {"d": {"e": "leaf"}}}}}
        s = _load_data(store, deep)
        result = get_structure(s, "d", max_depth=10)
        assert "leaf" not in result  # leaf value shouldn't appear, only types
        assert "string" in result

    def test_array_of_different_types_structure(self, store: JSONStore) -> None:
        s = _load_data(store, [1, "two", True, None])
        result = get_structure(s, "d")
        assert "array (4 items)" in result
        # Shows first element's type
        assert "number" in result

    def test_single_item_array_no_more_indicator(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": 1}])
        result = get_structure(s, "d")
        assert "more items" not in result

    def test_two_item_array_shows_more_indicator(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": 1}, {"x": 2}])
        result = get_structure(s, "d")
        assert "1 more items" in result

    # --- Additional edge cases ---

    def test_get_keys_single_element_array(self, store: JSONStore) -> None:
        """Single-element array should report 'indices 0..0'."""
        s = _load_data(store, [42])
        result = get_keys(s, "d")
        assert "indices 0..0" in result

    def test_get_keys_integer_scalar(self, store: JSONStore) -> None:
        """get_keys at an integer path returns 'not an object or array'."""
        s = _load_data(store, {"val": 99})
        result = get_keys(s, "d", path="val")
        assert "not an object or array" in result

    def test_structure_list_at_depth_limit(self, store: JSONStore) -> None:
        """A list at exactly max_depth should show header but no children."""
        s = _load_data(store, {"a": [1, 2, 3]})
        result = get_structure(s, "d", max_depth=1)
        # At depth=1 the array is encountered, depth >= max_depth so items not expanded
        assert "array (3 items)" in result
        assert "[0]" not in result

    def test_structure_multiline_dict_child(self, store: JSONStore) -> None:
        """Nested dict under a key should format with 'key:' on its own line."""
        s = _load_data(store, {"outer": {"inner": {"leaf": "val"}}})
        result = get_structure(s, "d", max_depth=5)
        assert "outer:" in result
        assert "inner:" in result
        assert "string" in result
