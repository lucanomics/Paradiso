# Codex implementation brief — safe Paradiso AI automation

> Read `docs/paradiso_ai_safe_automation_architecture.md` first. This
> brief is the precise step-by-step implementation companion to that
> architecture. The intended audience is a Codex pass (or a human
> implementer) executing **PR A** of the recommended sequence:
> "Source monitoring pipeline skeleton".

This brief is a *bounded* instruction. The architecture allows more,
but PR A only ships the skeleton below. Do not attempt PR B through
PR H in the same pass. Do not implement anything not listed here.

## 0. Hard rules for the Codex pass

Codex **must NOT**:

1. Change production `/api/ask` behavior or any code under
   `backend/paradiso_backend.py` (other than imports that are
   genuinely unavoidable — and only if explicitly required by this
   brief; today, it is not).
2. Add, edit, remove, or reorder any entry in
   `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`.
3. Create any file under `backend/data/manual_grounding/candidates/`
   other than the `README.md` specified below. No example candidate
   JSON files. No active grounding rows. No "sample" content that
   could be mistaken for production data.
4. Scrape any external website by default. The `check_source_updates`
   script may *declare* an HTTP mode, but it must be off by default and
   must require an explicit `--allow-http` flag. No code path may make
   a network request unless `--allow-http` is passed.
5. Store secrets in the repo. `LAW_API_KEY`, `OPENROUTER_API_KEY`,
   `GROQ_API_KEY`, `SUPABASE_*` keys are read from the operator's
   environment only. No `.env`, no defaults, no placeholders that look
   like real keys.
6. Store raw user logs. Any new analytics path reads only locally-
   supplied aggregate JSON the operator drops on disk; that JSON is
   not committed.
7. Auto-promote candidates. `promote_grounding_candidate.py` must be a
   **dry-run-by-default skeleton**. In this PR it does not actually
   write to the active fixture even with the write flag — it stops
   after printing the diff and instructing the operator to author the
   PR by hand. (Real promotion lands in PR G.)
8. Auto-merge anything. Any workflow added in this PR must be
   `workflow_dispatch:` only — no `on: push`, no `on: schedule`, no
   `on: pull_request` auto-triggers.
9. Touch `index.html`, `ai.html`, `visa_data.json`,
   `backend/data/visas.json`, or the registered-agent finder UX.
10. Push to `main`, or to any branch other than the one assigned to
    this task.

If a step below appears to require violating one of these rules,
**stop and ask** in the PR description rather than improvising.

## 1. Files to create

Codex creates exactly the following files in PR A. No others.

```
data/source_registry.json
backend/data/manual_grounding/candidates/README.md
scripts/check_source_updates.py
scripts/validate_manual_grounding_candidate.py
scripts/promote_grounding_candidate.py
scripts/analyze_coverage_gaps.py
docs/source_monitoring_pipeline.md
docs/privacy_safe_coverage_analytics.md
.github/workflows/source-monitoring.yml         # optional, workflow_dispatch only
```

Everything below describes each file's contract. Where the brief says
"skeleton", Codex implements just enough to validate inputs and print a
report — no real network calls, no fixture mutations.

### 1.1 `data/source_registry.json`

Allow-list of official sources Paradiso monitors. Versioned schema.

Required shape:

```json
{
  "schema_version": "1.0",
  "generated_for": "Paradiso AI safe automation — PR A",
  "sources": [
    {
      "id": "stay_manual_2026_05",
      "kind": "pdf_manual",
      "title_ko": "외국인체류 안내매뉴얼",
      "version": "2026.5",
      "authority": "법무부 출입국·외국인정책본부",
      "url": "https://www.moj.go.kr/...",
      "local_path": "docs/source-manuals/2026-05/stay_manual_2026_05.pdf",
      "fetch_mode": "offline",
      "notes": "Primary source for stay/extension grounding (schema 1.2)."
    },
    {
      "id": "visa_manual_2026_05",
      "kind": "pdf_manual",
      "title_ko": "사증발급 안내매뉴얼",
      "version": "2026.5",
      "authority": "법무부 출입국·외국인정책본부",
      "url": "https://www.moj.go.kr/...",
      "local_path": "docs/source-manuals/2026-05/visa_manual_2026_05.pdf",
      "fetch_mode": "offline",
      "notes": "Visa-issuance manual; not used for stay grounding."
    },
    {
      "id": "law_immigration_act",
      "kind": "law_clause",
      "title_ko": "출입국관리법",
      "authority": "국가법령정보센터",
      "url": "https://www.law.go.kr/법령/출입국관리법",
      "local_path": null,
      "fetch_mode": "http_optional",
      "notes": "Read via OPEN API in a future PR; offline by default."
    },
    {
      "id": "hikorea_notice_index",
      "kind": "notice_index",
      "title_ko": "HiKorea 공지사항",
      "authority": "법무부 출입국·외국인정책본부",
      "url": "https://www.hikorea.go.kr/...",
      "local_path": null,
      "fetch_mode": "http_optional",
      "notes": "Monitored only when --allow-http and --notices are both passed."
    }
  ]
}
```

