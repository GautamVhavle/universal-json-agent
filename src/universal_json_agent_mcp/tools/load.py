"""
Load Tools — MCP tools for loading, listing, and unloading JSON documents.

Each function is registered as an MCP tool in server.py. Functions here
contain pure business logic and return plain strings (tool responses).
"""

from __future__ import annotations

from universal_json_agent_mcp.store import JSONStore


def load_json(store: JSONStore, file_path: str, alias: str | None = None) -> str:
    """
    Load a JSON file from disk into the in-memory store.

    Args:
        store: The shared JSONStore instance.
        file_path: Path to the JSON file on disk.
        alias: Optional friendly name (defaults to file stem).

    Returns:
        A human-readable summary of the loaded document.
    """
    meta = store.load(file_path, alias)
    return (
        f"Loaded '{meta.alias}' from {meta.file_path}\n"
        f"  Type : {meta.root_type}\n"
        f"  Size : {meta.file_size_human}\n"
        f"  Items: {meta.top_level_count}"
    )


def list_loaded(store: JSONStore) -> str:
    """
    List all currently loaded JSON documents with their metadata.

    Returns:
        A formatted table of loaded documents, or a message if none are loaded.
    """
    docs = store.list_loaded()
    if not docs:
        return "No documents loaded. Use load_json to load a file."

    lines = [f"{'Alias':<20} {'Type':<10} {'Items':<10} {'File Size':<12} {'Memory':<12} Path"]
    lines.append("-" * 90)
    for meta in docs:
        lines.append(
            f"{meta.alias:<20} {meta.root_type:<10} "
            f"{meta.top_level_count:<10} {meta.file_size_human:<12} "
            f"{meta.memory_human:<12} {meta.file_path}"
        )
    return "\n".join(lines)


def unload_json(store: JSONStore, alias: str) -> str:
    """
    Remove a loaded document from memory.

    Args:
        store: The shared JSONStore instance.
        alias: The alias of the document to unload.

    Returns:
        Confirmation message.
    """
    return store.unload(alias)
