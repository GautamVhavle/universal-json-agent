# Plan 1 — MCP JSON Parser Agent for VS Code (GitHub Copilot)

> **Goal:** Build a production-quality MCP (Model Context Protocol) server in Python that exposes advanced JSON parsing tools to GitHub Copilot in VS Code. Users can load any JSON file — no matter how large or nested — and ask natural-language questions about its structure, values, keys, counts, filtering, searching, and more.

---

## Research & Architecture Notes

### What is MCP?

MCP (Model Context Protocol) is an open standard that lets AI assistants (like GitHub Copilot) call external **tools**, access **resources**, and use **prompt templates** via a lightweight JSON-RPC 2.0 protocol. An MCP server is a small process that:

1. Communicates over **stdio** (stdin/stdout) using JSON-RPC 2.0 messages.
2. Advertises a set of **tools** with typed input/output schemas.
3. Gets invoked by the AI agent whenever it decides a tool is relevant to the user's query.

### Why MCP for JSON Parsing?

- Copilot can read small files on its own, but **large JSON files** (MBs/GBs) overwhelm context windows.
- An MCP server can load, index, and query the JSON **outside** the LLM context — returning only the precise answer.
- Tools give the LLM structured interfaces (JSON Schema) so it knows exactly what parameters to pass.

### Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Language | Python 3.11+ | Rich JSON / data ecosystem |
| MCP SDK | `mcp[cli]` (FastMCP) | Official SDK, decorator-based, auto schema generation |
| Transport | stdio | Local VS Code integration, zero network overhead |
| JSON engine | `ijson` (streaming) + stdlib `json` | Handle both huge & normal files efficiently |
| Path queries | JSONPath (`jsonpath-ng`) | Industry-standard deep query syntax |
| Schema | Pydantic v2 | Typed tool params & structured outputs |
| Package mgr | `uv` | Fast, reproducible Python environments |

### Key Design Principles (SOLID)

| Principle | Application |
|-----------|------------|
| **S** — Single Responsibility | Each tool does exactly one thing (load, query, count, search, etc.) |
| **O** — Open/Closed | New tools are added by writing a new function + decorator — no changes to existing code |
| **L** — Liskov Substitution | All tool functions follow the same async signature contract |
| **I** — Interface Segregation | Tools are small, focused; the LLM picks only the ones it needs |
| **D** — Dependency Inversion | Core logic depends on abstractions (JSONStore protocol), not concrete implementations |

---

## Phase 1 — Foundation & Core Tools

**Objective:** Scaffold the project, set up the MCP server skeleton, and implement the fundamental tools that let a user load and explore any JSON file.

### 1.1 Project Scaffold

```
JSON-Agent/
├── plan1.md                  # This plan
├── pyproject.toml            # Project metadata & dependencies
├── README.md                 # Usage docs
├── .vscode/
│   └── mcp.json              # VS Code MCP server registration
├── src/
│   └── json_agent/
│       ├── __init__.py
│       ├── server.py          # MCP server entry point (FastMCP)
│       ├── store.py           # JSON document store (load, cache, manage)
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── load.py        # load_json, list_loaded, unload_json
│       │   ├── explore.py     # get_keys, get_value, get_type, get_structure
│       │   ├── query.py       # jsonpath_query, filter_objects, search_text
│       │   ├── aggregate.py   # count, sum_values, unique_values, min_max
│       │   └── transform.py   # flatten, pick_fields, group_by
│       └── utils/
│           ├── __init__.py
│           ├── path_resolver.py   # Resolve JSONPath / dot-notation paths
│           └── truncation.py      # Smart truncation for large outputs
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_store.py
    └── test_tools/
        ├── test_load.py
        ├── test_explore.py
        ├── test_query.py
        ├── test_aggregate.py
        └── test_transform.py
```

### 1.2 Core Components

#### `store.py` — JSON Document Store

