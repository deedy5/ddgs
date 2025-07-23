from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from html import unescape
from typing import Any, Literal
from urllib.parse import unquote

from .exceptions import DDGSException

try:
    HAS_ORJSON = True
    import orjson
except ImportError:
    HAS_ORJSON = False
    import json

_REGEX_STRIP_TAGS = re.compile("<.*?>")


def json_dumps(obj: Any) -> str:
    try:
        return (
            orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode()
            if HAS_ORJSON
            else json.dumps(obj, ensure_ascii=False, indent=2)
        )
    except Exception as ex:
        raise DDGSException(f"{type(ex).__name__}: {ex}") from ex


def json_loads(obj: str | bytes) -> Any:
    try:
        return orjson.loads(obj) if HAS_ORJSON else json.loads(obj)
    except Exception as ex:
        raise DDGSException(f"{type(ex).__name__}: {ex}") from ex


def _extract_vqd(html_bytes: bytes, query: str) -> str:
    """Extract vqd from html bytes."""
    for c1, c1_len, c2 in (
        (b'vqd="', 5, b'"'),
        (b"vqd=", 4, b"&"),
        (b"vqd='", 5, b"'"),
    ):
        try:
            start = html_bytes.index(c1) + c1_len
            end = html_bytes.index(c2, start)
            return html_bytes[start:end].decode()
        except ValueError:
            pass
    raise DDGSException(f"_extract_vqd() {query=} Could not extract vqd.")


def _normalize_url(url: str) -> str:
    """Unquote URL and replace spaces with '+'."""
    return unquote(url).replace(" ", "+") if url else ""


def _normalize_text(
    raw: str,
    normalize_form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC",
    collapse_spaces: bool = True,
) -> str:
    """
    Strip HTML tags, unescape HTML entities, normalize Unicode,
    replace all separator-like characters with spaces, then
    optionally collapse consecutive whitespace into a single space.
    """
    if not raw:
        return ""

    # 1. Strip HTML tags
    stripped = _REGEX_STRIP_TAGS.sub("", raw)

    # 2. Unescape HTML entities
    unescaped = unescape(stripped)

    # 3. Unicode normalization
    normalized = unicodedata.normalize(normalize_form, unescaped)

    # 4. Map both Z* (separators) AND Cf (format) to a plain space
    sep_to_space = {ord(ch): " " for ch in set(normalized) if unicodedata.category(ch).startswith(("Z", "C"))}
    translated = normalized.translate(sep_to_space)

    # 5. Collapse whitespace if requested
    if collapse_spaces:
        # \s covers all whitespace including separators we translated
        translated = re.sub(r"\s+", " ", translated).strip()

    return translated


def _normalize_date(date: int | str) -> str:
    """Normalize date from integer to ISO format if applicable."""
    return datetime.fromtimestamp(date, timezone.utc).isoformat() if isinstance(date, int) else date


def _expand_proxy_tb_alias(proxy: str | None) -> str | None:
    """Expand "tb" to a full proxy URL if applicable."""
    return "socks5h://127.0.0.1:9150" if proxy == "tb" else proxy
