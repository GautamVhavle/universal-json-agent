# JSON Agent

An MCP server + REST API for parsing, querying, and analysing JSON files using natural language.

Two ways to use it:

| Mode | How it works | Best for |
|------|-------------|----------|
| **MCP Server** | Connects to GitHub Copilot (VS Code) via stdio | Chat-driven JSON exploration in your editor |
| **Web API** | FastAPI server powered by LangChain + OpenRouter | Programmatic access, integrations, frontends |

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [1. MCP Server (GitHub Copilot)](#1-mcp-server-github-copilot)
- [2. Web API Server (FastAPI + LangChain)](#2-web-api-server-fastapi--langchain)
- [Tools Reference](#tools-reference)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Configuration](#configuration)

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **VS Code** with [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) (for MCP mode)
- **OpenRouter API key** (for Web API mode only) — get one at [openrouter.ai/keys](https://openrouter.ai/keys)

---

## Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd JSON-Agent

# Install core dependencies
uv sync

# Install dev dependencies (for running tests)
uv sync --extra dev

# The server is auto-discovered by VS Code via .vscode/mcp.json
# Open Copilot Chat and ask questions about your JSON files!
```

If you also want to use the **Web API** (FastAPI + LangChain):

```bash
# Install web server dependencies
uv pip install -r web/requirements.txt

# Create your .env file
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

---

## 1. MCP Server (GitHub Copilot)

The MCP server connects directly to GitHub Copilot Chat in VS Code. No API key needed — Copilot handles the LLM.

### Setup

The workspace already includes `.vscode/mcp.json` which auto-registers the server:

```json
{
  "servers": {
    "json-agent": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "${workspaceFolder}", "run", "python", "-m", "json_agent.server"]
    }
  }
}
```

Just open the project in VS Code and start a Copilot Chat. The 26 tools are available automatically.

### Usage

In Copilot Chat, ask natural-language questions about any JSON file:

```
Load the file sample.json and tell me what's in it
How many missions are there?
What are the codenames of all missions with status "in_progress"?
What's the total budget across all missions?
Show me the structure of the first mission object
Sort missions by budget descending
Get all personnel names using JSONPath
```

---

## 2. Web API Server (FastAPI + LangChain)

A standalone REST API that accepts a JSON file + a natural language question and returns the answer. An LLM agent (via OpenRouter) autonomously picks and chains the tools to answer your query.

### Setup

```bash
# 1. Install web dependencies
uv pip install -r web/requirements.txt

# 2. Create your environment file
cp .env.example .env
```

Edit `.env` with your OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini        # optional, any OpenRouter model
```

### Start the server

```bash
uv run python -m web.run --port 8000
```

Options:
- `--host` — bind address (default: `0.0.0.0`)
- `--port` — port number (default: `8000`)
- `--reload` — auto-reload on file changes (development)

### Endpoints

#### `GET /health`

Health check.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "model": "openai/gpt-4o-mini",
  "agent_ready": true
}
```

#### `POST /query` — Upload a file + ask a question

```bash
curl -X POST http://localhost:8000/query \
  -F "file=@data.json" \
  -F "question=How many users are there and what are their names?"
```

#### `POST /query/path` — Reference a file on disk

```bash
curl -X POST http://localhost:8000/query/path \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/absolute/path/to/data.json",
    "question": "What is the total revenue?"
  }'
```

### Response format

Both query endpoints return:

```json
{
  "answer": "There are 7 missions. The total budget is $36.7 billion...",
  "steps": [
    { "tool": "load_json", "output": "Loaded 'data' — object, 4 keys" },
    { "tool": "get_structure", "output": "object (4 keys)..." },
    { "tool": "sum_values", "output": "Sum: 36720000000.5" }
  ]
}
```

### Interactive docs

With the server running, open [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

---

## Tools Reference

All 26 tools are available in both MCP and Web API modes.

### Load & Manage
| Tool | Description |
|------|-------------|
| `load_json` | Load a JSON file from disk into memory |
| `list_loaded` | Show all loaded documents with metadata |
| `unload_json` | Remove a document from memory |

### Explore
| Tool | Description |
|------|-------------|
| `get_keys` | Get keys (object) or index range (array) at a path |
| `get_value` | Retrieve the value at a path (auto-truncated at 10KB) |
| `get_type` | Return the JSON type at a path |
| `get_structure` | Schema-like skeleton showing keys and types |

### Query
| Tool | Description |
|------|-------------|
| `jsonpath_query` | Execute a JSONPath expression (e.g. `$.users[*].email`) |
| `filter_objects` | Filter arrays by a field condition (eq, gt, lt, contains, regex…) |
| `search_text` | Recursively search all string values for a substring or regex |

### Aggregate
| Tool | Description |
|------|-------------|
| `count` | Count items in an array or keys in an object |
| `sum_values` | Sum numeric values at a JSONPath |
| `min_max` | Get min and max of numeric values |
| `unique_values` | Get distinct values at a JSONPath |
| `value_counts` | Frequency table of values (like pandas `value_counts()`) |

### Transform
| Tool | Description |
|------|-------------|
| `flatten` | Flatten nested objects into dot-notation key-value pairs |
| `pick_fields` | Project specific fields from array objects |
| `group_by` | Group array objects by a field value |
| `sort_by` | Sort array objects by a field |
| `sample` | Return N random items from an array |

### Analytics
| Tool | Description |
|------|-------------|
| `describe` | Statistical summary (count, mean, std, min, max, percentiles) |
| `multi_filter` | Filter with multiple AND/OR conditions |
| `compare` | Diff two JSON values — added/removed keys, type/value changes |

### Export
| Tool | Description |
|------|-------------|
| `export_csv` | Export an array of objects to CSV |
| `export_json` | Export a value at a path to a new JSON file |

### Introspect
| Tool | Description |
|------|-------------|
| `distinct_paths` | List every unique leaf path in a document with types |

---

## Project Structure

```
JSON-Agent/
├── src/json_agent/               # Core MCP server (no LLM dependency)
│   ├── server.py                 # MCP entry point — registers all 26 tools
│   ├── store.py                  # In-memory document store with metadata
│   ├── tools/
│   │   ├── load.py               # load_json, list_loaded, unload_json
│   │   ├── explore.py            # get_keys, get_value, get_type, get_structure
│   │   ├── query.py              # jsonpath_query, filter_objects, search_text
│   │   ├── aggregate.py          # count, sum_values, min_max, unique_values, value_counts
│   │   ├── transform.py          # flatten, pick_fields, group_by, sort_by, sample
│   │   ├── stats.py              # describe
│   │   ├── advanced_query.py     # multi_filter, compare
│   │   ├── export.py             # export_csv, export_json
│   │   └── introspect.py         # distinct_paths
│   └── utils/
│       ├── path_resolver.py      # Dot/bracket path navigation
│       └── truncation.py         # Smart output capping
│
├── web/                          # FastAPI + LangChain web server
│   ├── app.py                    # FastAPI app with /health, /query, /query/path
│   ├── agent.py                  # LangGraph ReAct agent (per-request isolation)
│   ├── tools.py                  # 26 LangChain StructuredTool wrappers
│   ├── config.py                 # Settings from environment variables
│   ├── run.py                    # Entry point (uvicorn)
│   └── requirements.txt          # Extra dependencies for the web server
│
├── tests/                        # 489 tests
│   ├── conftest.py
│   ├── test_store.py
│   ├── test_path_resolver.py
│   ├── test_truncation.py
│   ├── test_server.py
│   └── test_tools/               # One test file per tool module
│
├── .vscode/mcp.json              # Auto-registers MCP server in VS Code
├── .env.example                  # Template for environment variables
├── pyproject.toml                # Project metadata and dependencies
└── sample.json                   # Example JSON file for testing
```

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_tools/test_aggregate.py

# Run tests matching a name pattern
uv run pytest -k "test_filter"
```

---

## Configuration

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes (web only) | — | Your OpenRouter API key |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o-mini` | Any model from [openrouter.ai/models](https://openrouter.ai/models) |

### MCP server config

The MCP server requires no configuration. It's registered via `.vscode/mcp.json` and uses stdio transport.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| MCP server not appearing in Copilot | Make sure `.vscode/mcp.json` exists and the workspace is open. Restart VS Code. |
| "No document loaded" errors | Call `load_json` first before querying. |
| Truncated output | Large results are capped at ~10KB. Use specific paths or filters to narrow results. |
| `OPENROUTER_API_KEY not set` | Create a `.env` file from `.env.example` and add your key. |
| 429 Too Many Requests | You're rate-limited by the model provider. Wait a moment or switch to a different model. |
| Import errors in web server | Run `uv pip install -r web/requirements.txt` to install web dependencies. |
