"""Edge-case tests for the truncation utility."""

from __future__ import annotations

from universal_json_agent_mcp.utils.truncation import truncate_value, truncate_list, _serialize


class TestTruncateValue:
    def test_short_string_unchanged(self) -> None:
        assert truncate_value("hello") == "hello"

    def test_short_dict_unchanged(self) -> None:
        result = truncate_value({"a": 1})
        assert '"a": 1' in result

    def test_long_string_truncated(self) -> None:
        big = "x" * 20_000
        result = truncate_value(big, max_chars=100)
        assert len(result) < 200
        assert "truncated" in result

    def test_long_dict_truncated(self) -> None:
        big = {f"key_{i}": f"value_{i}" for i in range(1000)}
        result = truncate_value(big, max_chars=500)
        assert "truncated" in result

    def test_none_value(self) -> None:
        assert truncate_value(None) == "null"

    def test_boolean_true(self) -> None:
        assert truncate_value(True) == "true"

    def test_boolean_false(self) -> None:
        assert truncate_value(False) == "false"

    def test_integer(self) -> None:
        assert truncate_value(42) == "42"

    def test_float(self) -> None:
        result = truncate_value(3.14)
        assert "3.14" in result

    def test_empty_dict(self) -> None:
        assert truncate_value({}) == "{}"

    def test_empty_list(self) -> None:
        assert truncate_value([]) == "[]"

    def test_nested_structures(self) -> None:
        data = {"a": [1, {"b": [2, 3]}]}
        result = truncate_value(data)
        assert "a" in result
        assert "b" in result

    def test_unicode_preserved(self) -> None:
        result = truncate_value({"greet": "こんにちは 🎉"})
        assert "こんにちは" in result
        assert "🎉" in result

    def test_exact_max_chars_not_truncated(self) -> None:
        text = "x" * 100
        result = truncate_value(text, max_chars=100)
        assert "truncated" not in result

    def test_one_over_max_is_truncated(self) -> None:
        text = "x" * 101
        result = truncate_value(text, max_chars=100)
        assert "truncated" in result


class TestTruncateList:
    def test_small_list_intact(self) -> None:
        result = truncate_list([1, 2, 3])
        assert "1" in result and "3" in result

    def test_large_list_sliced(self) -> None:
        big = list(range(200))
        result = truncate_list(big, max_items=10)
        assert "showing 10 of 200" in result

    def test_empty_list(self) -> None:
        result = truncate_list([])
        assert result == "[]"

    def test_max_items_equals_length(self) -> None:
        items = [1, 2, 3]
        result = truncate_list(items, max_items=3)
        assert "showing" not in result

    def test_max_items_one(self) -> None:
        items = [{"a": 1}, {"b": 2}, {"c": 3}]
        result = truncate_list(items, max_items=1)
        assert "showing 1 of 3" in result

    def test_char_limit_applied_after_item_limit(self) -> None:
        big = [{"key": "v" * 500} for _ in range(100)]
        result = truncate_list(big, max_items=5, max_chars=200)
        assert "truncated" in result


class TestSerialize:
    def test_string_passthrough(self) -> None:
        assert _serialize("hello") == "hello"

    def test_dict_to_json(self) -> None:
        result = _serialize({"a": 1})
        assert '"a"' in result

    def test_non_serializable_falls_back(self) -> None:
        """Objects that can't be JSON serialized use str() via default=str."""
        result = _serialize({"s": set()})
        # set() is handled by default=str
        assert "set()" in result


class TestTruncateListBoundary:
    def test_truncate_list_boundary_one_over(self) -> None:
        """Exactly max_items + 1 items triggers truncation message."""
        items = [1, 2, 3, 4]
        result = truncate_list(items, max_items=3)
        assert "showing 3 of 4" in result.lower() or "Showing" in result
