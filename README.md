# NexusSSD — Agentic AI Fleet Health Copilot

An agentic AI platform that turns SSD SMART telemetry into natural-language diagnostics —
combining predictive failure modeling, semantic retrieval (RAG), SQL reasoning, and
multi-agent orchestration so storage engineers can investigate fleet health and maintenance
risk through a React/FastAPI application.

## Tech stack

- **Backend:** FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 (Python 3.12)
- **Frontend:** React · TypeScript · Tailwind CSS · React Query · Recharts (Vite)
- **Database:** PostgreSQL 16 + pgvector
- **AI/ML:** XGBoost · LlamaIndex · LangGraph · OpenAI / sentence-transformers
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

Apply database migrations (first run):

```bash
docker compose exec backend alembic upgrade head
```

### Option B — Run services locally (no Docker)

**Backend** (Python 3.12):

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Uses the DATABASE_URL from ../.env (Postgres). For a quick DB-less check:
DATABASE_URL="sqlite+pysqlite:///:memory:" uvicorn app.main:app --reload
pytest                       # run backend tests
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
2. ETL pipeline & database schema
3. XGBoost failure prediction model
4. RAG / vector search (LlamaIndex + pgvector)
5. LangGraph multi-agent workflow
6. Dashboard (Fleet Overview, Drive Details, Prediction Explorer, Chat, Metrics)
7. Logging, monitoring, Grafana
8. Deployment (Docker, GitHub Actions, AWS)

## API surface (grows per phase)

`GET /health` · `GET /` — service info. `GET /drives`, `POST /predict`, `POST /retrieve`,
`POST /chat` land in later phases.
