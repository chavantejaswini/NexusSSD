# NexusSSD — Agentic AI Fleet Health Copilot

An agentic AI platform that turns SSD SMART telemetry into natural-language diagnostics —
combining predictive failure modeling, semantic retrieval (RAG), SQL reasoning, and
multi-agent orchestration so storage engineers can investigate fleet health and maintenance
risk through a React/FastAPI application.

## Tech stack

- **Backend:** FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 (Python 3.12)
- **Frontend:** React · TypeScript · Tailwind CSS · React Query · Recharts (Vite)
- **Database:** PostgreSQL 16 + pgvector
- **AI/ML:** XGBoost · LlamaIndex over pgvector (native pgvector fallback) ·
  LangGraph · pluggable embeddings (offline hashing default · OpenAI or
  sentence-transformers optional)
- **DevOps:** Docker Compose · GitHub Actions · Grafana

## Repository layout

```
NexusSSD/
├── docker-compose.yml     # db (pgvector) + backend + frontend
├── backend/               # FastAPI app, Alembic migrations, tests
│   └── app/               # core/ db/ models/ schemas/ api/ services/ etl/ agents/
├── frontend/              # React + Vite dashboard
├── ml/                    # XGBoost training + feature engineering
├── data/                  # synthetic + Backblaze telemetry, RAG docs
└── docs/                  # architecture notes
```

## Getting started

### Option A — Docker Compose (full stack; requires Docker Desktop)

```bash
cp .env.example .env
docker compose up --build
# API   → http://localhost:8000  (docs at /docs)
# UI    → http://localhost:5173
```

Apply database migrations and seed telemetry (first run):

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.etl.loader --source synthetic --drives 200 --days 90
```

### Option B — Run services locally (no Docker)

**Backend** (Python 3.12):

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ml]"                             # ml extras for XGBoost
# macOS only: XGBoost needs the OpenMP runtime -> `brew install libomp`
# RAG backends: the offline default needs nothing extra. For LlamaIndex-over-pgvector
# (used automatically on Postgres) add: pip install -e ".[llamaindex,ai]"
alembic upgrade head                                   # create schema
python -m app.etl.loader --source synthetic --drives 200 --days 90   # seed telemetry
python -m app.ml.train --score                         # train model + score fleet
python -m app.rag.ingest                               # ingest sample SSD docs (RAG)
uvicorn app.main:app --reload                          # serve API
pytest                                                 # run backend tests

# Quick DB-less smoke check (SQLite, no schema needed for /health):
DATABASE_URL="sqlite+pysqlite:///:memory:" uvicorn app.main:app --reload
```

**Frontend** (Node 20):

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
npm run build                # type-check + production build
```

## Build phases

1. **Skeleton** — Docker Compose, FastAPI, React, Postgres+pgvector, `/health` ✅
2. **ETL pipeline & database schema** — 8 tables, synthetic + Backblaze sources, `/drives` ✅
3. **XGBoost failure prediction model** — training + calibration, `/predict`, fleet scoring + alerts ✅
4. **RAG / vector search** — LlamaIndex over pgvector (native fallback), pluggable embeddings, `/retrieve` ✅
5. LangGraph multi-agent workflow
6. Dashboard (Fleet Overview, Drive Details, Prediction Explorer, Chat, Metrics)
7. Logging, monitoring, Grafana
8. Deployment (Docker, GitHub Actions, AWS)

## API surface (grows per phase)

`GET /health` · `GET /` — service info. `GET /drives` (paged, `?status=` filter) ·
`GET /drives/{id}` (drive + telemetry + latest prediction) · `POST /predict`
(by `drive_id` or raw `features`; returns probability, risk band, top features) ·
`POST /retrieve` (semantic search over ingested docs, returns cited chunks).
`POST /chat` lands in Phase 5.
