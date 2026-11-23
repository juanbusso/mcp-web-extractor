# mcp-web-extractor

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that turns web pages and
documents into clean, LLM-friendly Markdown. It combines:

- **[Crawl4AI](https://github.com/unclecode/crawl4ai)** — headless-browser crawler with full JavaScript
  rendering, for dynamic web pages.
- **[Microsoft MarkItDown](https://github.com/microsoft/markitdown)** — converts PDF, Word, Excel,
  PowerPoint, HTML, CSV, images, audio and more to Markdown.

## Tools

| Tool | Arguments | Description |
| --- | --- | --- |
| `scrape_url` | `url`, `css_selector?`, `wait_for?`, `bypass_cache?` (default `true`), `max_length?` (default `50000`) | Render a web page in a headless browser and return Markdown. `css_selector` limits extraction to one section; `wait_for` waits for a selector/condition before extracting. |
| `convert_file` | `file_path`, `max_length?` | Convert a local file (`~` is expanded) to Markdown. |
| `convert_url_document` | `url`, `max_length?` | Download a remote document (PDF, XLSX, DOCX, …) and convert it to Markdown. |

Output longer than `max_length` characters is truncated with a marker.

## Requirements

- Python **3.10+**
- `mcp` **2.x** (the server uses `mcp.server.mcpserver.MCPServer`)

## Installation

```bash
git clone <this-repo-url> mcp-web-extractor
cd mcp-web-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Crawl4AI needs a Playwright browser the first time:
crawl4ai-setup        # or: python -m playwright install chromium
```

Check it compiles:

```bash
python3 -m py_compile server.py
```

## Usage with an MCP client

Add to your client's MCP config (Claude Desktop, Claude Code, Cursor, etc.), pointing at the
virtualenv's Python:

```json
{
  "mcpServers": {
    "web-extractor": {
      "command": "/ABSOLUTE/PATH/TO/mcp-web-extractor/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/TO/mcp-web-extractor/server.py"]
    }
  }
}
```

The server speaks MCP over **stdio**.

## Configuration

No configuration is required. Optional environment variables (see [`.env.example`](.env.example)),
passed through your MCP client's `env` block:

| Variable | Default | Description |
| --- | --- | --- |
| `WEB_EXTRACTOR_TIMEOUT` | `30` | Download timeout in seconds for `convert_url_document` |
| `WEB_EXTRACTOR_USER_AGENT` | `Mozilla/5.0` | `User-Agent` header for `convert_url_document` |

## Security notes

- `convert_file` can read any file the server process can read. Only connect this server to agents
  you trust with your filesystem.
- `scrape_url` and `convert_url_document` will fetch any URL they are given, including addresses on
  your local network.
