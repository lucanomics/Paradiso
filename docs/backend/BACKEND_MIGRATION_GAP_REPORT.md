# Backend Migration Gap Report

_Status: audit only — this document records the delta between the old
moonshot backend and the current Paradiso backend so that follow-up
PRs can scope work safely. Nothing in this PR claims feature parity._

## Sources inspected

- **Old (reference):** `/workspaces/moonshot-source/moonshot_backend_fastapi.py` (544 lines), `Procfile`, `railway.json`, `requirements.txt`, `.env.example`.
- **New (target):** `backend/paradiso_backend.py` (377 lines), `backend/Procfile`, `backend/railway.json`, `backend/requirements.txt`, `backend/.env.example`, `backend/README.md`.
- The repo also contains `backend/moonshot_backend_fastapi.py` — a 64-line legacy-style reference stub kept for documentation; it is **not** the live application.

## Routes — feature comparison

| Route | Old behavior | New behavior | Gap |
| --- | --- | --- | --- |
| `GET /health` | _(not defined)_ | Returns `{status, service, version, providers}` | New addition — keep. |
| `GET /api/visas` | Reads `visas_json` table from PostgreSQL via asyncpg pool. Returns `{data: []}` if no DB. | Returns hard-coded `DEFAULT_VISAS` only. Does **not** read `visa_data.json`. | **Closed in this PR** — add JSON load with multi-shape support and fallback warning. |
| `POST /api/ask` | Multi-model fallback (OpenRouter Kimi K2 → Gemma 4 → Groq Llama 3.3); `langdetect`-based prompt switching; injects `visa_data` block, RAG context, public-data caches and law lookup; appends disclaimer. | Single provider (first of OpenRouter / Groq), single model, single message. No language detection, no RAG, no disclaimer, no `consent` gate. | **Open** — significant feature gap. Suitable for a follow-up PR (see _Recommended next PRs_). |
| `POST /api/jobcodekeywords` | Calls Groq/OpenRouter LLMs with a strict KSCO/KSIC prompt; returns `{job_keywords, industry_keywords}` (5 each). | Pure-Python regex extractor; returns `{query, keywords}`. | **Open** — schema and behavior do not match the frontend's expectations from `index.html` (frontend reads `job_keywords` and `industry_keywords`). |
| `GET /` and `GET /index.html` | `FileResponse` of bundled `index.html`. | _(not defined)_ | Optional — Paradiso serves the static frontend separately, so this can stay out unless we co-host. |
| `GET /ai.html` | `FileResponse` of `ai.html`. | _(not defined)_ | Same as above. |

## Subsystem comparison

| Subsystem | Old | New | Gap |
| --- | --- | --- | --- |
| Public-data caching (data.go.kr `15103561` visa codes; `15117819` job/industry classification) | Cached at startup via `httpx`; results injected into `/api/ask` system prompt. | Not implemented. | **Open** — needs `LAW_API_KEY`. Defer to follow-up. |
| Real-time law lookup (`apis.data.go.kr/1170000/law`) | Triggered by Korean keywords in question; injected into prompt. | Not implemented. | **Open**. Defer to follow-up. |
| Manual RAG via Supabase pgvector (`match_manual_chunks` RPC, `text-embedding-3-small` via OpenRouter) | Implemented; degrades to empty string if not configured. | Not implemented. | **Open**. Highest-impact feature for answer quality. Defer. |
| PostgreSQL pool (asyncpg) | Optional, used by `/api/visas`. | Not implemented. | **Open**, but lower priority since `visa_data.json` works. |
| Language detection (`langdetect`) | Used for prompt branching (ko / ja / zh / other). | Not implemented. | **Open**. |
| Logging | Appends to `logs.json` per request. | stdlib `logging` only. | Acceptable; persistent log file in container is brittle. Recommend structured logs in follow-up. |
| Disclaimer / anti-hallucination guardrails | Hard-coded suffix and prompt instructions. | Not implemented. | **Open** — important for any AI deployment. |
| CORS | `allow_origins=["*"]`, `allow_credentials=False`, methods limited to `GET, POST`. | `allow_origins` configurable via `CORS_ALLOW_ORIGINS`, all methods allowed. | New is more flexible. Recommend tightening before production. |
| Static file serving | Serves `index.html`, `ai.html`. | Not implemented. | Acceptable — Paradiso ships static frontend separately. |

## Environment variable comparison

