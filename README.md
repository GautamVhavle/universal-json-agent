<div align="center">

<br />

<img src="https://raw.githubusercontent.com/GautamVhavle/universal-json-agent/main/assets/logo.png" alt="Universal JSON Agent MCP" width="180" />

<br />

# Universal JSON Agent MCP

### Talk to your JSON files using natural language.

**26 powerful tools** to load, explore, query, aggregate, transform, and export — right from your AI editor.

<br />

[![PyPI](https://img.shields.io/pypi/v/universal-json-agent-mcp?style=for-the-badge&logo=pypi&logoColor=white&color=0073b7)](https://pypi.org/project/universal-json-agent-mcp/)
&nbsp;
[![Python](https://img.shields.io/pypi/pyversions/universal-json-agent-mcp?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/universal-json-agent-mcp/)
&nbsp;
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
&nbsp;
[![CI](https://img.shields.io/github/actions/workflow/status/GautamVhavle/universal-json-agent/ci.yml?style=for-the-badge&logo=githubactions&logoColor=white&label=CI)](https://github.com/GautamVhavle/universal-json-agent/actions/workflows/ci.yml)
&nbsp;
[![Tests](https://img.shields.io/badge/tests-489%20passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)]()

<br />

```bash
uv tool install universal-json-agent-mcp
```

<br />

[**Getting Started**](#-getting-started) &nbsp;&middot;&nbsp; [**26 Tools**](#-tools-reference) &nbsp;&middot;&nbsp; [**Web Server**](#-web-server-subproject-web) &nbsp;&middot;&nbsp; [**Development**](#-development)

</div>

---

## Why?

Working with JSON shouldn't require writing a script every time. This tool lets you ask questions in plain English and get answers instantly.


```
You:  What's the total budget across all missions?

AI:   The total budget across all missions is $18,250,000,000.50
      (Used tools: load_json → sum_values)
```


### Supported Clients

<div align="center">

| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vscode/vscode-original.svg" width="28" /> | <img src="https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/claude-ai-icon.png" width="28" /> | <img src="https://www.cursor.com/favicon.ico" width="28" /> | Any MCP Client |
|:---:|:---:|:---:|:---:|
| VS Code / Copilot | Claude Desktop | Cursor | stdio |

</div>

---

## ⚡ Getting Started

### 1. Install

```bash
uv tool install universal-json-agent-mcp   # install CLI once
uvx universal-json-agent-mcp               # run without installing
uv add universal-json-agent-mcp            # add dependency to your project
```

### 2. Configure your editor

<details open>
<summary><b>VS Code / GitHub Copilot</b></summary>

Create `.vscode/mcp.json` in your workspace:

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

> **Tip:** Prefer zero-install? Use `"command": "uvx"` with `"args": ["universal-json-agent-mcp"]` instead.

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

Add to your Cursor MCP settings:

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
<summary><b>CLI / Standalone</b></summary>

```bash
universal-json-agent-mcp
# or
uv run python -m universal_json_agent_mcp
```

Starts on **stdio** — pipe any MCP client into it.

</details>

### 3. Start asking questions

```
> Load data/orders.json and tell me what's inside
> How many missions have status "in_progress"?
> What's the total budget across all missions?
> Filter personnel where role contains "engineer"
> Sort by priority descending and show codenames
> Export the filtered results to CSV
```

---

## 🛠 Tools Reference

### Load & Manage

| Tool | What it does |
|:-----|:-------------|
| `load_json` | Load a JSON file from disk into memory |
| `list_loaded` | List all loaded documents with metadata |
| `unload_json` | Remove a document from memory |

### Explore

| Tool | What it does |
|:-----|:-------------|
| `get_keys` | Get keys of an object or index range of an array |
| `get_value` | Retrieve value at a path (auto-truncated at 10 KB) |
| `get_type` | Return the JSON type at a path |
| `get_structure` | Schema-like skeleton — keys, types, nesting |

### Query

| Tool | What it does |
|:-----|:-------------|
| `jsonpath_query` | Run JSONPath — `$.missions[*].codename` |
| `filter_objects` | Filter by condition: `eq`, `gt`, `lt`, `contains`, `regex`… |
| `search_text` | Full-text search across all string values |

### Aggregate

| Tool | What it does |
|:-----|:-------------|
| `count` | Count items in an array or keys in an object |
| `sum_values` | Sum numeric values at a JSONPath |
| `min_max` | Get min and max of numeric values |
| `unique_values` | Distinct values at a JSONPath |
| `value_counts` | Frequency table — like pandas `value_counts()` |

### Transform

| Tool | What it does |
|:-----|:-------------|
| `flatten` | Flatten nested objects to dot-notation pairs |
| `pick_fields` | Project specific fields from array objects |
| `group_by` | Group objects by a field value |
| `sort_by` | Sort objects by a field |
| `sample` | Random N items from an array |

### Analytics

| Tool | What it does |
|:-----|:-------------|
| `describe` | Stats: count, mean, std, min, max, percentiles |
| `multi_filter` | Compound filters with AND / OR logic |
| `compare` | Diff two values — added, removed, changed keys |

### Export

| Tool | What it does |
|:-----|:-------------|
| `export_csv` | Export array of objects to CSV file |
| `export_json` | Export a value to a new JSON file |

### Introspect

| Tool | What it does |
|:-----|:-------------|
| `distinct_paths` | List every unique leaf path with types |

---

## 🌐 Web Server Subproject (web/)

> Optional **FastAPI + LangChain** web-server subproject inside this repo, wrapping all 26 root MCP tools for integrations, dashboards, or non-MCP workflows.

```bash
uv sync --extra web                       # install web deps with uv
cp .env.example .env                     # add your OpenRouter key
uv run python -m web.run --port 8000     # start server with uv
# open docs in browser: http://127.0.0.1:8000/docs
```

### Endpoints

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `GET` | `/health` | Health check |
| `POST` | `/query` | Upload JSON + ask a question |
| `POST` | `/query/path` | Reference a file on disk + ask a question |
| `GET` | `/docs` | Interactive Swagger UI |

### Example

```bash
curl -X POST http://localhost:8000/query \
  -F "file=@data/missions.json" \
  -F "query=What's the total budget?"
```

```json
{
  "answer": "The total budget across all missions is $18,250,000,000.50",
  "tools_used": ["load_json", "sum_values"]
}
```

### Configuration

| Variable | Required | Default | Description |
|:---------|:--------:|:--------|:------------|
| `OPENROUTER_API_KEY` | ✅ | — | Your [OpenRouter](https://openrouter.ai/) API key |
| `OPENROUTER_MODEL` | — | `openai/gpt-4o-mini` | Any [supported model](https://openrouter.ai/models) |

---

## 🧑‍💻 Development

```bash
git clone https://github.com/GautamVhavle/universal-json-agent.git
cd universal-json-agent
uv sync --extra dev
uv run pytest                            # 489 tests
```

<details>
<summary><b>More test commands</b></summary>

```bash
uv run pytest -v                                        # verbose
uv run pytest tests/test_tools/test_aggregate.py        # one file
uv run pytest -k "test_filter"                          # by pattern
```

</details>

### Releasing

Releases are fully automated via GitHub Actions:

```bash
git tag v0.3.0 -m "v0.3.0"
git push origin v0.3.0
```

Then [create a GitHub Release](https://github.com/GautamVhavle/universal-json-agent/releases/new) for the tag — CI runs tests, builds, and publishes to PyPI.

---

## Troubleshooting

<details>
<summary><b>MCP server not appearing in Copilot / Claude / Cursor</b></summary>

1. Verify the config file exists (`.vscode/mcp.json` for VS Code)
2. Check the command is on your PATH: `which universal-json-agent-mcp`
3. Restart the editor

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

The model provider is rate-limiting you. Wait a moment or switch to a different model in your `.env` file.

</details>

<details>
<summary><b>Import errors in web server</b></summary>

```bash
uv sync --extra web
```

</details>

---

<div align="center">

[MIT License](LICENSE) · Built with ❤️ by [Gautam Vhavle](https://github.com/GautamVhavle) · Star this repo if it helped you ⭐

</div>
