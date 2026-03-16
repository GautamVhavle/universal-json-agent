"""Tests for introspection tools (distinct_paths)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools.introspect import distinct_paths


def _load_data(store: JSONStore, data, alias: str = "d") -> JSONStore:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    store.load(f.name, alias=alias)
    os.unlink(f.name)
    return store


class TestDistinctPaths:
    def test_flat_object(self, store: JSONStore) -> None:
        s = _load_data(store, {"name": "test", "count": 42, "flag": True})
        result = distinct_paths(s, "d")
        assert "$.name" in result
        assert "$.count" in result
        assert "$.flag" in result
        assert "string" in result
        assert "integer" in result
        assert "boolean" in result

    def test_nested_object(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"b": {"c": "deep"}}})
        result = distinct_paths(s, "d")
        assert "$.a.b.c" in result
        assert "string" in result

    def test_array_of_objects(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"name": "A", "val": 1},
            {"name": "B", "val": 2},
        ]})
        result = distinct_paths(s, "d")
        assert "$.items[*].name" in result
        assert "$.items[*].val" in result

    def test_empty_object(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = distinct_paths(s, "d")
        assert "no nested paths" in result.lower() or "0 unique" in result.lower() \
            or "Single" in result or "object (empty)" in result

    def test_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = distinct_paths(s, "d")
        assert "empty" in result.lower()

    def test_scalar_root(self, store: JSONStore) -> None:
        s = _load_data(store, "hello")
        result = distinct_paths(s, "d")
        assert "string" in result

    def test_null_values(self, store: JSONStore) -> None:
        s = _load_data(store, {"key": None})
        result = distinct_paths(s, "d")
        assert "null" in result

    def test_max_depth_limits(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": {"b": {"c": {"d": {"e": "deep"}}}}})
        result = distinct_paths(s, "d", max_depth=2)
        assert "max depth" in result.lower()

    def test_path_parameter(self, store: JSONStore) -> None:
        s = _load_data(store, {"data": {"items": [{"x": 1}]}})
        result = distinct_paths(s, "d", path="data")
        assert "data.items[*].x" in result

    def test_mixed_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"name": "A"},
            42,
            "text",
        ]})
        result = distinct_paths(s, "d")
        # Should discover paths from the dict item
        assert "$.items[*].name" in result or "$.items[*]" in result

    def test_complex_structure(self, store: JSONStore) -> None:
        """Test with a realistic nested structure."""
        s = _load_data(store, {
            "users": [
                {
                    "name": "Alice",
                    "address": {"city": "NYC", "zip": "10001"},
                    "tags": ["admin", "user"],
                },
            ],
            "meta": {"version": 1},
        })
        result = distinct_paths(s, "d")
        assert "$.users[*].name" in result
        assert "$.users[*].address.city" in result
        assert "$.meta.version" in result

    def test_sample_array_items_parameter(self, store: JSONStore) -> None:
        """Only first N items should be sampled."""
        items = [{"x": i} for i in range(100)]
        s = _load_data(store, {"items": items})
        # Even with 100 items, should discover $.items[*].x
        result = distinct_paths(s, "d", sample_array_items=2)
        assert "$.items[*].x" in result

    def test_unknown_alias(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            distinct_paths(store, "missing")

    def test_nested_arrays(self, store: JSONStore) -> None:
        """Array of arrays: discovers $.matrix[*][*] as integer."""
        s = _load_data(store, {"matrix": [[1, 2], [3, 4]]})
        result = distinct_paths(s, "d")
        assert "$.matrix[*][*]" in result
        assert "integer" in result

    def test_nested_empty_dict(self, store: JSONStore) -> None:
        """Nested empty dict is reported as 'object (empty)'."""
        s = _load_data(store, {"outer": {"inner": {}}})
        result = distinct_paths(s, "d")
        assert "object (empty)" in result

    def test_nested_empty_array(self, store: JSONStore) -> None:
        """Nested empty array is reported as 'array (empty)'."""
        s = _load_data(store, {"outer": {"items": []}})
        result = distinct_paths(s, "d")
        assert "array (empty)" in result

    def test_float_type(self, store: JSONStore) -> None:
        """Float values should be typed as 'number'."""
        s = _load_data(store, {"pi": 3.14})
        result = distinct_paths(s, "d")
        assert "$.pi" in result
        assert "number" in result

    def test_boolean_root(self, store: JSONStore) -> None:
        """Boolean root should report 'Single boolean value'."""
        s = _load_data(store, True)
        result = distinct_paths(s, "d")
        assert "boolean" in result

    def test_integer_root(self, store: JSONStore) -> None:
        s = _load_data(store, 42)
        result = distinct_paths(s, "d")
        assert "integer" in result

    def test_null_root(self, store: JSONStore) -> None:
        s = _load_data(store, None)
        result = distinct_paths(s, "d")
        assert "null" in result
