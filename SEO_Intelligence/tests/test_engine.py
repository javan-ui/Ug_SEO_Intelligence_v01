from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path

from config.settings import Settings
from src.clustering.clusterer import cannibalization_warnings, cluster_keywords, serp_similarity
from src.filtering.intent import classify_intent
from src.filtering.relevance import score_relevance
from src.pages.onpage import analyze_page
from src.reports.html_report import render_report
from src.scoring.opportunity import opportunity_score
from src.serper.budget import SearchBudgetManager
from src.serper.cache import SerperCache
from src.serp.parser import parse_serp
from src.storage import Database


SAMPLE_RESPONSE = {
    "organic": [
        {
            "position": 1,
            "title": "Website Design Uganda",
            "link": "https://example.co.ug/website-design",
            "snippet": "Uganda website design services.",
        },
        {
            "position": 2,
            "title": "Website Design Services",
            "link": "https://example.co.ug/services",
            "snippet": "Professional websites for businesses.",
        },
    ],
    "peopleAlsoAsk": [{"question": "How much does a website cost in Uganda?", "snippet": "It depends on scope."}],
    "relatedSearches": [{"query": "website development Uganda"}],
    "places": [{"title": "Example"}],
}


class EngineTests(unittest.TestCase):
    def test_cache_key_is_deterministic_and_budget_tracks_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = SerperCache(Path(directory))
            payload = {"q": "website design Uganda", "gl": "ug", "hl": "en", "page": 1, "num": 10, "type": "search"}
            cache.put(payload, SAMPLE_RESPONSE)
            self.assertEqual(cache.get(payload), SAMPLE_RESPONSE)
            self.assertEqual(cache.key(payload), cache.key(dict(reversed(list(payload.items())))))
            budget = SearchBudgetManager(1)
            budget.record_cached()
            budget.record_attempt()
            budget.record_success()
            self.assertEqual(budget.remaining, 0)
            self.assertEqual(budget.cached, 1)

    def test_parser_captures_optional_serp_sections(self) -> None:
        parsed = parse_serp(SAMPLE_RESPONSE)
        self.assertEqual(len(parsed["organic"]), 2)
        self.assertEqual(parsed["organic"][0]["domain"], "example.co.ug")
        self.assertEqual(len(parsed["people_also_ask"]), 1)
        self.assertEqual(parsed["related_searches"], ["website development Uganda"])
        self.assertTrue(parsed["features"]["has_local_pack_or_places"])

    def test_normalized_intent_and_relevance(self) -> None:
        intent = classify_intent("website design cost Uganda")
        relevance = score_relevance("website design cost Uganda")
        self.assertIn("COMMERCIAL_INVESTIGATION", intent["intents"])
        self.assertIn("LOCAL", intent["intents"])
        self.assertGreater(relevance["business_relevance"], 40)
        self.assertGreater(relevance["local_relevance"], 50)

    def test_scoring_is_bounded_and_explainable(self) -> None:
        score, reasons = opportunity_score(80, 70, 90, 85, competition=30)
        self.assertTrue(0 <= score <= 100)
        self.assertGreater(len(reasons), 2)

    def test_serp_overlap_clustering_and_warning(self) -> None:
        first = parse_serp(SAMPLE_RESPONSE)
        second = parse_serp({**SAMPLE_RESPONSE, "organic": SAMPLE_RESPONSE["organic"]})
        self.assertEqual(serp_similarity(first, second), 1.0)
        records = [
            {"keyword": "website design Uganda", "opportunity": 80},
            {"keyword": "web design Uganda", "opportunity": 70},
        ]
        clusters = cluster_keywords({"bad": "not-used"} and records, {"website design Uganda": first, "web design Uganda": second})
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(cannibalization_warnings(clusters, {"website design Uganda": first, "web design Uganda": second})), 1)

    def test_on_page_analysis_and_secret_not_rendered(self) -> None:
        from src.pages.fetcher import FetchResult

        html = """<html><head><title>Website Design Uganda</title><meta name='description' content='Uganda website services'><meta name='viewport' content='width=device-width'></head><body><h1>Website Design Uganda</h1><h2>Services</h2><p>Contact us for a business website in Uganda.</p><a href='/about'>About</a><img src='/x.jpg' alt='team'></body></html>"""
        analysis = analyze_page(FetchResult("https://example.co.ug", html, "https://example.co.ug"), "website design Uganda")
        self.assertFalse(analysis["fetch_failed"])
        self.assertTrue(analysis["keyword_in_title"])
        self.assertTrue(analysis["https"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            settings = Settings(serper_api_key="do-not-render", serper_max_searches=1)
            render_report(
                output,
                run_id="test",
                settings=settings,
                budget={"attempted": 0, "successful": 0, "cached": 0, "failed": 0, "remaining": 1},
                records=[{"keyword": "website design Uganda", "intents": ["LOCAL"], "demand_signal": 1, "demand_confidence": "LOW", "uganda_relevance": 1, "commercial_value": 1, "serp_competition": 1, "rankability": 1, "opportunity": 1, "priority": "P3"}],
                clusters=[],
                recommendations=[],
                competitors=[],
                serp_by_keyword={},
                pages=[],
                warnings=[],
            )
            self.assertNotIn("do-not-render", output.read_text(encoding="utf-8"))

    def test_sqlite_schema_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.db")
            database.start_run("run")
            database.save_keyword({"keyword": "website design Uganda", "retained": True})
            self.assertEqual(database.keyword_records()[0]["keyword"], "website design Uganda")
            database.finish_run("run", {"attempted": 1, "successful": 1, "cached": 0, "failed": 0, "remaining": 0})
            self.assertEqual(len(database.rows("research_runs")), 1)
            database.close()


if __name__ == "__main__":
    unittest.main()