"""
LangChain Tool Wrappers — expose every json_agent tool to the LLM agent.

Each wrapper is a LangChain `StructuredTool` that delegates to the pure
functions in json_agent.tools.*. The shared JSONStore is injected at
creation time so the agent never needs to manage it.
"""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.tools import (
    load as load_mod,
    explore as explore_mod,
    query as query_mod,
    aggregate as agg_mod,
    transform as transform_mod,
    stats as stats_mod,
    advanced_query as adv_mod,
    export as export_mod,
    introspect as introspect_mod,
)


# ------------------------------------------------------------------
# Input schemas (Pydantic v2) — one per tool
# ------------------------------------------------------------------


class EmptyInput(BaseModel):
    """No parameters required."""
    pass


class LoadJsonInput(BaseModel):
    file_path: str = Field(description="Absolute path to the JSON file on disk.")
    alias: Optional[str] = Field(
        default=None,
        description="Friendly alias for the document (defaults to file stem).",
    )


class AliasInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")


class AliasPathInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(default="", description="Dot/bracket notation path (empty = root).")


class GetStructureInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(default="", description="Dot/bracket notation path.")
    max_depth: int = Field(default=3, description="Maximum depth to traverse.")


class JsonpathInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    expression: str = Field(description="JSONPath expression (e.g. '$.users[*].name').")


class FilterInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(description="Path to the array to filter.")
    field: str = Field(description="Field name to compare.")
    operator: str = Field(
        description="Operator: eq, neq, gt, gte, lt, lte, contains, regex."
    )
    value: Any = Field(description="Value to compare against.")


class SearchTextInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    pattern: str = Field(description="Substring or regex to search for.")
    path: str = Field(default="", description="Starting path to narrow scope.")
    case_sensitive: bool = Field(default=False, description="Case-sensitive matching.")


class FlattenInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(default="", description="Path to the object to flatten.")
    separator: str = Field(default=".", description="Key separator.")


class PickFieldsInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(description="Path to the array of objects.")
    fields: list[str] = Field(description="List of field names to keep.")


class GroupByInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(description="Path to the array of objects.")
    field: str = Field(description="Field to group by.")


class SortByInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(description="Path to the array of objects.")
    field: str = Field(description="Field to sort by.")
    descending: bool = Field(default=False, description="Sort descending.")


class SampleInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(default="", description="Path to the array.")
    n: int = Field(default=5, description="Number of items to sample.")
    seed: Optional[int] = Field(default=None, description="Random seed.")


class MultiFilterInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(description="Path to the array of objects.")
    conditions: list[dict[str, Any]] = Field(
        description=(
            "List of condition dicts, each with keys: field, operator, value. "
            "Operators: eq, neq, gt, gte, lt, lte, contains, regex."
        )
    )
    mode: str = Field(default="and", description="'and' or 'or'.")


class CompareInput(BaseModel):
    alias_a: str = Field(description="Alias of the first document.")
    alias_b: Optional[str] = Field(
        default=None,
        description="Alias of the second document (defaults to alias_a).",
    )
    path_a: str = Field(default="", description="Path in the first document.")
    path_b: str = Field(default="", description="Path in the second document.")


class ExportCsvInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(description="Path to the array of objects.")
    output_path: str = Field(description="File path for the output CSV.")
    fields: Optional[list[str]] = Field(
        default=None, description="Columns to include (all if omitted)."
    )


class ExportJsonInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(default="", description="Path to the value to export.")
    output_path: str = Field(description="File path for the output JSON.")
    indent: int = Field(default=2, description="JSON indentation level.")


class DistinctPathsInput(BaseModel):
    alias: str = Field(description="Alias of the loaded document.")
    path: str = Field(default="", description="Starting path (empty = root).")
    max_depth: int = Field(default=10, description="Maximum recursion depth.")
    sample_array_items: int = Field(
        default=5, description="How many array items to sample."
    )


# ------------------------------------------------------------------
# Factory — creates all LangChain tools bound to a shared store
# ------------------------------------------------------------------


