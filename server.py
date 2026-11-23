#!/usr/bin/env python3
"""
MCP Server: web-extractor
Combines Crawl4AI (fast, JS-rendered web crawler to Markdown) and
Microsoft MarkItDown (office/pdf/document to Markdown converter)
for MCP clients and AI agents.
"""

import os
import sys
import tempfile
import asyncio
from typing import Optional, List
import requests
from mcp.server.mcpserver import MCPServer
from markitdown import MarkItDown
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode

# Optional overrides (see .env.example)
REQUEST_TIMEOUT = float(os.environ.get("WEB_EXTRACTOR_TIMEOUT", "30"))
USER_AGENT = os.environ.get("WEB_EXTRACTOR_USER_AGENT", "Mozilla/5.0")

# Initialize MCP server
server = MCPServer(
    name="web-extractor",
    description="High-performance web scraping and document-to-markdown extraction powered by Crawl4AI and Microsoft MarkItDown."
)

# Global MarkItDown instance
_md = MarkItDown()


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n\n... [Content truncated to {max_length} characters] ..."


@server.tool(
    name="scrape_url",
    description="Scrape any public webpage with full JavaScript execution, anti-bot protection, and LLM-optimized Markdown output via Crawl4AI."
)
async def scrape_url(
    url: str,
    css_selector: Optional[str] = None,
    wait_for: Optional[str] = None,
    bypass_cache: bool = True,
    max_length: int = 50000
) -> str:
    """
    Scrape a webpage and return clean markdown.

    :param url: The URL to scrape.
    :param css_selector: Optional CSS selector to extract only a specific section.
    :param wait_for: Optional CSS selector or time to wait for before extracting.
    :param bypass_cache: Whether to bypass Crawl4AI cache.
    :param max_length: Maximum characters of markdown to return.
    """
    try:
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        run_config = CrawlerRunConfig(
            css_selector=css_selector,
            wait_for=wait_for,
            cache_mode=CacheMode.BYPASS if bypass_cache else CacheMode.ENABLED,
            word_count_threshold=10
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            if not result.success:
                return f"Error scraping {url}: {result.error_message}"

            markdown = result.markdown or ""
            metadata_header = f"# {result.metadata.get('title', 'Web Page')}\nSource: {url}\n\n"
            
            return _truncate(metadata_header + markdown, max_length)
    except Exception as e:
        return f"Exception while scraping {url}: {str(e)}"


@server.tool(
    name="convert_file",
    description="Convert any local document (PDF, Excel .xlsx, Word .docx, PowerPoint .pptx, HTML, CSV, TXT, images, audio) directly into clean Markdown using Microsoft MarkItDown."
)
def convert_file(file_path: str, max_length: int = 50000) -> str:
    """
    Convert a local file to markdown.

    :param file_path: Absolute path to the file on disk.
    :param max_length: Maximum characters of markdown to return.
    """
    expanded_path = os.path.expanduser(file_path)
    if not os.path.exists(expanded_path):
        return f"Error: File not found at '{expanded_path}'"

    try:
        result = _md.convert(expanded_path)
        content = result.text_content or ""
        
        header = f"# Document: {os.path.basename(expanded_path)}\n\n"
        return _truncate(header + content, max_length)
    except Exception as e:
        return f"Exception converting file {expanded_path}: {str(e)}"


@server.tool(
    name="convert_url_document",
    description="Download a document from a URL (e.g. remote PDF, spreadsheet, Word file) and convert it directly into clean Markdown using Microsoft MarkItDown."
)
def convert_url_document(url: str, max_length: int = 50000) -> str:
    """
    Download a document from URL and convert it to markdown.

    :param url: URL of the document.
    :param max_length: Maximum characters of markdown to return.
    """
    try:
        # Determine extension from URL
        clean_url = url.split("?")[0]
        ext = os.path.splitext(clean_url)[1] or ".bin"

        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            result = _md.convert(tmp_path)
            content = result.text_content or ""
            header = f"# Remote Document: {url}\n\n"
            return _truncate(header + content, max_length)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        return f"Exception downloading/converting document from {url}: {str(e)}"


if __name__ == "__main__":
    server.run("stdio")
