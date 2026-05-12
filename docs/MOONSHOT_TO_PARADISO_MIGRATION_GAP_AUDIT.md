# Moonshot-to-Paradiso Migration Gap Audit

_Branch: `audit/moonshot-to-paradiso-migration-gap`_
_Date: 2026-05-12_
_Scope: Audit only. Minimal safe fixes noted where evidence is clear and deterministic._
_Repos: legacy `lucanomics/moonshot` vs. current `lucanomics/Paradiso`_

---

## 1. Executive Verdict

**The static production UI is healthy and fully migrated.** The search, agent finder, i18n system, visa data, and all client-side features exist and pass repo validation.

**The backend/AI layer is NOT migrated in a working state.** The live Railway deployment still runs the old `moonshot_backend_fastapi.py`. The new `backend/paradiso_backend.py` exists in the repo but has never been deployed. Five data-grounding systems that moonshot used (RAG, public-data caches, law API, multi-model fallback, language detection) are unimplemented in the new backend. The result is that `ai.html` always returns generic "정보가 없습니다 / call 1345" answers.

**Six moonshot pipeline components are absent entirely from Paradiso** (RAG scripts, pgvector migration, public-data API client, law API client, source-registry crawler, HiKorea source seed).

---

## 2. Current Paradiso Implementation Status

