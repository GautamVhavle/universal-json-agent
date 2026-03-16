"""Register MCP tools for counting, summing, and summarising JSON data."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import aggregate as aggregate_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register aggregate tools and return them."""

    @mcp.tool()
    def count(alias: str, path: str = "") -> str:
        """Count items in an array or keys in an object at a given path.

        Args:
            alias: The alias of the loaded document.
            path: Dot/bracket notation path. Empty string means root.

        Returns:
            The item/key count at the given path.
        """
        try:
            return aggregate_tools.count(store, alias, path)
        except (KeyError, IndexError, TypeError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def sum_values(alias: str, expression: str) -> str:
        """Sum numeric values matched by a JSONPath expression.

        Args:
            alias: The alias of the loaded document.
            expression: A JSONPath expression resolving to numbers
                        (e.g. "$.orders[*].total").

        Returns:
            The sum and count of matched numeric values.
        """
        try:
            return aggregate_tools.sum_values(store, alias, expression)
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def min_max(alias: str, expression: str) -> str:
        """Get the minimum and maximum of numeric values matched by a JSONPath expression.

        Args:
            alias: The alias of the loaded document.
            expression: A JSONPath expression resolving to numbers.

        Returns:
            The min, max, and count of matched values.
        """
        try:
            return aggregate_tools.min_max(store, alias, expression)
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def unique_values(alias: str, expression: str) -> str:
        """Get distinct values matched by a JSONPath expression.

        Args:
            alias: The alias of the loaded document.
            expression: A JSONPath expression (e.g. "$.users[*].role").

        Returns:
            A list of unique values with count information.
        """
        try:
            return aggregate_tools.unique_values(store, alias, expression)
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def value_counts(alias: str, expression: str) -> str:
        """Count occurrences of each distinct value matched by a JSONPath expression.

        Like a frequency table: shows each unique value and how many times it appears.
        Results are sorted by count (most common first).

        Args:
            alias: The alias of the loaded document.
            expression: A JSONPath expression (e.g. "$.orders[*].status").

        Returns:
            A frequency table with values and their counts.
        """
        try:
            return aggregate_tools.value_counts(store, alias, expression)
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"

    return {
        "count": count,
        "sum_values": sum_values,
        "min_max": min_max,
        "unique_values": unique_values,
        "value_counts": value_counts,
    }