Rules:

- All `url` values must be official `.go.kr` or canonical authority
  pages. Codex does not have to verify the exact URLs are live — leave
  a clear `"TODO: confirm URL"` in `notes` when uncertain. Do **not**
  fabricate plausible-looking URLs without flagging them.
- `local_path` for committed PDFs must match files that already exist
  in this repository. Verify with `ls docs/source-manuals/2026-05/`.
- `fetch_mode` is one of `"offline"`, `"manual_upload"`,
  `"http_optional"`. Default to the most restrictive accurate value.

### 1.2 `backend/data/manual_grounding/candidates/README.md`

A README that:

- explains the directory exists for *candidate* manual grounding
  entries that have not been reviewed yet;
- explicitly states that nothing under this directory is read by
  `/api/ask` or by `_load_stay_manual_grounding()`;
- documents the candidate directory layout
  (`candidates/<slug>/candidate.json`, `candidates/<slug>/REVIEW.md`,
  `candidates/<slug>/notice.json`, `candidates/<slug>/law_excerpt.json`
  as optional siblings);
- documents the required schema fields and points the reader at
  `docs/manual_grounding_expansion_plan.md` for the schema 1.2 contract;
- says candidates start with `source_verification_status` of
  `"unverified"` or `"machine_extracted"` and are only upgraded to
  `"verified_locally"` by a human reviewer who adds a `REVIEW.md`
  signoff.

Codex must **not** create any subdirectory under `candidates/` and
must **not** ship an example candidate file.

### 1.3 `scripts/check_source_updates.py`

CLI. Reads `data/source_registry.json` and a state file
`data/source_state.json` (create it on first run with empty contents).

Required behaviors:

1. Default mode (no flags): iterate every `pdf_manual` entry whose
   `local_path` is set and exists, compute `sha256` and page count via
   `pdftotext` only if poppler is available; otherwise fall back to
   file size + mtime. Compare against the stored state and emit a
   report.
2. `--allow-http`: required to attempt any network call. Without it,
   `http_optional` entries are skipped with an explicit "skipped: HTTP
   disabled" line in the report.
3. `--notices`: opt-in flag that, combined with `--allow-http`, allows
   `notice_index` entries to be diffed. Without `--notices`, notice
   indexes are skipped.
4. `--report-path <path>`: write a structured JSON report to disk in
   addition to stdout. Default behavior is stdout only.
5. Output sections: `summary`, `changed`, `unchanged`, `skipped`,
   `errors`. Each `changed` entry carries `id`, `previous_hash`,
   `current_hash`, `observed_at` ISO-8601 timestamp.
6. The script must not modify `data/source_state.json` unless
   `--update-state` is passed. PR A leaves state updates off by
   default so the very first invocation reports "no previous state"
   without silently bootstrapping.
7. Exit non-zero only on validation errors (bad registry shape,
   missing required fields). Detected changes themselves are not
   failures.

The HTTP path may be a stub that raises `NotImplementedError("HTTP
fetch not implemented in PR A")` when both `--allow-http` and an
`http_optional` source are present, but the *flag handling and dry-run
behavior* must work end-to-end so the workflow is testable.

### 1.4 `scripts/validate_manual_grounding_candidate.py`

CLI: `validate_manual_grounding_candidate.py <path-to-candidate.json>`.

Behavior:

- Refuse to run on
  `backend/data/manual_grounding/stay_manual_grounding_2026_05.json` —
  the active fixture is out of scope; the script exits with a clear
  error if pointed at it.
