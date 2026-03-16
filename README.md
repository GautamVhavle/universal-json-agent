# Universal JSON Agent MCP

An MCP server for parsing, querying, and analysing JSON files — installable from PyPI.

```bash
pip install universal-json-agent-mcp
```

26 tools for loading, exploring, querying, aggregating, transforming, and exporting JSON — usable from **GitHub Copilot**, **Claude Desktop**, **Cursor**, or any MCP client.

---

## Table of Contents

- [Quick Start](#quick-start)
- [MCP Client Configuration](#mcp-client-configuration)
- [Web API Server (Optional)](#web-api-server-optional)
- [Tools Reference](#tools-reference)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Install

```bash
pip install universal-json-agent-mcp
# or
uv add universal-json-agent-mcp
```

### Run

```bash
universal-json-agent-mcp
# or
python -m universal_json_agent_mcp
```

The server starts on **stdio** — connect any MCP client to it.

---

## MCP Client Configuration

### VS Code / GitHub Copilot

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "universal-json-agent": {
      "type": "stdio",
      "command": "universal-json-agent-mcp"
    }
  }
}
```

Or use `uvx` (no install needed):

```json
{
  "servers": {
    "universal-json-agent": {
      "type": "stdio",
      "command": "uvx",
      "args": ["universal-json-agent-mcp"]
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "universal-json-agent": {
      "command": "universal-json-agent-mcp"
    }
  }
}
```

### Cursor

Add to Cursor's MCP settings:

```json
{
  "mcpServers": {
    "universal-json-agent": {
      "command": "universal-json-agent-mcp"
    }
  }
}
```

### Example prompts

Once connected, ask natural-language questions in your AI chat:

```
Load the file data/orders.json and tell me what's in it
How many missions are there?
What are the codenames of all missions with status "in_progress"?
What's the total budget across all missions?
Sort missions by budget descending
Get all personnel names using JSONPath
```

---

## Web API Server (Optional)

The repo also includes a standalone FastAPI + LangChain web server that wraps the same 26 tools behind a REST API. See [web/](web/) for details.

```bash
# Install web dependencies
pip install -r web/requirements.txt

# Set your OpenRouter API key
cp .env.example .env   # then edit .env

# Start the server
python -m web.run --port 8000
```

Endpoints: `GET /health`, `POST /query` (file upload), `POST /query/path` (file on disk). Swagger UI at `/docs`.

---

## Tools Reference

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

## Development

```bash
# Clone and install for development
git clone https://github.com/GautamVhavle/universal-json-agent.git
cd universal-json-agent
uv sync --extra dev
```

---

## Project Structure

```
universal-json-agent/
├── src/universal_json_agent_mcp/     # Installable MCP server package
│   ├── __init__.py
│   ├── __main__.py                   # python -m universal_json_agent_mcp
│   ├── server.py                     # MCP entry point — registers all 26 tools
│   ├── store.py                      # In-memory document store with metadata
│   ├── tools/
│   │   ├── load.py                   # load_json, list_loaded, unload_json
│   │   ├── explore.py                # get_keys, get_value, get_type, get_structure
│   │   ├── query.py                  # jsonpath_query, filter_objects, search_text
│   │   ├── aggregate.py              # count, sum_values, min_max, unique_values, value_counts
│   │   ├── transform.py              # flatten, pick_fields, group_by, sort_by, sample
│   │   ├── stats.py                  # describe
│   │   ├── advanced_query.py         # multi_filter, compare
│   │   ├── export.py                 # export_csv, export_json
│   │   └── introspect.py             # distinct_paths
│   └── utils/
│       ├── path_resolver.py          # Dot/bracket path navigation
│       └── truncation.py             # Smart output capping
│
├── web/                              # Optional FastAPI + LangChain web server
├── tests/                            # 489 tests
├── pyproject.toml                    # Package metadata (PyPI)
├── LICENSE                           # MIT
└── sample.json                       # Example JSON file
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
