import re
import unicodedata
from html import unescape
from typing import Literal
from urllib.parse import unquote

from .exceptions import DDGSException


def _extract_vqd(html_bytes: bytes, keywords: str) -> str:
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
    raise DDGSException(f"_extract_vqd() {keywords=} Could not extract vqd.")


def _normalize_url(url: str) -> str:
    """Unquote URL and replace spaces with '+'."""
    return unquote(url).replace(" ", "+") if url else ""


def _normalize_text(
    raw: str, normalize_form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC", collapse_spaces: bool = True
) -> str:
    # 1) Unescape HTML entities (&amp;, &eacute;, &#169;, etc.)
    """Normalize text by unescaping HTML entities, applying Unicode normalization,
    mapping Unicode separators to spaces, and optionally collapsing whitespace.

    Args:
        raw: The raw text input to be normalized.
        normalize_form: The Unicode normalization form to apply. Options are "NFC", "NFD", "NFKC", "NFKD".
        collapse_spaces: If True, collapse multiple whitespace characters into a single space.

    Returns:
        The normalized text as a string.
    """
    if raw is None:
        return ""

    s = unescape(raw)

    # 2) Unicode normalize
    s = unicodedata.normalize(normalize_form, s)

    # 3) Map *all* Unicode separator characters (category 'Z*') to U+0020
    sep_to_space = {ord(ch): " " for ch in set(s) if unicodedata.category(ch).startswith("Z")}
    s = s.translate(sep_to_space)

    # 4) Optionally collapse whitespace
    if collapse_spaces:
        # \s covers spaces, tabs, newlines; collapse them to a single space
        s = re.sub(r"\s+", " ", s).strip()

    return s