- Load the candidate JSON, validate schema 1.2 keys against the contract
  documented in `docs/manual_grounding_expansion_plan.md`:
  - required: `grounding_id`, `visa_code`, `procedure_type`,
    `source_verification_status`, `verification_note`, `page_range`
    (when `source_file` is a committed PDF), `source_excerpt`,
    `required_documents`, `caveats`, `language`, `country_scope`.
  - optional but checked: `visa_sub_code`, `sub_codes_covered`,
    `scenario`, `scenarios_covered`,
    `requires_clarification_when_missing_subcode`.
- Enforce: `source_verification_status` ∈ {`"unverified"`,
  `"machine_extracted"`, `"verified_locally"`}. If
  `"verified_locally"`, refuse unless a sibling `REVIEW.md` exists in
  the candidate directory.
- Enforce: `country_scope == "KR"` and `language == "ko"`.
- Enforce: `procedure_type == "체류기간 연장허가"` for this PR's scope
  (other procedure types are *allowed* but emit a warning, since the
  selector only grounds extensions today).
- Enforce sub-code consistency: if `visa_sub_code` is set, it must
  start with `visa_code + "-"`. If `sub_codes_covered` is set, every
  element must start with `visa_code + "-"`.
- The script **never writes** to the candidate file and **never**
  touches the active fixture.
- Exit 0 on pass, non-zero on validation failure. Output should be a
  human-readable list of findings plus a JSON summary at the end.

### 1.5 `scripts/promote_grounding_candidate.py` — dry-run skeleton

CLI: `promote_grounding_candidate.py <candidate-slug>`.

In PR A this script is a **skeleton**. It:

1. Resolves the candidate at
   `backend/data/manual_grounding/candidates/<slug>/candidate.json`
   and ensures `REVIEW.md` exists in the same directory.
2. Runs `validate_manual_grounding_candidate.py` on the candidate.
3. Reads `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
   and computes the **diff** that *would* be produced if the candidate
   were appended to `groundings[]`.
4. Prints the diff in unified format (or, if simpler, prints the
   prospective merged JSON for the operator to compare manually).
5. Exits with a banner explaining: "Dry-run only. Promotion will be
   wired up in PR G. To promote today, hand-edit the fixture in a
   draft PR after a human reviewer signs `REVIEW.md`."
6. Refuses to write to the fixture *even if* a `--i-am-a-human-reviewer`
   flag is passed. The flag is accepted (so the CLI contract is
   stable) but in PR A it only changes the banner text to say
   "promotion not yet implemented — please apply manually".

The script must not stage, commit, or push anything. No `git` calls.

### 1.6 `scripts/analyze_coverage_gaps.py` — privacy-safe skeleton

CLI: `analyze_coverage_gaps.py <path-to-aggregate-json>`.

Input contract (documented in `docs/privacy_safe_coverage_analytics.md`,
see 1.8): a local JSON file with shape:

```json
{
  "schema_version": "1.0",
  "window": { "start": "2026-04-01", "end": "2026-04-30" },
  "totals": { "asks": 12345 },
  "by_triple": [
    {
      "visa_code": "F-6",
      "visa_sub_code": null,
      "task_type": "extension",
      "count": 240,
      "grounded": false,
      "clarification_offered": false
    }
  ]
}
```

Rules:

- Input must already be PII-redacted. The script does **not** ingest
  raw prompts, session IDs, IP addresses, or any free-text fields. If
  the input JSON contains keys outside the documented schema, the
  script refuses to process the file and prints a list of forbidden
  keys.
- Input files are expected under `data/coverage_input/` but the
  directory is **not** created or committed by this PR. The
  `.gitignore` (if any change is needed) keeps `data/coverage_input/`
  and `data/coverage_reports/` out of version control. Codex must add
  a `.gitignore` entry under `data/` for those two paths if a `data/`
  ignore file does not already enforce them; otherwise leave the
  ignore rules alone.
- Output: a Markdown report listing the top N (default 20) ungrounded
  triples sorted by `count`, plus a recommended candidate-authoring
  queue. The report contains only counts and codes — no prompt text.
- The script does not call any LLM, does not compute embeddings, and
  does not make any network call.

### 1.7 `docs/source_monitoring_pipeline.md`

Short doc (300–600 words) that:

- explains the pipeline from `source_registry.json` → state file →
  change report → human triage → candidate folder;
- documents the `check_source_updates.py` CLI flags;
- restates that HTTP and notice fetching are opt-in and off by default;
- restates that no candidate file is auto-created, ever;
- restates that the active fixture is never written by any script.

Cross-link `docs/paradiso_ai_safe_automation_architecture.md` and
`docs/manual_grounding_expansion_plan.md`.

### 1.8 `docs/privacy_safe_coverage_analytics.md`

Short doc (300–600 words) that:

- documents the local-only aggregate input contract for
  `analyze_coverage_gaps.py`;
- enumerates the keys the script accepts and explicitly forbids every
  other key (especially `prompt`, `question`, `query`, `message`,
  `text`, `body`, `email`, `phone`, `passport`, `name`, `session_id`,
  `user_id`, `ip`, `country_of_origin`);
- explains why we do not persist raw prompts server-side and why
  analytics inputs are local-only files;
- explains that the output report contains counts and codes only and
  is safe to commit only when a human reviewer has confirmed it
  contains no leaked text.

### 1.9 `.github/workflows/source-monitoring.yml` (optional but preferred)

Workflow that:

- triggers **only** on `workflow_dispatch` — no `push`, no `schedule`,
  no `pull_request`;
- runs `scripts/check_source_updates.py` in default mode (no
  `--allow-http`) and uploads the report as a build artifact;
- does **not** open issues, does **not** open PRs, does **not** push
  commits, does **not** modify the repo state;
- does **not** set any secret in the runner. `LAW_API_KEY` etc. are
  not used by this workflow.

If Codex omits this file in PR A, that is acceptable — the architecture
allows the workflow to land in PR F. Prefer to include the workflow
because it makes the skeleton end-to-end testable.

## 2. Files Codex must NOT create or modify

- `backend/paradiso_backend.py`
- `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
- `backend/data/visas.json`
- `visa_data.json`
- `doc_master.json`
- `index.html`, `ai.html`
- `scripts/check_repo.sh`, `scripts/check_source_manuals.py`,
  `scripts/check_visa_text_corruption.py`, `scripts/check_i18n.js`,
  `scripts/smoke_ai_payload.js`, `scripts/sync_visa_data.py` —
  pre-existing validators are out of scope for PR A