- **In-memory cache** keyed by a user-friendly alias (e.g. `"orders"`) or file path.
- `load(file_path, alias)` → parses JSON, stores it, returns summary stats (type, top-level key count, size).
- `get(alias)` → returns the loaded document.
- `unload(alias)` → frees memory.
- `list_loaded()` → shows all loaded documents with metadata.
- For **large files** (>50 MB): use `ijson` streaming parser to avoid loading the whole file at once when only partial data is needed.

#### `tools/load.py` — Load & Manage Tools

| Tool | Description |
|------|-------------|
| `load_json` | Load a JSON file from disk into the store. Returns a summary (root type, key count / array length, file size). |
| `list_loaded` | Show all currently loaded JSON documents. |
| `unload_json` | Remove a document from memory. |

#### `tools/explore.py` — Structure Exploration Tools

| Tool | Description |
|------|-------------|
| `get_keys` | Get all keys at a given path (e.g. root, `data.users[0]`). |
| `get_value` | Retrieve the value at an exact path. Auto-truncates large outputs. |
| `get_type` | Return the JSON type (object, array, string, number, boolean, null) at a path. |
| `get_structure` | Return a schema-like skeleton of the JSON (keys + types, up to a configurable depth). |

### 1.3 Deliverables

- [x] `pyproject.toml` with all dependencies
- [x] MCP server boots and registers tools via stdio
- [x] `.vscode/mcp.json` configured — Copilot discovers the server
- [x] `load_json`, `list_loaded`, `unload_json` working
- [x] `get_keys`, `get_value`, `get_type`, `get_structure` working
- [x] Unit tests for store and all Phase 1 tools

---

## Phase 2 — Advanced Querying & Aggregation

**Objective:** Add powerful query and aggregation tools so the LLM can answer complex questions about the JSON data without pulling the entire file into context.

### 2.1 Query Tools — `tools/query.py`

| Tool | Description | Example User Question |
|------|-------------|----------------------|
| `jsonpath_query` | Execute a JSONPath expression against a loaded document. | *"Get all user emails"* → `$.users[*].email` |
| `filter_objects` | Filter an array of objects by field conditions (eq, gt, lt, contains, regex). | *"Which orders have status 'shipped'?"* |
| `search_text` | Recursively search all string values for a substring or regex match. Returns paths + values. | *"Where does 'error' appear in the config?"* |

### 2.2 Aggregation Tools — `tools/aggregate.py`

| Tool | Description | Example User Question |
|------|-------------|----------------------|
| `count` | Count items in an array, or count keys in an object, at a given path. | *"How many products are there?"* |
| `sum_values` | Sum numeric values at a path (e.g. `$.orders[*].total`). | *"What's the total revenue?"* |
| `min_max` | Get the min and max of numeric values at a path. | *"What's the cheapest product?"* |
| `unique_values` | Get distinct values at a path. | *"What are all the unique categories?"* |
| `value_counts` | Count occurrences of each distinct value (like pandas `value_counts`). | *"How many orders per status?"* |

### 2.3 Deliverables

- [x] JSONPath query engine integrated (`jsonpath-ng`)
- [x] `filter_objects` with composable conditions
- [x] `search_text` with recursive traversal
- [x] All 5 aggregation tools working
- [x] Smart output truncation (large results return first N items + total count)
- [x] Unit tests for all Phase 2 tools

---

## Phase 3 — Transform, Polish & Production Readiness

**Objective:** Add transformation tools for reshaping data, harden edge cases, add streaming support for huge files, and ensure the server is robust for daily use.

### 3.1 Transform Tools — `tools/transform.py`

| Tool | Description | Example User Question |
|------|-------------|----------------------|
| `flatten` | Flatten a nested JSON object into dot-notation key-value pairs. | *"Give me a flat view of the config"* |
| `pick_fields` | Extract specific fields from each object in an array (projection). | *"Show me just name and price for all products"* |
| `group_by` | Group an array of objects by a field value. | *"Group orders by customer_id"* |
| `sort_by` | Sort an array of objects by a field. | *"Sort products by price descending"* |
| `sample` | Return N random items from a large array. | *"Show me 5 sample records"* |

### 3.2 Production Hardening

