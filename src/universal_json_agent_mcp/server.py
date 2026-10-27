"""
MCP Server Entry Point — registers all tools and starts the stdio transport.

This module creates the shared MCP instance and JSONStore, then delegates
tool registration to the ``registrations`` package.  All business logic
lives in the ``tools/`` and ``store`` modules (Dependency Inversion Principle).

Every tool function created by the registrations is injected into this
module's namespace so that ``server.load_json``, ``server.store``, etc.
remain accessible for tests and external consumers.
"""

from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP

from universal_json_agent_mcp.registrations import register_all
from universal_json_agent_mcp.store import JSONStore

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
    "universal-json-agent",
    instructions=(
        "Advanced JSON parsing agent. Call load_json before any other tool. "
        "Use get_structure or distinct_paths to learn the shape, then answer "
        "with one bulk call: jsonpath_query (for example $.items[*].field), "
        "pick_fields, filter_objects, or an aggregate tool "
        "(count, sum_values, min_max, value_counts, describe). "
        "Do not loop get_value over array indexes. "
        "Large results are truncated; narrow the path when output is cut off. "
        "Pass replace=true to load_json to reload an alias already in memory."
    ),
)

# ---------------------------------------------------------------------------
# Register every tool category and expose the wrapper functions as
# module-level attributes (e.g. server.load_json, server.get_keys, …).
# ---------------------------------------------------------------------------

globals().update(register_all(mcp, store))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the MCP server with stdio transport."""
    logger.info("Starting JSON Agent MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
