"""Edge-case tests for the path_resolver utility."""

from __future__ import annotations

import pytest

from universal_json_agent_mcp.utils.path_resolver import resolve_path, _tokenize


class TestResolvePathBasic:
    """Basic resolution that wasn't covered before."""

    def test_root_empty_string(self) -> None:
        data = {"a": 1}
        assert resolve_path(data, "") is data

    def test_root_dot(self) -> None:
        data = [1, 2, 3]
        assert resolve_path(data, ".") is data

    def test_single_key(self) -> None:
        assert resolve_path({"x": 42}, "x") == 42

    def test_single_index(self) -> None:
        assert resolve_path([10, 20, 30], "1") == 20

    def test_bracket_index(self) -> None:
        assert resolve_path([10, 20, 30], "[2]") == 30


class TestResolvePathEdgeCases:
    """Edge cases and error paths for resolve_path."""

    def test_key_not_found_shows_available_keys(self) -> None:
        with pytest.raises(KeyError, match="Available keys"):
            resolve_path({"a": 1, "b": 2}, "c")

    def test_index_out_of_range(self) -> None:
        with pytest.raises(IndexError, match="out of range"):
            resolve_path([1, 2, 3], "10")

    def test_negative_index_rejected(self) -> None:
        """We explicitly disallow negative indices for safety."""
        with pytest.raises(IndexError, match="out of range"):
            resolve_path([1, 2, 3], "-1")

    def test_traverse_into_scalar_string(self) -> None:
        with pytest.raises(TypeError, match="Cannot traverse"):
            resolve_path({"name": "Alice"}, "name.length")

    def test_traverse_into_scalar_number(self) -> None:
        with pytest.raises(TypeError, match="Cannot traverse"):
            resolve_path({"val": 42}, "val.something")

    def test_traverse_into_null(self) -> None:
        with pytest.raises(TypeError, match="Cannot traverse"):
            resolve_path({"val": None}, "val.something")

    def test_traverse_into_bool(self) -> None:
        with pytest.raises(TypeError, match="Cannot traverse"):
            resolve_path({"flag": True}, "flag.x")

    def test_non_integer_key_on_array(self) -> None:
        with pytest.raises(TypeError, match="non-integer"):
            resolve_path([1, 2, 3], "name")

    def test_deeply_nested_path(self) -> None:
        obj = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        assert resolve_path(obj, "a.b.c.d.e") == "deep"

    def test_mixed_bracket_and_dot(self) -> None:
        data = {"items": [{"name": "x"}, {"name": "y"}]}
        assert resolve_path(data, "items[1].name") == "y"

    def test_multiple_brackets(self) -> None:
        data = [[10, 20], [30, 40]]
        assert resolve_path(data, "[1][0]") == 30

    def test_empty_dict(self) -> None:
        with pytest.raises(KeyError):
            resolve_path({}, "anything")

    def test_empty_list_index(self) -> None:
        with pytest.raises(IndexError, match="out of range"):
            resolve_path([], "0")

    def test_scalar_root_with_empty_path(self) -> None:
        assert resolve_path("hello", "") == "hello"
        assert resolve_path(42, "") == 42
        assert resolve_path(None, "") is None
        assert resolve_path(True, ".") is True

    def test_path_with_leading_trailing_dots(self) -> None:
        """Leading/trailing dots should be stripped gracefully."""
        data = {"a": {"b": 1}}
        assert resolve_path(data, ".a.b.") == 1

    def test_key_that_looks_like_number(self) -> None:
        """Dict keys that are numeric strings should still be resolved as keys."""
        data = {"0": "zero", "1": "one"}
        assert resolve_path(data, "0") == "zero"


class TestTokenize:
    """Tests for the internal _tokenize function."""

    def test_simple_dot(self) -> None:
        assert _tokenize("a.b.c") == ["a", "b", "c"]

    def test_bracket_notation(self) -> None:
        assert _tokenize("items[0].name") == ["items", "0", "name"]

    def test_multiple_brackets(self) -> None:
        assert _tokenize("[0][1][2]") == ["0", "1", "2"]

    def test_leading_dot(self) -> None:
        assert _tokenize(".a.b") == ["a", "b"]

    def test_trailing_dot(self) -> None:
        assert _tokenize("a.b.") == ["a", "b"]

    def test_empty_string(self) -> None:
        assert _tokenize("") == []

    def test_single_segment(self) -> None:
        assert _tokenize("root") == ["root"]

    def test_consecutive_dots_produce_no_empties(self) -> None:
        assert _tokenize("a..b") == ["a", "b"]
