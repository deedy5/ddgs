---
name: ddgs
description: Use when an agent needs to search the web, find images/news/videos/books, or extract content from a URL. Covers the ddgs Python library, CLI, and MCP server integration.
---

# ddgs — Web Search for Agents

## Overview

**ddgs** (Dux Distributed Global Search) is a Python metasearch library that aggregates results from multiple search engines. Agents can use it via Python API, CLI, or MCP server.

## Python API

```python
from ddgs import DDGS

# Text search
results = DDGS().text("python async", max_results=5)

# Images, news, videos, books
images = DDGS().images("butterfly", max_results=5)
news   = DDGS().news("ai regulation", timelimit="w")
videos = DDGS().videos("rust programming")
books  = DDGS().books("machine learning")

# Extract content from a URL
page = DDGS().extract("https://example.com")
page["content"]          # Markdown text (default)
page = DDGS().extract("https://example.com", fmt="text_plain")
page = DDGS().extract("https://example.com", fmt="content")  # raw bytes
```

All search methods return `list[dict[str, Any]]`. Each dict has keys depending on category:

| Method | Keys |
|--------|------|
| `text()` | `title`, `href`, `body` |
| `images()` | `title`, `image`, `thumbnail`, `url`, `height`, `width`, `source` |
| `videos()` | `title`, `content`, `description`, `duration`, `embed_url`, `images`, `publisher` |
| `news()` | `date`, `title`, `body`, `url`, `image`, `source` |
| `books()` | `title`, `author`, `publisher`, `info`, `url`, `thumbnail` |

## CLI

```bash
# Text search
ddgs text -q "python async" --max_results 5

# Other categories
ddgs images -q "cats" --color Blue
ddgs news -q "tech" --timelimit d
ddgs videos -q "cars" --duration medium
ddgs books -q "sea wolf"

# Extract content
ddgs extract -u https://example.com
ddgs extract -u https://example.com -f text_plain

# Save results
ddgs text -q "dogs" -o results.json
ddgs text -q "dogs" -o results.csv

# Version
ddgs version
```

## CLI for Agents

Agents can also use `ddgs` as a CLI tool via subprocess. Auto-detects non-TTY — outputs plain text without colors or interactive pauses.

To discover available options:
```bash
ddgs --help
ddgs text --help
ddgs images --help
```

## MCP Server

### stdio (for local MCP clients like Cursor, Claude Desktop)

```bash
pip install ddgs[mcp]
ddgs mcp                             # stdio MCP server
ddgs mcp -pr socks5h://127.0.0.1:9150  # with proxy
```

Client configuration:
```json
{
  "mcpServers": {
    "ddgs": {
      "command": "ddgs",
      "args": ["mcp"]
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_text` | Web text search |
| `search_images` | Image search |
| `search_news` | News search |
| `search_videos` | Video search |
| `search_books` | Book search |
| `extract_content` | Extract content from a URL |

## Quick Reference

| Parameter | Values | Default |
|-----------|--------|---------|
| `region` | `us-en`, `uk-en`, `ru-ru`, `de-de`, etc. | `us-en` |
| `safesearch` | `on`, `moderate`, `off` | `moderate` |
| `timelimit` | `d` (day), `w` (week), `m` (month), `y` (year) | None |
| `max_results` | int | 10 |
| `page` | int | 1 |
| `backend` | `auto`, `all`, or engine name | `auto` |

Available backends by method:

| Method | Backends |
|--------|----------|
| `text()` | `bing`, `brave`, `duckduckgo`, `google`, `grokipedia`, `mojeek`, `yandex`, `yahoo`, `wikipedia` |
| `images()` | `bing`, `duckduckgo` |
| `videos()` | `duckduckgo` |
| `news()` | `bing`, `duckduckgo`, `yahoo` |
| `books()` | `annasarchive` |

## Tips

- **Proxy (Python)**: `DDGS(proxy="socks5h://127.0.0.1:9150")` or set env `DDGS_PROXY`
- **Proxy (MCP)**: `ddgs mcp -pr socks5h://127.0.0.1:9150` or `export DDGS_PROXY=...`
- **Proxy (API)**: `ddgs api -pr socks5h://127.0.0.1:9150` or `export DDGS_PROXY=...`
- **SSL verification**: `DDGS(verify=False)` or `DDGS(verify="/path/to/cert.pem")`
- **Timeout**: `DDGS(timeout=10)` (default: 5 seconds)
- **Errors**: catches `DDGSException`, `RatelimitException`, `TimeoutException`
- **Multiple backends**: `backend="bing,google"` (comma-separated)
