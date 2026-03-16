"""Register MCP tools for multi-condition filtering and cross-path comparisons."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import advanced_query as adv_query_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register advanced query tools and return them."""

    @mcp.tool()
    def multi_filter(
        alias: str,
        path: str,
        conditions: list[dict],
        mode: str = "and",
    ) -> str:
        """Filter an array of objects with multiple conditions combined by AND/OR.

        Each condition is a dict with keys: field, operator, value.
        Operators: eq, neq, gt, gte, lt, lte, contains, regex.

        Examples:
          - [{"field": "status", "operator": "eq", "value": "active"},
             {"field": "score", "operator": "gt", "value": 80}]
          - mode="and" means ALL conditions must match.
          - mode="or" means ANY condition can match.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array of objects.
            conditions: List of condition dicts.
            mode: "and" or "or" (default "and").

        Returns:
            The filtered objects with a match count header.
        """
        try:
            return adv_query_tools.multi_filter(store, alias, path, conditions, mode)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def compare(
        alias_a: str,
        path_a: str = "",
        alias_b: str | None = None,
        path_b: str = "",
    ) -> str:
        """Compare two JSON values and report their differences.

        Can compare two paths within the same document or across two documents.
        Reports added keys, removed keys, type changes, and value changes.

        Args:
            alias_a: The alias of the first document.
            path_a: Path to the first value (default root).
            alias_b: The alias of the second document (defaults to alias_a).
            path_b: Path to the second value (default root).

        Returns:
            A structured diff report listing all differences found.
        """
        try:
            return adv_query_tools.compare(store, alias_a, alias_b, path_a, path_b)
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    return {
        "multi_filter": multi_filter,
        "compare": compare,
    }
