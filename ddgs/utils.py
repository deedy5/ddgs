"""Utilities."""

import re
import unicodedata
from contextlib import suppress
from datetime import datetime, timezone
from html import unescape
from urllib.parse import unquote

from .exceptions import DDGSException

_REGEX_STRIP_TAGS = re.compile("<.*?>")


def _extract_vqd(html_bytes: bytes, query: str) -> str:
    """Extract vqd from html bytes."""
    for c1, c1_len, c2 in (
        (b'vqd="', 5, b'"'),
        (b"vqd=", 4, b"&"),
        (b"vqd='", 5, b"'"),
    ):
        with suppress(ValueError):
            start = html_bytes.index(c1) + c1_len
            end = html_bytes.index(c2, start)
            return html_bytes[start:end].decode()

    msg = f"_extract_vqd() {query=} Could not extract vqd."
    raise DDGSException(msg)


def _normalize_url(url: str) -> str:
    """Unquote URL and replace spaces with '+'."""
    return unquote(url).replace(" ", "+") if url else ""


def _normalize_text(raw: str) -> str:
    """Normalize text.

    Strip HTML tags, unescape HTML entities, normalize Unicode,
    remove "c" category characters, and collapse whitespace.
    """
    if not raw:
        return ""

    # 1. Strip HTML tags
    text = _REGEX_STRIP_TAGS.sub("", raw)

    # 2. Unescape HTML entities
    text = unescape(text)

    # 3. Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # 4. Remove "C" category characters
    c_to_none = {ord(ch): None for ch in set(text) if unicodedata.category(ch)[0] == "C"}
    if c_to_none:
        text = text.translate(c_to_none)

    # 5. Collapse whitespace
    return " ".join(text.split())


def _normalize_date(date: int | str) -> str:
    """Normalize date from integer to ISO format if applicable."""
    return datetime.fromtimestamp(date, timezone.utc).isoformat() if isinstance(date, int) else date


def _expand_proxy_tb_alias(proxy: str | None) -> str | None:
    """Expand "tb" to a full proxy URL if applicable."""
    return "socks5h://127.0.0.1:9150" if proxy == "tb" else proxy
