# Paradiso AI — Safe Automation Architecture

> **Status:** design document only. No production behavior is changed by
> merging this file. No active grounding entries are added. No `/api/ask`
> path is touched. This document defines what we will and will not build
> next, and what stays mandatory-human-review.

## 1. Purpose

Paradiso AI cannot yet answer concrete, status-specific Korean
immigration questions reliably across all stay/visa statuses. Today the
backend ships deterministic manual grounding for only three procedures
(D-2 체류기간 연장허가, D-4 어학연수생(D-4-1, D-4-7) 체류기간 연장허가,
E-7 일반 체류기간 연장허가) and falls back to a generic LLM answer for
everything else.

This document defines a **safe automation architecture** that lets us
expand coverage without ever silently rewriting what Paradiso AI tells
users. The end-to-end flow is:

```
official sources
  → source monitoring (detect change)
  → change reports (issue / PR comment, never auto-merge)
  → draft candidates (under candidates/, not active fixtures)
  → validation (schema + verification metadata, automated checks only)
  → draft PR with human reviewers
  → human review (Korean immigration domain reviewer)
  → merge
  → production grounding effect
```

Every arrow except the last two is allowed to be automated. The last two
— review and merge — stay human, always.

## 2. Why this is NOT automatic model training

The architecture below is deliberately **not** a self-learning loop. In
particular:

- We do **not** fine-tune the answering LLM on user queries.
- We do **not** train embeddings on user queries or law text.
- We do **not** retrieve from a live law API at request time.
- We do **not** keep an index of user queries to "teach" the model.
- We do **not** auto-promote machine-generated content into the active
  grounding fixture.
- We do **not** auto-merge any PR that touches grounding, law
  interpretation, notice content, or any user-visible knowledge.

"Learning" in this system means: a human reviewer reads a candidate that
references a specific, committed PDF page or a specific law clause and
either approves a verbatim excerpt, edits it, or rejects it. The model
itself never updates from user behavior. The fixture only updates
through a reviewed PR. Coverage gaps inform **what humans should review
next**, not what the model autonomously absorbs.

## 3. Why production knowledge must not update without human review

Korean immigration content has three properties that make autonomous
updates unsafe:

1. **High legal sensitivity.** Wrong document lists, status-code
   confusions, or paraphrased exceptions can cause users to miss filings
   or be denied. Paradiso provides reference information only; it must
   not silently invent or paraphrase requirements.
2. **Fine-grained sub-code semantics.** D-4-1 vs D-4-2K, F-6-1 vs F-6-3,
   E-7 일반 vs E-7-4 숙련기능인력 differ in 제출서류, 심사기준, and
   체류기간. A summarizer that drops the sub-code is dangerous; today the
   selector explicitly refuses to over-generalize (see
   `_GROUNDED_VISA_CODES`, `sub_codes_covered`).
3. **Source provenance must be reproducible.** Every active grounding
   row carries `source_file`, `page_range`, and a `verification_note`
   that says exactly which `pdftotext` extraction produced it. Auto-
   promoted content cannot guarantee that, because no human re-checked
   the extraction.

Human review is therefore mandatory before any production grounding
change, including:

- adding a new `(visa_code, procedure_type)` entry;
- adding or modifying a sub-code-scoped entry;
- modifying `required_documents`, `caveats`, or `source_excerpt`;
- changing the answering system prompt;
- changing fallback / out-of-scope behavior.

## 4. Architecture overview

```
┌────────────────────────────────────────────────────────────────────┐
│ data/source_registry.json   (allow-list of official sources)       │
└────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│ scripts/check_source_updates.py                                    │
│   - reads source_registry                                          │
│   - records last-seen hashes/etags in data/source_state.json        │
│   - emits a change report (stdout + optional GH issue)             │
│   - does NOT scrape by default; HTTP fetch is opt-in per source    │
└────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Human triage                                                       │
│   - decides whether the change is in scope                         │
│   - opens a candidate folder under                                 │
│     backend/data/manual_grounding/candidates/<slug>/                │
└────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│ scripts/validate_manual_grounding_candidate.py                      │
│   - JSON schema + provenance lint only                              │
│   - never writes to stay_manual_grounding_2026_05.json              │
└────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│ scripts/promote_grounding_candidate.py  (DRY-RUN by default)       │
│   - prints diff that *would* be applied                            │
│   - refuses to write unless --i-am-a-human-reviewer is passed      │
│   - even with the flag, it only stages a branch + opens a draft PR │
└────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────┐
│ Draft PR → human review → merge to main                            │
│   (only at this point does the active fixture change)              │
└────────────────────────────────────────────────────────────────────┘
```

