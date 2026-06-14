# FairLens

> AI Fairness Audit Platform — upload a dataset with model predictions, get back a regulator-grade fairness audit mapped to the EU AI Act, NIST AI RMF, and ISO/IEC 42001.

**Status:** Phase 2 — production-grade. Auth (JWT + httpOnly cookies + refresh), upload (with MIME / magic-byte / NUL sniffing), audit pipeline, SHAP explainability with proxy-discrimination warnings, mitigation suggestions, multi-page PDF reports, observability (Prometheus + structured logs), rate limiting, CI with strict mypy + ruff, and Render deployment config. Demo runs end-to-end on the Adult Income dataset.

The frontend is a code-split React/Vite SPA with a minimalist dark-glass design system and a lazy-loaded WebGL (three.js / @react-three/fiber) prism — the 3D assets ship in their own chunk and never enter the initial page load.

## What it does

You give FairLens a CSV containing a `label` column (ground truth), a `prediction` column (your model's output), and one or more sensitive attributes (e.g. `sex`, `race`). It computes seven fairness metrics for each sensitive attribute, scores the system on a 0–100 fairness scale, classifies it Low / Medium / High Risk, and maps every metric to the specific clauses of the EU AI Act, NIST AI RMF, and ISO/IEC 42001 that govern it.

### Fairness metrics

| Metric | Formula | Pass when |
|---|---|---|
| Demographic parity difference | max(SR_g) − min(SR_g) | ≤ 0.10 |
| Disparate impact ratio | min(SR_g) / max(SR_g) | ≥ 0.80 (EEOC 4/5ths) |
| Equal opportunity difference | max(TPR_g) − min(TPR_g) | ≤ 0.10 |
| Equalized odds difference | max(TPR gap, FPR gap) | ≤ 0.10 |
| Predictive parity difference | max(PPV_g) − min(PPV_g) | ≤ 0.10 |
| Calibration difference | avg(per-bucket gaps) | ≤ 0.10 |
| Individual fairness consistency | mean fraction of k-NN sharing prediction | ≥ 0.75 |

The math is in [`backend/app/services/fairness/metrics.py`](backend/app/services/fairness/metrics.py) and is verified against hand-calculated values in [`backend/tests/test_fairness_metrics.py`](backend/tests/test_fairness_metrics.py).

## Architecture

```
┌─────────────┐   HTTPS   ┌──────────────┐   asyncpg  ┌──────────┐
│  Frontend   │ ────────▶ │   FastAPI    │ ─────────▶ │ Postgres │
│ (React/TS)  │           │  (uvicorn)   │            └──────────┘
└─────────────┘           │              │   sync ┌──────────┐
                          │              │ ─────▶ │  Redis   │ ◀──┐
                          └──────┬───────┘        └──────────┘    │
                                 │ Celery enqueue                  │ progress
                                 ▼                                 │
                          ┌──────────────┐                         │
                          │ Celery Worker│ ────────────────────────┘
                          │ (fairness +  │
                          │  regulatory) │
                          └──────┬───────┘
                                 │ S3 API
                                 ▼
                          ┌──────────────┐
                          │ MinIO (CSVs) │
                          └──────────────┘
```

## Run it locally (Docker)

Requires **Docker Desktop running**.

```bash
git clone https://github.com/sboppudi4/fairlens.git
cd fairlens
docker compose up --build
```

The first build takes a few minutes — it installs the backend's ML stack (pandas, scikit-learn, xgboost, shap). This starts Postgres, Redis, MinIO, the FastAPI backend, the Celery worker, and the Vite frontend.

Once the backend is healthy (`curl http://localhost:8000/health` → `{"status":"ok"}`), **seed the demo** — this is what creates the login account; the demo user does not exist until you run it:

```bash
# Creates demo@fairlens.dev / fairlens2026, downloads Adult Income, trains XGBoost,
# uploads predictions to MinIO, and queues a real audit. Idempotent for the user.
docker compose exec backend python -m scripts.seed_demo
```

Open:

- **Frontend**: http://localhost:5173 — log in as `demo@fairlens.dev` / `fairlens2026`
- **API docs**: http://localhost:8000/docs
- **MinIO console**: http://localhost:9001 — `minioadmin` / `minioadmin`

The Dashboard auto-refreshes every 5s; the seeded audit moves `pending → running → completed` within ~10s. Click into it for the full results.

<details>
<summary><b>Troubleshooting</b></summary>

- **`Conflict. The container name "/fairlens-…" is already in use`** — stale containers from a previous run. Clear them and retry:
  ```bash
  docker compose down --remove-orphans
  docker rm -f $(docker ps -aq --filter name=fairlens)   # if any remain
  docker compose up --build
  ```
- **Login shows a network error** — the backend isn't up yet. Wait for `http://localhost:8000/health` to return `{"status":"ok"}`.
- **Login fails with invalid credentials** — run the `seed_demo` step above; it creates the demo user.
</details>

## Frontend development (hot reload)

The design system, pages, and the 3D prism live in `frontend/`. To iterate on the UI with hot-module reload while the rest of the stack runs in Docker:

```bash
docker compose up -d backend worker                       # backend + its deps (postgres/redis/minio); leaves :5173 free
docker compose exec backend python -m scripts.seed_demo   # once, so the demo login works

cd frontend
npm install
npm run dev                                               # Vite dev server → http://localhost:5173
```

The frontend reads `VITE_API_BASE_URL` (defaults to `http://localhost:8000`). Stack: React 18 + Vite + Tailwind, route-level code splitting, and a lazy `three.js` hero/backdrop. Useful scripts: `npm run build` (typecheck + production build), `npm run type-check`.

## Running the tests

```bash
docker compose exec backend pytest tests -v
```

The fairness math tests use hand-calculated values for a tiny 10-row dataset, so any regression in the math is immediately visible.

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://fairlens:fairlens@postgres:5432/fairlens` | Async URL for FastAPI; converted to sync for Celery |
| `REDIS_URL` | `redis://redis:6379/0` | App + progress tracking |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Separate DB to avoid collisions |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Separate DB for task results |
| `SECRET_KEY` | required, min 32 chars | JWT signing key |
| `AWS_ENDPOINT_URL` | `http://minio:9000` | Set to `null` for real S3 |
| `MAX_UPLOAD_SIZE_MB` | `50` | Hard limit on dataset uploads |

Full reference: [.env.example](.env.example).

## Project layout

```
fairlens/
├── backend/
│   ├── app/
│   │   ├── api/v1/                # FastAPI routers (auth, datasets, audits, health)
│   │   ├── core/                  # database, security, storage, redis, exceptions
│   │   ├── models/                # SQLAlchemy 2.0 ORM
│   │   ├── schemas/               # Pydantic v2
│   │   ├── services/
│   │   │   ├── fairness/
│   │   │   │   ├── metrics.py     # ★ The seven fairness metrics
│   │   │   │   └── regulatory.py  # ★ Verbatim mapping → EU AI Act / NIST RMF / ISO 42001
│   │   │   ├── auth_service.py
│   │   │   ├── dataset_service.py
│   │   │   └── audit_service.py
│   │   ├── tasks/audit_tasks.py   # Celery task: download → metrics → regulatory → save
│   │   ├── utils/csv_parser.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── migrations/                # Alembic
│   ├── scripts/seed_demo.py       # Adult Income end-to-end demo
│   ├── tests/                     # Hand-calculated fairness math tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/                    # sitemap.xml, robots.txt (served at site root)
│   ├── src/
│   │   ├── api/                   # axios clients
│   │   ├── pages/                 # Login / Register / Dashboard / NewAudit / AuditResults
│   │   ├── components/
│   │   │   ├── landing/           # ★ WebGL prism (three.js) — hero + page backdrops
│   │   │   ├── layout/            # Navbar / Sidebar / Layout shell
│   │   │   ├── results/ ...       # charts, gauges, regulatory map
│   │   │   └── ui/                # Button / Card / Input / Badge primitives
│   │   ├── index.css              # Tailwind + dark-glass design tokens & animations
│   │   ├── store/authStore.ts
│   │   └── types/index.ts
│   ├── nginx.conf                 # static-serving config (gzip + immutable asset cache)
│   ├── tailwind.config.ts         # design-system color/type tokens
│   ├── Dockerfile                 # dev + multi-stage prod
│   └── package.json
├── nginx/                         # reverse proxy (API + SPA) for the compose prod stack
├── docker-compose.yml
└── README.md
```

## Regulatory mapping — what's cited where

Every fairness metric maps to specific clauses of the three frameworks. The mapping is **verbatim** from the source documents (uploaded as the authoritative reference). For example, `demographic_parity_difference` maps to:

- **EU AI Act** — Article 10(2)(f)–(g): "*examination in view of possible biases that are likely to … lead to discrimination prohibited under Union law … appropriate measures to detect, prevent and mitigate possible biases identified.*"
- **NIST AI RMF** — `MEASURE 2.11`: "*Fairness and bias — as identified in the MAP function — are evaluated and results are documented.*"
- **ISO/IEC 42001** — Annex A.7.4: "*The organization shall consider the impact of bias on system performance and system fairness and make such adjustments as necessary…*"

Full table: [`backend/app/services/fairness/regulatory.py`](backend/app/services/fairness/regulatory.py).

## Deploying to Render

Render reads [`render.yaml`](render.yaml) at the repo root and provisions:

1. `fairlens-db` — managed PostgreSQL 16 (free plan)
2. `fairlens-redis` — managed Redis (free plan)
3. `fairlens-backend` — uvicorn web service (starter plan)
4. `fairlens-worker` — Celery background worker (starter plan)
5. `fairlens-frontend` — built Vite SPA served as a static site

### Steps

1. Create a Render account and connect this GitHub repo (`sboppudi4/fairlens`).
2. In the Render dashboard, click **New → Blueprint** and point it at the repo. Render auto-discovers `render.yaml` and proposes the five resources above. Approve.
3. **Set the secrets** Render couldn't infer (these are marked `sync: false` in the blueprint):
   - `ALLOWED_ORIGINS` on the backend → your frontend URL, e.g. `https://fairlens-frontend.onrender.com`.
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_BUCKET_NAME` on backend + worker → an S3-compatible bucket (real AWS S3, Cloudflare R2, Backblaze B2…). MinIO won't work on Render's free network.
   - `VITE_API_BASE_URL` on the frontend → your backend URL, e.g. `https://fairlens-backend.onrender.com`.
4. The first deploy auto-runs `alembic upgrade head` as part of the backend's build command, so the schema is created without manual intervention.
5. (Optional) Add the deploy hooks Render generated to GitHub repository secrets so [.github/workflows/deploy.yml](.github/workflows/deploy.yml) can re-deploy on every green CI run on `main`:
   - `RENDER_BACKEND_DEPLOY_HOOK`
   - `RENDER_WORKER_DEPLOY_HOOK`
   - `RENDER_FRONTEND_DEPLOY_HOOK`

### Smoke check after deploy

```bash
curl -sf https://fairlens-backend.onrender.com/health           # → {"status":"ok"}
curl -sf https://fairlens-backend.onrender.com/ready            # → {"status":"ok","db":"ok","redis":"ok"}
curl -sf https://fairlens-backend.onrender.com/metrics | head   # Prometheus exposition
```

## License

MIT
