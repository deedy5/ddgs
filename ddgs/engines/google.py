from __future__ import annotations

import string
from random import choices
from time import time
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult
from ..utils import _is_custom_date_range, _parse_date_range

_arcid_random = None  # (random_part, timestamp)


def ui_async(start: int) -> str:
    global _arcid_random
    now = int(time())
    # regen if first call or TTL expired
    if not _arcid_random or now - _arcid_random[1] > 3600:
        rnd = "".join(choices(string.ascii_letters + string.digits + "_-", k=23))
        _arcid_random = (rnd, now)
    return f"arc_id:srp_{_arcid_random[0]}_1{start:02},use_ac:true,_fmt:prog"


class Google(BaseSearchEngine[TextResult]):
    """Google search engine"""

    name = "google"
    category = "text"
    provider = "google"

    search_url = "https://www.google.com/search"
    search_method = "GET"

    items_xpath = "//div[@data-snc]"
    elements_xpath = {
        "title": ".//h3//text()",
        "href": ".//a[h3]/@href",
        "body": ".//div[starts-with(@data-sncf, '1')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        safesearch_base = {"on": "2", "moderate": "1", "off": "0"}
        start = (page - 1) * 10
        payload = {
            "q": query,
            "filter": safesearch_base[safesearch.lower()],
            "start": str(start),
            "asearch": "arc",
            "async": ui_async(start),
            "ie": "UTF-8",
            "oe": "UTF-8",
        }
        country, lang = region.split("-")
        payload["hl"] = f"{lang}-{country.upper()}"  # interface language
        payload["lr"] = f"lang_{lang}"  # restricts to results written in a particular language
        payload["cr"] = f"country{country.upper()}"  # restricts to results written in a particular country
        if timelimit:
            if _is_custom_date_range(timelimit):
                # Handle custom date range: YYYY-MM-DD..YYYY-MM-DD
                date_range = _parse_date_range(timelimit)
                if date_range:
                    start_date, end_date = date_range
                    # Convert YYYY-MM-DD to MM/DD/YYYY format for Google
                    start_parts = start_date.split("-")
                    end_parts = end_date.split("-")
                    start_formatted = f"{start_parts[1]}/{start_parts[2]}/{start_parts[0]}"
                    end_formatted = f"{end_parts[1]}/{end_parts[2]}/{end_parts[0]}"
                    payload["tbs"] = f"cdr:1,cd_min:{start_formatted},cd_max:{end_formatted}"
            else:
                # Handle predefined time limits (d, w, m, y)
                payload["tbs"] = f"qdr:{timelimit}"
        return payload
