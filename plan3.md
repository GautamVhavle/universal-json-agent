# Plan 3 — Publish `universal-json-agent-mcp` to PyPI

> Goal: anyone can run `pip install universal-json-agent-mcp` (or `uv add universal-json-agent-mcp`) and immediately use the MCP server — no cloning, no manual setup.

Reference: <https://packaging.python.org/en/latest/tutorials/packaging-projects/>  
GitHub repo: <https://github.com/GautamVhavle/universal-json-agent>

---

## 0. Naming

| Concept | Value |
|---------|-------|
| **PyPI project name** | `universal-json-agent-mcp` |
| **Import package name** | `universal_json_agent_mcp` (underscores, what users `import`) |
| **GitHub repo** | `GautamVhavle/universal-json-agent` |
| **MCP server name** | `universal-json-agent` |

---

## 1. Restructure the source tree

The current layout:

```
src/json_agent/          ← import name is "json_agent"
    __init__.py
    server.py
    store.py
    tools/
    utils/
```

We need to **rename the import package** to match the PyPI name so users do:

```python
from universal_json_agent_mcp import server
```

### Steps

- [ ] **1.1** Rename `src/json_agent/` → `src/universal_json_agent_mcp/`
- [ ] **1.2** Update `__init__.py` version string and docstring
- [ ] **1.3** Fix **every internal import** — all files under `tools/`, `utils/`, `server.py`, `store.py` that do `from json_agent.xxx import ...` must become `from universal_json_agent_mcp.xxx import ...`
- [ ] **1.4** Fix **all test imports** — every file under `tests/` that does `from json_agent import ...` must become `from universal_json_agent_mcp import ...`
- [ ] **1.5** Fix `web/` imports — `web/tools.py`, `web/agent.py` etc. reference `json_agent.*`
- [ ] **1.6** Add `src/universal_json_agent_mcp/__main__.py` so `python -m universal_json_agent_mcp` works:
  ```python
  from universal_json_agent_mcp.server import main
  main()
  ```

---

## 2. Rewrite `pyproject.toml`

Replace the current `pyproject.toml` contents with:

```toml
[project]
name = "universal-json-agent-mcp"
version = "0.1.0"
description = "MCP server for advanced JSON parsing — load, query, aggregate, transform any JSON file from GitHub Copilot, Claude, Cursor, or any MCP client."
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
license-files = ["LICENSE"]
authors = [
    { name = "Gautam Vhavle" },
]
keywords = ["mcp", "json", "copilot", "agent", "parsing", "jsonpath"]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries",
    "Intended Audience :: Developers",
]
dependencies = [
    "mcp[cli]>=1.0.0",
    "pydantic>=2.0.0",
    "jsonpath-ng>=1.6.0",
    "ijson>=3.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.urls]
Homepage = "https://github.com/GautamVhavle/universal-json-agent"
Repository = "https://github.com/GautamVhavle/universal-json-agent"
Issues = "https://github.com/GautamVhavle/universal-json-agent/issues"

# Console script — gives users the `universal-json-agent-mcp` command
[project.scripts]
universal-json-agent-mcp = "universal_json_agent_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/universal_json_agent_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Key changes from current `pyproject.toml`:

| What | Why |
|------|-----|
| `name = "universal-json-agent-mcp"` | PyPI distribution name |
| `packages = ["src/universal_json_agent_mcp"]` | Points hatch to the renamed package |
| `[project.scripts]` | Creates a CLI entry point — `universal-json-agent-mcp` runs `server:main()` |
| `authors`, `keywords`, `classifiers`, `urls` | Required/recommended metadata for PyPI |
| `license = "MIT"` + `license-files` | Following PEP 639 |

---

## 3. Create a LICENSE file

- [ ] **3.1** Create `LICENSE` (MIT) at the project root:

```
MIT License

Copyright (c) 2026 Gautam Vhavle

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. Update `.vscode/mcp.json`

After the rename, the MCP config needs to point to the new module:

```json
{
  "servers": {
    "universal-json-agent": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "${workspaceFolder}",
        "run",
        "python",
        "-m",
        "universal_json_agent_mcp"
      ]
    }
  }
}
```

---

## 5. Update the MCP server name