In parallel, two read-only feedback loops feed the triage step:

- **Notice monitoring** (HiKorea / Ministry of Justice notice pages)
  produces *notice candidates* that link to the originating notice URL
  and a captured snapshot. Candidates open issues or draft PRs; they
  never edit visa data or grounding fixtures directly.
- **Privacy-safe coverage analytics** runs only on locally-supplied,
  PII-redacted aggregate JSON. It reports which `(visa_code,
  procedure_type, sub_code)` combinations users ask about but Paradiso
  cannot ground. It tells humans what to write next; it never proposes
  text.

## 5. Source monitoring flow

1. `data/source_registry.json` enumerates every official source we
   monitor: the 2026.5 stay manual, the 2026.5 visa-issuance manual,
   the relevant 법령 (Acts and Enforcement Decrees), the relevant
   고시/지침, and named HiKorea notice indexes. Each entry carries:
   - `id`, `kind` (`pdf_manual` | `law_clause` | `notice_index`),
   - `authority` (e.g. `법무부 출입국·외국인정책본부`),
   - `url` (canonical, public),
   - `local_path` (when committed) or `null`,
   - `fetch_mode` (`offline` | `manual_upload` | `http_optional`),
   - `notes` (why this source matters).
2. `scripts/check_source_updates.py` reads the registry and compares:
   - committed PDFs against `data/source_state.json` (sha256, page
     count, last-seen mtime),
   - optional HTTP HEAD/GET against a stored ETag/Last-Modified, but
     **only** when `fetch_mode == "http_optional"` and the operator
     passes `--allow-http`.
3. Output is a structured change report (JSON) plus a human-readable
   summary. The report can be posted as a GitHub issue from a
   `workflow_dispatch` workflow; it is never auto-applied.
4. No scraping of HiKorea, 국가법령정보센터, or any third-party site is
   performed by default. The HTTP path is opt-in, rate-limited, fetches
   only the registry's explicit URLs, and respects `robots.txt`.

## 6. Law API candidate flow (법령 조문 interpretation)

Today `LAW_API_KEY` is declared but unused
(`backend/paradiso_backend.py:54`). We will *not* wire a live law-API
call into `/api/ask`. Instead:

1. A future `scripts/fetch_law_clauses.py` (out of scope for this PR)
   will, given a list of statute IDs in `source_registry.json`, fetch
   clauses via the official 국가법령정보센터 OPEN API using
   `LAW_API_KEY` from the operator's environment.
2. The fetched clauses are written to
   `backend/data/manual_grounding/candidates/<slug>/law_excerpt.json`
   with: clause text, statute ID, article number, effective date,
   retrieval timestamp, and a `verification_status: "machine_fetched"`
   flag.
3. A human reviewer reads the clause, decides whether it is a citation
   or an interpretation, and either:
   - upgrades it to a manual grounding candidate (with explicit
     `required_documents` and caveats taken from the verified manual,
     not paraphrased from the clause), or
   - rejects it.
4. No 법령 interpretation is ever surfaced through `/api/ask` without
   passing the same review gate that PDF-derived grounding passes.

## 7. Notice monitoring flow

HiKorea notices (공지사항) and Ministry of Justice notices change
faster than the printed manual. A notice can affect document checklists
mid-cycle. To handle this safely:

1. `source_registry.json` lists notice index URLs as
   `kind: "notice_index"` with `fetch_mode: "http_optional"`.
2. `scripts/check_source_updates.py --notices` (future, opt-in) fetches
   each index page once, extracts notice titles, dates, and URLs, and
   diffs against `data/source_state.json`.
3. New notices produce *notice candidates* in
   `backend/data/manual_grounding/candidates/<slug>/notice.json`:
   `{ title_ko, url, captured_snapshot_path, observed_at,
   relevant_visa_codes (human-tagged), proposed_action }`.
