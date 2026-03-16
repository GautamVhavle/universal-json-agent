"""Register MCP tools for loading, listing, and unloading JSON documents."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import load as load_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register load/unload/list tools and return them."""

    @mcp.tool()
    def load_json(file_path: str, alias: str | None = None) -> str:
        """Load a JSON file from disk into memory.

        Args:
            file_path: Absolute or relative path to the JSON file.
            alias: Optional friendly name for the document (defaults to filename stem).

        Returns:
            Summary of the loaded document including type, size, and item count.
        """
        try:
            return load_tools.load_json(store, file_path, alias)
        except (FileNotFoundError, ValueError, Exception) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def list_loaded() -> str:
        """List all currently loaded JSON documents with their metadata.

        Returns:
            A formatted table showing alias, type, item count, size, and path
            for each loaded document, or a message if none are loaded.
        """
        return load_tools.list_loaded(store)

    @mcp.tool()
    def unload_json(alias: str) -> str:
        """Remove a loaded JSON document from memory.

        Args:
            alias: The alias of the document to unload.

        Returns:
            Confirmation that the document was unloaded.
        """
        try:
            return load_tools.unload_json(store, alias)
        except KeyError as exc:
            return f"Error: {exc}"

    return {
        "load_json": load_json,
        "list_loaded": list_loaded,
        "unload_json": unload_json,
    }