In `server.py`, the `FastMCP(...)` call currently uses `"json-agent"`. Change to:

```python
mcp = FastMCP(
    "universal-json-agent",
    instructions=(...),
)
```

---

## 6. Update `README.md`

Update the README to reflect:
- New package name in install commands: `pip install universal-json-agent-mcp` / `uv add universal-json-agent-mcp`
- New CLI command: `universal-json-agent-mcp`
- New `python -m universal_json_agent_mcp` invocation
- New `.vscode/mcp.json` config pointing to the installed package
- Add a **"Usage after install"** section showing MCP client configs:
  - VS Code (Copilot)
  - Claude Desktop
  - Cursor
  - Generic stdio

### Example MCP client configs to document:

**VS Code / Copilot (`.vscode/mcp.json`):**
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

**Claude Desktop (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "universal-json-agent": {
      "command": "universal-json-agent-mcp"
    }
  }
}
```

**Or using uvx (no install):**
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

---

## 7. Update `.gitignore`

Add these entries for packaging artifacts:

```gitignore
# Packaging / distribution
dist/
build/
*.egg-info/
```

---

## 8. Build the package locally

```bash
# Install the build tool
uv pip install build

# Build both sdist and wheel
python3 -m build
```

This creates:
```
dist/
├── universal_json_agent_mcp-0.1.0-py3-none-any.whl
└── universal_json_agent_mcp-0.1.0.tar.gz
```

- [ ] **8.1** Verify the wheel contains all expected files:
  ```bash
  unzip -l dist/*.whl
  ```
- [ ] **8.2** Test local install in a fresh venv:
  ```bash
  python3 -m venv /tmp/test-install
  source /tmp/test-install/bin/activate
  pip install dist/universal_json_agent_mcp-0.1.0-py3-none-any.whl
  universal-json-agent-mcp  # should start the MCP server
  ```

---

## 9. Test on TestPyPI first

```bash
# Install twine
uv pip install twine

# Upload to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps universal-json-agent-mcp
```

- Need a TestPyPI account: <https://test.pypi.org/account/register/>
- Need an API token: <https://test.pypi.org/manage/account/#api-tokens>

---

## 10. Publish to real PyPI

```bash
python3 -m twine upload dist/*
```

- Need a PyPI account: <https://pypi.org/account/register/>
- Need an API token: <https://pypi.org/manage/account/#api-tokens>

After upload, anyone can:
```bash
pip install universal-json-agent-mcp
# or
uv add universal-json-agent-mcp
# or
uvx universal-json-agent-mcp
```

---

## 11. Run all tests after changes

```bash
uv run pytest -v
```

All 489 tests must still pass after the rename.

---

## Execution order (checklist)

| # | Task | Status |
|---|------|--------|
| 1 | Rename `src/json_agent/` → `src/universal_json_agent_mcp/` | ⬜ |
| 2 | Add `__main__.py` | ⬜ |
| 3 | Update all internal imports (`json_agent` → `universal_json_agent_mcp`) | ⬜ |
| 4 | Update all test imports | ⬜ |
| 5 | Update `web/` imports | ⬜ |
| 6 | Rewrite `pyproject.toml` | ⬜ |
| 7 | Create `LICENSE` file | ⬜ |
| 8 | Update `server.py` MCP server name | ⬜ |
| 9 | Update `.vscode/mcp.json` | ⬜ |
| 10 | Update `.gitignore` with dist entries | ⬜ |
| 11 | Update `README.md` with install/usage docs | ⬜ |
| 12 | Run tests — all 489 must pass | ⬜ |
| 13 | Build with `python3 -m build` | ⬜ |
| 14 | Verify wheel contents | ⬜ |
| 15 | Test local install in fresh venv | ⬜ |
| 16 | Upload to TestPyPI and test install | ⬜ |
| 17 | Upload to real PyPI | ⬜ |
| 18 | Commit + push to GitHub | ⬜ |

---

## What the user gets after `pip install`

```
$ pip install universal-json-agent-mcp
$ universal-json-agent-mcp          # starts MCP server via stdio
$ python -m universal_json_agent_mcp  # also works
```

No cloning, no `uv --directory`, no `${workspaceFolder}`. Just install and point any MCP client at the command.