def build_tools(store: JSONStore) -> list[StructuredTool]:
    """
    Build and return the full list of LangChain tools, each bound to *store*.

    The agent calls these tools by name; each one delegates to the matching
    json_agent.tools function and catches exceptions so the agent always
    gets a text response (never a traceback).
    """

    def _safe(fn, *a, **kw) -> str:
        try:
            return fn(store, *a, **kw)
        except Exception as exc:
            return f"Error: {exc}"

    tools: list[StructuredTool] = [
        # ---- Load ----
        StructuredTool.from_function(
            name="load_json",
            description=(
                "Load a JSON file from disk into memory. "
                "Returns a summary with alias, type, size, and item count. "
                "You MUST call this first before using any other tool."
            ),
            func=lambda file_path, alias=None: _safe(
                load_mod.load_json, file_path, alias
            ),
            args_schema=LoadJsonInput,
        ),
        StructuredTool.from_function(
            name="list_loaded",
            description="List all currently loaded JSON documents with metadata.",
            func=lambda: _safe(load_mod.list_loaded),
            args_schema=EmptyInput,
        ),
        StructuredTool.from_function(
            name="unload_json",
            description="Remove a loaded document from memory to free resources.",
            func=lambda alias: _safe(load_mod.unload_json, alias),
            args_schema=AliasInput,
        ),
        # ---- Explore ----
        StructuredTool.from_function(
            name="get_keys",
            description=(
                "Get all keys (object) or index range (array) at a path. "
                "Use this to understand the structure before querying."
            ),
            func=lambda alias, path="": _safe(explore_mod.get_keys, alias, path),
            args_schema=AliasPathInput,
        ),
        StructuredTool.from_function(
            name="get_value",
            description="Retrieve the value at an exact path (large results auto-truncated).",
            func=lambda alias, path="": _safe(explore_mod.get_value, alias, path),
            args_schema=AliasPathInput,
        ),
        StructuredTool.from_function(
            name="get_type",
            description="Return the JSON type (object, array, string, number, boolean, null) at a path.",
            func=lambda alias, path="": _safe(explore_mod.get_type, alias, path),
            args_schema=AliasPathInput,
        ),
        StructuredTool.from_function(
            name="get_structure",
            description=(
                "Return a schema-like tree showing keys and types up to max_depth. "
                "Great first step after loading to understand the document shape."
            ),
            func=lambda alias, path="", max_depth=3: _safe(
                explore_mod.get_structure, alias, path, max_depth
            ),
            args_schema=GetStructureInput,
        ),
        # ---- Query ----
        StructuredTool.from_function(
            name="jsonpath_query",
            description=(
                "Execute a JSONPath expression (e.g. '$.users[*].email') and return matches."
            ),
            func=lambda alias, expression: _safe(
                query_mod.jsonpath_query, alias, expression
            ),
            args_schema=JsonpathInput,
        ),
        StructuredTool.from_function(
            name="filter_objects",
            description=(
                "Filter an array of objects by a single field condition. "
                "Operators: eq, neq, gt, gte, lt, lte, contains, regex."
            ),
            func=lambda alias, path, field, operator, value: _safe(
                query_mod.filter_objects, alias, path, field, operator, value
            ),
            args_schema=FilterInput,
        ),
        StructuredTool.from_function(
            name="search_text",
            description=(
                "Recursively search all string values for a substring or regex. "
                "Best for finding a specific value without knowing its path."
            ),
            func=lambda alias, pattern, path="", case_sensitive=False: _safe(
                query_mod.search_text, alias, pattern, path, case_sensitive
            ),
            args_schema=SearchTextInput,
        ),
        # ---- Aggregate ----
        StructuredTool.from_function(
            name="count",
            description="Count items in an array or keys in an object at a path.",
            func=lambda alias, path="": _safe(agg_mod.count, alias, path),
            args_schema=AliasPathInput,
        ),
        StructuredTool.from_function(
            name="sum_values",
            description="Sum numeric values matched by a JSONPath expression.",
            func=lambda alias, expression: _safe(
                agg_mod.sum_values, alias, expression
            ),
            args_schema=JsonpathInput,
        ),
        StructuredTool.from_function(
            name="min_max",
            description="Get the minimum and maximum of numeric values matched by a JSONPath.",
            func=lambda alias, expression: _safe(
                agg_mod.min_max, alias, expression
            ),
            args_schema=JsonpathInput,
        ),
        StructuredTool.from_function(
            name="unique_values",
            description="Get distinct values matched by a JSONPath expression.",
            func=lambda alias, expression: _safe(
                agg_mod.unique_values, alias, expression
            ),
            args_schema=JsonpathInput,
        ),
        StructuredTool.from_function(
            name="value_counts",
            description=(
                "Count occurrences of each distinct value matched by a JSONPath. "
                "Like pandas value_counts() — great for distribution questions."
            ),
            func=lambda alias, expression: _safe(
                agg_mod.value_counts, alias, expression
            ),
            args_schema=JsonpathInput,
        ),
        # ---- Transform ----
        StructuredTool.from_function(
            name="flatten",
            description="Flatten a nested object into dot-notation key-value pairs.",
            func=lambda alias, path="", separator=".": _safe(
                transform_mod.flatten, alias, path, separator
            ),
            args_schema=FlattenInput,
        ),
        StructuredTool.from_function(
            name="pick_fields",
            description="Project specific fields from each object in an array.",
            func=lambda alias, path, fields: _safe(
                transform_mod.pick_fields, alias, path, fields
            ),
            args_schema=PickFieldsInput,
        ),
        StructuredTool.from_function(
            name="group_by",
            description="Group an array of objects by a field value.",
            func=lambda alias, path, field: _safe(
                transform_mod.group_by, alias, path, field
            ),
            args_schema=GroupByInput,
        ),
        StructuredTool.from_function(
            name="sort_by",
            description="Sort an array of objects by a field.",
            func=lambda alias, path, field, descending=False: _safe(
                transform_mod.sort_by, alias, path, field, descending
            ),
            args_schema=SortByInput,
        ),
        StructuredTool.from_function(
            name="sample",
            description="Return N random items from an array.",
            func=lambda alias, path="", n=5, seed=None: _safe(
                transform_mod.sample, alias, path, n, seed
            ),
            args_schema=SampleInput,
        ),
        # ---- Stats ----
        StructuredTool.from_function(
            name="describe",
            description=(
                "Statistical summary (count, mean, std dev, min, max, "
                "percentiles, sum) for numeric values matched by a JSONPath."
            ),
            func=lambda alias, expression: _safe(
                stats_mod.describe, alias, expression
            ),
            args_schema=JsonpathInput,
        ),
        # ---- Advanced Query ----
        StructuredTool.from_function(
            name="multi_filter",
            description=(
                "Filter an array with multiple conditions combined by AND/OR. "
                "Each condition: {field, operator, value}."
            ),
            func=lambda alias, path, conditions, mode="and": _safe(
                adv_mod.multi_filter, alias, path, conditions, mode
            ),
            args_schema=MultiFilterInput,
        ),
        StructuredTool.from_function(
            name="compare",
            description=(
                "Compare two JSON values and report differences: "
                "added/removed keys, type changes, value changes."
            ),
            func=lambda alias_a, alias_b=None, path_a="", path_b="": _safe(
                adv_mod.compare, alias_a, alias_b, path_a, path_b
            ),
            args_schema=CompareInput,
        ),
        # ---- Export ----
        StructuredTool.from_function(
            name="export_csv",
            description="Export an array of objects to a CSV file.",
            func=lambda alias, path, output_path, fields=None: _safe(
                export_mod.export_csv, alias, path, output_path, fields
            ),
            args_schema=ExportCsvInput,
        ),
        StructuredTool.from_function(
            name="export_json",
            description="Export a value at a path to a new JSON file.",
            func=lambda alias, path, output_path, indent=2: _safe(
                export_mod.export_json, alias, path, output_path, indent
            ),
            args_schema=ExportJsonInput,
        ),
        # ---- Introspect ----
        StructuredTool.from_function(
            name="distinct_paths",
            description=(
                "List every unique leaf path in a JSON document with types. "
                "Essential for understanding unknown/complex documents."
            ),
            func=lambda alias, path="", max_depth=10, sample_array_items=5: _safe(
                introspect_mod.distinct_paths, alias, path, max_depth, sample_array_items
            ),
            args_schema=DistinctPathsInput,
        ),
    ]

    return tools
