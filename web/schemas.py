"""
Pydantic input schemas for LangChain tool wrappers.

Each schema maps to one tool in ``tools.build_tools`` and defines the
parameters the LLM agent can supply.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


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
