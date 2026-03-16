"""
MCP Server Entry Point — registers all tools and starts the stdio transport.

This is the only module that depends on the MCP SDK. All business logic lives
in the tools/ and store modules, keeping the server layer thin and focused on
wiring (Dependency Inversion Principle).
"""

from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP

from json_agent.store import JSONStore
from json_agent.tools import load as load_tools
from json_agent.tools import explore as explore_tools
from json_agent.tools import query as query_tools
from json_agent.tools import aggregate as aggregate_tools
from json_agent.tools import transform as transform_tools
from json_agent.tools import stats as stats_tools
from json_agent.tools import advanced_query as adv_query_tools
from json_agent.tools import export as export_tools
from json_agent.tools import introspect as introspect_tools

# ---------------------------------------------------------------------------
# Logging — all output goes to stderr so stdout stays clean for JSON-RPC
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

store = JSONStore()

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "json-agent",
    instructions=(
        "Advanced JSON parsing agent. Load any JSON file and query its "
        "structure, values, keys, counts, and more."
    ),
)

# ===================================================================
# LOAD TOOLS
# ===================================================================


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


# ===================================================================
# EXPLORE TOOLS
# ===================================================================


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


# ===================================================================
# QUERY TOOLS (Phase 2)
# ===================================================================


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


# ===================================================================
# AGGREGATE TOOLS (Phase 2)
# ===================================================================


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


# ===================================================================
# TRANSFORM TOOLS (Phase 3)
# ===================================================================


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


# ===================================================================
# STATS TOOLS (Phase 4)
# ===================================================================


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


# ===================================================================
# ADVANCED QUERY TOOLS (Phase 4)
# ===================================================================


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


# ===================================================================
# EXPORT TOOLS (Phase 4)
# ===================================================================


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


# ===================================================================
# INTROSPECTION TOOLS (Phase 4)
# ===================================================================


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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the MCP server with stdio transport."""
    logger.info("Starting JSON Agent MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
