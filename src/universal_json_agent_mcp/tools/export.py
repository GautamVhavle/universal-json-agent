"""
Export Tools — save JSON data to external formats (CSV, filtered JSON).

Allows the LLM to produce downloadable artefacts from query results,
which is essential for handing data off to external tools like Excel,
pandas, or other pipelines.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.utils.path_resolver import resolve_path


def export_csv(
    store: JSONStore,
    alias: str,
    path: str,
    output_path: str,
    fields: list[str] | None = None,
) -> str:
    """
    Export an array of objects to a CSV file.

    If *fields* is omitted, the union of all keys across all objects is used
    (sorted alphabetically).

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the array of objects to export.
        output_path: Absolute or relative path for the output CSV file.
        fields: Optional list of field names to include as columns.
                If omitted, all fields found across all objects are used.

    Returns:
        A confirmation message with the file path and row/column counts.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    if not isinstance(target, list):
        raise TypeError(
            f"Value at path '{path}' is {type(target).__name__}, expected an array."
        )

    # Filter to dicts only
    rows = [item for item in target if isinstance(item, dict)]
    if not rows:
        return f"No object rows found at path '{path}'. Nothing to export."

    # Determine columns
    if fields:
        columns = fields
    else:
        seen: dict[str, None] = {}
        for row in rows:
            for key in row:
                if key not in seen:
                    seen[key] = None
        columns = list(seen.keys())

    # Resolve output path
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Write CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            # Serialize non-scalar values to JSON strings
            sanitized = {}
            for col in columns:
                val = row.get(col)
                if isinstance(val, (dict, list)):
                    sanitized[col] = json.dumps(val, default=str)
                else:
                    sanitized[col] = val
            writer.writerow(sanitized)

    return (
        f"Exported {len(rows)} rows × {len(columns)} columns to:\n"
        f"  {output_path}"
    )


def export_json(
    store: JSONStore,
    alias: str,
    path: str,
    output_path: str,
    indent: int = 2,
) -> str:
    """
    Export a value at a given path to a new JSON file.

    Useful for saving a filtered subset or nested section of a large document.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the loaded document.
        path: Dot-notation path to the value to export. Empty means root.
        output_path: Absolute or relative path for the output JSON file.
        indent: JSON indentation level (default 2).

    Returns:
        A confirmation message with the file path and type/size info.
    """
    data = store.get(alias)
    target = resolve_path(data, path)

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(target, f, indent=indent, default=str, ensure_ascii=False)

    size_bytes = os.path.getsize(output_path)
    type_name = type(target).__name__

    return (
        f"Exported {type_name} at '{path or '$'}' to:\n"
        f"  {output_path}  ({_humanize(size_bytes)})"
    )


def _humanize(n: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if isinstance(n, float) else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
