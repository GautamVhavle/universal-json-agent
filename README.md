<div align="center">

<br />

<img src="assets/logo.png" alt="Universal JSON Agent MCP" width="180" />

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
pip install universal-json-agent-mcp
```

<br />

[**Getting Started**](#-getting-started) &nbsp;&middot;&nbsp; [**26 Tools**](#-tools-reference) &nbsp;&middot;&nbsp; [**Web API**](#-web-api-server) &nbsp;&middot;&nbsp; [**Development**](#-development)

<br />

</div>

---

<br />

## 💡 Why?

Working with JSON shouldn't require writing a script every time. **Universal JSON Agent MCP** lets you ask questions in plain English and get answers instantly.

<table>
<tr>
<td width="50%">

**Without this tool**
```python
import json

with open("missions.json") as f:
    data = json.load(f)

total = sum(
    m["budget_credits"]
    for m in data["missions"]
)
print(f"Total: {total}")
```

</td>
<td width="50%">

**With this tool**
```
You:  What's the total budget
      across all missions?

AI:   The total budget is
      $18,250,000,000.50
```

</td>
</tr>
</table>

<br />

### Supported Clients

<div align="center">

| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vscode/vscode-original.svg" width="28" /> | <img src="https://upload.wikimedia.org/wikipedia/commons/8/8a/Claude_AI_logo.svg" width="28" /> | <img src="https://www.cursor.com/favicon.ico" width="28" /> | Any MCP Client |
|:---:|:---:|:---:|:---:|
| **VS Code / Copilot** | **Claude Desktop** | **Cursor** | **stdio** |

</div>

<br />

---

<br />

## ⚡ Getting Started

### 1. Install

Choose your preferred method:

```bash
pip install universal-json-agent-mcp     # pip
uv add universal-json-agent-mcp          # uv
uvx universal-json-agent-mcp             # zero-install, runs instantly
```

### 2. Configure your editor

<details open>
<summary><b>&nbsp;📘&nbsp; VS Code / GitHub Copilot</b></summary>

<br />

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
<summary><b>&nbsp;🟠&nbsp; Claude Desktop</b></summary>

<br />

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
<summary><b>&nbsp;🟣&nbsp; Cursor</b></summary>

<br />

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
<summary><b>&nbsp;⌨️&nbsp; CLI / Standalone</b></summary>

<br />

```bash
universal-json-agent-mcp
# or
python -m universal_json_agent_mcp
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

Your AI handles the rest — no code required.

<br />

---

<br />

## 🛠 Tools Reference

<table>
<tr><td>

### 📂 &nbsp;Load & Manage

| Tool | What it does |
|:-----|:-------------|
| `load_json` | Load a JSON file from disk into memory |
| `list_loaded` | List all loaded documents with metadata |
| `unload_json` | Remove a document from memory |

</td></tr>
<tr><td>

### 🔍 &nbsp;Explore

| Tool | What it does |
|:-----|:-------------|
| `get_keys` | Get keys of an object or index range of an array |
| `get_value` | Retrieve value at a path (auto-truncated at 10 KB) |
| `get_type` | Return the JSON type at a path |
| `get_structure` | Schema-like skeleton — keys, types, nesting |

</td></tr>
<tr><td>

### 🎯 &nbsp;Query

| Tool | What it does |
|:-----|:-------------|
| `jsonpath_query` | Run JSONPath — `$.missions[*].codename` |
| `filter_objects` | Filter by condition: `eq`, `gt`, `lt`, `contains`, `regex`… |
| `search_text` | Full-text search across all string values |

</td></tr>
<tr><td>

### 📊 &nbsp;Aggregate

| Tool | What it does |
|:-----|:-------------|
| `count` | Count items in an array or keys in an object |
| `sum_values` | Sum numeric values at a JSONPath |
| `min_max` | Get min and max of numeric values |
| `unique_values` | Distinct values at a JSONPath |
| `value_counts` | Frequency table — like pandas `value_counts()` |

</td></tr>
<tr><td>

### 🔄 &nbsp;Transform

| Tool | What it does |
|:-----|:-------------|
| `flatten` | Flatten nested objects to dot-notation pairs |
| `pick_fields` | Project specific fields from array objects |
| `group_by` | Group objects by a field value |
| `sort_by` | Sort objects by a field |
| `sample` | Random N items from an array |

</td></tr>
<tr><td>

### 📈 &nbsp;Analytics

| Tool | What it does |
|:-----|:-------------|
| `describe` | Stats: count, mean, std, min, max, percentiles |
| `multi_filter` | Compound filters with AND / OR logic |
| `compare` | Diff two values — added, removed, changed keys |