### What is working
| Component | Location | Status |
|-----------|----------|--------|
| Static search UI (39 visa codes) | `index.html` | ✅ Working |
| Agent finder (3,967 records) | `index.html` + `data/agent_registry_2026-04-30.json` | ✅ Working |
| i18n (ko/en/zh) | `index.html` UI_TRANSLATIONS | ✅ Working (PR #36 fixes CI) |
| AI modal UI | `ai.html` | ✅ UI works; backend is broken |
| Visa data (58 records) | `visa_data.json` | ✅ Valid JSON |
| Job code data | `data/jobcode_master.json` | ✅ Present |
| Doc master | `doc_master.json` | ✅ Present |
| Manual registry | `docs/source-manuals/source_manifest.json` | ✅ 2026.5 manuals registered |
| Backend code | `backend/paradiso_backend.py` | ✅ Code exists; ❌ never deployed |
| Backend routes | `/health`, `/api/visas`, `/api/ask`, `/api/jobcodekeywords` | ✅ Routes defined; ❌ not live |
| Validation scripts | `scripts/check_repo.sh`, `check_i18n.js`, `check_source_manuals.py` | ✅ All pass |

---

## 3. What Existed in Moonshot but Is Missing in Paradiso

### 3.1 RAG pipeline — entirely absent

| Moonshot file | Paradiso equivalent | Gap |
|---|---|---|
| `scripts/rag/extract_pdf.py` | _absent_ | Full PDF→Markdown extractor using pypdf/pdfplumber |
| `scripts/rag/index_manuals.py` | _absent_ | Chunk/embed/upsert to Supabase `manual_chunks` via OpenRouter text-embedding-3-small |
| `scripts/rag/README.md` | _absent_ | Operational docs for RAG indexing |
| `migrations/002_rag_pgvector.sql` | _absent_ | `manual_chunks` table with `vector(1024)`, HNSW index, `match_manual_chunks` RPC |

**Evidence:** `ls /workspaces/Paradiso/scripts/` shows no `rag/` subdirectory. `find /workspaces/Paradiso -name "index_manuals.py"` returns nothing.

**Impact:** `ai.html` always returns generic answers. `retrieve_manual_context()` in the live backend has `retrieval_used:false` on every request (confirmed via live probe in `docs/AI_PIPELINE_DIAGNOSIS.md`).

### 3.2 Supabase pgvector schema — not applied

| Moonshot file | Paradiso equivalent | Gap |
|---|---|---|
| `migrations/001_schema.sql` | _absent_ | `visas` and `visa_sub_codes` PostgreSQL tables |
| `migrations/002_rag_pgvector.sql` | _absent_ | `manual_chunks`, `vector` extension, `match_manual_chunks` RPC |

**Evidence:** `find /workspaces/Paradiso -name "*.sql" -not -path "*/node_modules/*"` finds only `seed_registry_insert.sql` (a source-registry seed, not the schema). No `migrations/` directory exists.

**Impact:** Even if RAG scripts were run, there is no target table.

### 3.3 Public-data API integration — not implemented

Moonshot's `moonshot_backend_fastapi.py` called two `api.odcloud.kr` endpoints at startup:
- `15103561` — Ministry of Justice visa code list
- `15117819` — Statistics Korea job/industry classification

Results were cached in `cached_public_visa_data` / `cached_public_job_data` and injected into the `/api/ask` system prompt.

**Paradiso's `paradiso_backend.py`:** `LAW_API_KEY` is declared in `.env.example` but not wired into any API call. No `init_public_data_cache()` equivalent exists.

**Impact:** AI context is missing live government visa-code data.

### 3.4 Real-time law API lookup — not implemented

Moonshot called `apis.data.go.kr/1170000/law` with Korean keyword triggering:
```python
triggers = ["법", "벌금", "불법", "퇴거", "위반", "체류", "연장", "사증", "비자", "출입국"]
```

**Paradiso's `paradiso_backend.py`:** No `fetch_realtime_law_data()` equivalent. `LAW_API_KEY` is declared but unused.

### 3.5 Source-registry crawler — absent

| Moonshot file | Paradiso equivalent | Gap |
|---|---|---|
| `moonshot_crawler.py` | _absent_ | FastAPI app using asyncpg; fetches Hi Korea, immigration.go.kr |
| `seed_registry_insert.sql` (moonshot) | present in Paradiso root | ✅ Present — 3 source rows (Hi Korea, KIS, MOJ Guide PDF) |

**Note:** `seed_registry_insert.sql` exists in Paradiso root but the `source_registry` table it references has no schema migration and no crawler to run it.

### 3.6 Multi-model fallback chain — not implemented

Moonshot used a chain:
1. `moonshotai/kimi-k2:free` (OpenRouter)
2. `google/gemma-4-26b-a4b-it:free` (OpenRouter)
3. `llama-3.3-70b-versatile` (Groq)

Paradiso uses the first configured provider only (OpenRouter if set, else Groq). No fallback chain.

### 3.7 Language detection (`langdetect`) — not implemented

Moonshot called `langdetect.detect(question)` to branch the prompt between Korean and non-Korean instructions.

Paradiso has no language detection. All `/api/ask` calls use the same English-only system prompt template.

### 3.8 Anti-hallucination disclaimer — not implemented

Moonshot appended a hard-coded disclaimer to every AI response:
> "⚠️ 본 답변은 출입국관리법 공개 자료를 기반으로 제공되며 법률 자문이 아닙니다..."

Paradiso's `/api/ask` returns the raw LLM output with no disclaimer suffix.

---

## 4. What Exists in Paradiso but Appears Broken or Incomplete

### 4.1 Live backend is still Moonshot code — critical

**Evidence from `docs/AI_PIPELINE_DIAGNOSIS.md`:**
- `GET /health` → **404** (Moonshot has no /health; new backend would return 200)
- `POST /api/ask {}` → **422** expecting `question` + `consent` (Moonshot schema, not Paradiso's `message`/`query`)
- `GET /api/visas` → **500** (Moonshot reads PostgreSQL; `DATABASE_URL` missing)

The deployed Railway app is `moonshot_backend_fastapi.py`. `backend/paradiso_backend.py` has never been deployed.

### 4.2 `ai.html` hardcodes the legacy Railway URL

`ai.html` line ~395 hardcodes `API_BASE = "https://web-production-14f9a.up.railway.app"`. `window.PARADISO_BACKEND_URL` is declared in a `<script>` block but is never read by the actual `loadVisaData()` or `sendAi()` functions. Switching backends requires an `ai.html` edit.

### 4.3 `/api/jobcodekeywords` schema mismatch

| Aspect | Moonshot shape | Paradiso shape | Frontend reads |
|---|---|---|---|
| Response body | `{job_keywords: [...], industry_keywords: [...]}` | `{query: str, keywords: [...]}` | `job_keywords` and `industry_keywords` |

The frontend (`index.html`) reads `job_keywords` and `industry_keywords` from the response. The new backend returns a flat `keywords` array. This is a silent failure when the backend is live.

### 4.4 `HF_TOKEN` / embedding env var missing from `.env.example`

Moonshot RAG used `HF_TOKEN` for HuggingFace embedding (and OpenRouter for embedding in the final version). Neither `HF_TOKEN` nor `OPENROUTER_API_KEY` for embedding is mentioned in `backend/.env.example` in the context of RAG reactivation.

### 4.5 `backend/moonshot_backend_fastapi.py` is a 64-line stub, not the real file

The repo contains `backend/moonshot_backend_fastapi.py` as a documentation stub. The real moonshot backend (544 lines with public-data caching, RAG, multi-model) is `moonshot_backend_fastapi.py` in the moonshot repo. The stub says "Not wired into the static production app."

### 4.6 `seed_registry_insert.sql` has no schema to insert into

The file exists at repo root but the `source_registry` table it targets was never created (no schema migration).

---

## 5. What Is Documented but Not Actually Implemented

| Documentation claim | Actual code status |
|---|---|
| `backend/.env.example`: `SUPABASE_URL=` / `SUPABASE_SERVICE_KEY=` — "declared for forward-compatibility" | No Supabase client code in `paradiso_backend.py` |
| `backend/.env.example`: `LAW_API_KEY=` — "Optional integrations (declared for forward-compatibility)" | Not wired to any endpoint |
| `backend/.env.example`: `DATABASE_URL=` — same | Not wired; `asyncpg` not in `requirements.txt` |
| `docs/data-sources/data-sources-overview.md`: "docs/sajeung-manual.md, docs/ceryu-manual.md" | These markdown files do not exist in the repo; not in `docs/` |
| `docs/data-pipeline/README.md`: `scripts/fetch_jobcodes.py` "produce data/jobcode_master.json" | `fetch_jobcodes.py` requires `JOBCODE_API_KEY` and network access; `data/jobcode_master.json` exists as a static file — unclear if it was ever generated from the API |
| `docs/MOONSHOT_TO_PARADISO_REMAINING_MIGRATION_AUDIT.md`: previous audit performed against moonshot only (network blocked); described as "cautious phase plan" | That audit did not have direct access to the moonshot repo |

---

## 6. File-Level Evidence

```
Paradiso                               Moonshot                         Status
───────────────────────────────────────────────────────────────────────────────
backend/paradiso_backend.py (377 ln)   moonshot_backend_fastapi.py(544) PARTIAL
backend/moonshot_backend_fastapi.py    (stub, 64 lines)                 STUB ONLY
backend/requirements.txt (4 pkgs)      requirements.txt                 INCOMPLETE
                                       │  langdetect                    MISSING
                                       │  asyncpg                       MISSING
                                       └─ pdfplumber, pypdf, sentence-  MISSING
                                          transformers
scripts/build_agent_registry.py        (not in moonshot)                PARADISO-NEW
scripts/fetch_jobcodes.py              scripts/fetch_jobcodes.py        PRESENT
scripts/generate_seed.py               (not in moonshot)                PARADISO-NEW
scripts/check_repo.sh                  scripts/check_repo.sh            UPDATED
scripts/check_i18n.js                  (not in moonshot)                PARADISO-NEW
scripts/check_source_manuals.py        (not in moonshot)                PARADISO-NEW
                                       scripts/rag/extract_pdf.py       MISSING
                                       scripts/rag/index_manuals.py     MISSING
                                       scripts/rag/README.md            MISSING
                                       migrations/001_schema.sql        MISSING
                                       migrations/002_rag_pgvector.sql  MISSING
seed_registry_insert.sql               seed_registry_insert.sql         PRESENT (orphaned)
data/agent_registry_2026-04-30.json    (not in moonshot)                PARADISO-NEW
data/jobcode_master.json               data/jobcode_master.json         PRESENT
visa_data.json (58 records)            visa_data.json                   UPDATED
docs/AI_PIPELINE_DIAGNOSIS.md         (not in moonshot)                PARADISO-NEW
docs/backend/BACKEND_MIGRATION_GAP_REPORT.md                           PARADISO-NEW
docs/MOONSHOT_TO_PARADISO_REMAINING_MIGRATION_AUDIT.md                 PARADISO-NEW (network-blocked)
                                       moonshot_crawler.py              MISSING
                                       moonshot_pipeline_architecture.md PRESENT at root (ref)
.env.example                           .env.example                    PARADISO: backend/.env.example
                                       │  GROQ_API_KEY, LAW_API_KEY,   Paradiso: adds OPENROUTER,
                                       └─ DATABASE_URL only             SUPABASE, SITE_URL, CORS
```

---

## 7. Risks for Contest / Public Claims

| Risk | Severity | Detail |
|---|---|---|
| AI answers are generic/useless | **HIGH** | Live backend is broken Moonshot code; RAG empty; public-data caches empty. Every `/api/ask` falls back to "정보가 없습니다 / call 1345." |
| `/api/visas` returns 500 | **HIGH** | Frontend AI page fails to load visa context; `aiBody.visa_data` always sends `{code:'N/A',cat:'N/A'}` |
| `/api/jobcodekeywords` schema mismatch | **MEDIUM** | Returns `{keywords:[]}` not `{job_keywords:[], industry_keywords:[]}` — silent failure in frontend |
| New backend never deployed | **HIGH** | `backend/paradiso_backend.py` is repo code only; Railway runs moonshot code |
| RAG and manuals not indexed | **HIGH** | `docs/sajeung-manual.md` and `docs/ceryu-manual.md` don't exist; pgvector table not created |
| `seed_registry_insert.sql` is orphaned | **LOW** | No schema, no crawler to run it; harmless but misleading |
| Documentation refers to unbuilt components | **MEDIUM** | `.env.example` lists Supabase/DB vars as "forward-compatibility" but no code reads them |

---

## 8. Recommended PR Sequence

| Priority | PR title | Scope | Risk |
|---|---|---|---|
| 1 | **Deploy new backend to Railway** | Point Railway to `backend/paradiso_backend.py` via `backend/Procfile`. Verify `/health` returns 200. | LOW — backend is simple and gracefully degrades |
| 2 | **Fix `ai.html` to use `window.PARADISO_BACKEND_URL`** | Wire `loadVisaData()` and `sendAi()` to read `window.PARADISO_BACKEND_URL \|\| ''`. Remove hardcoded Railway URL. | LOW — only 2 JS constants change |
| 3 | **Fix `/api/jobcodekeywords` response schema** | Return `{job_keywords:[...], industry_keywords:[...]}` shape matching frontend expectation. | LOW — pure backend; no HTML change |
| 4 | **Restore manual Markdown files and RAG schema** | Extract PDFs to `docs/sajeung-manual.md` + `docs/ceryu-manual.md` via moonshot's `extract_pdf.py`. Apply `migrations/002_rag_pgvector.sql` to Supabase. | MEDIUM — requires PDF access and Supabase credentials |
| 5 | **Run RAG indexing and verify retrieval** | Port and run `scripts/rag/index_manuals.py`. Smoke-test `match_manual_chunks` RPC. | MEDIUM — requires HF_TOKEN / OpenRouter embedding key |
| 6 | **Restore multi-model fallback chain in `/api/ask`** | Port model fallback list, language detection, disclaimer suffix, and consent gate from moonshot. | MEDIUM |
| 7 | **Wire public-data caching** | Restore `init_public_data_cache()` for `api.odcloud.kr` endpoints. Gate on `LAW_API_KEY`. | LOW after #6 — degrades gracefully |
| 8 | **Wire law API lookup** | Restore `fetch_realtime_law_data()`. Gate on keyword trigger and `LAW_API_KEY`. | LOW |
| 9 | **Drop orphaned root-level files** | `seed_registry_insert.sql` at repo root is orphaned (no schema, no crawler). Add schema migration or document as deferred. | LOW |

---

## 9. Immediate Next PRs (ranked by priority)

### PR-A (unblock AI — highest impact, ~2 hours)
**Title:** Deploy new Paradiso backend and fix ai.html API base URL

Changes:
1. In Railway, update `Root Directory` to `backend/` and redeploy — no code change required.
2. In `ai.html`, replace hardcoded `API_BASE = "https://web-production-..."` with `window.PARADISO_BACKEND_URL || ''` (2 lines).
3. Verify `GET /health` → 200 after deploy.

This immediately makes `/api/visas` serve the real 58-record visa list and `/api/ask` use Paradiso's cleaner backend (even without RAG).

### PR-B (fix jobcodekeywords schema — medium, ~1 hour)
**Title:** Fix `/api/jobcodekeywords` response to match frontend schema

Change `backend/paradiso_backend.py` response model from `{query, keywords}` to `{query, job_keywords, industry_keywords}`. Use the same regex extractor but split tokens by a pattern-match heuristic (KSCO codes vs. industry terms), or accept the current flat list and split it 50/50 for now.

### PR-C (restore RAG foundation — several hours, blocking for full AI quality)
**Title:** Port RAG scripts, apply pgvector schema, index 2026.5 manuals

1. Copy `scripts/rag/extract_pdf.py` and `scripts/rag/index_manuals.py` from moonshot.
2. Adjust `EMBED_DIM` and `EMBED_URL` to match current embedding API (OpenRouter `text-embedding-3-small`, dim=1536).
3. Apply `migrations/002_rag_pgvector.sql` to Supabase.
4. Run extraction on the two 2026.05 PDFs in `data/sources/`.
5. Run indexing. Verify `match_manual_chunks` returns results.
6. Add `HF_TOKEN` / `OPENROUTER_API_KEY` embedding usage to `backend/.env.example`.

---

## Validation Results for This Audit

```
python3 -m py_compile scripts/build_agent_registry.py   → OK
bash scripts/check_repo.sh                              → PASSED (all 6 checks)
node scripts/check_i18n.js                              → OK (253 keys in en, 253 in ko)
git diff --check                                        → clean
```

No production files were modified in this audit branch.
