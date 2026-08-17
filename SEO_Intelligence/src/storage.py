from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS research_runs (
    research_run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    git_commit TEXT,
    serper_queries_attempted INTEGER DEFAULT 0,
    serper_queries_successful INTEGER DEFAULT 0,
    serper_queries_cached INTEGER DEFAULT 0,
    serper_queries_failed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS keywords (
    keyword TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    retained INTEGER DEFAULT 1,
    relevance_score REAL DEFAULT 0,
    commercial_intent REAL DEFAULT 0,
    informational_intent REAL DEFAULT 0,
    local_relevance REAL DEFAULT 0,
    business_relevance REAL DEFAULT 0,
    intents TEXT DEFAULT '[]',
    demand_signal REAL DEFAULT 0,
    demand_confidence TEXT DEFAULT 'LOW',
    commercial_value REAL DEFAULT 0,
    serp_competition REAL DEFAULT 0,
    rankability REAL DEFAULT 0,
    uganda_relevance REAL DEFAULT 0,
    opportunity REAL DEFAULT 0,
    evidence_confidence REAL DEFAULT 0,
    reasons TEXT DEFAULT '[]',
    data TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS keyword_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    source_seed TEXT,
    discovery_method TEXT,
    discovery_query TEXT,
    first_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS serp_searches (
    query_key TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    request TEXT NOT NULL,
    response TEXT,
    cached INTEGER DEFAULT 0,
    error TEXT,
    fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS serp_results (
    keyword TEXT NOT NULL,
    position INTEGER,
    title TEXT,
    link TEXT,
    snippet TEXT,
    domain TEXT,
    display_domain TEXT,
    data TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS people_also_ask (keyword TEXT, question TEXT, answer TEXT);
CREATE TABLE IF NOT EXISTS related_searches (keyword TEXT, query TEXT);
CREATE TABLE IF NOT EXISTS competitor_pages (
    keyword TEXT,
    position INTEGER,
    url TEXT,
    domain TEXT,
    title TEXT,
    snippet TEXT,
    domain_type TEXT,
    country_relevance REAL,
    business_type TEXT,
    page_type TEXT,
    confidence REAL,
    data TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS page_analysis (
    url TEXT PRIMARY KEY,
    keyword TEXT,
    fetch_failed INTEGER DEFAULT 0,
    reason TEXT,
    data TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS keyword_clusters (
    cluster_id INTEGER,
    keyword TEXT,
    primary_keyword TEXT,
    data TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS page_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_keyword TEXT,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    module TEXT,
    operation TEXT,
    keyword TEXT,
    url TEXT,
    exception TEXT,
    retry_count INTEGER DEFAULT 0
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def start_run(self, research_run_id: str, git_commit: str | None = None) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO research_runs (research_run_id, started_at, git_commit) VALUES (?, ?, ?)",
            (research_run_id, utc_now(), git_commit),
        )
        self.connection.commit()

    def finish_run(self, research_run_id: str, budget: dict[str, int]) -> None:
        self.connection.execute(
            """UPDATE research_runs SET completed_at=?, serper_queries_attempted=?,
            serper_queries_successful=?, serper_queries_cached=?, serper_queries_failed=?
            WHERE research_run_id=?""",
            (
                utc_now(),
                budget["attempted"],
                budget["successful"],
                budget["cached"],
                budget["failed"],
                research_run_id,
            ),
        )
        self.connection.commit()

    def save_keyword(self, record: dict[str, Any]) -> None:
        keyword = record["keyword"]
        values = (
            keyword,
            record.get("first_seen", utc_now()),
            int(record.get("retained", True)),
            float(record.get("relevance_score", 0)),
            float(record.get("commercial_intent", 0)),
            float(record.get("informational_intent", 0)),
            float(record.get("local_relevance", 0)),
            float(record.get("business_relevance", 0)),
            json.dumps(record.get("intents", []), ensure_ascii=False),
            float(record.get("demand_signal", 0)),
            record.get("demand_confidence", "LOW"),
            float(record.get("commercial_value", 0)),
            float(record.get("serp_competition", 0)),
            float(record.get("rankability", 0)),
            float(record.get("uganda_relevance", 0)),
            float(record.get("opportunity", 0)),
            float(record.get("evidence_confidence", 0)),
            json.dumps(record.get("reasons", []), ensure_ascii=False),
            json.dumps(record, ensure_ascii=False),
        )
        self.connection.execute(
            """INSERT INTO keywords (keyword, first_seen, retained, relevance_score, commercial_intent,
            informational_intent, local_relevance, business_relevance, intents, demand_signal,
            demand_confidence, commercial_value, serp_competition, rankability, uganda_relevance,
            opportunity, evidence_confidence, reasons, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(keyword) DO UPDATE SET data=excluded.data, retained=excluded.retained,
            relevance_score=excluded.relevance_score, commercial_intent=excluded.commercial_intent,
            informational_intent=excluded.informational_intent, local_relevance=excluded.local_relevance,
            business_relevance=excluded.business_relevance, intents=excluded.intents,
            demand_signal=excluded.demand_signal, demand_confidence=excluded.demand_confidence,
            commercial_value=excluded.commercial_value, serp_competition=excluded.serp_competition,
            rankability=excluded.rankability, uganda_relevance=excluded.uganda_relevance,
            opportunity=excluded.opportunity, evidence_confidence=excluded.evidence_confidence,
            reasons=excluded.reasons""",
            values,
        )
        self.connection.commit()

    def save_source(self, record: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO keyword_sources (keyword, source_seed, discovery_method, discovery_query, first_seen) VALUES (?, ?, ?, ?, ?)",
            (
                record["keyword"],
                record.get("source_seed"),
                record.get("discovery_method"),
                record.get("discovery_query"),
                record.get("first_seen", utc_now()),
            ),
        )
        self.connection.commit()

    def save_serp(self, keyword: str, request_key: str, request: dict[str, Any], response: dict[str, Any] | None, cached: bool, error: str | None = None) -> None:
        self.connection.execute(
            """INSERT OR REPLACE INTO serp_searches (query_key, keyword, request, response, cached, error, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (request_key, keyword, json.dumps(request), json.dumps(response) if response else None, int(cached), error, utc_now()),
        )
        self.connection.commit()

    def save_serp_details(self, keyword: str, parsed: dict[str, Any]) -> None:
        for result in parsed.get("organic", []):
            self.connection.execute(
                "INSERT INTO serp_results VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    keyword,
                    result.get("position"),
                    result.get("title"),
                    result.get("link"),
                    result.get("snippet"),
                    result.get("domain"),
                    result.get("display_domain"),
                    json.dumps(result, ensure_ascii=False),
                ),
            )
        for item in parsed.get("people_also_ask", []):
            self.connection.execute(
                "INSERT INTO people_also_ask VALUES (?, ?, ?)",
                (keyword, item.get("question"), item.get("answer")),
            )
        for item in parsed.get("related_searches", []):
            self.connection.execute("INSERT INTO related_searches VALUES (?, ?)", (keyword, item))
        self.connection.commit()

    def save_competitors(self, competitors: Iterable[dict[str, Any]]) -> None:
        for competitor in competitors:
            self.connection.execute(
                """INSERT INTO competitor_pages (keyword, position, url, domain, title, snippet, domain_type,
                country_relevance, business_type, page_type, confidence, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    competitor.get("keyword"),
                    competitor.get("position"),
                    competitor.get("url"),
                    competitor.get("domain"),
                    competitor.get("title"),
                    competitor.get("snippet"),
                    competitor.get("domain_type"),
                    competitor.get("country_relevance", 0),
                    competitor.get("business_type"),
                    competitor.get("page_type"),
                    competitor.get("confidence", 0),
                    json.dumps(competitor, ensure_ascii=False),
                ),
            )
        self.connection.commit()

    def save_page_analysis(self, analysis: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO page_analysis (url, keyword, fetch_failed, reason, data) VALUES (?, ?, ?, ?, ?)",
            (
                analysis["url"],
                analysis.get("keyword"),
                int(analysis.get("fetch_failed", False)),
                analysis.get("reason"),
                json.dumps(analysis, ensure_ascii=False),
            ),
        )
        self.connection.commit()

    def save_cluster(self, cluster: dict[str, Any]) -> None:
        for keyword in cluster.get("keywords", []):
            self.connection.execute(
                "INSERT INTO keyword_clusters VALUES (?, ?, ?, ?)",
                (cluster["cluster_id"], keyword, cluster["primary_keyword"], json.dumps(cluster, ensure_ascii=False)),
            )
        self.connection.commit()

    def save_recommendation(self, recommendation: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO page_recommendations (primary_keyword, data) VALUES (?, ?)",
            (recommendation.get("primary_keyword"), json.dumps(recommendation, ensure_ascii=False)),
        )
        self.connection.commit()

    def record_error(self, module: str, operation: str, exception: str, keyword: str | None = None, url: str | None = None, retry_count: int = 0) -> None:
        self.connection.execute(
            "INSERT INTO errors (timestamp, module, operation, keyword, url, exception, retry_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (utc_now(), module, operation, keyword, url, exception, retry_count),
        )
        self.connection.commit()

    def rows(self, table: str) -> list[dict[str, Any]]:
        allowed = {"keywords", "serp_results", "competitor_pages", "page_analysis", "page_recommendations", "research_runs"}
        if table not in allowed:
            raise ValueError(f"Unsupported table export: {table}")
        return [dict(row) for row in self.connection.execute(f"SELECT * FROM {table}")]

    def keyword_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for row in self.connection.execute("SELECT data FROM keywords WHERE retained=1"):
            try:
                value = json.loads(row["data"])
                if isinstance(value, dict):
                    records.append(value)
            except json.JSONDecodeError:
                continue
        return records


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)