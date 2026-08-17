from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from http.client import HTTPResponse
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config.settings import Settings
from src.serper.budget import SearchBudgetManager
from src.serper.cache import SerperCache


@dataclass
class SearchResult:
    response: dict[str, Any] | None
    cached: bool = False
    error: str | None = None


class SerperClient:
    def __init__(
        self,
        settings: Settings,
        cache: SerperCache,
        budget: SearchBudgetManager,
        logger: logging.Logger,
    ):
        self.settings = settings
        self.cache = cache
        self.budget = budget
        self.logger = logger

    def search(self, query: str, *, page: int = 1, num: int = 10, search_type: str = "search") -> SearchResult:
        payload: dict[str, Any] = {
            "q": query,
            "gl": self.settings.serper_country,
            "hl": self.settings.serper_language,
            "page": page,
            "num": num,
            "type": search_type,
        }
        cached = self.cache.get(payload)
        if cached is not None:
            self.budget.record_cached()
            return SearchResult(cached, cached=True)
        if not self.budget.can_search():
            return SearchResult(None, error="search budget exhausted")
        if not self.settings.serper_api_key:
            return SearchResult(None, error="SERPER_API_KEY is not configured")

        self.budget.record_attempt()
        body = json.dumps({key: value for key, value in payload.items() if key != "type"}).encode("utf-8")
        request = Request(
            self.settings.serper_endpoint,
            data=body,
            method="POST",
            headers={
                "X-API-KEY": self.settings.serper_api_key,
                "Content-Type": "application/json",
                "User-Agent": "UgandaSEOIntelligence/1.0",
            },
        )
        last_error = ""
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.settings.serper_timeout_seconds) as response:
                    raw = response.read()
                    parsed = json.loads(raw.decode("utf-8"))
                    if not isinstance(parsed, dict):
                        raise ValueError("Serper returned a non-object JSON response")
                    self.cache.put(payload, parsed)
                    self.budget.record_success()
                    return SearchResult(parsed)
            except HTTPError as exc:
                last_error = f"HTTP {exc.code}: {self._safe_error_body(exc)}"
                if exc.code in {401, 403}:
                    break
            except (URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)
            if attempt < 2:
                time.sleep(0.5 * (2**attempt))
        self.budget.record_failure()
        self.logger.warning("Serper request failed for %r: %s", query, last_error)
        return SearchResult(None, error=last_error or "unknown Serper error")

    @staticmethod
    def _safe_error_body(error: HTTPError) -> str:
        try:
            return error.read(300).decode("utf-8", errors="replace")
        except Exception:
            return "unreadable response"