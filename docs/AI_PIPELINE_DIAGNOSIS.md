# Paradiso AI Pipeline Diagnosis

_Branch: `audit/ai-pipeline-diagnosis` (from `origin/main`)_
_Date: 2026-05-11_
_Scope: Diagnosis only. No production files modified._

---

## TL;DR

The deployed Paradiso AI gives generic "참고 자료에 정보가 없습니다 / call 1345" answers
for almost every question because **the live Railway backend is the legacy Moonshot
codebase whose RAG and public-data grounding pipelines are no longer functional**,
while its anti-hallucination prompt is still active and correctly refuses to answer
without grounding.

The repository's *new* `backend/paradiso_backend.py` (which would also be broken in a
different way — schema mismatch with the frontend) has **never been deployed**.

Root cause: **the Supabase pgvector RAG, the data.go.kr public-data cache, and the
realtime law-API lookup are all returning empty**, so the system prompt's "answer
only from [참고 자료]" rule forces a refusal on every question.

A live probe of `/api/ask` with the question
"F-6-1 결혼이민 비자에서 한국인 배우자와 이혼했을 때..." returns
`retrieval_used: false` and the exact "정보가 없습니다 / 1345" pattern users see.

---

## 1. Current AI architecture map

```
Browser (lucanomics.github.io/Paradiso/ai.html)
   │
   │  POST { question, consent, context, lang, visa_data:{code:'N/A',cat:'N/A'} }
   ▼
Railway: web-production-14f9a.up.railway.app
   │   Code running: LEGACY moonshot_backend_fastapi.py (NOT backend/paradiso_backend.py)
   │
   ├─► langdetect(question) → user_lang
   ├─► fetch_realtime_law_data(question)        ← apis.data.go.kr/1170000/law   [FAILING / DATA MISSING]
   ├─► retrieve_manual_context(question, code)  ← Supabase pgvector RPC          [FAILING — retrieval_used:false]
   │     ├─► _embed_query  → OpenRouter text-embedding-3-small
   │     └─► RPC /rest/v1/rpc/match_manual_chunks
   ├─► cached_public_visa_data (startup)        ← api.odcloud.kr 15103561        [DATA MISSING]
   ├─► cached_public_job_data  (startup)        ← api.odcloud.kr 15117819        [DATA MISSING]
   ├─► _build_visa_block(visa_data)             ← frontend always sends N/A      [EMPTY]
   │
   ├─► system prompt: "[참고 자료]에 명시된 내용만을 근거로 답변하라"
   ├─► user prompt:
   │     - rag_block: ""    (RAG dead)
   │     - visa_block: ""   (frontend never sends real visa context)
   │     - extra_context: small generic ko sentence
   │     - "[중요] 참고 자료가 부족합니다. 구체 수치/요건 단정 금지..." (injected because has_grounding=False)
   │
   └─► ASK_MODELS fallback chain:
         1) moonshotai/kimi-k2:free       (openrouter)
         2) google/gemma-4-26b-a4b-it:free(openrouter)
         3) llama-3.3-70b-versatile       (groq)        ← currently winning the fallback
```

Live evidence (see §3 for full curl trace):
- `GET /health` → **404** (Moonshot backend has no /health route; new backend would return 200).
- `POST /api/ask {}` → **422** demanding `question` and `consent` (matches Moonshot `AskRequest`, not the new schema).
- `GET /api/visas` → **500** (Moonshot version reads PostgreSQL; `DATABASE_URL` is missing/expired).
- `POST /api/ask` real Korean question → 200 with
  `model_resolved:"llama-3.3-70b-versatile", provider:"groq", lang_detected:"ko", retrieval_used:false`
  and the exact "[참고 자료]에는 ... 정보가 없습니다 ... ☎ 1345" pattern.

---

## 2. Data sources used by `ai.html` (current main)

