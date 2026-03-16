"""Tests for load tools (load_json, list_loaded, unload_json)."""

from __future__ import annotations

import pytest

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools.load import load_json, list_loaded, unload_json


class TestLoadJson:
    def test_load_success(self, store: JSONStore, json_file: str) -> None:
        result = load_json(store, json_file, alias="demo")
        assert "Loaded 'demo'" in result
        assert "object" in result
        assert store.has("demo")

    def test_load_array_file(self, store: JSONStore, array_json_file: str) -> None:
        result = load_json(store, array_json_file, alias="items")
        assert "array" in result
        assert "5" in result  # 5 items

    def test_load_output_format(self, store: JSONStore, json_file: str) -> None:
        """Output should contain alias, type, size, and items lines."""
        result = load_json(store, json_file, alias="fmt")
        assert "Loaded 'fmt'" in result
        assert "Type" in result
        assert "Size" in result
        assert "Items" in result


class TestListLoaded:
    def test_empty(self, store: JSONStore) -> None:
        result = list_loaded(store)
        assert "No documents loaded" in result

    def test_with_documents(self, loaded_store: JSONStore) -> None:
        result = list_loaded(loaded_store)
        assert "test" in result
        assert "object" in result

    def test_table_format_multiple_docs(
        self, store: JSONStore, json_file: str, array_json_file: str
    ) -> None:
        """Multiple loaded docs produce a table with header, separator, and rows."""
        store.load(json_file, alias="alpha")
        store.load(array_json_file, alias="beta")
        result = list_loaded(store)
        assert "Alias" in result          # header
        assert "---" in result            # separator line
        assert "alpha" in result
        assert "beta" in result


class TestUnloadJson:
    def test_unload_success(self, loaded_store: JSONStore) -> None:
        result = unload_json(loaded_store, "test")
        assert "Unloaded" in result
        assert not loaded_store.has("test")

    def test_unload_missing(self, store: JSONStore) -> None:
        # Should raise — the server.py wrapper catches exceptions
        with pytest.raises(KeyError):
            unload_json(store, "nonexistent")
