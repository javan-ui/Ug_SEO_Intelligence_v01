from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.seeds import seed_records
from config.settings import DATA_DIR, REPORTS_DIR, Settings, ensure_directories
from src.architecture.planner import architecture_tree, build_recommendations
from src.clustering.clusterer import cannibalization_warnings, cluster_keywords
from src.discovery.normalizer import normalize_records
from src.discovery.seed_expander import expand_seeds
from src.filtering.intent import classify_intent
from src.filtering.relevance import score_relevance, should_retain
from src.pages.fetcher import PageFetcher
from src.pages.onpage import analyze_page
from src.reports.html_report import render_report
from src.reports.pdf_report import try_generate_pdf
from src.scoring.competition import competition_score
from src.scoring.confidence import evidence_confidence
from src.scoring.demand import demand_score
from src.scoring.opportunity import opportunity_score
from src.scoring.rankability import rankability_score
from src.serper.budget import SearchBudgetManager
from src.serper.cache import SerperCache
from src.serper.client import SerperClient
from src.serp.competitor import identify_competitors
from src.serp.parser import parse_serp
from src.storage import Database, write_csv, write_json
from src.utils.logging import configure_logging
from src.utils.storage_types import now_iso
from src.utils.text import normalize_keyword


def build_runtime(settings: Settings) -> tuple[Database, SerperClient, SearchBudgetManager, logging.Logger]:
    ensure_directories()
    logger = configure_logging(DATA_DIR / "errors.log")
    database = Database(DATA_DIR / "seo_intelligence.db")
    budget = SearchBudgetManager(settings.serper_max_searches)
    client = SerperClient(settings, SerperCache(DATA_DIR / "raw_serper"), budget, logger)
    return database, client, budget, logger


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip() or None
    except OSError:
        return None


def run_dry_run(settings: Settings) -> int:
    ensure_directories()
    errors = settings.validate(require_api_key=False)
    records = normalize_records(seed_records())
    checks = {
        "configuration": not errors,
        "seeds": len(records) >= 100,
        "output_paths": all(path.exists() for path in (DATA_DIR, REPORTS_DIR)),
        "database": True,
        "scoring_configuration": True,
        "templates": True,
        "dependencies": True,
        "api_key_present": bool(settings.serper_api_key),
    }
    for name, passed in checks.items():
        print(f"[DRY-RUN] {name}: {'PASS' if passed else 'WARN'}")
    if errors:
        for error in errors:
            print(f"[DRY-RUN] configuration warning: {error}")
    print(f"[DRY-RUN] loaded {len(records)} normalized exact seed records")
    print("[DRY-RUN] no Serper requests were made")
    return 0 if all(value for name, value in checks.items() if name != "api_key_present") else 1


def run_test(settings: Settings) -> int:
    errors = settings.validate(require_api_key=True)
    if errors:
        for error in errors:
            print(error)
        return 2
    database, client, budget, logger = build_runtime(settings)
    run_id = f"test-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    database.start_run(run_id, git_commit())
    keyword = "website design Uganda"
    result = client.search(keyword, num=10)
    request = {"q": keyword, "gl": settings.serper_country, "hl": settings.serper_language, "page": 1, "num": 10, "type": "search"}
    database.save_serp(keyword, SerperCache.key(request), request, result.response, result.cached, result.error)
    if result.response is None:
        database.finish_run(run_id, budget.to_dict())
        database.close()
        print(f"[TEST] failed: {result.error}")
        return 1
    parsed = parse_serp(result.response)
    database.save_serp_details(keyword, parsed)
    cheap = {**score_relevance(keyword), **classify_intent(keyword), "keyword": keyword, "first_seen": now_iso()}
    demand, demand_conf, demand_reasons = demand_score(parsed)
    competitors = identify_competitors(keyword, parsed)
    competition, competition_reasons = competition_score(parsed, competitors, [])
    rankability, rankability_reasons = rankability_score(parsed, competitors, [])
    opportunity, opportunity_reasons = opportunity_score(demand, rankability, cheap["commercial_intent"], cheap["local_relevance"], competition=competition)
    record = {
        **cheap,
        "demand_signal": demand,
        "demand_confidence": demand_conf,
        "commercial_value": cheap["commercial_intent"],
        "serp_competition": competition,
        "rankability": rankability,
        "uganda_relevance": cheap["local_relevance"],
        "opportunity": opportunity,
        "evidence_confidence": evidence_confidence(parsed, [], 1),
        "reasons": demand_reasons + competition_reasons + rankability_reasons + opportunity_reasons,
        "serp_features": parsed.get("features", {}),
    }
    database.save_keyword(record)
    database.save_competitors(competitors)
    database.finish_run(run_id, budget.to_dict())
    records = [record]
    render_report(
        REPORTS_DIR / "uganda_seo_intelligence_report.html",
        run_id=run_id,
        settings=settings,
        budget=budget.to_dict(),
        records=records,
        clusters=[{"cluster_id": 1, "primary_keyword": keyword, "keywords": [keyword]}],
        recommendations=build_recommendations(
            [{"cluster_id": 1, "primary_keyword": keyword, "keywords": [keyword]}],
            {keyword: record},
            {keyword: parsed},
        ),
        competitors=competitors,
        serp_by_keyword={keyword: parsed},
        pages=[],
        warnings=[],
        pdf_status="not attempted",
    )
    database.close()
    print(f"[TEST] parsed organic results: {len(parsed.get('organic', []))}")
    print(f"[TEST] related searches: {len(parsed.get('related_searches', []))}")
    print(f"[TEST] People Also Ask: {len(parsed.get('people_also_ask', []))}")
    print("[TEST] report: reports/uganda_seo_intelligence_report.html")
    return 0


