<div align="center">

<img src="assets/logo.png" alt="Universal JSON Agent MCP" width="200" />

# Universal JSON Agent MCP

**The Swiss Army knife for JSON — load, query, aggregate, transform, and export any JSON file from your AI editor.**

[![PyPI version](https://img.shields.io/pypi/v/universal-json-agent-mcp?color=blue&label=PyPI)](https://pypi.org/project/universal-json-agent-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/universal-json-agent-mcp)](https://pypi.org/project/universal-json-agent-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/GautamVhavle/universal-json-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/GautamVhavle/universal-json-agent/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-489%20passed-brightgreen)]()

```bash
pip install universal-json-agent-mcp
```

[Getting Started](#-getting-started) · [Tools](#-tools-reference-26) · [Web API](#-web-api-server) · [Contributing](#-development)

</div>

---

## What is this?

An [MCP server](https://modelcontextprotocol.io/) that gives AI assistants **26 powerful tools** to work with JSON files. Load any JSON file and talk to it using natural language — filter, aggregate, transform, export, and more.

Works with **GitHub Copilot**, **Claude Desktop**, **Cursor**, and any MCP-compatible client.

### What can it do?

```
> Load data/missions.json and tell me what's in it
> How many missions have status "in_progress"?
> What's the total budget across all missions?
> Sort missions by priority and show their codenames
> Export the results to CSV
```

Your AI assistant calls the right tools behind the scenes — no code required.

---

## ⚡ Getting Started

### Install

```bash
# Using pip
pip install universal-json-agent-mcp

# Using uv
uv add universal-json-agent-mcp

# Zero-install with uvx
uvx universal-json-agent-mcp
```

### Connect to your editor

<details>
<summary><b>VS Code / GitHub Copilot</b></summary>

Add to `.vscode/mcp.json`:

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

**Or zero-install with uvx:**

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

</details>

<details>
<summary><b>Claude Desktop</b></summary>

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

</details>

<details>
<summary><b>Cursor</b></summary>

Add to your MCP settings:

```json
{
  "mcpServers": {
    "universal-json-agent": {
      "command": "universal-json-agent-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>Run standalone (CLI)</b></summary>

```bash
universal-json-agent-mcp
# or
python -m universal_json_agent_mcp
```

Starts on **stdio** — pipe any MCP client into it.

</details>

---

## 🛠 Tools Reference (26)

### 📂 Load & Manage

| Tool | Description |
|:-----|:------------|
| `load_json` | Load a JSON file from disk into memory |
| `list_loaded` | Show all loaded documents with metadata |
| `unload_json` | Remove a document from memory |

### 🔍 Explore

| Tool | Description |
|:-----|:------------|
| `get_keys` | Get keys of an object or index range of an array |
| `get_value` | Retrieve the value at a path (auto-truncated at 10 KB) |
| `get_type` | Return the JSON type at a path |
| `get_structure` | Schema-like skeleton showing keys and types |

### 🎯 Query

| Tool | Description |
|:-----|:------------|
| `jsonpath_query` | Run a JSONPath expression — `$.missions[*].codename` |
| `filter_objects` | Filter arrays by condition (`eq`, `gt`, `lt`, `contains`, `regex`…) |
| `search_text` | Recursive full-text search across all string values |

### 📊 Aggregate

| Tool | Description |
|:-----|:------------|
| `count` | Count items in an array or keys in an object |
| `sum_values` | Sum numeric values at a JSONPath |
| `min_max` | Get min and max of numeric values |
| `unique_values` | Distinct values at a JSONPath |
| `value_counts` | Frequency table (like pandas `value_counts()`) |

### 🔄 Transform

| Tool | Description |
|:-----|:------------|
| `flatten` | Flatten nested objects into dot-notation key-value pairs |
| `pick_fields` | Project specific fields from array objects |
| `group_by` | Group array objects by a field value |
| `sort_by` | Sort array objects by a field |
| `sample` | Return N random items from an array |

### 📈 Analytics

| Tool | Description |
|:-----|:------------|
| `describe` | Statistical summary — count, mean, std, min, max, percentiles |
| `multi_filter` | Filter with multiple AND/OR conditions |
| `compare` | Diff two JSON values — added/removed keys, type & value changes |

### 💾 Export

| Tool | Description |
|:-----|:------------|
| `export_csv` | Export an array of objects to a CSV file |
| `export_json` | Export a value at a path to a new JSON file |

### 🗺 Introspect

| Tool | Description |
|:-----|:------------|
| `distinct_paths` | List every unique leaf path in a document with types |

---

## 🌐 Web API Server

The repo includes an optional **FastAPI + LangChain** web server that wraps all 26 tools behind a REST API — useful for integrations, dashboards, or non-MCP clients.

```bash
# Install web dependencies
pip install -r web/requirements.txt

# Configure
cp .env.example .env   # add your OpenRouter API key

# Run
python -m web.run --port 8000
```

### Endpoints

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/health` | Health check |
| `POST` | `/query` | Upload a JSON file + ask a question |
| `POST` | `/query/path` | Point to a file on disk + ask a question |
| `GET` | `/docs` | Interactive Swagger UI |

### Example

```bash
curl -X POST http://localhost:8000/query \
  -F "file=@data/missions.json" \
  -F "query=What's the total budget?"
```

### Environment variables

| Variable | Required | Default | Description |
|:---------|:--------:|:--------|:------------|
| `OPENROUTER_API_KEY` | Yes | — | Your [OpenRouter](https://openrouter.ai/) API key |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o-mini` | Any model from [openrouter.ai/models](https://openrouter.ai/models) |

---

## 🏗 Project Structure

```
universal-json-agent/
│
├── src/universal_json_agent_mcp/    # 📦 Installable MCP server
│   ├── server.py                    #    Entry point — registers all 26 tools
│   ├── store.py                     #    In-memory document store
│   ├── tools/
│   │   ├── load.py                  #    load, list, unload
│   │   ├── explore.py               #    keys, value, type, structure
│   │   ├── query.py                 #    jsonpath, filter, search
│   │   ├── aggregate.py             #    count, sum, min/max, unique, value_counts
│   │   ├── transform.py             #    flatten, pick, group, sort, sample
│   │   ├── stats.py                 #    describe
│   │   ├── advanced_query.py        #    multi_filter, compare
│   │   ├── export.py                #    CSV & JSON export
│   │   └── introspect.py            #    distinct_paths
│   └── utils/
│       ├── path_resolver.py         #    Dot/bracket path navigation
│       └── truncation.py            #    Smart output truncation
│
├── web/                             # 🌐 FastAPI + LangChain web server
├── tests/                           # ✅ 489 tests
├── pyproject.toml
├── LICENSE                          # MIT
└── README.md
```

---

## 🧑‍💻 Development

```bash
# Clone
git clone https://github.com/GautamVhavle/universal-json-agent.git
cd universal-json-agent

# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_tools/test_aggregate.py

# Run tests matching a pattern
uv run pytest -k "test_filter"
```

### Releasing a new version

1. Commit your changes and push to `main`
2. Create a git tag: `git tag v0.2.0 -m "v0.2.0"`
3. Push the tag: `git push origin v0.2.0`
4. [Create a GitHub Release](https://github.com/GautamVhavle/universal-json-agent/releases/new) for the tag
5. CI automatically runs tests, builds, and publishes to PyPI

---

## ❓ Troubleshooting

<details>
<summary><b>MCP server not appearing in Copilot / Claude / Cursor</b></summary>

Make sure the config file exists (`.vscode/mcp.json` for VS Code) and restart the editor. Verify the command is on your PATH: `which universal-json-agent-mcp`

</details>

<details>
<summary><b>"No document loaded" errors</b></summary>

You need to load a file first. Ask your AI: *"Load the file data/example.json"* — this calls `load_json` behind the scenes.

</details>

<details>
<summary><b>Truncated output</b></summary>

Large results are capped at ~10 KB. Use more specific paths, filters, or `pick_fields` to narrow results.

</details>

<details>
<summary><b>429 Too Many Requests (web server)</b></summary>

The model provider is rate-limiting you. Wait a moment or switch to a different model in `.env`.

</details>

<details>
<summary><b>Import errors in web server</b></summary>

Install the web dependencies: `pip install -r web/requirements.txt`

</details>

---

## 📄 License

[MIT](LICENSE) — use it however you want.
