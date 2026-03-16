"""Register MCP tools for statistical summaries."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import stats as stats_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register stats tools and return them."""

    @mcp.tool()
    def describe(alias: str, expression: str) -> str:
        """Get a full statistical summary of numeric values matched by a JSONPath.

        Returns count, mean, median, standard deviation, min, max, 25th/75th
        percentiles, and sum — like pandas .describe() for JSON.

        Args:
            alias: The alias of the loaded document.
            expression: A JSONPath expression resolving to numbers
                        (e.g. "$.orders[*].total").

        Returns:
            A formatted statistical summary table.
        """
        try:
            return stats_tools.describe(store, alias, expression)
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"

    return {"describe": describe}