4. A human reviewer decides whether the notice warrants a fixture
   change. If so, they author a manual grounding candidate (PDF-page-
   verified, not notice-paraphrased). If the notice merely contradicts
   the current manual until the manual is reissued, the reviewer can
   ship a caveat-only PR — still human-authored, still reviewed.
5. Notice text is **never** copied verbatim into `/api/ask` prompts.

## 8. Manual grounding candidate flow

This is the central, deterministic path. It does not depend on
embeddings, vector search, or live retrieval.

1. A reviewer (human or a future Codex pass under human direction)
   identifies a `(visa_code, visa_sub_code, scenario, procedure_type)`
   target — for example, D-10-1 점수제 적용 체류기간 연장허가.
2. They create
   `backend/data/manual_grounding/candidates/<slug>/candidate.json`
   following the schema 1.2 contract documented in
   `docs/manual_grounding_expansion_plan.md`. The file must include:
   `source_file`, `page_range`, `source_excerpt` (verbatim),
   `required_documents` (verbatim bullets), `caveats`,
   `verification_note`, `source_verification_status` (must start as
   `"unverified"` or `"machine_extracted"`, never `"verified_locally"`).
3. `scripts/validate_manual_grounding_candidate.py` enforces:
   - schema parity with the active fixture's schema 1.2,
   - presence of `verification_note`, `page_range`, `source_file`,
   - that `visa_sub_code` / `sub_codes_covered` / `scenario` are
     populated consistently with `_select_grounding`'s rules,
   - that `source_verification_status != "verified_locally"` unless a
     reviewer has signed off in a sibling `REVIEW.md` file.
4. The candidate sits under `candidates/` indefinitely. The active
   fixture (`stay_manual_grounding_2026_05.json`) is **not** touched by
   any script.

## 9. Reviewed-only promotion flow

`scripts/promote_grounding_candidate.py` is the only script that can
move a candidate into the active fixture, and it is intentionally
hostile to automation:

- Default mode: `--dry-run`. Prints the diff that *would* be applied to
  `stay_manual_grounding_2026_05.json`, runs the validator, and exits 0
  without writing anything.
- Write mode: requires `--i-am-a-human-reviewer` **and** a
  `REVIEW.md` next to the candidate with a human signoff line
  (`Reviewed-by: <name> <email>` and `Verification: pdftotext -f N -l M
  ...`). In write mode, the script:
  1. creates a new local branch (`grounding/<candidate-slug>`),
  2. applies the diff,
  3. commits with a deterministic message,
  4. exits, telling the operator to open a **draft** PR.
- The script **never** pushes, never opens a PR, and never merges. CI
  forbids direct pushes to `main`.
