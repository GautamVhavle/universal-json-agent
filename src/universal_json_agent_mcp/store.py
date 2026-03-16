"""
JSON Document Store — in-memory cache for loaded JSON documents.

Manages the lifecycle of JSON documents: loading from disk, caching in memory,
and providing access to tools. Each document is stored with metadata (file path,
size, root type) under a user-friendly alias.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from universal_json_agent_mcp.utils.json_types import json_type_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentMeta:
    """Immutable metadata for a loaded JSON document."""

    alias: str
    file_path: str
    file_size_bytes: int
    root_type: str          # "object", "array", "string", "number", "boolean", "null"
    top_level_count: int    # number of keys (object) or items (array), else 0
    memory_bytes: int = 0   # approximate in-memory size

    @property
    def file_size_human(self) -> str:
        """Human-readable file size (e.g. '2.4 MB')."""
        return self._humanize(self.file_size_bytes)

    @property
    def memory_human(self) -> str:
        """Human-readable approximate memory usage."""
        return self._humanize(self.memory_bytes)

    @staticmethod
    def _humanize(size: int | float) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class _CachedDocument:
    """Internal wrapper holding a document and its metadata."""

    meta: DocumentMeta
    data: Any


class JSONStore:
    """
    Singleton-style in-memory store for JSON documents.

    Responsibilities (Single Responsibility):
        - Load a JSON file from disk and parse it.
        - Cache parsed documents keyed by alias.
        - Provide read access to cached documents.
        - Unload documents to free memory.

    Thread safety is *not* required — MCP stdio servers are single-threaded.
    """

    def __init__(self) -> None:
        self._documents: dict[str, _CachedDocument] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, file_path: str, alias: str | None = None) -> DocumentMeta:
        """
        Load a JSON file into the store.

        Args:
            file_path: Absolute or relative path to the JSON file.
            alias: Optional friendly name. Defaults to the file stem (e.g. "orders").

        Returns:
            DocumentMeta with summary information about the loaded document.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
            ValueError: If the alias is already in use.
        """
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        alias = alias or path.stem

        if alias in self._documents:
            raise ValueError(
                f"Alias '{alias}' is already in use. "
                f"Unload it first or choose a different alias."
            )

        file_size = path.stat().st_size
        logger.info("Loading %s (%s bytes) as '%s'", path, file_size, alias)

        data = self._parse_file(path)
        mem_bytes = self._estimate_memory(data)

        meta = DocumentMeta(
            alias=alias,
            file_path=str(path),
            file_size_bytes=file_size,
            root_type=json_type_name(data),
            top_level_count=self._top_level_count(data),
            memory_bytes=mem_bytes,
        )

        self._documents[alias] = _CachedDocument(meta=meta, data=data)
        logger.info("Loaded '%s' — %s, %d top-level items", alias, meta.root_type, meta.top_level_count)
        return meta

    def get(self, alias: str) -> Any:
        """
        Retrieve the parsed JSON data for a loaded document.

        Raises:
            KeyError: If no document is loaded under the given alias.
        """
        try:
            return self._documents[alias].data
        except KeyError:
            raise KeyError(
                f"No document loaded with alias '{alias}'. "
                f"Loaded documents: {list(self._documents.keys()) or '(none)'}"
            )

    def get_meta(self, alias: str) -> DocumentMeta:
        """
        Retrieve metadata for a loaded document.

        Raises:
            KeyError: If no document is loaded under the given alias.
        """
        try:
            return self._documents[alias].meta
        except KeyError:
            raise KeyError(
                f"No document loaded with alias '{alias}'. "
                f"Loaded documents: {list(self._documents.keys()) or '(none)'}"
            )

    def unload(self, alias: str) -> str:
        """
        Remove a document from the store and free its memory.

        Returns:
            Confirmation message.

        Raises:
            KeyError: If no document is loaded under the given alias.
        """
        if alias not in self._documents:
            raise KeyError(
                f"No document loaded with alias '{alias}'. "
                f"Loaded documents: {list(self._documents.keys()) or '(none)'}"
            )
        meta = self._documents.pop(alias).meta
        logger.info("Unloaded '%s' (%s)", alias, meta.file_path)
        return f"Unloaded '{alias}' ({meta.file_path})"

    def list_loaded(self) -> list[DocumentMeta]:
        """Return metadata for all currently loaded documents."""
        return [doc.meta for doc in self._documents.values()]

    def has(self, alias: str) -> bool:
        """Check whether a document is loaded under the given alias."""
        return alias in self._documents

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_file(path: Path) -> Any:
        """Parse a JSON file from disk."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _estimate_memory(value: Any) -> int:
        """Rough estimate of in-memory size using sys.getsizeof + traversal."""
        total = sys.getsizeof(value)
        if isinstance(value, dict):
            total += sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in value.items())
        elif isinstance(value, list):
            total += sum(sys.getsizeof(item) for item in value)
        return total

    @staticmethod
    def _top_level_count(value: Any) -> int:
        """Count top-level keys (object) or items (array)."""
        if isinstance(value, (dict, list)):
            return len(value)
        return 0
