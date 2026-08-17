# Uganda SEO Intelligence Research Engine

A deterministic, evidence-first Python research engine for discovering and prioritizing Google search opportunities for Uganda-focused website, ecommerce, hosting, local SEO, and online-presence services.

It does not claim official search volume, true keyword difficulty, or guaranteed rankings. It records live SERP evidence from Serper, analyzes publicly accessible competitor pages, scores opportunities with explainable heuristics, clusters related keywords, proposes a site architecture, and writes machine-readable data plus a self-contained HTML report.

## Quick start

```bash
cd SEO_Intelligence
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Put your key in .env locally, or use Replit Secrets as described below.

python -m src.main --dry-run
python -m src.main --mode test
python -m src.main --mode full --resume
```

The first live test is intentionally limited to `website design Uganda`, localized with `gl=ug` and `hl=en`. It verifies caching, parsing, and scoring without spending a large budget.

## Where to put the API keys

### In Replit

Use the Secrets panel, not a committed file:

1. Open **Tools → Secrets** (or the project’s Secrets panel).
2. Add `SERPER_API_KEY`.
3. If you will use an external scraping service, add `SCRAPING_API_KEY` too.
4. Set `SCRAPING_API_URL` as a normal environment variable if the provider has an endpoint.

The program reads these environment variables at runtime. It never prints their values, writes them to reports, or stores them in SQLite.

### On GitHub Actions

In the GitHub repository, open:

**Settings → Secrets and variables → Actions → New repository secret**

Create:

- `SERPER_API_KEY` — required for live Serper research.
- `SCRAPING_API_KEY` — optional, only if `SCRAPING_API_URL` is configured.

Repository variables may be used for non-secret scraper configuration:

- `SCRAPING_API_URL`
- `SCRAPING_API_KEY_HEADER` (default: `Authorization`)
- `SCRAPING_API_KEY_PREFIX` (default: `Bearer `)

The workflow passes `SERPER_API_KEY` and the optional scraper key as masked secrets. Never place a real key in `.env.example`, YAML, Python files, a commit message, or generated output.

### Local `.env`

`.env` is ignored by Git and is loaded automatically using a small standard-library parser:

```bash
cp .env.example .env
# Edit SEO_Intelligence/.env and replace the placeholders:
# SERPER_API_KEY=your-key
# SCRAPING_API_KEY=your-scraper-key
# SCRAPING_API_URL=https://your-provider.example/fetch
python -m src.main --mode test
```

The checked-in `.env.example` documents the supported names.

## Architecture

```text
config/       Settings, exact Uganda seed concepts, and scoring weights
src/serper/   Localized HTTP client, response cache, and search budget
src/discovery/ Candidate extraction and normalization
src/filtering/ Relevance and deterministic intent classification
src/serp/     SERP parsing, features, and competitor heuristics
src/pages/    Conservative page fetching and on-page analysis
src/scoring/  Demand, competition, rankability, opportunity, confidence
src/clustering/ Keyword grouping, SERP overlap, cannibalization
src/architecture/ Page recommendations and internal-link graph
src/reports/ HTML report and optional PDF conversion
data/         SQLite history, raw SERPs, intermediate data, and final exports
tests/        Unit tests with mocked Serper responses
```

## Research modes

```bash
python -m src.main --dry-run
python -m src.main --mode test
python -m src.main --mode discovery
python -m src.main --mode validation
python -m src.main --mode report
python -m src.main --mode full --resume
```

- `--dry-run` validates configuration, seeds, paths, database, and templates without consuming credits.
- `--mode test` performs the required one-query live check.
- `discovery` expands seed searches and saves candidates.
- `validation` validates retained candidates, fetches selected pages, and scores them.
- `report` rebuilds exports and reports from stored SQLite data.
- `full` runs all phases. `--resume` reuses cached SERPs and existing database rows.

The default budget is 2,500 attempted searches with planning guidance of 300 discovery, 500 expansion, 1,300 validation, 250 competitor investigation, and 150 reserve/recovery. The budget manager enforces the configured total; unused credits are preserved.

## Outputs

- `reports/uganda_seo_intelligence_report.html` — mandatory self-contained report.
- `reports/uganda_seo_intelligence_report.pdf` — optional PDF if WeasyPrint is installed.
- `data/final/keywords.csv`
- `data/final/keywords.json`
- `data/final/clusters.json`
- `data/final/competitors.json`
- `data/final/site_architecture.json`
- `data/final/page_recommendations.json`
- `data/seo_intelligence.db` — historical SQLite research runs.
- `data/raw_serper/` — exact successful Serper JSON responses keyed by request hash.
- `data/errors.log` — stage failures that did not stop the run.

Generated files are intentionally ignored by Git except for directory placeholders. The GitHub workflow commits generated artifacts after a run; remove those ignore rules if you want the data committed.

## Localization and scoring

All Serper requests use one central configuration:

```text
SERPER_COUNTRY=ug
SERPER_LANGUAGE=en
```

The pipeline distinguishes:

- **Demand Signal Score** — an internal estimate from related searches, PAA, query-family breadth, and repeated discovery; not official monthly volume.
- **SERP Competition Score** — this project’s model of observed SERP strength, not true keyword difficulty.
- **Rankability** — an explainable estimate of how promising weak or mismatched SERPs may be for a strong new site.
- **Evidence Confidence** — how complete and consistent the observed evidence is; it is not the same as opportunity.

The initial opportunity model weights demand 25%, rankability 30%, commercial value 25%, and Uganda relevance 20%, with bounded penalties and bonuses. Every recommendation includes reasons and evidence notes.

## Scraping API adapter

Direct HTTP fetching is the default and follows conservative timeouts, redirects, a clear user agent, limited concurrency, and no CAPTCHA or anti-bot bypass. If you configure `SCRAPING_API_URL`, the optional fallback sends:

```text
GET <SCRAPING_API_URL>?url=<competitor-url>
Authorization: Bearer <SCRAPING_API_KEY>
```

If your provider uses a different request shape, adjust `src/pages/fetcher.py` in the single `ScrapingApi` adapter; do not spread provider-specific secrets or logic through the analysis pipeline. Failed fetches remain explicit and are never converted into a zero score.

## GitHub Actions

`.github/workflows/research.yml` is manual-only (`workflow_dispatch`). It installs Python dependencies, runs the full resumable engine, attempts PDF generation without failing the research run, and commits generated data/reports back to the repository. Test locally or in Replit before running a large GitHub job.

## Limitations

Serper provides Google result data, not authoritative keyword-volume figures. Results vary with time and context. Public pages may block automated fetching. Backlink data is not available from configured sources. Scores are proprietary internal calculations and do not guarantee rankings. Search Console data is unavailable until the target site exists and receives impressions.

## Troubleshooting

- `SERPER_API_KEY is required`: set it in Replit Secrets, your shell, or GitHub Actions.
- `401/403`: verify the key and account permissions; the raw response is not written if the request fails.
- `429`: the client retries with backoff, records the failure, and the budget remains honest.
- empty result sections: Serper fields are optional; the parser records what exists.
- blocked competitor pages: the report records `fetch_failed` and reason instead of assigning zero.
- PDF unavailable: HTML remains the primary report and the run still completes.

## License

Private project scaffold; choose and add a license before publishing.