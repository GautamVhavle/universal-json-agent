"""Register MCP tools for exporting JSON data to CSV and JSON files."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import export as export_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register export tools and return them."""

    @mcp.tool()
    def export_csv(
        alias: str,
        path: str,
        output_path: str,
        fields: list[str] | None = None,
    ) -> str:
        """Export an array of objects to a CSV file.

        If fields is omitted, all keys found across all objects are used as columns.
        Nested values (dicts, arrays) are serialized as JSON strings in the CSV.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array of objects.
            output_path: File path for the output CSV.
            fields: Optional list of column names to include.

        Returns:
            Confirmation with file path, row count, and column count.
        """
        try:
            return export_tools.export_csv(store, alias, path, output_path, fields)
        except (KeyError, TypeError, IndexError, OSError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def export_json(
        alias: str,
        output_path: str,
        path: str = "",
        indent: int = 2,
    ) -> str:
        """Export a value at a path to a new JSON file.

        Useful for saving a filtered subset or nested section of a large document.

        Args:
            alias: The alias of the loaded document.
            output_path: File path for the output JSON.
            path: Dot-notation path to the value to export (default root).
            indent: JSON indentation level (default 2).

        Returns:
            Confirmation with file path and size.
        """
        try:
            return export_tools.export_json(store, alias, path, output_path, indent)
        except (KeyError, TypeError, IndexError, OSError) as exc:
            return f"Error: {exc}"

    return {
        "export_csv": export_csv,
        "export_json": export_json,
    }
