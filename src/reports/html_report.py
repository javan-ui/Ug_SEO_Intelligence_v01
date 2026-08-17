from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils.text import html_escape


CSS = """
:root { color-scheme: light; --ink:#17324d; --muted:#59718a; --accent:#0b7285; --line:#d9e4ec; --wash:#f3f8fa; }
* { box-sizing:border-box; } body { margin:0; color:var(--ink); background:#f7fafb; font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
main { max-width:1280px; margin:0 auto; padding:32px 20px 80px; } header { background:linear-gradient(135deg,#17324d,#0b7285); color:white; padding:44px; border-radius:18px; margin-bottom:24px; }
h1,h2,h3 { line-height:1.2; } h1 { font-size:clamp(2rem,5vw,4rem); margin:0 0 12px; } h2 { margin-top:36px; border-bottom:2px solid var(--line); padding-bottom:8px; }
.eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:.76rem; opacity:.8; } .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:22px 0; } .stat { background:white; border:1px solid var(--line); border-radius:12px; padding:16px; } .stat strong { display:block; font-size:1.7rem; color:var(--accent); }
.section { background:white; border:1px solid var(--line); border-radius:14px; padding:22px; margin:20px 0; box-shadow:0 5px 18px #17324d0b; }
.table-wrap { overflow:auto; } table { width:100%; border-collapse:collapse; min-width:720px; } th,td { text-align:left; vertical-align:top; padding:10px; border-bottom:1px solid var(--line); } th { position:sticky; top:0; background:#eaf3f5; cursor:pointer; } tr:nth-child(even) { background:var(--wash); }
a { color:var(--accent); } code { background:#eef5f7; padding:2px 5px; border-radius:4px; } ul { padding-left:22px; } .notice { border-left:4px solid var(--accent); padding:12px 16px; background:#eef8f8; }
@media print { body { background:white; } main { max-width:none; } .section,header { box-shadow:none; break-inside:avoid; } }
"""


