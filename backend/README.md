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

1. Create a new Railway service from this repository.
2. In **Settings → Service → Source**, set **Root Directory** to
   `backend`.
3. Railway will detect `requirements.txt` and `Procfile` automatically.
   The start command is also pinned in `railway.json`:

   ```
   uvicorn paradiso_backend:app --host 0.0.0.0 --port $PORT
   ```

4. Add the variables you need under **Variables**. At minimum, set one
   LLM provider key (`OPENROUTER_API_KEY` or `GROQ_API_KEY`).
5. Set `CORS_ALLOW_ORIGINS` to your frontend origin(s) for production,
   for example:

   ```
   CORS_ALLOW_ORIGINS=https://paradiso.example.com
   ```

6. The service exposes `/health` and Railway will use it as the health
   check (already configured in `railway.json`).

## Wiring the frontend

The frontend reads `window.PARADISO_BACKEND_URL` (set in `index.html`)
and falls back to same-origin if unset. Point it at your Railway URL
either by editing `index.html` or by injecting the value at deploy time.

```html
<script>window.PARADISO_BACKEND_URL = "https://your-paradiso-backend.up.railway.app";</script>
```

## Production hardening checklist

- [ ] Set `CORS_ALLOW_ORIGINS` to an explicit allow-list (do not leave `*`).
- [ ] Restrict provider keys to least-privilege scopes where possible.
- [ ] Rotate keys regularly; store them only in Railway, not in git.
- [ ] Add request logging / observability before exposing to real users.
