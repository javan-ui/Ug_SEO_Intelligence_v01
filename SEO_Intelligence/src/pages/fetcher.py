from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from config.settings import Settings


@dataclass
class FetchResult:
    url: str
    html: str | None
    final_url: str | None = None
    failed: bool = False
    reason: str | None = None
    method: str = "direct_http"


class ScrapingApi:
    def __init__(self, settings: Settings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger

    def fetch(self, url: str) -> FetchResult:
        if not self.settings.scraping_api_url or not self.settings.scraping_api_key:
            return FetchResult(url, None, failed=True, reason="scraping API is not configured", method="scraping_api")
        endpoint = f"{self.settings.scraping_api_url}?{urlencode({'url': url})}"
        request = Request(
            endpoint,
            headers={
                "User-Agent": "UgandaSEOIntelligence/1.0",
                self.settings.scraping_api_key_header: f"{self.settings.scraping_api_key_prefix}{self.settings.scraping_api_key}",
            },
        )
        try:
            with urlopen(request, timeout=self.settings.scraping_timeout_seconds) as response:
                body = response.read(3_000_000).decode("utf-8", errors="replace")
                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type:
                    import json

                    payload = json.loads(body)
                    body = str(payload.get("html") or payload.get("content") or payload.get("body") or "")
                if not body:
                    return FetchResult(url, None, failed=True, reason="scraping API returned empty content", method="scraping_api")
                return FetchResult(url, body, final_url=url, method="scraping_api")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            self.logger.warning("Scraping API failed for %s: %s", url, exc)
            return FetchResult(url, None, failed=True, reason=f"scraping API error: {exc}", method="scraping_api")


class PageFetcher:
    def __init__(self, settings: Settings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.scraping_api = ScrapingApi(settings, logger)

    def fetch(self, url: str) -> FetchResult:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; UgandaSEOIntelligence/1.0; +research)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=self.settings.scraping_timeout_seconds) as response:
                content_type = response.headers.get("Content-Type", "")
                body = response.read(3_000_000).decode("utf-8", errors="replace")
                if "html" not in content_type and "<html" not in body.casefold():
                    return FetchResult(url, None, response.geturl(), True, "response was not HTML")
                return FetchResult(url, body, response.geturl())
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            direct = FetchResult(url, None, failed=True, reason=f"direct HTTP error: {exc}")
            if self.settings.scraping_api_url:
                fallback = self.scraping_api.fetch(url)
                if not fallback.failed:
                    return fallback
            self.logger.info("Competitor fetch failed for %s: %s", url, exc)
            return direct


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(html)).strip()