| Source | Where | Used? | Notes |
| --- | --- | --- | --- |
| `https://web-production-14f9a.up.railway.app/api/visas` | `ai.html:395` `loadVisaData()` | yes (currently failing — 500) | Hardcoded in `API_BASE` |
| `./visa_data.json` (local 58-record file) | `ai.html:402` fallback | yes — used when `/api/visas` fails | Loaded into `VISA_DATA = []` |
| `https://web-production-14f9a.up.railway.app/api/ask` | `ai.html:555` `sendAi()` | yes — primary chat endpoint | Hardcoded |
| `VISA_DATA` (loaded at startup) | local JS state | **NOT passed to backend** | Body always sends `visa_data: { code: 'N/A', cat: 'N/A' }` (constant placeholder, line 563) |
| `doc_master.json` / `data/jobcode_master.json` | repo root / `data/` | not used by `ai.html` | Used by `index.html` only |

`ai.html` reads `lang: "ko"` only — there is no UI language selector on this page,
so multilingual users still post Korean-tagged prompts. The page does not honour
`window.PARADISO_BACKEND_URL` (documented as a follow-up in
`docs/backend/BACKEND_MIGRATION_GAP_REPORT.md`).

---

## 3. Backend / API endpoints — used vs missing

### Deployed (legacy Moonshot, live on Railway)

