"""Tests for query tools (jsonpath_query, filter_objects, search_text)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools.query import jsonpath_query, filter_objects, search_text


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


class TestJsonpathQuery:
    def test_simple_field(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.name")
        assert "Test Store" in result

    def test_wildcard_array(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.products[*].name")
        assert "Widget" in result
        assert "Gadget" in result
        assert "Doohickey" in result

    def test_nested_path(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.config.theme")
        assert "dark" in result

    def test_array_index(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.tags[0]")
        assert "alpha" in result

    def test_no_matches(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.nonexistent")
        assert "No matches" in result

    def test_invalid_expression(self, loaded_store: JSONStore) -> None:
        with pytest.raises(ValueError, match="Invalid JSONPath"):
            jsonpath_query(loaded_store, "test", "$$$$[invalid")

    def test_unknown_alias(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            jsonpath_query(store, "missing", "$.foo")

    # --- Edge cases ---

    def test_root_query(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$")
        assert "Test Store" in result  # Root object serialized

    def test_deep_recursive(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.config.nested.deep.value")
        assert "found_it" in result

    def test_all_array_elements(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.tags[*]")
        assert "alpha" in result
        assert "beta" in result
        assert "gamma" in result

    def test_single_result_not_wrapped_in_list(self, loaded_store: JSONStore) -> None:
        """When there's exactly one match, it should be returned directly, not as a list."""
        result = jsonpath_query(loaded_store, "test", "$.version")
        assert result.strip() == "2"

    def test_boolean_values(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.products[*].in_stock")
        assert "true" in result
        assert "false" in result

    def test_numeric_values(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.products[*].price")
        assert "9.99" in result
        assert "24.5" in result

    def test_query_on_array_root(self, store: JSONStore) -> None:
        s = _load_data(store, [{"a": 1}, {"a": 2}, {"a": 3}])
        result = jsonpath_query(s, "d", "$[*].a")
        assert "1" in result and "2" in result and "3" in result

    def test_empty_array_query(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = jsonpath_query(s, "d", "$.items[*].name")
        assert "No matches" in result

    def test_query_returns_objects(self, loaded_store: JSONStore) -> None:
        result = jsonpath_query(loaded_store, "test", "$.products[0]")
        assert "Widget" in result
        assert "9.99" in result


class TestFilterObjects:
    def test_eq(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "name", "eq", "Widget")
        assert "1 of 3" in result
        assert "Widget" in result

    def test_gt(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "price", "gt", 10)
        assert "1 of 3" in result
        assert "Gadget" in result

    def test_lt(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "price", "lt", 10)
        assert "2 of 3" in result

    def test_gte(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "price", "gte", 9.99)
        assert "2 of 3" in result

    def test_lte(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "price", "lte", 4.75)
        assert "1 of 3" in result

    def test_neq(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "in_stock", "neq", True)
        assert "1 of 3" in result

    def test_contains(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "name", "contains", "idge")
        assert "Widget" in result

    def test_regex(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "name", "regex", "^G")
        assert "Gadget" in result

    def test_no_matches(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "price", "gt", 1000)
        assert "0 of 3" in result

    def test_invalid_operator(self, loaded_store: JSONStore) -> None:
        with pytest.raises(ValueError, match="Unknown operator"):
            filter_objects(loaded_store, "test", "products", "price", "nope", 10)

    def test_not_an_array(self, loaded_store: JSONStore) -> None:
        with pytest.raises(TypeError, match="expected an array"):
            filter_objects(loaded_store, "test", "config", "theme", "eq", "dark")

    # --- Edge cases ---

    def test_filter_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": []})
        result = filter_objects(s, "d", "items", "id", "eq", 1)
        assert "0 of 0" in result

    def test_filter_mixed_array_skips_non_dicts(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [{"id": 1}, "not_a_dict", 42, None, {"id": 2}]})
        result = filter_objects(s, "d", "items", "id", "eq", 1)
        assert "1 of 5" in result

    def test_filter_on_missing_field_skips(self, store: JSONStore) -> None:
        """Objects missing the filter field are silently skipped."""
        s = _load_data(store, {"items": [
            {"id": 1, "name": "A"},
            {"id": 2},  # no "name"
            {"id": 3, "name": "C"},
        ]})
        result = filter_objects(s, "d", "items", "name", "eq", "A")
        assert "1 of 3" in result

    def test_eq_with_null(self, store: JSONStore) -> None:
        s = _load_data(store, {"items": [
            {"id": 1, "val": None},
            {"id": 2, "val": "x"},
        ]})
        result = filter_objects(s, "d", "items", "val", "eq", None)
        assert "1 of 2" in result

    def test_eq_with_boolean(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "in_stock", "eq", True)
        assert "2 of 3" in result

    def test_contains_case_sensitive(self, loaded_store: JSONStore) -> None:
        # "contains" is case-sensitive in our implementation
        result = filter_objects(loaded_store, "test", "products", "name", "contains", "WIDGET")
        assert "0 of 3" in result

    def test_regex_complex_pattern(self, loaded_store: JSONStore) -> None:
        result = filter_objects(loaded_store, "test", "products", "name", "regex", "^(Widget|Gadget)$")
        assert "2 of 3" in result

    def test_gt_with_type_mismatch_skips(self, store: JSONStore) -> None:
        """If field is string and value is int, comparison should skip gracefully."""
        s = _load_data(store, {"items": [
            {"id": 1, "val": "text"},
            {"id": 2, "val": 100},
        ]})
        result = filter_objects(s, "d", "items", "val", "gt", 50)
        assert "1 of 2" in result

    def test_filter_on_root_array(self, store: JSONStore) -> None:
        s = _load_data(store, [{"x": 1}, {"x": 2}, {"x": 3}])
        result = filter_objects(s, "d", "", "x", "gt", 1)
        assert "2 of 3" in result


class TestSearchText:
    def test_simple_search(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", "Widget")
        assert "1 match" in result
        assert "Widget" in result

    def test_case_insensitive(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", "widget", case_sensitive=False)
        assert "1 match" in result

    def test_case_sensitive_miss(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", "widget", case_sensitive=True)
        assert "No matches" in result

    def test_regex_pattern(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", r"^[a-z]+$")
        assert "match" in result.lower()

    def test_scoped_search(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", "dark", path="config")
        assert "1 match" in result

    def test_no_matches(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", "ZZZZNONEXISTENT")
        assert "No matches" in result

    def test_invalid_regex(self, loaded_store: JSONStore) -> None:
        with pytest.raises(ValueError, match="Invalid regex"):
            search_text(loaded_store, "test", "[invalid(")

    def test_deep_nested_search(self, loaded_store: JSONStore) -> None:
        result = search_text(loaded_store, "test", "found_it")
        assert "found_it" in result
        assert "nested" in result or "deep" in result

    # --- Edge cases ---

    def test_empty_pattern_matches_all_strings(self, loaded_store: JSONStore) -> None:
        """An empty regex matches every string."""
        result = search_text(loaded_store, "test", "")
        assert "match" in result.lower()

    def test_search_in_empty_object(self, store: JSONStore) -> None:
        s = _load_data(store, {})
        result = search_text(s, "d", "anything")
        assert "No matches" in result

    def test_search_in_empty_array(self, store: JSONStore) -> None:
        s = _load_data(store, [])
        result = search_text(s, "d", "anything")
        assert "No matches" in result

    def test_search_unicode(self, store: JSONStore) -> None:
        s = _load_data(store, {"text": "こんにちは世界"})
        result = search_text(s, "d", "こんにちは")
        assert "1 match" in result

    def test_search_with_special_regex_chars(self, loaded_store: JSONStore) -> None:
        """Dot in regex should match any character."""
        result = search_text(loaded_store, "test", "W.dget")
        assert "Widget" in result

    def test_search_literal_dot(self, store: JSONStore) -> None:
        """Escaped dot should match literal dots only."""
        s = _load_data(store, {"url": "www.example.com", "name": "wxyzexamplezcom"})
        result = search_text(s, "d", r"www\.example\.com")
        assert "1 match" in result

    def test_search_across_array_elements(self, store: JSONStore) -> None:
        s = _load_data(store, {"users": [
            {"name": "Alice Smith"},
            {"name": "Bob Jones"},
            {"name": "Alice Cooper"},
        ]})
        result = search_text(s, "d", "Alice")
        assert "2 match" in result

    def test_search_does_not_match_numbers(self, store: JSONStore) -> None:
        """search_text only searches string values, not numbers."""
        s = _load_data(store, {"id": 42, "name": "42nd street"})
        result = search_text(s, "d", "42")
        # Should find the string "42nd street" but not the number 42
        assert "1 match" in result

    def test_search_capped_at_100(self, store: JSONStore) -> None:
        """When there are >100 matches, results are capped."""
        items = [{"text": f"match_{i}"} for i in range(150)]
        s = _load_data(store, {"items": items})
        result = search_text(s, "d", "match_")
        assert "capped at 100" in result

    def test_search_case_sensitive_true(self, store: JSONStore) -> None:
        s = _load_data(store, {"a": "Hello", "b": "hello", "c": "HELLO"})
        result = search_text(s, "d", "Hello", case_sensitive=True)
        assert "1 match" in result

    def test_filter_regex_invalid_pattern_skips(self, store: JSONStore) -> None:
        """Invalid regex in value silently skips items via re.error catch."""
        s = _load_data(store, {"items": [
            {"code": "ABC"},
            {"code": "DEF"},
        ]})
        # The comparison lambda catches re.error from invalid regex
        result = filter_objects(s, "d", "items", "code", "regex", "[invalid(")
        assert "0 of 2" in result

    def test_filter_contains_non_string_field_skips(self, store: JSONStore) -> None:
        """'contains' on a non-string field returns False (no crash)."""
        s = _load_data(store, {"items": [
            {"val": 42},
            {"val": "hello world"},
        ]})
        result = filter_objects(s, "d", "items", "val", "contains", "hello")
        assert "1 of 2" in result

    def test_filter_regex_non_string_field_skips(self, store: JSONStore) -> None:
        """'regex' on a non-string field returns False (no crash)."""
        s = _load_data(store, {"items": [
            {"val": 123},
            {"val": "abc-123"},
        ]})
        result = filter_objects(s, "d", "items", "val", "regex", "abc")
        assert "1 of 2" in result

    def test_search_text_skips_booleans(self, store: JSONStore) -> None:
        """Boolean values should not be matched by search_text."""
        s = _load_data(store, {"flag": True, "name": "True"})
        result = search_text(s, "d", "True")
        # Only the string "True" should match, not the boolean True
        assert "1 match" in result

    def test_search_text_skips_null(self, store: JSONStore) -> None:
        """None/null values should not be matched by search_text."""
        s = _load_data(store, {"val": None, "text": "null"})
        result = search_text(s, "d", "null")
        assert "1 match" in result

    def test_search_text_path_prefix_in_results(self, store: JSONStore) -> None:
        """When path is provided, matching paths should include the prefix."""
        s = _load_data(store, {"config": {"theme": "dark"}})
        result = search_text(s, "d", "dark", path="config")
        assert "config" in result
        assert "theme" in result