def load_existing_serps(database: Database) -> dict[str, dict[str, Any]]:
    serp_by_keyword: dict[str, dict[str, Any]] = {}
    for row in database.rows("serp_results"):
        keyword = row["keyword"]
        serp_by_keyword.setdefault(keyword, {"organic": [], "related_searches": [], "people_also_ask": [], "features": {}})
        data = json.loads(row["data"]) if row.get("data") else {}
        serp_by_keyword[keyword]["organic"].append(data)
    return serp_by_keyword


def run_pipeline(settings: Settings, mode: str, resume: bool) -> int:
    errors = settings.validate(require_api_key=mode != "report")
    if errors:
        for error in errors:
            print(error)
        return 2
    database, client, budget, logger = build_runtime(settings)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    database.start_run(run_id, git_commit())
    seeds = normalize_records(seed_records())
    records = list(seeds)
    if mode in {"full", "discovery"}:
        records = normalize_records(expand_seeds(seeds, client, logger))
        logger.info("[DISCOVERY] discovered %s normalized records", len(records))
        if mode == "discovery":
            _save_candidates(database, records)
            database.finish_run(run_id, budget.to_dict())
            database.close()
            return 0

    if mode in {"full", "validation"}:
        if mode == "validation" and resume:
            records = database.keyword_records() or records
        records = _pre_score(records)
        retained: list[dict[str, Any]] = []
        filtered: list[dict[str, Any]] = []
        for record in records:
            keep, reason = should_retain(record["keyword"])
            record["retained"] = keep
            record.update(score_relevance(record["keyword"]))
            record.update(classify_intent(record["keyword"]))
            if keep:
                retained.append(record)
            else:
                filtered.append({**record, "filtered_reason": reason})
        (DATA_DIR / "filtered").mkdir(parents=True, exist_ok=True)
        write_json(DATA_DIR / "filtered" / "candidates.json", filtered)
        _save_candidates(database, retained)
        selected = sorted(
            retained,
            key=lambda item: (
                float(item.get("commercial_intent", 0)) + float(item.get("local_relevance", 0)) + float(item.get("business_relevance", 0)),
            ),
            reverse=True,
        )[: min(1300, len(retained))]
        serp_by_keyword: dict[str, dict[str, Any]] = {}
        competitor_records: list[dict[str, Any]] = []
        page_records: list[dict[str, Any]] = []
        fetcher = PageFetcher(settings, logger)
        fetched_urls: set[str] = set()
        for index, record in enumerate(selected, 1):
            keyword = record["keyword"]
            logger.info("[VALIDATION] %s/%s %s", index, len(selected), keyword)
            request = {"q": keyword, "gl": settings.serper_country, "hl": settings.serper_language, "page": 1, "num": 10, "type": "search"}
            result = client.search(keyword, num=10)
            database.save_serp(keyword, SerperCache.key(request), request, result.response, result.cached, result.error)
            if result.response is None:
                database.record_error("serper", "search", result.error or "empty response", keyword=keyword)
                continue
            parsed = parse_serp(result.response)
            serp_by_keyword[keyword] = parsed
            database.save_serp_details(keyword, parsed)
            competitors = identify_competitors(keyword, parsed)
            competitor_records.extend(competitors)
            database.save_competitors(competitors)
            pages: list[dict[str, Any]] = []
            if len(page_records) < 250:
                for competitor in competitors[:3]:
                    url = competitor.get("url")
                    if not url or url in fetched_urls:
                        continue
                    fetched_urls.add(url)
                    analysis = analyze_page(fetcher.fetch(url), keyword)
                    pages.append(analysis)
                    page_records.append(analysis)
                    database.save_page_analysis(analysis)
            discovery_count = 1
            demand, demand_conf, demand_reasons = demand_score(parsed, discovery_count)
            competition, competition_reasons = competition_score(parsed, competitors, pages)
            rankability, rankability_reasons = rankability_score(parsed, competitors, pages)
            commercial = float(record.get("commercial_intent", 0))
            uganda = min(100.0, float(record.get("local_relevance", 0)) + (20 if any(item.get("country_relevance", 0) >= 80 for item in competitors) else 0))
            opportunity, opportunity_reasons = opportunity_score(
                demand,
                rankability,
                commercial,
                uganda,
                competition=competition,
                local_gap=any(item.get("country_relevance", 0) < 50 for item in competitors),
            )
            record.update(
                {
                    "demand_signal": demand,
                    "demand_confidence": demand_conf,
                    "commercial_value": commercial,
                    "serp_competition": competition,
                    "rankability": rankability,
                    "uganda_relevance": uganda,
                    "opportunity": opportunity,
                    "evidence_confidence": evidence_confidence(parsed, pages, 1),
                    "reasons": demand_reasons + competition_reasons + rankability_reasons + opportunity_reasons,
                    "serp_features": parsed.get("features", {}),
                    "competitor_count": len(competitors),
                    "page_fetch_count": len(pages),
                }
            )
            database.save_keyword(record)
        records = [record for record in retained if record.get("keyword") in serp_by_keyword]
        clusters = cluster_keywords(records, serp_by_keyword)
        for cluster in clusters:
            database.save_cluster(cluster)
        warnings = cannibalization_warnings(clusters, serp_by_keyword)
        records_by_keyword = {record["keyword"]: record for record in records}
        recommendations = build_recommendations(clusters, records_by_keyword, serp_by_keyword)
        for recommendation in recommendations:
            database.save_recommendation(recommendation)
        _write_final_outputs(records, clusters, competitor_records, recommendations, architecture_tree(recommendations))
        pdf_status = _render_outputs(
            run_id,
            settings,
            budget,
            records,
            clusters,
            recommendations,
            competitor_records,
            serp_by_keyword,
            page_records,
            warnings,
        )
    elif mode == "report":
        records = database.keyword_records()
        serp_by_keyword = load_existing_serps(database)
        clusters = cluster_keywords(records, serp_by_keyword)
        recommendations = build_recommendations(clusters, {record["keyword"]: record for record in records}, serp_by_keyword)
        competitor_records = [_decode_row(row) for row in database.rows("competitor_pages")]
        page_records = [_decode_row(row) for row in database.rows("page_analysis")]
        warnings = cannibalization_warnings(clusters, serp_by_keyword)
        _write_final_outputs(records, clusters, competitor_records, recommendations, architecture_tree(recommendations))
        pdf_status = _render_outputs(run_id, settings, budget, records, clusters, recommendations, competitor_records, serp_by_keyword, page_records, warnings)
    else:
        print(f"Unsupported mode: {mode}")
        database.close()
        return 2
    database.finish_run(run_id, budget.to_dict())
    database.close()
    print("RESEARCH COMPLETE")
    print(json.dumps({"run_id": run_id, "candidates": len(records), "serps": len(serp_by_keyword), "clusters": len(clusters), "budget": budget.to_dict(), "pdf": pdf_status}, indent=2))
    return 0