| Area | Action |
|------|--------|
| **Error handling** | Graceful errors for: file not found, invalid JSON, path not found, out-of-memory. Every tool returns a clear error message — never a stack trace. |
| **Large file streaming** | For files >50 MB, use `ijson` to stream-parse and answer queries without loading the full file. |
| **Output truncation** | All tools enforce a max output size (configurable, default 10 KB text). Arrays are sliced with a `"... and N more items"` indicator. |
| **Memory management** | `unload_json` clears references; `list_loaded` shows approximate memory usage per document. |
| **Logging** | All logs go to `stderr` (never `stdout` — that's the JSON-RPC channel). Structured logging with levels. |
| **Type safety** | Full type hints on every function. Pydantic models for all tool inputs. |
| **Documentation** | `README.md` with setup instructions, tool catalog, example queries, and troubleshooting. |

### 3.3 Deliverables

- [x] All 5 transform tools working
- [x] Streaming support for large files via `ijson`
- [x] Output truncation with configurable limits
- [x] Comprehensive error handling (no unhandled exceptions)
- [x] Logging to stderr with configurable verbosity
- [x] `README.md` with full setup & usage guide
- [x] All tests passing
- [x] End-to-end manual test: load a 100 MB+ JSON, ask complex questions via Copilot

---

## Tool Catalog Summary (All Phases)

| # | Tool | Phase | Category |
|---|------|-------|----------|
| 1 | `load_json` | 1 | Load |
| 2 | `list_loaded` | 1 | Load |
| 3 | `unload_json` | 1 | Load |
| 4 | `get_keys` | 1 | Explore |
| 5 | `get_value` | 1 | Explore |
| 6 | `get_type` | 1 | Explore |
| 7 | `get_structure` | 1 | Explore |
| 8 | `jsonpath_query` | 2 | Query |
| 9 | `filter_objects` | 2 | Query |
| 10 | `search_text` | 2 | Query |
| 11 | `count` | 2 | Aggregate |
| 12 | `sum_values` | 2 | Aggregate |
| 13 | `min_max` | 2 | Aggregate |
| 14 | `unique_values` | 2 | Aggregate |
| 15 | `value_counts` | 2 | Aggregate |
| 16 | `flatten` | 3 | Transform |
| 17 | `pick_fields` | 3 | Transform |
| 18 | `group_by` | 3 | Transform |
| 19 | `sort_by` | 3 | Transform |
| 20 | `sample` | 3 | Transform |

---

## How It All Connects

```
┌──────────────────────────────────────────────────────┐
│                   VS Code + Copilot                   │
│                                                      │
│  User: "How many orders have status 'delivered'?"    │
│                        │                             │
│                        ▼                             │
│  Copilot Agent ──► picks tools: load_json, count,   │
│                    filter_objects                     │
│                        │                             │
│                        ▼                             │
│  ┌─────────── stdio (JSON-RPC 2.0) ──────────────┐  │
│  │                                                │  │
│  │           MCP JSON Agent Server                │  │
│  │                                                │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │  Store   │  │  Tools   │  │   Utils      │  │  │
│  │  │ (cache)  │◄─┤ (20 fns) │  │ (truncation, │  │  │
│  │  │         │  │          │  │  paths, etc) │  │  │
│  │  └─────────┘  └──────────┘  └──────────────┘  │  │
│  │                                                │  │
│  └────────────────────────────────────────────────┘  │
│                        │                             │
│                        ▼                             │
│  Copilot: "There are 42 orders with status           │
│            'delivered' out of 150 total."             │
└──────────────────────────────────────────────────────┘
```

---

## Quick Start (After Implementation)

```bash
# 1. Install dependencies
cd JSON-Agent && uv sync

# 2. VS Code auto-discovers the server via .vscode/mcp.json

# 3. In Copilot Chat, ask:
#    "Load the file data/orders.json and tell me how many orders are pending"
```

---

*This plan covers only the MCP server for VS Code. FastAPI endpoint and LangChain agent integration will be planned in `plan2.md`.*