</td></tr>
<tr><td>

### 💾 &nbsp;Export

| Tool | What it does |
|:-----|:-------------|
| `export_csv` | Export array of objects to CSV file |
| `export_json` | Export a value to a new JSON file |

</td></tr>
<tr><td>

### 🗺 &nbsp;Introspect

| Tool | What it does |
|:-----|:-------------|
| `distinct_paths` | List every unique leaf path with types |

</td></tr>
</table>

<br />

---

<br />

## 🌐 Web API Server

> **Optional.** A standalone **FastAPI + LangChain** REST API wrapping all 26 tools — useful for integrations, dashboards, or non-MCP workflows.

### Quick Start

```bash
pip install -r web/requirements.txt      # install deps
cp .env.example .env                     # add your OpenRouter key
python -m web.run --port 8000            # start server
```

### API Endpoints

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `GET` | `/health` | Health check |
| `POST` | `/query` | Upload JSON + ask a question |
| `POST` | `/query/path` | Reference a file on disk + ask a question |
| `GET` | `/docs` | Interactive Swagger UI |

### Example Request

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

<br />

---

<br />

## 🏗 Project Structure

```
universal-json-agent/
│
├── src/universal_json_agent_mcp/   # 📦 MCP Server (pip-installable)
│   ├── server.py                   #    FastMCP entry point — 26 tools
│   ├── store.py                    #    In-memory JSON document store
│   ├── tools/
│   │   ├── load.py                 #    load · list · unload
│   │   ├── explore.py              #    keys · value · type · structure
│   │   ├── query.py                #    jsonpath · filter · search
│   │   ├── aggregate.py            #    count · sum · min/max · unique · value_counts
│   │   ├── transform.py            #    flatten · pick · group · sort · sample
│   │   ├── stats.py                #    describe
│   │   ├── advanced_query.py       #    multi_filter · compare
│   │   ├── export.py               #    CSV · JSON export
│   │   └── introspect.py           #    distinct_paths
│   └── utils/
│       ├── path_resolver.py        #    Dot/bracket path navigation
│       └── truncation.py           #    Smart output truncation
│
├── web/                            # 🌐 FastAPI + LangChain server
├── tests/                          # ✅ 489 tests
├── assets/                         # 🎨 Logo & media
├── pyproject.toml                  #    Package config & metadata
├── LICENSE                         #    MIT
└── README.md
```

<br />

---

<br />

## 🧑‍💻 Development

```bash
# Clone the repo
git clone https://github.com/GautamVhavle/universal-json-agent.git
cd universal-json-agent

# Install with dev dependencies
uv sync --extra dev

# Run the full test suite (489 tests)
uv run pytest
```

<details>
<summary><b>More test commands</b></summary>

<br />

```bash
# Verbose output
uv run pytest -v

# Run one test file
uv run pytest tests/test_tools/test_aggregate.py

# Run tests matching a pattern
uv run pytest -k "test_filter"
```

</details>

### 🚀 Releasing

Releases are **fully automated** via GitHub Actions:

```
git tag v0.3.0 -m "v0.3.0"       # create a version tag
git push origin v0.3.0            # push the tag
```

Then [create a GitHub Release](https://github.com/GautamVhavle/universal-json-agent/releases/new) → CI runs tests → builds → publishes to PyPI. Done.

<br />

---

<br />

## ❓ Troubleshooting

<details>
<summary><b>MCP server not appearing in Copilot / Claude / Cursor</b></summary>

<br />

1. Verify the config file exists (`.vscode/mcp.json` for VS Code)
2. Check the command is on your PATH: `which universal-json-agent-mcp`
3. Restart the editor

</details>

<details>
<summary><b>"No document loaded" errors</b></summary>

<br />

You need to load a file first. Ask your AI: *"Load the file data/example.json"* — this calls `load_json` behind the scenes.

</details>

<details>
<summary><b>Truncated output</b></summary>

<br />

Large results are capped at ~10 KB to keep responses fast. Use more specific paths, filters, or `pick_fields` to narrow results.

</details>

<details>
<summary><b>429 Too Many Requests (web server)</b></summary>

<br />

The model provider is rate-limiting you. Wait a moment or switch to a different model in your `.env` file.

</details>

<details>
<summary><b>Import errors in web server</b></summary>

<br />

```bash
pip install -r web/requirements.txt
```

</details>

<br />

---

<br />

<div align="center">

### 📄 License

[MIT](LICENSE) — free for personal and commercial use.

<br />

**Built by [Gautam Vhavle](https://github.com/GautamVhavle)**

<br />

If this project helped you, consider giving it a ⭐

<br />

</div>