| Endpoint | Status | Evidence |
| --- | --- | --- |
| `GET /health` | **404** (route doesn't exist on Moonshot backend) | `curl https://.../health → 404` |
| `GET /api/visas` | **500** (DB not configured) | `curl https://.../api/visas → 500` |
| `POST /api/ask` | 200, but refusal-only | See §1 live trace. `retrieval_used:false` returned |
| `POST /api/jobcodekeywords` | not probed, likely 200 via Groq fallback | LLM-based keyword extractor |

External integrations required by the Moonshot backend and their state:

| Integration | Env var(s) | State |
| --- | --- | --- |
| OpenRouter (LLM + embeddings) | `OPENROUTER_API_KEY` | Partially up — embedding call (RAG) returning empty; kimi-k2 and gemma free-tier appear unreachable so the chain falls to Groq |
| Groq (LLM) | `GROQ_API_KEY` | Up — `llama-3.3-70b-versatile` answers |
| Supabase pgvector RAG | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, RPC `match_manual_chunks` | **Dead** — `retrieval_used:false` |
| PostgreSQL visa source | `DATABASE_URL`, table `visas_json` | **Dead** — `/api/visas` 500 |
| data.go.kr public-data cache | `PUBLIC_DATA_KEY` | **Dead** — startup cache stays at `"DATA MISSING"` (inferred from refusal pattern) |
| apis.data.go.kr law lookup | `LAW_API_KEY` | **Dead** — keyword triggers fire but no `<law>` results inject |

### In-repo (new, never deployed)

`backend/paradiso_backend.py` — present on `main`, prepared but not deployed:

| Endpoint | Schema | Frontend compatibility |
| --- | --- | --- |
| `GET /health` | yes | n/a |
| `GET /api/visas` | reads `visa_data.json` | compatible |
| `POST /api/ask` | accepts `{message, query, history, model}` | **INCOMPATIBLE** — frontend sends `{question, consent, context, lang, visa_data}`. Pydantic v2 drops unknown fields, so `prompt = (req.message or req.query or '').strip()` → `""` → **HTTP 400 empty_prompt**. Verified locally. |
| `POST /api/jobcodekeywords` | regex extractor returning `{keywords:[]}` | **INCOMPATIBLE** — frontend (`index.html`) expects `{job_keywords, industry_keywords}` |

Conclusion: if the new backend were swapped in today, all AI flows would 400/500.

---

## 4. Moonshot-era code: where it still lives

| Path | Has law/RAG code? | Notes |
| --- | --- | --- |
| `/workspaces/moonshot-source/moonshot_backend_fastapi.py` (544 lines) | **Yes — full implementation** | Outside the Paradiso repo, in a sibling workspace. Contains langdetect, multi-model fallback (kimi-k2 → gemma-4 → llama-3.3), `init_public_data_cache()` for `api.odcloud.kr/15103561` and `/15117819`, `fetch_realtime_law_data()` against `apis.data.go.kr/1170000/law`, full Supabase pgvector RAG via `match_manual_chunks` RPC, anti-hallucination system prompt, and `_build_visa_block()` for frontend-provided visa context. **This is the file currently deployed on Railway.** |
| `backend/moonshot_backend_fastapi.py` (in repo, 64 lines) | **No** | Stub kept for documentation only. Per `docs/backend/BACKEND_MIGRATION_GAP_REPORT.md`: _"a 64-line legacy-style reference stub kept for documentation; it is **not** the live application."_ |
| Git history (`git log --all -S "law.go.kr"`, `"api.data.go.kr"`, `"match_manual_chunks"`, `"moonshotai/kimi"`, `"langdetect"`) | **Nothing** | Public-data/law/RAG code was **never committed to this repo**. Only docs in `docs/backend/BACKEND_MIGRATION_GAP_REPORT.md` describe the old behavior. |
| `docs/backend/BACKEND_MIGRATION_GAP_REPORT.md` | n/a | Authoritative inventory of the Moonshot ↔ Paradiso gap. Matches this diagnosis. |

Candidate restoration files / refs:
- Authoritative reference: `/workspaces/moonshot-source/moonshot_backend_fastapi.py`.
- Sibling reference docs: `/workspaces/moonshot-source/moonshot_pipeline_architecture.md`, `/workspaces/moonshot-source/migrations/moonshot_schema.sql`.
- No commit in the Paradiso repo ever introduced or removed the law/RAG integration.

---

## 5. F-6-1 specific check

`visa_data.json` contains 58 records. F-6-1 is **not a top-level code**; the strings
`F-6-1`, `F-6-2`, `F-6-3`, `이혼`, `별거`, `자녀` all live **inside the `F-6` record's
`subCodes` / `subcodes` / `procedures` fields**. So:

- The data is present in the repo.
- The deployed `/api/ask` is not loading it (no `visa_block` reaches the prompt).
- Even if RAG were alive, embeddings would need to have ingested the nested
  subCodes chunks for F-6-1 retrieval to fire correctly. (Cannot verify without
  Supabase access.)

---

## 6. Why answers are generic — root-cause hypotheses, ranked

1. **(Highest)** Live Moonshot backend's RAG and public-data grounding return empty,
   so the system prompt's `"[참고 자료]에 명시된 내용만을 근거로 답변하라"`
   rule + `"[중요] 참고 자료가 부족합니다"` injection forces a uniform refusal.
   _Evidence:_ live `/api/ask` response includes `retrieval_used:false` and the exact
   refusal phrasing seen in production.
2. **(High)** Frontend never sends real `visa_data` — it ships a constant
   `{code:'N/A', cat:'N/A'}` payload (`ai.html:563`). So even when the user is on a
   page that *knows* the visa code, the backend's `_build_visa_block()` produces an
   empty `visa_block`. This is a second grounding hole, independent of RAG.
3. **(Medium)** Multi-model fallback now lands on Groq `llama-3.3-70b-versatile`
   because the OpenRouter free models (`kimi-k2:free`, `gemma-4-26b-a4b-it:free`)
   appear unavailable. Llama-3.3 with the anti-hallucination instruction is strict
   and never improvises, amplifying #1.
4. **(Medium)** Occasional Chinese-character leakage is consistent with the
   OpenRouter free-tier paths used by the Moonshot backend's earlier model chain
   when langdetect fell back to a non-`ko` label on short prompts. Less likely on
   today's chain (now Groq llama), but historical chats can still show it.
5. **(Lower)** New `backend/paradiso_backend.py` schema mismatch
   (`question` vs `message/query`) would break the frontend if it ever became the
   live target. Not the current production failure, but a future trap.
6. **(Background)** Public-data cache `DATA MISSING` and law-API silence are
   *causes* of #1, not separate failures. Same root: missing/expired keys
   (`PUBLIC_DATA_KEY`, `LAW_API_KEY`, `SUPABASE_*`).

The Korean-mixed-with-Chinese behavior is a symptom of #3/#4, not a separate bug.

---

## 7. Minimal safe repair plan

Do **not** modify production files in this branch. The smallest safe path to
restored answer quality, in priority order:

### Tier 0 — Verify and unblock the live backend (lowest risk, biggest win)

1. **Check Railway environment variables** on the `web-production-14f9a` service:
   `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `SUPABASE_URL`,
   `SUPABASE_SERVICE_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`), `PUBLIC_DATA_KEY`,
   `LAW_API_KEY`, `DATABASE_URL`. Confirm validity by hitting each provider
   directly.
2. **Verify Supabase RPC** `match_manual_chunks` is callable and has populated
   `manual_chunks` rows + embeddings. If the table is empty or the function was
   dropped, RAG returns nothing regardless of keys.
3. **Verify the `visas_json` Postgres table** powering `/api/visas`, or
   accept the 500 and rely on the frontend's `./visa_data.json` fallback.

If any of (1)/(2) repairs the grounding pipeline, the refusal pattern disappears
without any code change.

### Tier 1 — Frontend grounding hardening (small, safe)

4. In `ai.html`, when the user message mentions a known visa code, look it up in
   the locally-loaded `VISA_DATA` and send the real record as `visa_data` (instead
   of `{code:'N/A',cat:'N/A'}`). The Moonshot backend's `_build_visa_block()`
   already supports the schema. This restores a grounding source even with RAG
   still dead.

### Tier 2 — Reconcile the two backends

5. Decide which backend is the source of truth going forward:
   - **Path A (recommended short term):** keep the deployed Moonshot backend,
     restore its env config, and treat `backend/paradiso_backend.py` as work-in-
     progress that must reach parity before any cutover.
   - **Path B (longer):** port the Moonshot features (langdetect, multi-model
     fallback, public-data cache, law lookup, RAG, anti-hallucination prompt,
     `visa_block`) into `backend/paradiso_backend.py`, align its `AskRequest`
     schema with `{question, consent, context, lang, visa_data}`, and only then
     swap the Railway deployment. Follow the order already laid out in
     `docs/backend/BACKEND_MIGRATION_GAP_REPORT.md` §_Recommended next PRs_.
6. Once Path B lands, rewire `ai.html` and `index.html` to read
   `window.PARADISO_BACKEND_URL` instead of the hardcoded legacy URL.

### Tier 3 — Data-coverage gaps

7. Confirm the manual-chunks index covers F-6 subcodes (F-6-1, F-6-2, F-6-3) and
   their divorce/separation/custody provisions. The repo's `visa_data.json` has
   these strings under `F-6.subCodes`; verify they were chunked and embedded.

---

## 8. Recommended branch plan

| Branch | Purpose | Touches |
| --- | --- | --- |
| `audit/ai-pipeline-diagnosis` (this branch) | Diagnosis report only | adds `docs/AI_PIPELINE_DIAGNOSIS.md` |
| `ops/restore-railway-env-config` | Tier 0 — re-enter missing keys on Railway; verify Supabase + DB; document `.env.example` updates if needed | no production code changes; possibly `backend/.env.example` and `docs/backend/*` |
| `feat/ai-html-send-real-visa-data` | Tier 1 — `ai.html` enriches `visa_data` payload from local `VISA_DATA` when the user message contains a visa code | `ai.html` only |
| `feat/paradiso-backend-parity-{langdetect,visa-block,prompt}` | Tier 2.B step 1 — incremental parity, no live cutover | `backend/paradiso_backend.py` |
| `feat/paradiso-backend-rag` | Tier 2.B step 2 — Supabase RAG | `backend/paradiso_backend.py` |
| `feat/paradiso-backend-public-data` | Tier 2.B step 3 — data.go.kr + law lookup | `backend/paradiso_backend.py` |
| `feat/frontend-use-window-paradiso-backend-url` | Tier 2 step 6 | `ai.html`, `index.html` |
| `chore/ops-railway-cutover` | Final swap when parity reached | Railway config + smoke tests |

Each branch is independently shippable. None require touching this diagnostic
branch.

---

## 9. What this branch does and does not do

**Does:**
- Document the live failure mode end-to-end with reproducible evidence.
- Map the deployed architecture, the in-repo architecture, and the gap between them.
- Identify the Moonshot-era reference implementation at
  `/workspaces/moonshot-source/moonshot_backend_fastapi.py`.

**Does not:**
- Restore any code from the sibling workspace.
- Modify `ai.html`, `index.html`, `backend/*`, or `visa_data.json`.
- Touch Railway, Supabase, or any external provider.
- Open a PR or push.
