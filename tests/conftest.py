"""
Shared test fixtures for JSON Agent tests.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

from universal_json_agent_mcp.store import JSONStore


@pytest.fixture
def store() -> JSONStore:
    """Fresh JSONStore instance for each test."""
    return JSONStore()


@pytest.fixture
def sample_object() -> dict[str, Any]:
    """A representative nested JSON object for testing."""
    return {
        "name": "Test Store",
        "version": 2,
        "active": True,
        "metadata": None,
        "tags": ["alpha", "beta", "gamma"],
        "products": [
            {"id": 1, "name": "Widget", "price": 9.99, "in_stock": True},
            {"id": 2, "name": "Gadget", "price": 24.50, "in_stock": False},
            {"id": 3, "name": "Doohickey", "price": 4.75, "in_stock": True},
        ],
        "config": {
            "theme": "dark",
            "max_items": 100,
            "nested": {
                "deep": {
                    "value": "found_it"
                }
            }
        }
    }


@pytest.fixture
def sample_array() -> list[dict[str, Any]]:
    """A representative JSON array for testing."""
    return [
        {"id": 1, "status": "active", "score": 85},
        {"id": 2, "status": "inactive", "score": 42},
        {"id": 3, "status": "active", "score": 93},
        {"id": 4, "status": "pending", "score": 67},
        {"id": 5, "status": "active", "score": 71},
    ]


# ------------------------------------------------------------------
# Edge-case data fixtures
# ------------------------------------------------------------------


@pytest.fixture
def empty_object() -> dict:
    """An empty JSON object."""
    return {}


@pytest.fixture
def empty_array() -> list:
    """An empty JSON array."""
    return []


@pytest.fixture
def scalar_string() -> str:
    """A bare JSON string (valid JSON root)."""
    return "just a string"


@pytest.fixture
def scalar_number() -> int:
    """A bare JSON number (valid JSON root)."""
    return 42


@pytest.fixture
def scalar_bool() -> bool:
    """A bare JSON boolean."""
    return True


@pytest.fixture
def scalar_null() -> None:
    """A bare JSON null."""
    return None


@pytest.fixture
def deeply_nested() -> dict:
    """A 10-level deep nested structure."""
    obj: dict[str, Any] = {"leaf": "deep_value"}
    for i in range(9, -1, -1):
        obj = {f"level_{i}": obj}
    return obj


@pytest.fixture
def mixed_array() -> list:
    """An array containing mixed types (not all dicts)."""
    return [
        {"id": 1, "name": "Alice"},
        "bare_string",
        42,
        None,
        True,
        [1, 2, 3],
        {"id": 2, "name": "Bob"},
    ]


@pytest.fixture
def unicode_data() -> dict:
    """JSON with unicode, emoji, and special characters."""
    return {
        "greeting": "こんにちは",
        "emoji": "🎉🚀",
        "accented": "café résumé naïve",
        "escaped": "line1\nline2\ttab",
        "empty_string": "",
        "special_chars": '<script>alert("xss")</script>',
    }


@pytest.fixture
def numeric_edge_cases() -> dict:
    """Numbers at boundaries: zero, negative, float precision, large."""
    return {
        "zero": 0,
        "negative": -42,
        "float_precision": 0.1 + 0.2,  # 0.30000000000000004
        "large_int": 10**18,
        "tiny_float": 1e-10,
        "negative_float": -3.14,
        "values": [0, -1, 1, 100, -100, 0.5, -0.5],
    }


@pytest.fixture
def duplicate_values_array() -> list:
    """Array where many objects share the same field values."""
    return [
        {"category": "A", "val": 10},
        {"category": "B", "val": 20},
        {"category": "A", "val": 30},
        {"category": "C", "val": 40},
        {"category": "B", "val": 50},
        {"category": "A", "val": 60},
    ]


@pytest.fixture
def sparse_array() -> list:
    """Array of objects where some fields are missing on some items."""
    return [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob"},
        {"id": 3, "age": 25},
        {"id": 4},
        {"id": 5, "name": "Eve", "age": 28, "extra": True},
    ]


# ------------------------------------------------------------------
# File fixtures
# ------------------------------------------------------------------


def _write_json(data: Any) -> str:
    """Write data to a temp JSON file, return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


@pytest.fixture
def json_file(sample_object: dict[str, Any]) -> Generator[str, None, None]:
    """Write sample_object to a temp file, yield its path, then clean up."""
    path = _write_json(sample_object)
    yield path
    os.unlink(path)


@pytest.fixture
def array_json_file(sample_array: list[dict[str, Any]]) -> Generator[str, None, None]:
    """Write sample_array to a temp file, yield its path, then clean up."""
    path = _write_json(sample_array)
    yield path
    os.unlink(path)


@pytest.fixture
def empty_object_file(empty_object: dict) -> Generator[str, None, None]:
    path = _write_json(empty_object)
    yield path
    os.unlink(path)


@pytest.fixture
def empty_array_file(empty_array: list) -> Generator[str, None, None]:
    path = _write_json(empty_array)
    yield path
    os.unlink(path)


@pytest.fixture
def scalar_string_file(scalar_string: str) -> Generator[str, None, None]:
    path = _write_json(scalar_string)
    yield path
    os.unlink(path)


@pytest.fixture
def scalar_number_file(scalar_number: int) -> Generator[str, None, None]:
    path = _write_json(scalar_number)
    yield path
    os.unlink(path)


@pytest.fixture
def scalar_null_file() -> Generator[str, None, None]:
    path = _write_json(None)
    yield path
    os.unlink(path)


@pytest.fixture
def deeply_nested_file(deeply_nested: dict) -> Generator[str, None, None]:
    path = _write_json(deeply_nested)
    yield path
    os.unlink(path)


@pytest.fixture
def mixed_array_file(mixed_array: list) -> Generator[str, None, None]:
    path = _write_json(mixed_array)
    yield path
    os.unlink(path)


@pytest.fixture
def unicode_file(unicode_data: dict) -> Generator[str, None, None]:
    path = _write_json(unicode_data)
    yield path
    os.unlink(path)


@pytest.fixture
def numeric_edge_file(numeric_edge_cases: dict) -> Generator[str, None, None]:
    path = _write_json(numeric_edge_cases)
    yield path
    os.unlink(path)


@pytest.fixture
def duplicate_values_file(duplicate_values_array: list) -> Generator[str, None, None]:
    path = _write_json(duplicate_values_array)
    yield path
    os.unlink(path)


@pytest.fixture
def sparse_array_file(sparse_array: list) -> Generator[str, None, None]:
    path = _write_json(sparse_array)
    yield path
    os.unlink(path)


# ------------------------------------------------------------------
# Pre-loaded store fixtures
# ------------------------------------------------------------------


@pytest.fixture
def loaded_store(store: JSONStore, json_file: str) -> JSONStore:
    """A JSONStore with the sample_object already loaded as 'test'."""
    store.load(json_file, alias="test")
    return store


@pytest.fixture
def loaded_array_store(store: JSONStore, array_json_file: str) -> JSONStore:
    """A JSONStore with the sample_array already loaded as 'arr'."""
    store.load(array_json_file, alias="arr")
    return store
