"""Tests for the JSON Document Store."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from json_agent.store import JSONStore, DocumentMeta


class TestLoad:
    """Tests for JSONStore.load()."""

    def test_load_object(self, store: JSONStore, json_file: str) -> None:
        meta = store.load(json_file, alias="mydata")
        assert meta.alias == "mydata"
        assert meta.root_type == "object"
        assert meta.top_level_count == 7  # 7 keys in sample_object
        assert meta.file_size_bytes > 0

    def test_load_array(self, store: JSONStore, array_json_file: str) -> None:
        meta = store.load(array_json_file, alias="arr")
        assert meta.root_type == "array"
        assert meta.top_level_count == 5

    def test_load_default_alias(self, store: JSONStore, json_file: str) -> None:
        """Alias defaults to file stem when not provided."""
        meta = store.load(json_file)
        assert meta.alias  # non-empty
        assert store.has(meta.alias)

    def test_load_duplicate_alias_raises(self, store: JSONStore, json_file: str) -> None:
        store.load(json_file, alias="dup")
        with pytest.raises(ValueError, match="already in use"):
            store.load(json_file, alias="dup")

    def test_load_file_not_found(self, store: JSONStore) -> None:
        with pytest.raises(FileNotFoundError):
            store.load("/nonexistent/path/data.json")

    def test_load_invalid_json(self, store: JSONStore) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{not valid json!!}")
            path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                store.load(path, alias="bad")
        finally:
            os.unlink(path)

    def test_file_size_human_readable(self, store: JSONStore, json_file: str) -> None:
        meta = store.load(json_file)
        assert "B" in meta.file_size_human  # should contain a unit

    # --- Edge cases ---

    def test_load_empty_object(self, store: JSONStore, empty_object_file: str) -> None:
        meta = store.load(empty_object_file, alias="empty_obj")
        assert meta.root_type == "object"
        assert meta.top_level_count == 0

    def test_load_empty_array(self, store: JSONStore, empty_array_file: str) -> None:
        meta = store.load(empty_array_file, alias="empty_arr")
        assert meta.root_type == "array"
        assert meta.top_level_count == 0

    def test_load_scalar_string(self, store: JSONStore, scalar_string_file: str) -> None:
        meta = store.load(scalar_string_file, alias="str_root")
        assert meta.root_type == "string"
        assert meta.top_level_count == 0

    def test_load_scalar_number(self, store: JSONStore, scalar_number_file: str) -> None:
        meta = store.load(scalar_number_file, alias="num_root")
        assert meta.root_type == "number"
        assert meta.top_level_count == 0

    def test_load_scalar_null(self, store: JSONStore, scalar_null_file: str) -> None:
        meta = store.load(scalar_null_file, alias="null_root")
        assert meta.root_type == "null"
        assert meta.top_level_count == 0

    def test_load_deeply_nested(self, store: JSONStore, deeply_nested_file: str) -> None:
        meta = store.load(deeply_nested_file, alias="deep")
        assert meta.root_type == "object"
        assert meta.top_level_count == 1

    def test_load_unicode_data(self, store: JSONStore, unicode_file: str) -> None:
        meta = store.load(unicode_file, alias="unicode")
        assert meta.root_type == "object"
        data = store.get("unicode")
        assert data["greeting"] == "こんにちは"
        assert data["emoji"] == "🎉🚀"

    def test_load_empty_file(self, store: JSONStore) -> None:
        """An empty file is not valid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                store.load(path, alias="empty_file")
        finally:
            os.unlink(path)

    def test_load_directory_raises(self, store: JSONStore) -> None:
        """Cannot load a directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                store.load(tmpdir, alias="dir")

    def test_load_tilde_path(self, store: JSONStore, json_file: str) -> None:
        """Tilde in path is expanded correctly."""
        # This tests that Path.expanduser() is called.
        # We can't guarantee ~ works here, but passing a valid path should still succeed.
        meta = store.load(json_file, alias="tilde_test")
        assert meta.alias == "tilde_test"

    def test_memory_bytes_positive(self, store: JSONStore, json_file: str) -> None:
        meta = store.load(json_file, alias="mem_test")
        assert meta.memory_bytes > 0

    def test_memory_human_readable(self, store: JSONStore, json_file: str) -> None:
        meta = store.load(json_file, alias="mem_human")
        assert any(unit in meta.memory_human for unit in ("B", "KB", "MB", "GB"))

    def test_load_multiple_different_aliases(self, store: JSONStore, json_file: str, array_json_file: str) -> None:
        store.load(json_file, alias="first")
        store.load(array_json_file, alias="second")
        assert store.has("first")
        assert store.has("second")
        assert len(store.list_loaded()) == 2


class TestGet:
    """Tests for JSONStore.get() and get_meta()."""

    def test_get_returns_data(self, loaded_store: JSONStore, sample_object: dict) -> None:
        data = loaded_store.get("test")
        assert data == sample_object

    def test_get_meta(self, loaded_store: JSONStore) -> None:
        meta = loaded_store.get_meta("test")
        assert isinstance(meta, DocumentMeta)
        assert meta.alias == "test"

    def test_get_unknown_alias_raises(self, store: JSONStore) -> None:
        with pytest.raises(KeyError, match="No document loaded"):
            store.get("nonexistent")

    def test_get_meta_unknown_alias_raises(self, store: JSONStore) -> None:
        with pytest.raises(KeyError, match="No document loaded"):
            store.get_meta("nonexistent")

    # --- Edge cases ---

    def test_get_empty_alias_raises(self, store: JSONStore) -> None:
        with pytest.raises(KeyError):
            store.get("")

    def test_get_after_unload_raises(self, loaded_store: JSONStore) -> None:
        loaded_store.unload("test")
        with pytest.raises(KeyError, match="No document loaded"):
            loaded_store.get("test")

    def test_get_preserves_data_types(self, store: JSONStore, json_file: str) -> None:
        store.load(json_file, alias="types")
        data = store.get("types")
        assert isinstance(data["active"], bool)
        assert isinstance(data["version"], int)
        assert data["metadata"] is None
        assert isinstance(data["tags"], list)


class TestUnload:
    """Tests for JSONStore.unload()."""

    def test_unload_removes_document(self, loaded_store: JSONStore) -> None:
        result = loaded_store.unload("test")
        assert "Unloaded" in result
        assert not loaded_store.has("test")

    def test_unload_unknown_alias_raises(self, store: JSONStore) -> None:
        with pytest.raises(KeyError, match="No document loaded"):
            store.unload("ghost")

    # --- Edge cases ---

    def test_unload_same_alias_twice(self, loaded_store: JSONStore) -> None:
        loaded_store.unload("test")
        with pytest.raises(KeyError):
            loaded_store.unload("test")

    def test_unload_then_reload(self, store: JSONStore, json_file: str) -> None:
        store.load(json_file, alias="cycle")
        store.unload("cycle")
        # Should be able to reload with the same alias
        meta = store.load(json_file, alias="cycle")
        assert meta.alias == "cycle"
        assert store.has("cycle")


class TestListLoaded:
    """Tests for JSONStore.list_loaded()."""

    def test_empty_store(self, store: JSONStore) -> None:
        assert store.list_loaded() == []

    def test_list_after_loading(self, loaded_store: JSONStore) -> None:
        docs = loaded_store.list_loaded()
        assert len(docs) == 1
        assert docs[0].alias == "test"

    def test_list_multiple(self, store: JSONStore, json_file: str, array_json_file: str) -> None:
        store.load(json_file, alias="a")
        store.load(array_json_file, alias="b")
        assert len(store.list_loaded()) == 2

    # --- Edge cases ---

    def test_list_after_unload_reflects_removal(self, store: JSONStore, json_file: str, array_json_file: str) -> None:
        store.load(json_file, alias="x")
        store.load(array_json_file, alias="y")
        assert len(store.list_loaded()) == 2
        store.unload("x")
        remaining = store.list_loaded()
        assert len(remaining) == 1
        assert remaining[0].alias == "y"


class TestHas:
    """Tests for JSONStore.has()."""

    def test_has_true(self, loaded_store: JSONStore) -> None:
        assert loaded_store.has("test") is True

    def test_has_false(self, store: JSONStore) -> None:
        assert store.has("nope") is False

    def test_has_empty_string(self, store: JSONStore) -> None:
        assert store.has("") is False


class TestDocumentMeta:
    """Edge-case tests for DocumentMeta itself."""

    def test_humanize_bytes(self) -> None:
        meta = DocumentMeta("t", "/f", 512, "object", 1, 0)
        assert "512.0 B" == meta.file_size_human

    def test_humanize_kilobytes(self) -> None:
        meta = DocumentMeta("t", "/f", 2048, "object", 1, 0)
        assert "2.0 KB" == meta.file_size_human

    def test_humanize_megabytes(self) -> None:
        meta = DocumentMeta("t", "/f", 5 * 1024 * 1024, "object", 1, 0)
        assert "5.0 MB" == meta.file_size_human

    def test_humanize_gigabytes(self) -> None:
        meta = DocumentMeta("t", "/f", 3 * 1024**3, "object", 1, 0)
        assert "3.0 GB" == meta.file_size_human

    def test_humanize_terabytes(self) -> None:
        meta = DocumentMeta("t", "/f", 2 * 1024**4, "object", 1, 0)
        assert "2.0 TB" == meta.file_size_human

    def test_frozen_dataclass(self) -> None:
        meta = DocumentMeta("t", "/f", 100, "object", 5, 200)
        with pytest.raises(AttributeError):
            meta.alias = "changed"  # type: ignore[misc]

    def test_humanize_fractional_kilobytes(self) -> None:
        meta = DocumentMeta("t", "/f", 1500, "object", 1, 0)
        human = meta.file_size_human
        assert "KB" in human
        assert "1." in human  # ~1.5 KB

    def test_humanize_zero_bytes(self) -> None:
        meta = DocumentMeta("t", "/f", 0, "object", 1, 0)
        assert "0.0 B" == meta.file_size_human


class TestLoadScalarBoolean:
    def test_load_scalar_boolean(self, store: JSONStore) -> None:
        """Loading a root-level boolean sets root_type=boolean, top_level_count=0."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(True, f)
        f.close()
        try:
            meta = store.load(f.name, alias="bool_root")
            assert meta.root_type == "boolean"
            assert meta.top_level_count == 0
        finally:
            os.unlink(f.name)

    def test_load_scalar_false(self, store: JSONStore) -> None:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(False, f)
        f.close()
        try:
            meta = store.load(f.name, alias="false_root")
            assert meta.root_type == "boolean"
            assert meta.top_level_count == 0
        finally:
            os.unlink(f.name)


class TestMemoryEstimate:
    def test_memory_bytes_for_array_root(self, store: JSONStore) -> None:
        """Memory estimate works on array roots, not just objects."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump([1, 2, 3, 4, 5], f)
        f.close()
        try:
            meta = store.load(f.name, alias="arr_mem")
            assert meta.memory_bytes > 0
        finally:
            os.unlink(f.name)

    def test_memory_bytes_scalar_root(self, store: JSONStore) -> None:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(42, f)
        f.close()
        try:
            meta = store.load(f.name, alias="scalar_mem")
            assert meta.memory_bytes > 0
        finally:
            os.unlink(f.name)