- `.github/workflows/repo-validation.yml`
- any file under `assets/`, `guidelines/`, `data/sources/` (the
  registered-agent finder data)

If Codex notices a bug in any of these, file an issue in the PR
description; do not fix it in this PR.

## 3. Tests Codex must add (lightweight, optional in PR A)

PR A is allowed to ship without new backend tests because nothing in
`backend/` changes. If Codex wants to add tests, they must:

- live alongside the new scripts (e.g. `scripts/tests/`) or as standalone
  `python -m` self-tests inside the scripts themselves;
- not depend on network access;
- not call OpenRouter / Groq;
- not import anything from `paradiso_backend.py`;
- not read or write the active grounding fixture.

The existing repo validation (`scripts/check_repo.sh`) must continue
to pass with no changes to its body.

## 4. Documentation cross-linking

Codex must add a single short paragraph at the bottom of
`docs/manual_grounding_expansion_plan.md` (under a new
`## Related documents` heading) that links to:

- `docs/paradiso_ai_safe_automation_architecture.md`
- `docs/source_monitoring_pipeline.md`
- `docs/privacy_safe_coverage_analytics.md`
- `backend/data/manual_grounding/candidates/README.md`

No other content in `manual_grounding_expansion_plan.md` may change.

## 5. PR contract

Codex opens **one draft PR** with the title:

> `Add source monitoring + candidate pipeline skeleton (PR A)`

PR body must include, at minimum:

- a one-paragraph summary;
- the list of files added;
- an explicit "What was intentionally not implemented" section that
  mentions: no fixture changes, no `/api/ask` changes, no real HTTP
  fetch, no candidate file creation, no auto-promotion, no auto-merge;
- a "Validation" section showing the output of:
  - `git status --short`
  - `bash scripts/check_repo.sh`
  - `python3 scripts/check_source_updates.py` (default mode)
  - `python3 scripts/validate_manual_grounding_candidate.py
    backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
    (this must fail with the "active fixture is out of scope" error —
    that failure is the validation, not a regression).

PR must be opened as a **draft** and target `main`. Codex must not
merge. Codex must not enable auto-merge.

## 6. After PR A

Do not start PR B in the same pass. Wait for human reviewer feedback
on PR A. Subsequent PRs (B–H) follow the sequence in
`docs/paradiso_ai_safe_automation_architecture.md` §14.