def render_report(
    path: Path,
    *,
    run_id: str,
    settings: Any,
    budget: dict[str, int],
    records: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    competitors: list[dict[str, Any]],
    serp_by_keyword: dict[str, dict[str, Any]],
    pages: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    pdf_status: str = "not attempted",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(records, key=lambda item: float(item.get("opportunity", 0)), reverse=True)
    commercial = sorted(records, key=lambda item: float(item.get("commercial_value", 0)), reverse=True)
    rankable = sorted(records, key=lambda item: float(item.get("rankability", 0)), reverse=True)
    counts = {
        "candidates": len(records),
        "validated": len(serp_by_keyword),
        "pages": len(pages),
        "clusters": len(clusters),
        "p0": sum(1 for item in recommendations if item.get("priority") == "P0"),
        "p1": sum(1 for item in recommendations if item.get("priority") == "P1"),
    }
    sort_script = """<script>document.querySelectorAll('th').forEach(function(th){th.addEventListener('click',function(){var table=th.closest('table'),i=Array.from(th.parentNode.children).indexOf(th),rows=Array.from(table.tBodies[0].rows);rows.sort(function(a,b){return a.cells[i].innerText.localeCompare(b.cells[i].innerText,undefined,{numeric:true})});rows.forEach(function(r){table.tBodies[0].appendChild(r)})})});</script>"""
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Uganda SEO Intelligence Report</title><style>{CSS}</style></head><body><main>
<header><div class="eyebrow">Evidence-led market research</div><h1>Uganda SEO Intelligence</h1><p>Research run <code>{html_escape(run_id)}</code> · {html_escape(datetime.now(timezone.utc).isoformat())}</p><p>Search evidence is localized to <strong>Uganda</strong> (<code>gl=ug</code>, <code>hl=en</code>). Scores are internal estimates, not guarantees.</p></header>
<section class="section"><h2>Executive Summary</h2><p>We identified <strong>{counts["candidates"]}</strong> retained candidate keywords, validated <strong>{counts["validated"]}</strong> localized SERPs, analyzed <strong>{counts["pages"]}</strong> competitor page records, and formed <strong>{counts["clusters"]}</strong> topic clusters. The evidence currently supports <strong>{counts["p0"]}</strong> P0 and <strong>{counts["p1"]}</strong> P1 page recommendations.</p><p>The strongest opportunities are determined by observed demand signals, Uganda relevance, commercial intent, and the relative weakness or mismatch of ranking pages. This report does not say that any page will rank #1.</p><div class="notice">Demand Signal Score is an internal estimate based on observed search ecosystem signals. It is not an official monthly Google search-volume figure.</div></section>
<section class="stats">{_stats(counts, budget)}</section>
<section class="section"><h2>Research Configuration</h2><ul><li>Serper country: <code>{html_escape(settings.serper_country)}</code></li><li>Serper language: <code>{html_escape(settings.serper_language)}</code></li><li>Configured search budget: {settings.serper_max_searches}</li><li>PDF status: {html_escape(pdf_status)}</li></ul></section>
<section class="section"><h2>Top 50 Opportunities</h2>{_opportunity_table(ranked[:50])}</section>
<section class="section"><h2>Top Commercial Opportunities</h2>{_opportunity_table(commercial[:50], sort_label="Commercial Value")}</section>
<section class="section"><h2>Top Rankability Opportunities</h2>{_opportunity_table(rankable[:50], sort_label="Rankability")}</section>
<section class="section"><h2>Keyword Clusters</h2>{_cluster_table(clusters)}</section>
<section class="section"><h2>SERP Competition Analysis</h2>{_competition_table(records)}</section>
<section class="section"><h2>Competitor Analysis</h2>{_competitor_table(competitors)}</section>
<section class="section"><h2>Content Gaps</h2>{_content_gap_table(pages)}</section>
<section class="section"><h2>Location and Business-Vertical Opportunities</h2><p>Location and vertical recommendations are generated from the retained keyword set and clustered evidence; the engine does not blindly combine every seed with every city.</p>{_location_table(records)}</section>
<section class="section"><h2>Recommended Site Architecture</h2>{_recommendation_table(recommendations)}</section>
<section class="section"><h2>Page-by-Page Content Briefs</h2>{_briefs(recommendations)}</section>
<section class="section"><h2>Internal Linking Strategy</h2>{_link_graph(recommendations)}</section>
<section class="section"><h2>Cannibalization Warnings</h2>{_warnings(warnings)}</section>
<section class="section"><h2>SERP Evidence Report</h2>{_serp_evidence(serp_by_keyword, pages)}</section>
<section class="section"><h2>Methodology, Scoring, and Limitations</h2><p><strong>Demand:</strong> related searches, People Also Ask, query-family breadth, and repeated discovery. <strong>Competition:</strong> observed result/domain/page strength and SERP feature pressure. <strong>Rankability:</strong> observed weak pages, local gaps, directories, and mixed intent. <strong>Opportunity:</strong> demand 25%, rankability 30%, commercial value 25%, Uganda relevance 20%, with bounded penalties/bonuses. <strong>Confidence:</strong> data completeness and independent evidence, not likelihood of ranking.</p><ul><li>Serper provides Google search-result data, not authoritative keyword-volume figures.</li><li>Competition scores are proprietary internal calculations.</li><li>Page analysis uses publicly accessible information; some pages may block fetching.</li><li>Backlink data is not available from configured data sources.</li><li>Rankings change over time and by context. No score guarantees ranking.</li><li>Search Console data is unavailable until the target site exists and gathers impressions.</li></ul></section>
<section class="section"><h2>Raw Research Statistics</h2><pre>{html_escape(str({"counts": counts, "budget": budget, "run_id": run_id}))}</pre></section>
</main>{sort_script}</body></html>"""
    path.write_text(html, encoding="utf-8")


def _stats(counts: dict[str, int], budget: dict[str, int]) -> str:
    values = [
        ("Candidates retained", counts["candidates"]),
        ("SERPs validated", counts["validated"]),
        ("Pages analyzed", counts["pages"]),
        ("Clusters", counts["clusters"]),
        ("P0 pages", counts["p0"]),
        ("P1 pages", counts["p1"]),
        ("Searches attempted", budget.get("attempted", 0)),
        ("Searches cached", budget.get("cached", 0)),
    ]
    return "".join(f'<div class="stat"><span>{html_escape(label)}</span><strong>{value:,}</strong></div>' for label, value in values)


def _opportunity_table(records: list[dict[str, Any]], sort_label: str = "SEO Opportunity") -> str:
    rows = []
    for index, item in enumerate(records, 1):
        rows.append(
            f"<tr><td>{index}</td><td>{html_escape(item.get('keyword'))}</td><td>{html_escape(', '.join(item.get('intents', [])))}</td><td>{item.get('demand_signal', 0):.1f} ({html_escape(item.get('demand_confidence', 'LOW'))})</td><td>{item.get('uganda_relevance', 0):.1f}</td><td>{item.get('commercial_value', 0):.1f}</td><td>{item.get('serp_competition', 0):.1f}</td><td>{item.get('rankability', 0):.1f}</td><td><strong>{item.get('opportunity', 0):.1f}</strong></td><td>{html_escape(item.get('priority', ''))}</td></tr>"
        )
    return _table(["Rank", "Keyword", "Intent", "Demand / confidence", "Uganda relevance", "Commercial", "Competition", "Rankability", sort_label, "Priority"], rows)


def _cluster_table(clusters: list[dict[str, Any]]) -> str:
    rows = [f"<tr><td>{item['cluster_id']}</td><td>{html_escape(item['primary_keyword'])}</td><td>{html_escape('; '.join(item['keywords']))}</td></tr>" for item in clusters]
    return _table(["Cluster", "Primary keyword", "Grouped keywords"], rows)


def _competition_table(records: list[dict[str, Any]]) -> str:
    rows = [f"<tr><td>{html_escape(item.get('keyword'))}</td><td>{item.get('serp_competition', 0):.1f}</td><td>{item.get('rankability', 0):.1f}</td><td>{html_escape('; '.join(item.get('reasons', [])[-3:]))}</td></tr>" for item in records[:50]]
    return _table(["Keyword", "SERP Competition Score", "Rankability", "Evidence/reasons"], rows)


def _competitor_table(competitors: list[dict[str, Any]]) -> str:
    rows = [f'<tr><td>{html_escape(item.get("keyword"))}</td><td>{item.get("position")}</td><td>{html_escape(item.get("domain"))}</td><td><a href="{html_escape(item.get("url"))}">{html_escape(item.get("title"))}</a></td><td>{html_escape(item.get("domain_type"))}</td><td>{item.get("country_relevance", 0):.1f}</td></tr>' for item in competitors[:100]]
    return _table(["Keyword", "Position", "Domain", "Title / URL", "Domain type", "Uganda relevance"], rows)


def _content_gap_table(pages: list[dict[str, Any]]) -> str:
    rows = [f"<tr><td>{html_escape(item.get('keyword'))}</td><td>{html_escape(item.get('url'))}</td><td>{item.get('word_count', 'n/a')}</td><td>{item.get('local_relevance_score', 'n/a')}</td><td>{html_escape('; '.join(item.get('observed_weaknesses', [])))}</td></tr>" for item in pages[:100]]
    return _table(["Keyword", "URL", "Words", "Local relevance", "Observed weaknesses"], rows)


def _location_table(records: list[dict[str, Any]]) -> str:
    rows = []
    for item in records[:80]:
        keyword = item.get("keyword", "")
        if any(location.casefold() in keyword.casefold() for location in ("kampala", "wakiso", "entebbe", "jinja", "mbarara", "mbale", "gulu", "masaka", "mukono", "fort portal")) or "uganda" in keyword.casefold():
            rows.append(f"<tr><td>{html_escape(keyword)}</td><td>{item.get('opportunity', 0):.1f}</td><td>{html_escape(item.get('priority', ''))}</td></tr>")
    return _table(["Observed location/market keyword", "Opportunity", "Priority"], rows)


def _recommendation_table(recommendations: list[dict[str, Any]]) -> str:
    rows = [f"<tr><td>{html_escape(item.get('priority'))}</td><td>{html_escape(item.get('primary_keyword'))}</td><td>{html_escape(item.get('recommended_url'))}</td><td>{item.get('opportunity_score', 0):.1f}</td><td>{html_escape(item.get('reason_for_creation'))}</td></tr>" for item in recommendations]
    return _table(["Priority", "Primary keyword", "Recommended URL", "Opportunity", "Why"], rows)


def _briefs(recommendations: list[dict[str, Any]]) -> str:
    chunks = []
    for item in recommendations:
        if item.get("priority") not in {"P0", "P1"}:
            continue
        brief = item.get("content_brief", {})
        chunks.append(f"<h3>{html_escape(item.get('primary_keyword'))} · {html_escape(item.get('priority'))}</h3><ul><li>Intent: {html_escape(', '.join(brief.get('search_intent', [])))}</li><li>Audience: {html_escape(brief.get('target_audience'))}</li><li>H2 topics: {html_escape(', '.join(brief.get('suggested_h2_topics', [])))}</li><li>Questions: {html_escape('; '.join(brief.get('questions_to_answer', [])))}</li><li>CTA: {html_escape(brief.get('recommended_cta_type'))}</li></ul>")
    return "".join(chunks) or "<p>No P0/P1 recommendations were supported by current evidence.</p>"


def _link_graph(recommendations: list[dict[str, Any]]) -> str:
    rows = [f"<tr><td>{html_escape(item.get('recommended_url'))}</td><td>{html_escape(', '.join(item.get('internal_link_targets', [])))}</td></tr>" for item in recommendations]
    return _table(["Page", "Suggested internal links"], rows)


def _warnings(warnings: list[dict[str, Any]]) -> str:
    rows = [f"<tr><td>{html_escape(item['page_a'])}</td><td>{html_escape(item['page_b'])}</td><td>{item['shared_serp_ratio']}</td><td>{html_escape(item['recommendation'])}</td></tr>" for item in warnings]
    return _table(["Page A", "Page B", "Shared SERP ratio", "Recommendation"], rows) if rows else "<p>No high-overlap cannibalization warnings were identified from available SERPs.</p>"


def _serp_evidence(serp_by_keyword: dict[str, dict[str, Any]], pages: list[dict[str, Any]]) -> str:
    rows = []
    for keyword, parsed in list(serp_by_keyword.items())[:50]:
        for result in parsed.get("organic", [])[:10]:
            page = next((item for item in pages if item.get("url") == result.get("link")), {})
            rows.append(f'<tr><td>{html_escape(keyword)}</td><td>{result.get("position")}</td><td>{html_escape(result.get("domain"))}</td><td><a href="{html_escape(result.get("link"))}">{html_escape(result.get("title"))}</a></td><td>{html_escape("; ".join(page.get("observed_weaknesses", [])))}</td></tr>')
    return _table(["Keyword", "Position", "Domain", "Title / URL", "Observed weaknesses"], rows)


def _table(headers: list[str], rows: list[str]) -> str:
    if not rows:
        return "<p>No records available for this section.</p>"
    header = "".join(f"<th>{html_escape(value)}</th>" for value in headers)
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'