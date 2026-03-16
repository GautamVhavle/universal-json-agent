"""Tests for export tools (export_csv, export_json)."""

from __future__ import annotations

import csv
import json
import os
import tempfile

import pytest

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools.export import export_csv, export_json


def _load_data(store: JSONStore, data, alias: str = "d") -> JSONStore:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    store.load(f.name, alias=alias)
    os.unlink(f.name)
    return store


class TestExportCsv:
    def test_basic_export(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": [
            {"name": "A", "val": 1},
            {"name": "B", "val": 2},
        ]})
        out = str(tmp_path / "out.csv")
        result = export_csv(s, "d", "items", out)
        assert "2 rows" in result
        assert "2 columns" in result
        assert os.path.exists(out)

        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["name"] == "A"

    def test_specific_fields(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": [
            {"name": "A", "val": 1, "extra": "x"},
        ]})
        out = str(tmp_path / "out.csv")
        result = export_csv(s, "d", "items", out, fields=["name"])
        assert "1 columns" in result

        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert "name" in rows[0]
        assert "extra" not in rows[0]

    def test_nested_values_serialized(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": [
            {"name": "A", "meta": {"deep": True}},
        ]})
        out = str(tmp_path / "out.csv")
        export_csv(s, "d", "items", out)

        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        # nested dict should be JSON-serialized
        assert '"deep"' in rows[0]["meta"]

    def test_not_array_raises(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"obj": {"x": 1}})
        with pytest.raises(TypeError, match="expected an array"):
            export_csv(s, "d", "obj", str(tmp_path / "out.csv"))

    def test_no_objects_in_array(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": [1, 2, 3]})
        result = export_csv(s, "d", "items", str(tmp_path / "out.csv"))
        assert "No object rows" in result

    def test_empty_array(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": []})
        result = export_csv(s, "d", "items", str(tmp_path / "out.csv"))
        assert "No object rows" in result

    def test_sparse_fields(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": [
            {"a": 1},
            {"b": 2},
            {"a": 3, "b": 4},
        ]})
        out = str(tmp_path / "out.csv")
        export_csv(s, "d", "items", out)

        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        # Both columns should exist
        assert "a" in reader.fieldnames
        assert "b" in reader.fieldnames


class TestExportJson:
    def test_basic_export(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"items": [1, 2, 3]})
        out = str(tmp_path / "out.json")
        result = export_json(s, "d", "items", out)
        assert os.path.exists(out)
        assert "list" in result

        with open(out) as f:
            data = json.load(f)
        assert data == [1, 2, 3]

    def test_export_nested_path(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"a": {"b": {"c": 42}}})
        out = str(tmp_path / "out.json")
        export_json(s, "d", "a.b", out)

        with open(out) as f:
            data = json.load(f)
        assert data == {"c": 42}

    def test_export_root(self, store: JSONStore, tmp_path) -> None:
        original = {"x": 1, "y": [2, 3]}
        s = _load_data(store, original)
        out = str(tmp_path / "out.json")
        export_json(s, "d", "", out)

        with open(out) as f:
            data = json.load(f)
        assert data == original

    def test_custom_indent(self, store: JSONStore, tmp_path) -> None:
        s = _load_data(store, {"x": 1})
        out = str(tmp_path / "out.json")
        export_json(s, "d", "", out, indent=4)

        with open(out) as f:
            content = f.read()
        # 4-space indent
        assert "    " in content

    def test_export_csv_list_value_serialized(self, store: JSONStore, tmp_path) -> None:
        """List values in rows are serialized as JSON strings."""
        s = _load_data(store, {"items": [{"tags": [1, 2, 3]}]})
        out = str(tmp_path / "out.csv")
        export_csv(s, "d", "items", out)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert "[1, 2, 3]" in rows[0]["tags"]

    def test_export_csv_none_values(self, store: JSONStore, tmp_path) -> None:
        """None values should become empty strings in CSV."""
        s = _load_data(store, {"items": [{"name": None, "val": 1}]})
        out = str(tmp_path / "out.csv")
        export_csv(s, "d", "items", out)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["name"] == ""

    def test_export_csv_column_order(self, store: JSONStore, tmp_path) -> None:
        """Auto columns preserve insertion order from objects."""
        s = _load_data(store, {"items": [
            {"b": 1, "a": 2},
            {"c": 3},
        ]})
        out = str(tmp_path / "out.csv")
        export_csv(s, "d", "items", out)
        with open(out) as f:
            reader = csv.DictReader(f)
            list(reader)
            cols = reader.fieldnames
        assert cols[0] == "b"
        assert cols[1] == "a"
        assert cols[2] == "c"

    def test_export_csv_creates_parent_dirs(self, store: JSONStore, tmp_path) -> None:
        """Output path with deep nested dirs should create them."""
        s = _load_data(store, {"items": [{"x": 1}]})
        out = str(tmp_path / "deep" / "nested" / "out.csv")
        result = export_csv(s, "d", "items", out)
        assert os.path.exists(out)
        assert "1 rows" in result

    def test_export_csv_mixed_array_skips_non_dicts(self, store: JSONStore, tmp_path) -> None:
        """Only dict items are exported as rows."""
        s = _load_data(store, {"items": [{"a": 1}, 42, {"b": 2}]})
        out = str(tmp_path / "out.csv")
        result = export_csv(s, "d", "items", out)
        assert "2 rows" in result

    def test_export_json_scalar_value(self, store: JSONStore, tmp_path) -> None:
        """Exporting a scalar value at a path."""
        s = _load_data(store, {"name": "test"})
        out = str(tmp_path / "out.json")
        result = export_json(s, "d", "name", out)
        assert "str" in result
        with open(out) as f:
            data = json.load(f)
        assert data == "test"

    def test_export_json_unicode_preserved(self, store: JSONStore, tmp_path) -> None:
        """Unicode chars should be preserved (ensure_ascii=False)."""
        s = _load_data(store, {"text": "こんにちは"})
        out = str(tmp_path / "out.json")
        export_json(s, "d", "", out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert "こんにちは" in content

    def test_export_json_indent_zero(self, store: JSONStore, tmp_path) -> None:
        """Export with indent=0."""
        s = _load_data(store, {"a": 1, "b": 2})
        out = str(tmp_path / "out.json")
        export_json(s, "d", "", out, indent=0)
        with open(out) as f:
            data = json.load(f)
        assert data == {"a": 1, "b": 2}

    def test_export_json_creates_parent_dirs(self, store: JSONStore, tmp_path) -> None:
        """Missing parent dir is created by os.makedirs."""
        s = _load_data(store, {"x": 1})
        out = str(tmp_path / "deep" / "nested" / "out.json")
        export_json(s, "d", "", out)
        assert os.path.exists(out)

    def test_export_json_reports_file_size(self, store: JSONStore, tmp_path) -> None:
        """Result string should include file size info."""
        s = _load_data(store, {"x": 1})
        out = str(tmp_path / "out.json")
        result = export_json(s, "d", "", out)
        assert "B" in result  # should contain byte unit


class TestExportHumanize:
    def test_humanize_integer_bytes(self) -> None:
        from universal_json_agent_mcp.tools.export import _humanize
        assert _humanize(512) == "512 B"

    def test_humanize_float_kb(self) -> None:
        from universal_json_agent_mcp.tools.export import _humanize
        result = _humanize(1500)
        assert "KB" in result

    def test_humanize_terabytes(self) -> None:
        from universal_json_agent_mcp.tools.export import _humanize
        result = _humanize(2 * 1024 ** 4)
        assert "TB" in result
