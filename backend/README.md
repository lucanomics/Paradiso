# Paradiso Backend

FastAPI service that powers the Paradiso frontend's chatbot and visa
lookup flows.

## Routes

| Method | Path                    | Purpose                                                       |
| ------ | ----------------------- | ------------------------------------------------------------- |
| GET    | `/health`               | Liveness probe; reports which providers are configured.       |
| GET    | `/api/visas`            | Returns the visa catalog used by the frontend visa explorer.  |
| POST   | `/api/ask`              | Chatbot endpoint. Routes to OpenRouter or Groq if configured. |
| POST   | `/api/jobcodekeywords`  | Extracts keywords from a job-code search query.               |

## Local development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in the values you need locally
uvicorn paradiso_backend:app --reload --port 8000
```

Quick checks:

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/api/visas | jq '.count'
curl -s -X POST http://localhost:8000/api/jobcodekeywords \
  -H 'content-type: application/json' \
  -d '{"query":"senior backend engineer Seoul"}' | jq
curl -s -X POST http://localhost:8000/api/ask \
  -H 'content-type: application/json' \
  -d '{"message":"hello"}' | jq
```

`/api/ask` returns `503 no_llm_provider_configured` until you set
either `OPENROUTER_API_KEY` or `GROQ_API_KEY`.

## Required and optional environment variables

All variables are read from the process environment. None are baked
into the image. See `.env.example` for the full list.

| Variable                | Required? | Notes                                                    |
| ----------------------- | --------- | -------------------------------------------------------- |
| `OPENROUTER_API_KEY`    | optional* | Enables `/api/ask` via OpenRouter.                       |
| `OPENROUTER_MODEL`      | optional  | Defaults to `openrouter/auto`.                           |
| `GROQ_API_KEY`          | optional* | Enables `/api/ask` via Groq if OpenRouter is not set.    |
| `GROQ_MODEL`            | optional  | Defaults to `llama-3.1-8b-instant`.                      |
| `SITE_URL`              | optional  | Sent as `HTTP-Referer` to OpenRouter; set to your frontend origin. |
| `SITE_TITLE`            | optional  | Sent as `X-Title` to OpenRouter. Defaults to `Paradiso`. |
| `LAW_API_KEY`           | optional  | Reserved for future law-data integration.                |
| `DATABASE_URL`          | optional  | Reserved for future Postgres integration.                |
| `SUPABASE_URL`          | optional  | Reserved for future Supabase integration.                |
| `SUPABASE_SERVICE_KEY`  | optional  | Reserved for future Supabase integration.                |
| `CORS_ALLOW_ORIGINS`    | optional  | Comma-separated origins. Defaults to `*` (dev only).     |
| `LOG_LEVEL`             | optional  | Defaults to `INFO`.                                      |

\* At least one of `OPENROUTER_API_KEY` or `GROQ_API_KEY` is required
for `/api/ask` to return answers.

> **Never commit `.env`.** Only commit `.env.example`.

## Deploying to Railway

> **Status:** the files in this directory **prepare** Railway
> deployment but do not deploy it. Each step below is a manual action a
> human must perform once. No CI deploy hook is configured.

1. Sign in to Railway and choose **New Project → Deploy from GitHub
   repo**.
2. Select **Repo:** `lucanomics/Paradiso`.
3. After the service is created, open **Settings → Service → Source**
   and set **Root Directory** to `backend`.
4. Railway will detect `requirements.txt` and `Procfile` automatically.
   The start command is also pinned in `railway.json`:

   ```
   uvicorn paradiso_backend:app --host 0.0.0.0 --port $PORT
   ```

5. Open **Variables** and add the values below. At minimum, set one
   LLM provider key (`OPENROUTER_API_KEY` or `GROQ_API_KEY`):

   ```
   OPENROUTER_API_KEY=...        # or GROQ_API_KEY=...
   CORS_ALLOW_ORIGINS=https://paradiso.example.com
   SITE_URL=https://paradiso.example.com
   # Optional, declared but not yet wired:
   # LAW_API_KEY=...
   # DATABASE_URL=...
   # SUPABASE_URL=...
   # SUPABASE_SERVICE_KEY=...
   ```

   Replace `paradiso.example.com` with your real Paradiso frontend
   origin. Use `*` for `CORS_ALLOW_ORIGINS` only in development.