| Variable | Old | New | Notes |
| --- | --- | --- | --- |
| `OPENROUTER_API_KEY` | optional | optional | Both. |
| `GROQ_API_KEY` | optional | optional | Both. |
| `LAW_API_KEY` | optional (used) | declared but unused | Wire when public-data caching/law lookup is restored. |
| `DATABASE_URL` | optional (used) | declared but unused | Wire when DB-backed `/api/visas` is restored. |
| `SUPABASE_URL` | optional (used) | declared but unused | Wire when RAG is restored. |
| `SUPABASE_SERVICE_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`) | optional (used) | declared but unused | Same. |
| `SITE_URL` | used in `HTTP-Referer` for OpenRouter | **missing** | **Closed in this PR** — add to `.env.example` and README. |
| `CORS_ALLOW_ORIGINS` | n/a | configurable | New addition. |
| `LOG_LEVEL` | n/a | configurable | New addition. |
| `OPENROUTER_MODEL` / `GROQ_MODEL` | hard-coded fallback chain | configurable defaults | New addition. |

## Data-loading gaps

- The current `/api/visas` does not read the repository's authoritative
  `visa_data.json` (58 records, validated by `scripts/check_repo.sh`).
  Consumers of the endpoint therefore see a 5-record stub list.
- The repo root `visa_data.json` is a **list of records**, not the
  `{data: [...]}` envelope the old DB row used. The frontend's
  `parse()` accepts either shape, so this PR returns
  `{data: [...], count, warning?}` for compatibility with the existing
  frontend and any moonshot-era consumers.

## Are Supabase and Railway actually deployed?

- **Supabase RAG:** declared in `.env.example` only. No code path
  references Supabase in `paradiso_backend.py`. Conclusion: **not
  implemented in Paradiso**, only documented.
- **Railway:** `Procfile`, `railway.json`, and README instructions
  exist. No GitHub Actions deploy hook is wired. The frontend does not
  yet read `window.PARADISO_BACKEND_URL`. Conclusion: **prepared, not
  deployed** — the live frontend (`index.html`, `ai.html`) still hard-
  codes the legacy moonshot Railway URL on lines noted in the audit.

## Frontend wiring gap

`index.html` and `ai.html` still contain a hard-coded `API_BASE`
pointing at the legacy Railway host. The `window.PARADISO_BACKEND_URL`
hook added in PR #20 is present but unused by the search/chat code
paths. This PR intentionally does **not** modify `index.html` or
`ai.html` (per the task constraints). A follow-up PR should:

- Replace the hard-coded `API_BASE` with `window.PARADISO_BACKEND_URL || ""`.
- Confirm both pages still fall through to local `visa_data.json` when
  the backend is unreachable.

## Recommended next PRs (in order)

1. **Frontend rewire (small, safe):** make `index.html` and `ai.html`
   read `window.PARADISO_BACKEND_URL` instead of the hard-coded legacy
   host. No design change.
2. **`/api/jobcodekeywords` parity:** restore the LLM-driven KSCO/KSIC
   keyword extractor; match the `{job_keywords, industry_keywords}`
   shape the frontend expects.
3. **`/api/ask` parity:** restore multi-model fallback chain,
   `langdetect`, disclaimer suffix, and the visa context block.
4. **RAG reactivation:** wire Supabase pgvector + OpenRouter
   embeddings; gate strictly on env presence so the service still boots
   without it.
5. **Public-data caching / law lookup:** restore data.go.kr integration
   on a configurable timer (don't fail startup if the API rate-limits).
6. **DB-backed `/api/visas`:** optional; only if the JSON file becomes
   too large or needs runtime updates.
7. **Production hardening:** tighten CORS, add structured logging,
   request IDs, and a `/metrics` or equivalent.

Each item above is independently shippable and can be reviewed in
isolation; the order minimizes blast radius.

## What this PR closes

- Wires `/api/visas` to read the real `visa_data.json` (root or
  `backend/data/visas.json`), preserves `DEFAULT_VISAS` fallback, and
  surfaces a `warning` field when the data file is missing/malformed.
- Adds `SITE_URL` to `.env.example` and the Railway setup doc.
- Documents the gaps above so future PRs can scope cleanly.

## What this PR explicitly does **not** do

- Does not change frontend code (`index.html`, `ai.html`).
- Does not change `visa_data.json`, `doc_master.json`, assets, or
  `scripts/check_repo.sh`.
- Does not deploy Railway.
- Does not enter any real provider keys or secrets.
- Does not restore RAG, multi-model fallback, public-data caching, or
  langdetect — those are explicit follow-ups.
