from __future__ import annotations

from urllib.parse import urlparse


def domain_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return (parsed.netloc or parsed.path).split("@")[-1].split(":")[0].lower()


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}