6. **Never commit `backend/.env`.** The repo `.gitignore` already
   excludes it; only `backend/.env.example` is tracked.
7. The service exposes `/health` and Railway uses it as the health
   check (already configured in `railway.json`).
8. After the first deploy, verify each route with curl using the
   Railway public URL — see _Verification_ below.

### Visa data file path on Railway

`/api/visas` reads from a JSON file. With **Root Directory = backend**,
the repo-root `visa_data.json` is not in the build context, so the
loader looks in three places, in order:

1. `VISA_DATA_PATH` env var (absolute path, e.g. a Railway volume mount).
2. `backend/data/visas.json` — the **committed copy** that ships with
   the backend deploy context.
3. `<repo-root>/visa_data.json` — used only when the backend is built
   from the repo root.

The committed `backend/data/visas.json` is kept in sync with the
canonical repo-root `visa_data.json` by `scripts/sync_visa_data.py`,
which `scripts/check_repo.sh` runs in `--check` mode to fail CI if the
two files drift. Update the canonical file at the repo root, then run
`python3 scripts/sync_visa_data.py` to refresh the backend copy before
committing.

`/api/visas` reports which source it served from via the `source_type`
field: `backend-data`, `repo-root`, `explicit` (from `VISA_DATA_PATH`),
or `fallback` (DEFAULT_VISAS, with an accompanying `warning`).

## Verification

After deploying (or when running locally), verify each route:

```bash
BASE=https://your-paradiso-backend.up.railway.app   # or http://localhost:8000

curl -fsS "$BASE/health" | jq
curl -fsS "$BASE/api/visas" | jq '.count, .warning // "ok"'
curl -fsS -X POST "$BASE/api/jobcodekeywords" \
  -H 'content-type: application/json' \
  -d '{"query":"한식 조리사"}' | jq
curl -fsS -X POST "$BASE/api/ask" \
  -H 'content-type: application/json' \
  -d '{"message":"E-7 비자 갱신 요건은?"}' | jq
curl -fsS -X POST "$BASE/api/ask" \
  -H 'content-type: application/json' \
  -d '{"question":"D-2 비자 연장에 필요한 서류는?","visa_code":"D-2"}' | jq
```

`/api/ask` accepts the prompt under any of `message`, `query`, or
`question` (resolution order: `message` → `query` → `question`). The
frontend currently sends `question` plus optional metadata (`consent`,
`context`, `lang`, `visa_data`); curl-driven clients can use any
alias. Schema-only fields (`visa_code`, `visa_data`, …) are accepted
to keep the contract stable even when they are not yet consumed by
answer generation.

`/health` should return `status: "ok"` and a `providers` map showing
which integrations are configured. `/api/visas` should return a non-
empty `data` array and `source_type: "backend-data"` (no `warning`
field) once the deploy includes `backend/data/visas.json`.

## Wiring the frontend

Both `index.html` and `ai.html` define `API_BASE` from a documented
precedence chain (see `docs/backend/BACKEND_DEPLOYMENT_ALIGNMENT.md`):

1. `window.PARADISO_BACKEND_URL` if set and non-empty (highest priority).
2. `""` for local development (`localhost`, `127.0.0.1`, or `file:`).
3. `DEFAULT_API_BASE` constant (currently the legacy Railway URL).

Two ways to point the frontend at a different backend:

1. Inline override in `index.html` head:

   ```html
   <script>window.PARADISO_BACKEND_URL = "https://your-paradiso-backend.up.railway.app";</script>
   ```

2. Or proxy `/api/*` from your static-frontend host to the backend, so
   same-origin (`window.PARADISO_BACKEND_URL = ""`) works.

## Production hardening checklist

- [ ] Set `CORS_ALLOW_ORIGINS` to an explicit allow-list (do not leave `*`).
- [ ] Restrict provider keys to least-privilege scopes where possible.
- [ ] Rotate keys regularly; store them only in Railway, not in git.
- [ ] Add request logging / observability before exposing to real users.
