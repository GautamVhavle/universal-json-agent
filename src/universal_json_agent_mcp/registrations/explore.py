"""Register MCP tools for inspecting JSON structure and values."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import explore as explore_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register explore tools and return them."""

    @mcp.tool()
    def get_keys(alias: str, path: str = "") -> str:
        """Get all keys at a given path in a loaded JSON document.

        Works on objects (returns key names) and arrays (returns index count).

        Args:
            alias: The alias of the loaded document.
            path: Dot/bracket notation path to navigate into the document.
                  Examples: "", "data.users", "items[0].tags".
                  Empty string means root.

        Returns:
            List of keys (for objects) or item count (for arrays).
        """
        try:
            return explore_tools.get_keys(store, alias, path)
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def get_value(alias: str, path: str = "") -> str:
        """Retrieve the value at an exact path in a loaded JSON document.

        The output is automatically truncated if it exceeds 10KB to prevent
        overwhelming the context window.

        Args:
            alias: The alias of the loaded document.
            path: Dot/bracket notation path. Empty string means root.

        Returns:
            The JSON value at the given path (serialized, possibly truncated).
        """
        try:
            return explore_tools.get_value(store, alias, path)
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def get_type(alias: str, path: str = "") -> str:
        """Return the JSON type of the value at a given path.

        Possible types: object, array, string, number, boolean, null.
        For objects and arrays, also includes the count of keys/items.

        Args:
            alias: The alias of the loaded document.
            path: Dot/bracket notation path. Empty string means root.

        Returns:
            The JSON type (e.g. "object (5 keys)", "array (100 items)", "string").
        """
        try:
            return explore_tools.get_type(store, alias, path)
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def get_structure(alias: str, path: str = "", max_depth: int = 3) -> str:
        """Return a schema-like skeleton of a JSON document showing keys and types.

        Useful for understanding the shape of deeply nested JSON without viewing
        all the actual data.

        Args:
            alias: The alias of the loaded document.
            path: Dot/bracket notation path. Empty string means root.
            max_depth: How many levels deep to show (default 3).

        Returns:
            An indented tree showing the document structure with types.
        """
        try:
            return explore_tools.get_structure(store, alias, path, max_depth)
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    return {
        "get_keys": get_keys,
        "get_value": get_value,
        "get_type": get_type,
        "get_structure": get_structure,
    }
