# Deployment

This document covers running NexusSSD in production. Two paths are described: a
single-host Docker Compose deployment (simplest) and an AWS deployment
(ECS/Fargate + RDS).

## Images

- **backend** — `backend/Dockerfile` (Python 3.12, installs `.[ml,ai,llamaindex,agents,monitoring]`,
  includes `libgomp1` for XGBoost). Runs `uvicorn app.main:app`.
- **frontend** — `frontend/Dockerfile.prod` (multi-stage: Vite build → nginx).
  The API URL is baked at build time via the `VITE_API_BASE_URL` build arg, so it
  must be set to the backend's public URL when building.

CI builds both images on every push (`.github/workflows/ci.yml`).

## Configuration (environment)

| Variable | Purpose | Example |
|---|---|---|
| `DATABASE_URL` | Postgres+pgvector DSN | `postgresql+psycopg://user:pass@host:5432/nexus` |
| `CORS_ORIGINS` | Allowed UI origins (comma-sep) | `https://app.example.com` |
| `OPENAI_API_KEY` | Enables OpenAI LLM/embeddings (optional) | `sk-…` |
| `LLM_PROVIDER` | `auto` \| `openai` \| `local` | `auto` |
| `EMBEDDING_DIM` | Must match the embedder + `embeddings` column | `1536` |
| `RAG_BACKEND` | `auto` \| `native` \| `llamaindex` | `auto` |
| `VITE_API_BASE_URL` | (frontend build arg) public API URL | `https://api.example.com` |

Never bake secrets into images. Supply them at runtime (ECS task secrets, SSM
Parameter Store, or a `.env` on the host — never committed).

## Option A — single host (Docker Compose)

```bash
cp .env.example .env         # set POSTGRES_*, OPENAI_API_KEY, etc.
VITE_API_BASE_URL=http://<host>:8000 \
  docker compose -f docker-compose.prod.yml up --build -d
```

The backend container runs `alembic upgrade head` before starting, so the schema
is created/updated on deploy. Then seed data and train once:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python -m app.etl.loader --source synthetic --drives 200 --days 90
docker compose -f docker-compose.prod.yml exec backend python -m app.ml.train --score
docker compose -f docker-compose.prod.yml exec backend python -m app.rag.ingest
```

Ports: UI `:8080`, API `:8000`, Grafana `:3000`, Prometheus `:9090`.

## Option B — AWS (ECS/Fargate + RDS)

1. **Database** — RDS for PostgreSQL 16 with the `vector` extension enabled
   (`CREATE EXTENSION vector;`). Put it in a private subnet; allow the backend
   security group on 5432.
2. **Images** — push backend + frontend images to ECR (extend CI with an ECR
   login + `docker push` on `main`).
3. **Backend service** — ECS Fargate service from the backend image. Inject
   `DATABASE_URL`, `CORS_ORIGINS`, and `OPENAI_API_KEY` as task secrets (SSM /
   Secrets Manager). Run `alembic upgrade head` as a one-off task on each deploy
   (or keep the compose-style `sh -c "alembic upgrade head && uvicorn …"`).
4. **Frontend** — either serve the nginx image behind the same ALB, or drop the
   built `dist/` on S3 + CloudFront. Build it with `VITE_API_BASE_URL` pointing at
   the backend's public URL/ALB.
5. **Load balancer** — an ALB routes the API hostname to the backend target group
   (health check `GET /health`) and the app hostname to the frontend.
6. **Observability** — scrape `/metrics` with Amazon Managed Prometheus (or the
   bundled Prometheus container) and visualize with the provided Grafana
   dashboard (`infra/grafana/dashboards/nexusssd.json`).
7. **Model artifacts** — bake the trained `ml/artifacts/` into the image, or store
   them on S3 and set `MODEL_ARTIFACT_DIR` to a mounted path pulled at startup.

## CI/CD

`.github/workflows/ci.yml` runs on push/PR to `main`:
- **backend** — ruff lint + pytest (with `libgomp1` for XGBoost)
- **frontend** — `tsc` typecheck + Vite build
- **docker-build** — builds both images

To add continuous deployment, extend the workflow (gated on `main`) with an ECR
login, `docker push`, and an ECS service update / task-definition deploy.
