"""Register MCP tools for reshaping and sampling JSON data."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import transform as transform_tools


def register(mcp: FastMCP, store: JSONStore) -> dict:
    """Register transform tools and return them."""

    @mcp.tool()
    def flatten(alias: str, path: str = "", separator: str = ".") -> str:
        """Flatten a nested JSON object into dot-notation key-value pairs.

        Converts nested structures like {"a": {"b": 1}} into {"a.b": 1}.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the object to flatten. Empty means root.
            separator: The separator for flattened keys (default ".").

        Returns:
            A flat mapping of dotted-path keys to their values.
        """
        try:
            return transform_tools.flatten(store, alias, path, separator)
        except (KeyError, TypeError, IndexError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def pick_fields(alias: str, path: str, fields: list[str]) -> str:
        """Extract specific fields from each object in an array (projection).

        Like SQL SELECT — picks only the columns you care about.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array of objects.
            fields: List of field names to include (e.g. ["name", "price"]).

        Returns:
            The projected array containing only the specified fields.
        """
        try:
            return transform_tools.pick_fields(store, alias, path, fields)
        except (KeyError, TypeError, IndexError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def group_by(alias: str, path: str, field: str) -> str:
        """Group an array of objects by a field value.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array of objects.
            field: The field to group by (e.g. "category", "status").

        Returns:
            A summary of groups with counts, plus the grouped data.
        """
        try:
            return transform_tools.group_by(store, alias, path, field)
        except (KeyError, TypeError, IndexError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def sort_by(alias: str, path: str, field: str, descending: bool = False) -> str:
        """Sort an array of objects by a field.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array of objects.
            field: The field to sort by (e.g. "price", "name").
            descending: Sort in descending order (default False = ascending).

        Returns:
            The sorted array.
        """
        try:
            return transform_tools.sort_by(store, alias, path, field, descending)
        except (KeyError, TypeError, IndexError) as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def sample(alias: str, path: str = "", n: int = 5, seed: int | None = None) -> str:
        """Return N random items from an array.

        Useful for previewing large datasets without loading everything.

        Args:
            alias: The alias of the loaded document.
            path: Dot-notation path to the array. Empty means root.
            n: Number of items to sample (default 5).
            seed: Optional random seed for reproducible results.

        Returns:
            N randomly selected items from the array.
        """
        try:
            return transform_tools.sample(store, alias, path, n, seed)
        except (KeyError, TypeError, IndexError) as exc:
            return f"Error: {exc}"

    return {
        "flatten": flatten,
        "pick_fields": pick_fields,
        "group_by": group_by,
        "sort_by": sort_by,
        "sample": sample,
    }
