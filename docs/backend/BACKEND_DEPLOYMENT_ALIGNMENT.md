# Backend Deployment & API Base URL Alignment

_Scope: PR-A from `docs/MOONSHOT_TO_PARADISO_MIGRATION_GAP_AUDIT.md`._
_This document records the deployment entrypoint, frontend API base
strategy, and what is intentionally deferred._

---

## Current backend entrypoint

| File | Value | Notes |
|---|---|---|
| `backend/paradiso_backend.py` | `app = FastAPI(...)` | The actual application. Imports cleanly with `fastapi`, `pydantic`, `httpx`. |
| `backend/Procfile` | `web: uvicorn paradiso_backend:app --host 0.0.0.0 --port $PORT` | Correctly points at the new backend. |
| `backend/railway.json` | `startCommand: uvicorn paradiso_backend:app ...`, `healthcheckPath: /health` | Correctly points at the new backend. |
| `backend/requirements.txt` | `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx` | Minimal dependency set; no `asyncpg`, no `langdetect`, no `supabase` (these are deferred). |
| `backend/moonshot_backend_fastapi.py` | 64-line stub | Kept only as a documentation reference. **Not** wired into deployment. |

**Routes registered** (verified via `importlib`):

```
GET  /health
GET  /api/visas
POST /api/ask
POST /api/jobcodekeywords
```

**Deployment provider:** Railway is the only deployment configuration present (`backend/Procfile` + `backend/railway.json`). No alternative provider (Render, Fly, Vercel, etc.) is configured in this repo. To deploy, set Railway **Root Directory** to `backend` (per `backend/README.md`).

---

## Frontend API base behavior

Both `index.html` and `ai.html` now compute `API_BASE` from a documented
precedence chain:

```js
const DEFAULT_API_BASE = "https://web-production-14f9a.up.railway.app";
const API_BASE = (window.PARADISO_BACKEND_URL && window.PARADISO_BACKEND_URL.trim())
    || ((location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.protocol === 'file:') ? "" : DEFAULT_API_BASE);
```

### Priority order

1. **`window.PARADISO_BACKEND_URL`** — if set non-empty before this script runs, use it. This is the operator override mechanism.
2. **Local dev** — if `location.hostname` is `localhost` / `127.0.0.1` or the page is loaded from `file://`, `API_BASE = ""`. The frontend falls through to local `visa_data.json` and the AI page returns a local-mode message.
3. **`DEFAULT_API_BASE`** — the legacy Railway URL is preserved as a fallback so the live GitHub Pages deployment keeps working until a new backend is wired up.

### How to switch backends

**Option A — runtime override (preferred):**

Inject one line *before* the main page script:

```html
<head>
  <script>window.PARADISO_BACKEND_URL = "https://your-paradiso-backend.up.railway.app";</script>
  ...
</head>
```

This requires no edit to `index.html` / `ai.html` source if you can inject via a deploy pipeline. Otherwise edit the inline `<script>` already in `index.html` (search for `window.PARADISO_BACKEND_URL`).

**Option B — change the default:**

Edit the `DEFAULT_API_BASE` constant in both files (one location per file, identical name and pattern). Useful when the new backend has fully replaced the legacy one.

**Option C — same-origin proxy:**

Set `window.PARADISO_BACKEND_URL = ""` *and* proxy `/api/*` on your static-frontend host to the backend. The frontend will then issue same-origin requests (`fetch('/api/visas')`).

---

## What this PR fixes

1. **Frontend API base is now configurable** without editing inline string literals across the page. A single named constant (`DEFAULT_API_BASE`) lives in each file, and `window.PARADISO_BACKEND_URL` overrides it.
2. **Backend README** no longer says the rewiring is a follow-up PR; the precedence chain is documented in this file.
3. **Backend import** is verified to load cleanly with the pinned `requirements.txt` (`fastapi`, `uvicorn`, `pydantic`, `httpx`) and exposes all four expected routes.
4. **`Procfile` and `railway.json`** were already correct (pointing at `paradiso_backend:app`); no change needed.

---

## What this PR intentionally does NOT do

- **Does not deploy.** Railway deployment requires a human action in the Railway dashboard (set Root Directory = `backend`, add env vars, redeploy). This PR only makes the repo state coherent so that action will succeed.
- **Does not implement RAG.** No `manual_chunks`, no Supabase pgvector wiring, no embedding code. The new backend's `/api/ask` will return LLM output without document grounding until follow-up PR-C lands.
- **Does not implement public-data caching.** No `api.odcloud.kr` integration.
- **Does not implement the real-time law API.** No `apis.data.go.kr/1170000/law` calls.
- **Does not implement Hi Korea crawling / source registry.** `seed_registry_insert.sql` at repo root remains orphaned.
- **Does not implement legal article mapping.** No law-article schema or lookup.
- **Does not change `/api/jobcodekeywords` response schema** (still `{query, keywords}`, not `{job_keywords, industry_keywords}`). That mismatch is deferred to PR-B.
- **Does not change `/api/ask` semantics** — single-provider, no `langdetect`, no disclaimer suffix, no multi-model fallback. Deferred.
- **Does not modify** `visa_data.json`, `data/agent_registry_2026-04-30.json`, `doc_master.json`, or any other data file.
- **Does not redesign UI** or change visible copy.

---

## Validation commands

```bash
# Backend syntax + import
python3 -m py_compile backend/paradiso_backend.py
python3 - <<'PY'
import importlib.util
spec = importlib.util.spec_from_file_location("paradiso_backend", "backend/paradiso_backend.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("has app:", hasattr(mod, "app"))
PY

# Repository validators
bash scripts/check_repo.sh
node scripts/check_i18n.js
git diff --check

# Frontend API base reference sanity check
grep -n "DEFAULT_API_BASE\|PARADISO_BACKEND_URL\|API_BASE" index.html ai.html
```

---

## Risks remaining

- **Live AI is still broken** until Railway redeploy + RAG restoration (see audit PR-C). This PR makes the wiring correct but does not fix the AI quality issue.
- **Legacy Railway URL is still the default** — the live frontend continues to call the broken legacy backend until an operator either redeploys the new backend at the same URL or overrides `window.PARADISO_BACKEND_URL`.
- **`/api/jobcodekeywords` schema mismatch** with frontend is still present (PR-B).

---

## Follow-up PRs (from migration audit)

1. **PR-B** — Fix `/api/jobcodekeywords` response shape: return `{job_keywords:[...], industry_keywords:[...]}` to match what the frontend reads.
2. **PR-C** — Port RAG scripts (`extract_pdf.py`, `index_manuals.py`), apply Supabase pgvector schema, index 2026.5 manuals.
3. **PR-D** — Multi-model fallback chain, `langdetect` language branching, AI disclaimer suffix.
4. **PR-E** — Public-data caching (`api.odcloud.kr` 15103561 / 15117819).
5. **PR-F** — Real-time law API lookup.
