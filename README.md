# Job Title Archaeology

Alternative-data hiring intelligence pipeline. Built for Web Data UNLOCKED hackathon (Track 2: Finance & Market Intelligence).

Job postings on the open web leak hiring intent before earnings calls. Job Title Archaeology turns Bright Data job-listing snapshots into a structured signal: which companies are hiring, which titles are accelerating, where new operating roles emerge. Everything lands in a newspaper-styled archive UI.

## What it does

- **Ingests** Indeed and LinkedIn job postings via Bright Data Web Scraper API
- **Normalizes** raw titles using rule-based cleanup (strips location suffixes, IDs, shift markers, parenthetical noise)
- **Scores** trends by recency × velocity × concentration, grouping postings by canonical title
- **Aggregates** company-level hiring velocity over rolling 30-day windows; resolves tickers (NVDA, AMD, PLTR, MSFT) from raw company names
- **Enriches** top trends with Bright Data SERP API press signals
- **Renders** an editorial archive of emerging titles, plus a Field Reports view that surfaces ticker-level hiring spikes for finance teams

## Bright Data integration

Two products wired in:

- `backend/ingest/sources/brightdata.py` — Web Scraper API (`/datasets/v3/trigger`, `/progress`, `/snapshot`) for Indeed + LinkedIn job listings, retries on transient HTTP errors, resume command for snapshots that outlive the trigger call
- `backend/serp/client.py` — SERP API (`/request`) for press-signal enrichment of top trending titles

Snapshots dedupe on `(source, posting_id)` so weekly re-runs preserve time-series instead of collapsing the same posting across runs.

## Architecture

```
Bright Data → ingest → normalize → trends → archive enrichment → API → React UI
                                       ↓                ↑
                                  companies      Gemini / OpenRouter / Ollama
```

- **Backend**: FastAPI + SQLite (Postgres-compatible), Pydantic models throughout
- **Frontend**: React + Vite + hash routing; newspaper aesthetic, no chart libs (inline SVG)
- **LLM providers**: Gemini for archive metadata + sector breakdown, swappable via CLI flag (`--provider gemini|openrouter|ollama`)
- **Deploy**: single Dockerfile, FastAPI serves both API and built React static, SQLite seeded from `data/seed/` snapshot at container start

## Endpoints

| Route | Purpose |
|---|---|
| `GET /health` | liveness |
| `GET /archive/titles?limit=50` | trending normalized titles |
| `GET /archive/titles/{record_id}` | full dossier with adoption velocity, sector breakdown, SERP press signals |
| `GET /companies?limit=20` | company hiring leaderboard |
| `GET /companies/{ticker_or_key}` | per-company weekly hires + top roles |
| `GET /dashboard/trends?limit=5` | scored trend cards (legacy dashboard view) |

## Local setup

```bash
# python deps
pip install -e ".[dev]"

# frontend deps
npm --prefix frontend ci

# env
cp .env.example .env
# fill BRIGHTDATA_API_TOKEN, BRIGHTDATA_WEB_SCRAPER_ID_INDEED,
# BRIGHTDATA_WEB_SCRAPER_ID_LINKEDIN, GEMINI_API_KEY

# init db (or use seed: cp data/seed/job_title_archaeology.db ./)
python init_db.py

# backend
uvicorn backend.app.main:app --reload --port 8000

# frontend
npm --prefix frontend run dev
```

## CLI commands

```bash
# trigger fresh keyword snapshot (Indeed)
python -m backend.ingest.cli discover \
  --source indeed \
  --keywords "AI Workflow Architect,Climate Risk Modeler,Clinical AI Safety Officer" \
  --locations "United States" \
  --limit-per-input 200

# resume a stalled snapshot by id
python -m backend.ingest.cli resume --snapshot-id sd_xxxx

# ingest a local JSON file (Bright Data export or sample)
python -m backend.ingest.cli import-json data/raw/sample.json

# generate editorial metadata + sector breakdown for top titles
python -m backend.archive.cli generate --limit 50 --provider gemini --request-delay 2

# generate cover images
python -m backend.archive.cli generate-images --limit 10

# enrich top titles with SERP press signals
python -m backend.archive.cli enrich-serp --limit 30

# recompute company hiring leaderboard
python -m backend.companies.cli recompute
```

## Data model

```
raw_job_postings        — envelope of every scraped record, dedup on posting_id
normalized_titles       — canonical title + token_key
job_posting_titles      — link table raw → normalized
archive_metadata_cache  — LLM-generated editorial metadata per title
company_signals         — recomputed hiring velocity per company
serp_signals            — cached SERP API hits per title
```

## Tests

```bash
python -m pytest                       # 133 backend tests
npm --prefix frontend test -- --run    # 12 frontend tests
```

Tests cover ingest (mocked Bright Data via respx), normalize rules, trend scoring, archive rendering, company aggregation, SERP cache round-trip, and React routing/filtering.

## Deploy

Render web service (free tier):

1. Connect repo on render.com → Web Service → Docker → `./Dockerfile` → free plan
2. Set env vars: `DATABASE_URL=sqlite:////app/runtime/job_title_archaeology.db`, `PORT=8080`, `BRIGHTDATA_API_TOKEN`, `BRIGHTDATA_WEB_SCRAPER_ID_INDEED`, `BRIGHTDATA_WEB_SCRAPER_ID_LINKEDIN`, `GEMINI_API_KEY`
3. Deploy. `entrypoint.sh` seeds SQLite from `data/seed/` on first boot.

To refresh production data:

```bash
# trigger snapshots, recompute, copy seed, push
python -m backend.ingest.cli discover --source indeed --keywords "..."
python -m backend.companies.cli recompute
cp job_title_archaeology.db data/seed/
git commit -am "data: refresh seed snapshot"
git push
```

`fly.toml` also included for Fly.io deploys (paid).

## Project layout

```
backend/
  app/main.py            FastAPI entrypoint, mounts /assets and SPA fallback
  archive/               editorial dossier rendering, LLM metadata cache, image gen
  companies/             ticker resolver, hiring velocity aggregation
  dashboard/             scored trend cards
  db/                    sqlite/postgres connection + migrations
  ingest/                Bright Data Web Scraper API client + JSONL/SQLite sinks
  narratives/            LLM provider abstractions (Gemini / OpenRouter / Ollama)
  normalize/             rule-based title cleanup
  serp/                  Bright Data SERP API client + cache
  trends/                grouping, scoring, weekly bucket queries
frontend/src/            React + Vite, hash-routed archive + field reports
data/seed/               SQLite snapshot bundled into Docker image
configs/                 ingest config defaults
init_db.py               local migration runner
Dockerfile               single-stage build → FastAPI serves UI + API
entrypoint.sh            seeds DB from snapshot if missing, then uvicorn
fly.toml                 Fly.io deploy config
render.yaml              Render Blueprint config
```

## Stack

- Python 3.11+, FastAPI, Pydantic v2, Typer, httpx, psycopg, google-genai
- React 18, Vite, TypeScript, Vitest + Testing Library
- SQLite (default) / Postgres (swap via `DATABASE_URL`)
- Bright Data Web Scraper API + SERP API
- Gemini 2.5 Flash (default) / OpenRouter / local Ollama for archive metadata generation

## License

Hackathon submission. Not yet licensed for redistribution.