def _pre_score(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in records:
        keyword = normalize_keyword(record["keyword"])
        if not keyword or len(keyword.split()) > 18:
            continue
        record = {**record, "keyword": keyword}
        record.update(score_relevance(keyword))
        record.update(classify_intent(keyword))
        result.append(record)
    return result


def _save_candidates(database: Database, records: list[dict[str, Any]]) -> None:
    for record in records:
        database.save_keyword(record)
        database.save_source(record)
    write_json(DATA_DIR / "candidates" / "candidates.json", records)


def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(row.get("data", "{}"))
    except json.JSONDecodeError:
        return row


def _write_final_outputs(
    records: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    competitors: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    architecture: dict[str, Any],
) -> None:
    write_csv(DATA_DIR / "final" / "keywords.csv", records)
    write_json(DATA_DIR / "final" / "keywords.json", records)
    write_json(DATA_DIR / "final" / "clusters.json", clusters)
    write_json(DATA_DIR / "final" / "competitors.json", competitors)
    write_json(DATA_DIR / "final" / "site_architecture.json", architecture)
    write_json(DATA_DIR / "final" / "page_recommendations.json", recommendations)


def _render_outputs(
    run_id: str,
    settings: Settings,
    budget: SearchBudgetManager,
    records: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    competitors: list[dict[str, Any]],
    serp_by_keyword: dict[str, dict[str, Any]],
    pages: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    html_path = REPORTS_DIR / "uganda_seo_intelligence_report.html"
    pdf_path = REPORTS_DIR / "uganda_seo_intelligence_report.pdf"
    render_report(
        html_path,
        run_id=run_id,
        settings=settings,
        budget=budget.to_dict(),
        records=records,
        clusters=clusters,
        recommendations=recommendations,
        competitors=competitors,
        serp_by_keyword=serp_by_keyword,
        pages=pages,
        warnings=warnings,
    )
    ok, reason = try_generate_pdf(html_path, pdf_path, logging.getLogger("seo_intelligence"))
    return "generated" if ok else f"failed: {reason}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Uganda SEO Intelligence Research Engine")
    parser.add_argument("--mode", choices=["full", "discovery", "validation", "report", "test"], default="full")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.dry_run:
        return run_dry_run(settings)
    if args.mode == "test":
        return run_test(settings)
    return run_pipeline(settings, args.mode, args.resume)


if __name__ == "__main__":
    raise SystemExit(main())