"""Register MCP tools for JSONPath queries, filtering, and text search."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import query as query_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register query tools and return them."""

    @mcp.tool()
    def jsonpath_query(alias: str, expression: str) -> str:
        """Execute a JSONPath expression against a loaded JSON document.

        Use standard JSONPath syntax to extract data. Examples:
          - $.users[*].email         — all user emails
          - $.orders[?@.total>100]   — orders over 100
          - $.config.database.host   — specific nested value

        Args:
            alias: The alias of the loaded document.
            expression: A JSONPath expression (must start with $).

        Returns:
            The matched values as a list, or a message if nothing matched.
        """
        try:
            return query_tools.jsonpath_query(store, alias, expression)
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def filter_objects(
        alias: str,
        path: str,
        field: str,
        operator: str,
        value: str | int | float | bool | None,
    ) -> str:
        """Filter an array of objects by a field condition.

        Operators: eq, neq, gt, gte, lt, lte, contains, regex.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array (e.g. "products", "data.users").
            field: The field name to filter on (e.g. "status", "price").
            operator: Comparison operator (eq, neq, gt, gte, lt, lte, contains, regex).
            value: The value to compare against.

        Returns:
            The filtered objects with a match count header.
        """
        try:
            return query_tools.filter_objects(store, alias, path, field, operator, value)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def search_text(
        alias: str,
        pattern: str,
        path: str = "",
        case_sensitive: bool = False,
    ) -> str:
        """Recursively search all string values for a substring or regex pattern.

        Returns the paths and values of every match found. Useful for finding
        where a specific term appears anywhere in a large JSON document.

        Args:
            alias: The alias of the loaded document.
            pattern: A substring or regex pattern to search for.
            path: Optional starting path to narrow the search scope.
            case_sensitive: Whether matching is case-sensitive (default False).

        Returns:
            A list of matching paths and their string values.
        """
        try:
            return query_tools.search_text(store, alias, pattern, path, case_sensitive)
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            return f"Error: {exc}"

    return {
        "jsonpath_query": jsonpath_query,
        "filter_objects": filter_objects,
        "search_text": search_text,
    }
