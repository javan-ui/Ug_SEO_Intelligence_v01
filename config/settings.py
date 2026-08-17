from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass(frozen=True)
class Settings:
    serper_api_key: str | None
    serper_country: str = "ug"
    serper_language: str = "en"
    serper_max_searches: int = 2500
    serper_endpoint: str = "https://google.serper.dev/search"
    serper_timeout_seconds: float = 30.0
    scraping_api_url: str | None = None
    scraping_api_key: str | None = None
    scraping_api_key_header: str = "Authorization"
    scraping_api_key_prefix: str = "Bearer "
    scraping_timeout_seconds: float = 30.0
    page_fetch_concurrency: int = 4

    @classmethod
    def from_env(cls) -> "Settings":
        _load_local_env()
        return cls(
            serper_api_key=os.getenv("SERPER_API_KEY") or None,
            serper_country=os.getenv("SERPER_COUNTRY", "ug").lower(),
            serper_language=os.getenv("SERPER_LANGUAGE", "en").lower(),
            serper_max_searches=_int_env("SERPER_MAX_SEARCHES", 2500),
            serper_endpoint=os.getenv("SERPER_ENDPOINT", "https://google.serper.dev/search"),
            serper_timeout_seconds=_float_env("SERPER_TIMEOUT_SECONDS", 30.0),
            scraping_api_url=os.getenv("SCRAPING_API_URL") or None,
            scraping_api_key=os.getenv("SCRAPING_API_KEY") or None,
            scraping_api_key_header=os.getenv("SCRAPING_API_KEY_HEADER", "Authorization"),
            scraping_api_key_prefix=os.getenv("SCRAPING_API_KEY_PREFIX", "Bearer "),
            scraping_timeout_seconds=_float_env("SCRAPING_TIMEOUT_SECONDS", 30.0),
            page_fetch_concurrency=max(1, _int_env("PAGE_FETCH_CONCURRENCY", 4)),
        )

    def validate(self, require_api_key: bool = True) -> list[str]:
        errors: list[str] = []
        if require_api_key and not self.serper_api_key:
            errors.append("SERPER_API_KEY is required for live Serper requests.")
        if self.serper_country != "ug":
            errors.append("SERPER_COUNTRY must remain 'ug' for the Uganda research engine.")
        if self.serper_language != "en":
            errors.append("SERPER_LANGUAGE must remain 'en' for the initial English research.")
        if self.serper_max_searches < 1:
            errors.append("SERPER_MAX_SEARCHES must be greater than zero.")
        if self.scraping_api_url and not self.scraping_api_key:
            errors.append("SCRAPING_API_KEY is required when SCRAPING_API_URL is configured.")
        return errors


def ensure_directories() -> None:
    for path in (
        DATA_DIR / "raw_serper",
        DATA_DIR / "candidates",
        DATA_DIR / "validated",
        DATA_DIR / "competitors",
        DATA_DIR / "clusters",
        DATA_DIR / "scores",
        DATA_DIR / "final",
        REPORTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _load_local_env() -> None:
    """Load simple KEY=VALUE pairs without adding a dotenv runtime dependency."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)