- A repository policy (documented here, enforced by branch protection)
  forbids merging any PR that touches
  `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
  without at least one human reviewer with domain context.

## 10. Privacy-safe coverage analytics flow

The goal is to know which questions Paradiso AI cannot answer, without
training on user data, without storing raw user logs, and without ever
shipping user-supplied text into the active prompt or fixture.

Constraints encoded in the architecture:

- `/api/ask` does **not** persist raw prompts. Backend logs remain at
  `INFO` level and contain only operational metadata (provider, model,
  detection booleans, latency). No prompt text is stored server-side.
- Analytics input is a **locally-supplied** aggregate JSON file the
  operator drops into `data/coverage_input/*.json`. This file must
  already be redacted (no email, phone, passport numbers, names,
  free-text quotes). Contributors generate it from their own
  environment; the repository does not ingest user data.
- `scripts/analyze_coverage_gaps.py` reads only that local JSON,
  produces a report of:
  - top ungrounded `(visa_code, sub_code, procedure_type)` triples,
  - top off-topic / non-Korean-immigration triggers,
  - top sub-code-missing-clarification cases,
  - a recommended candidate authoring queue.
- The report is printed and optionally written to
  `data/coverage_reports/<date>.md`. No call to the answering LLM is
  made; no embeddings are computed.
- The report contains **counts and codes only** — no user text, no
  free-form excerpts, no IDs traceable to a session.

A separate document, `docs/privacy_safe_coverage_analytics.md`, will
describe the input schema and the redaction contract in detail.

## 11. Golden evaluation suite

To detect regressions when grounding changes, we add a *golden*
evaluation suite of human-authored Korean immigration questions with
expected detection outcomes (not expected free-form answers, since the
LLM response is non-deterministic). The suite asserts on:

- `visa_code_detected`, `visa_sub_code_detected`, `task_type_detected`,
- `grounding_used` boolean,
- `grounding_sources[*].page_range` and `source_file`,
- absence of generic global-immigration boilerplate (USCIS / Home
  Office mentions) in deterministic-prompt unit assertions.

The suite ships as additional cases inside
`backend/tests/test_paradiso_backend.py` or a sibling file. It does
**not** call the live LLM provider; it asserts on the deterministic
selection and prompt-building layer the existing tests already exercise.

## 12. Allowed automation vs forbidden automation

| Area                                      | Allowed automation                                                                 | Forbidden automation                                                                          |
| ----------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Source change detection                   | Hash/etag diff on committed PDFs and opt-in HTTP HEAD on registry URLs             | Default-on scraping of HiKorea, 국가법령정보센터, or any third-party site                       |
| 법령 조문 retrieval                         | Opt-in OPEN API fetch into `candidates/` with `machine_fetched` status              | Live law-API call from `/api/ask`; paraphrasing a clause into a checklist                     |
| Notice monitoring                         | Opt-in notice-index diff into a notice candidate                                    | Auto-copying notice text into prompts; auto-modifying visa data                               |
| Manual grounding candidate generation     | Schema-valid candidate files under `candidates/` with verbatim extracts             | Writing to `stay_manual_grounding_2026_05.json` from any script                               |
| Candidate validation                      | JSON schema + provenance lint                                                      | Approving content correctness; declaring `verified_locally` without `REVIEW.md`               |
| Candidate promotion                       | Dry-run diff; branch + commit only with `--i-am-a-human-reviewer` + `REVIEW.md`     | Auto-push, auto-PR, auto-merge                                                                |
| Coverage analytics                        | Local PII-redacted aggregate JSON → counts-only report                              | Persisting raw prompts; computing embeddings on user data; calling the answering LLM           |
| Evaluation                                | Deterministic golden cases on detection + prompt building                          | Asserting on free-form LLM output text                                                        |
| Production knowledge updates              | Draft PR opened by a human reviewer                                                | Direct-to-`main` commits; auto-merge; bot-only review                                         |
| `/api/ask` behavior                       | No change in this architecture                                                      | Any behavior change without an explicit, separately-reviewed PR                               |

## 13. Safety policy table (dangerous → safe equivalent)

| Dangerous automation                                         | Safe equivalent                                                                                                 |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 법령 조문 자동 해석 → 사용자 응답                              | legal reference candidate (`candidates/<slug>/law_excerpt.json`, verbatim clause) + human review + manual citation |
| HiKorea/법무부 공지 자동 요약 → 사용자 응답                    | notice candidate + GitHub issue or draft PR + human review                                                       |
| manual fixture 자동 promotion                                  | reviewed-only promotion PR (`--dry-run` by default, requires `REVIEW.md` + `--i-am-a-human-reviewer`)            |
| 문서 체크리스트 자동 active 삽입                                | source-verified candidate (PDF page + `verification_note`) + validator + tests + human merge                     |
| 사용자 로그 기반 학습/파인튜닝                                 | PII-redacted aggregate coverage analytics (counts of `(visa_code, sub_code, procedure_type)` triples only)        |
| 자동 paraphrase of 매뉴얼/법령 into prompt                     | verbatim 발췌 only; paraphrase is a human task at review time, never a script's task                              |
| 자동 cross-status generalization (e.g. D-4 → D-4-2K)           | per-sub-code entries, `sub_codes_covered` allow-list, top-level gate via `_GROUNDED_VISA_CODES`                  |
| 자동 fallback to generic global-immigration boilerplate        | Korea-immigration guardrail in the ungrounded fallback prompt (PR C below); explicit "source unavailable" answer  |

## 14. Recommended PR sequence

Each PR below is intended to be small enough for one human reviewer to
read end-to-end. None of them changes `/api/ask` answers without
explicit human merge.

- **PR A — Source monitoring pipeline skeleton.**
  Adds `data/source_registry.json`,
  `backend/data/manual_grounding/candidates/README.md`,
  `scripts/check_source_updates.py`,
  `scripts/validate_manual_grounding_candidate.py`,
  `docs/source_monitoring_pipeline.md`, and optionally a
  `workflow_dispatch`-only workflow. No HTTP by default. No fixture
  changes. No `/api/ask` changes.

- **PR B — Coverage / eval suite.**
  Adds deterministic golden evaluation cases (detection + prompt
  building), and the privacy-safe coverage analytics skeleton
  (`scripts/analyze_coverage_gaps.py`,
  `docs/privacy_safe_coverage_analytics.md`). No new grounding entries.
  No user-log ingestion.

- **PR C — Fallback Korea-immigration guardrail.**
  Tightens the ungrounded `/api/ask` prompt so that, when no
  deterministic grounding is selected, the model is still constrained
  to (a) stay within Korean immigration scope, (b) refuse to invent
  document lists, (c) tell the user the source is not loaded for this
  case and to verify with the 출입국·외국인청 / 1345 / HiKorea, and (d)
  not blend in USCIS / Home Office content. Requires test updates that
  assert on the deterministic prompt-building path only.

- **PR D — Subcode-aware selector hardening.**
  Extends the existing selector to accept a `requires_clarification`
  hint when sub-code is missing for top-levels whose document list
  varies materially by sub-code (e.g. D-10, F-6). Backend returns a
  clarification message instead of a generic answer. No new active
  entries; only behavior on detection of an under-specified question.

- **PR E — Law API adapter (offline-first).**
  Adds `scripts/fetch_law_clauses.py` that reads
  `data/source_registry.json` clauses and writes machine-fetched
  excerpts into `candidates/<slug>/law_excerpt.json`. Requires
  `LAW_API_KEY` in the operator's environment; never reads or writes
  the active fixture. Documented but not wired to `/api/ask`.

- **PR F — Notice watcher (opt-in).**
  Extends `check_source_updates.py` with a `--notices` opt-in mode that
  diffs notice-index URLs and writes notice candidates. Rate-limited.
  Respects `robots.txt`. No automatic prompt change.

- **PR G — Reviewed-only candidate promotion.**
  Adds `scripts/promote_grounding_candidate.py` as a dry-run-by-default
  promoter. Adds branch protection / CODEOWNERS coverage for
  `backend/data/manual_grounding/**`. Includes a worked-example
  candidate (e.g. D-10-1 점수제 적용) under `candidates/` but **not**
  in the active fixture.

- **PR H — Privacy-safe coverage analytics.**
  Fills in the analytics report generator, the local-only input
  contract, and a sample redacted aggregate input. Never reads raw
  prompts or session IDs. Output is counts + codes only.

PRs A and B are independent and can land in either order. PR C is the
first user-visible behavior change; it is intentionally a tightening,
not an expansion. PRs D–H build on A and B and should each land as a
separate small PR with its own human reviewer.

## 15. Hard constraints (recap)

The following must hold at every step of every PR above:

- Do **not** push directly to `main`.
- Do **not** change `/api/ask` behavior outside of PR C and PR D, and
  only with explicit human review and tests.
- Do **not** add new active grounding entries from any script. Active
  entries live only in `stay_manual_grounding_2026_05.json` and are
  added by a reviewed PR.
- Do **not** implement full RAG.
- Do **not** implement embeddings or vector search.
- Do **not** implement production law-API retrieval reachable from
  `/api/ask`.
- Do **not** scrape external websites by default.
- Do **not** store secrets in the repository. `LAW_API_KEY`,
  `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `SUPABASE_*` stay in the
  operator's environment.
- Do **not** store raw user logs.
- Do **not** touch `index.html` or `ai.html`.
- Do **not** modify `visa_data.json` or `backend/data/visas.json` from
  any automation script.
- Do **not** touch the registered-agent finder UX.
- Do **not** create autonomous production updates.
- Human review must remain mandatory before any production grounding
  change.

## 16. Open questions (intentionally deferred)

- Whether to host candidate review in GitHub issues vs. draft PRs (this
  document allows either; PR G picks one).
- Whether to mirror notice-page snapshots in-repo (large) or out-of-
  repo (link only). Default: link only; capture a hash, not the full
  HTML.
- Whether to add a 2026.x manual rev-bump workflow that auto-opens an
  issue when `source_manifest.json` changes hands. Out of scope for the
  PRs above; revisit after PR A.
