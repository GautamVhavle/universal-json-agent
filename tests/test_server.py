"""
Server integration tests — verify MCP tool wrappers catch exceptions
and return 'Error: ...' strings instead of propagating exceptions.

These tests exercise the thin wrappers in server.py to confirm they
correctly delegate to the underlying tool functions and handle errors
gracefully so the MCP protocol layer never crashes.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from json_agent import server


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_store():
    """Reset the shared server store before each test."""
    server.store._documents.clear()
    yield
    server.store._documents.clear()


def _write_json(data) -> str:
    """Write data to a temp JSON file and return the path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    json.dump(data, f)
    f.close()
    return f.name


# ==================================================================
# Load Tools
# ==================================================================


class TestServerLoadTools:
    def test_load_json_success(self) -> None:
        path = _write_json({"a": 1})
        result = server.load_json(path, alias="doc")
        os.unlink(path)
        assert "doc" in result
        assert "Error" not in result

    def test_load_json_file_not_found(self) -> None:
        result = server.load_json("/nonexistent/path.json")
        assert result.startswith("Error:")

    def test_load_json_invalid_json(self) -> None:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        f.write("{bad json")
        f.close()
        result = server.load_json(f.name)
        os.unlink(f.name)
        assert result.startswith("Error:")

    def test_list_loaded_empty(self) -> None:
        result = server.list_loaded()
        assert "No documents" in result

    def test_list_loaded_with_doc(self) -> None:
        path = _write_json([1, 2])
        server.load_json(path, alias="x")
        os.unlink(path)
        result = server.list_loaded()
        assert "x" in result

    def test_unload_json_success(self) -> None:
        path = _write_json({"a": 1})
        server.load_json(path, alias="gone")
        os.unlink(path)
        result = server.unload_json("gone")
        assert "Error" not in result

    def test_unload_json_missing_alias(self) -> None:
        result = server.unload_json("nope")
        assert result.startswith("Error:")


# ==================================================================
# Explore Tools
# ==================================================================


class TestServerExploreTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({"name": "test", "items": [1, 2]})
        server.load_json(path, alias="e")
        os.unlink(path)

    def test_get_keys_success(self) -> None:
        result = server.get_keys("e")
        assert "name" in result

    def test_get_keys_bad_alias(self) -> None:
        result = server.get_keys("missing")
        assert result.startswith("Error:")

    def test_get_value_success(self) -> None:
        result = server.get_value("e", "name")
        assert "test" in result

    def test_get_value_bad_path(self) -> None:
        result = server.get_value("e", "nonexistent")
        assert result.startswith("Error:")

    def test_get_type_success(self) -> None:
        result = server.get_type("e")
        assert "object" in result

    def test_get_type_bad_alias(self) -> None:
        result = server.get_type("missing")
        assert result.startswith("Error:")

    def test_get_structure_success(self) -> None:
        result = server.get_structure("e")
        assert "name" in result

    def test_get_structure_bad_alias(self) -> None:
        result = server.get_structure("missing")
        assert result.startswith("Error:")


# ==================================================================
# Query Tools
# ==================================================================


class TestServerQueryTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({
            "items": [
                {"name": "A", "val": 1},
                {"name": "B", "val": 2},
            ]
        })
        server.load_json(path, alias="q")
        os.unlink(path)

    def test_jsonpath_query_success(self) -> None:
        result = server.jsonpath_query("q", "$.items[*].name")
        assert "A" in result

    def test_jsonpath_query_bad_alias(self) -> None:
        result = server.jsonpath_query("missing", "$.x")
        assert result.startswith("Error:")

    def test_jsonpath_query_invalid_expr(self) -> None:
        result = server.jsonpath_query("q", "$$$$bad")
        assert result.startswith("Error:")

    def test_filter_objects_success(self) -> None:
        result = server.filter_objects("q", "items", "val", "gt", 1)
        assert "B" in result

    def test_filter_objects_bad_alias(self) -> None:
        result = server.filter_objects("missing", "items", "val", "eq", 1)
        assert result.startswith("Error:")

    def test_search_text_success(self) -> None:
        result = server.search_text("q", "A")
        assert "A" in result

    def test_search_text_bad_alias(self) -> None:
        result = server.search_text("missing", "hello")
        assert result.startswith("Error:")


# ==================================================================
# Aggregate Tools
# ==================================================================


class TestServerAggregateTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({"vals": [10, 20, 30]})
        server.load_json(path, alias="a")
        os.unlink(path)

    def test_count_success(self) -> None:
        result = server.count("a", "vals")
        assert "3 items" in result

    def test_count_bad_alias(self) -> None:
        result = server.count("missing")
        assert result.startswith("Error:")

    def test_sum_values_success(self) -> None:
        result = server.sum_values("a", "$.vals[*]")
        assert "60" in result

    def test_sum_values_bad_alias(self) -> None:
        result = server.sum_values("missing", "$.x")
        assert result.startswith("Error:")

    def test_min_max_success(self) -> None:
        result = server.min_max("a", "$.vals[*]")
        assert "10" in result
        assert "30" in result

    def test_unique_values_success(self) -> None:
        result = server.unique_values("a", "$.vals[*]")
        assert "3 unique" in result

    def test_value_counts_success(self) -> None:
        result = server.value_counts("a", "$.vals[*]")
        assert "3 unique" in result


# ==================================================================
# Transform Tools
# ==================================================================


class TestServerTransformTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({
            "nested": {"a": {"b": 1}},
            "items": [
                {"cat": "X", "val": 3},
                {"cat": "Y", "val": 1},
                {"cat": "X", "val": 2},
            ],
        })
        server.load_json(path, alias="t")
        os.unlink(path)

    def test_flatten_success(self) -> None:
        result = server.flatten("t", path="nested")
        assert "a.b" in result

    def test_flatten_bad_alias(self) -> None:
        result = server.flatten("missing")
        assert result.startswith("Error:")

    def test_flatten_not_object(self) -> None:
        result = server.flatten("t", path="items")
        assert result.startswith("Error:")

    def test_pick_fields_success(self) -> None:
        result = server.pick_fields("t", "items", ["cat"])
        assert "X" in result

    def test_pick_fields_bad_alias(self) -> None:
        result = server.pick_fields("missing", "items", ["cat"])
        assert result.startswith("Error:")

    def test_group_by_success(self) -> None:
        result = server.group_by("t", "items", "cat")
        assert "2 group(s)" in result

    def test_group_by_bad_alias(self) -> None:
        result = server.group_by("missing", "items", "cat")
        assert result.startswith("Error:")

    def test_sort_by_success(self) -> None:
        result = server.sort_by("t", "items", "val")
        assert "ascending" in result

    def test_sort_by_bad_alias(self) -> None:
        result = server.sort_by("missing", "items", "val")
        assert result.startswith("Error:")

    def test_sample_success(self) -> None:
        result = server.sample("t", path="items", n=2, seed=0)
        assert "2 item(s) from 3 total" in result

    def test_sample_bad_alias(self) -> None:
        result = server.sample("missing")
        assert result.startswith("Error:")


# ==================================================================
# Stats Tools (Phase 4)
# ==================================================================


class TestServerStatsTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({"vals": [10, 20, 30, 40, 50]})
        server.load_json(path, alias="st")
        os.unlink(path)

    def test_describe_success(self) -> None:
        result = server.describe("st", "$.vals[*]")
        assert "Count  : 5" in result
        assert "Error" not in result

    def test_describe_bad_alias(self) -> None:
        result = server.describe("missing", "$.vals[*]")
        assert result.startswith("Error:")

    def test_describe_invalid_expression(self) -> None:
        result = server.describe("st", "$$$$bad")
        assert result.startswith("Error:")


# ==================================================================
# Advanced Query Tools (Phase 4)
# ==================================================================


class TestServerAdvancedQueryTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({
            "items": [
                {"name": "A", "val": 10},
                {"name": "B", "val": 20},
                {"name": "C", "val": 30},
            ]
        })
        server.load_json(path, alias="aq")
        os.unlink(path)

    def test_multi_filter_success(self) -> None:
        result = server.multi_filter(
            "aq", "items",
            [{"field": "val", "operator": "gt", "value": 15}],
        )
        assert "Matched 2 of 3" in result
        assert "Error" not in result

    def test_multi_filter_bad_alias(self) -> None:
        result = server.multi_filter(
            "missing", "items",
            [{"field": "val", "operator": "eq", "value": 1}],
        )
        assert result.startswith("Error:")

    def test_multi_filter_invalid_conditions(self) -> None:
        result = server.multi_filter("aq", "items", [])
        assert result.startswith("Error:")

    def test_compare_success(self) -> None:
        result = server.compare(
            "aq", path_a="items[0]", path_b="items[1]",
        )
        assert "CHANGED" in result or "difference" in result.lower()
        assert "Error" not in result

    def test_compare_bad_alias(self) -> None:
        result = server.compare("missing")
        assert result.startswith("Error:")


# ==================================================================
# Export Tools (Phase 4)
# ==================================================================


class TestServerExportTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({
            "items": [{"x": 1}, {"x": 2}],
            "nested": {"val": 42},
        })
        server.load_json(path, alias="ex")
        os.unlink(path)

    def test_export_csv_success(self, tmp_path) -> None:
        out = str(tmp_path / "out.csv")
        result = server.export_csv("ex", "items", out)
        assert "2 rows" in result
        assert "Error" not in result

    def test_export_csv_bad_alias(self, tmp_path) -> None:
        out = str(tmp_path / "out.csv")
        result = server.export_csv("missing", "items", out)
        assert result.startswith("Error:")

    def test_export_json_success(self, tmp_path) -> None:
        out = str(tmp_path / "out.json")
        result = server.export_json("ex", out, path="nested")
        assert os.path.exists(out)
        assert "Error" not in result

    def test_export_json_bad_alias(self, tmp_path) -> None:
        out = str(tmp_path / "out.json")
        result = server.export_json("missing", out)
        assert result.startswith("Error:")


# ==================================================================
# Introspection Tools (Phase 4)
# ==================================================================


class TestServerIntrospectTools:
    @pytest.fixture(autouse=True)
    def _load_doc(self):
        path = _write_json({"name": "test", "items": [{"a": 1}]})
        server.load_json(path, alias="intr")
        os.unlink(path)

    def test_distinct_paths_success(self) -> None:
        result = server.distinct_paths("intr")
        assert "$.name" in result
        assert "$.items[*].a" in result
        assert "Error" not in result

    def test_distinct_paths_bad_alias(self) -> None:
        result = server.distinct_paths("missing")
        assert result.startswith("Error:")


# ==================================================================
# Server-level Load edge cases
# ==================================================================


class TestServerLoadEdgeCases:
    def test_load_duplicate_alias(self) -> None:
        path = _write_json({"a": 1})
        server.load_json(path, alias="dup_test")
        result = server.load_json(path, alias="dup_test")
        os.unlink(path)
        assert result.startswith("Error:")
