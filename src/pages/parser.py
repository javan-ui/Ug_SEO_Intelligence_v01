from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class PageHTMLParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.headings: dict[str, list[str]] = {"h1": [], "h2": [], "h3": []}
        self.paragraphs: list[str] = []
        self.images: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.meta: dict[str, str] = {}
        self.schema_types: list[str] = []
        self._active: str | None = None
        self._buffer: list[str] = []
        self._current_link: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        tag = tag.casefold()
        if tag in self.headings or tag in {"title", "p"}:
            self._active = tag
            self._buffer = []
        if tag == "meta":
            name = (attributes.get("name") or attributes.get("property") or "").casefold()
            content = attributes.get("content") or ""
            if name:
                self.meta[name] = content.strip()
        if tag == "link":
            rel = (attributes.get("rel") or "").casefold()
            if "canonical" in rel:
                self.meta["canonical"] = urljoin(self.base_url, attributes.get("href") or "")
        if tag == "img":
            self.images.append({"src": urljoin(self.base_url, attributes.get("src") or ""), "alt": attributes.get("alt") or ""})
        if tag == "a":
            href = urljoin(self.base_url, attributes.get("href") or "")
            self._current_link = {"href": href, "text": ""}
        if tag == "script" and (attributes.get("type") or "").casefold() == "application/ld+json":
            self.meta["has_json_ld"] = "true"

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if self._active == tag:
            content = " ".join("".join(self._buffer).split())
            if tag == "title":
                self.title = content
            elif tag in self.headings:
                self.headings[tag].append(content)
            elif tag == "p" and content:
                self.paragraphs.append(content)
            self._active = None
            self._buffer = []
        if tag == "a" and self._current_link is not None:
            self.links.append(self._current_link)
            self._current_link = None

    def handle_data(self, data: str) -> None:
        if self._active:
            self._buffer.append(data)
        if self._current_link is not None:
            self._current_link["text"] += data


def parse_html(html: str, url: str) -> PageHTMLParser:
    parser = PageHTMLParser(url)
    parser.feed(html)
    return parser


def same_domain(url: str, other: str) -> bool:
    return urlparse(url).netloc.casefold() == urlparse(other).netloc.casefold()