"""Register MCP tools for deep structure discovery."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import introspect as introspect_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register introspection tools and return them."""

    @mcp.tool()
    def distinct_paths(
        alias: str,
        path: str = "",
        max_depth: int = 10,
        sample_array_items: int = 5,
    ) -> str:
        """List every unique leaf path in a JSON document.

        Essential for understanding the shape of an unknown JSON file.
        For arrays, only the first N items are sampled to discover paths
        efficiently without scanning thousands of identical objects.

        Args:
            alias: The alias of the loaded document.
            path: Starting path (default root).
            max_depth: Maximum recursion depth (default 10).
            sample_array_items: How many array elements to inspect (default 5).

        Returns:
            A list of all discovered paths with their JSON types.
        """
        try:
            return introspect_tools.distinct_paths(
                store, alias, path, max_depth, sample_array_items
            )
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    return {"distinct_paths": distinct_paths}
