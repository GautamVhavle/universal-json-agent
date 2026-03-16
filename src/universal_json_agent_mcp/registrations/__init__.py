"""
MCP Tool Registrations — each sub-module registers one category of tools.

The ``register_all`` function wires every tool onto the shared MCP server
instance so ``server.py`` stays small and focused.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.store import JSONStore
from universal_json_agent_mcp.registrations import (
    load,
    explore,
    query,
    aggregate,
    transform,
    stats,
    advanced_query,
    export,
    introspect,
)

_MODULES = [
    load,
    explore,
    query,
    aggregate,
    transform,
    stats,
    advanced_query,
    export,
    introspect,
]


def register_all(mcp: FastMCP, store: JSONStore) -> dict:
    """Register every tool category onto *mcp*.

    Returns:
        A dict mapping tool names to their wrapper functions, so the
        caller can expose them as module-level attributes.
    """
    all_tools: dict = {}
    for module in _MODULES:
        all_tools.update(module.register(mcp, store))
    return all_tools
