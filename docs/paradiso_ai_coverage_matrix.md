# Paradiso AI — Coverage Matrix

> **Status:** foundation document and data file.
> Merging this PR does **not** change `/api/ask` behavior. No active
> grounding is added. No candidate is promoted. No external content is
> fetched. The matrix is metadata only.

## 1. What this is

The coverage matrix is a machine-readable file at
`backend/data/eval/paradiso_coverage_matrix.json` that lists every
Korean visa-status / procedure / scenario combination Paradiso AI is
expected to handle, together with the deterministic answer path that
exists today (if any).

It is the **control plane** for future grounding expansion. It tells a
human reviewer — and any automation we later layer on top — which rows
are already grounded, which have a candidate awaiting review, which
have no source yet, and which require per-subcode or per-scenario
routing before a single answer is even safe.

## 2. What this is NOT

- **Not training data.** No row in this matrix is fed to any model.
  The backend does not import this file.
- **Not full coverage.** The matrix seeds a practical first batch
  (D-2, D-4, E-7, F-6 family, F-1-6, D-10, F-2, F-5, plus common
  cross-status procedures). Many statuses and procedures are still
  missing on purpose; fabricating rows we cannot back with a verified
  source is worse than leaving them out.
- **Not a promise of correctness.** A row's existence means we plan to
  cover it. Correctness comes from the active grounding fixture and a
  Korean immigration domain reviewer, not from this file.
- **Not a RAG index.** There are no embeddings, no chunking, no
  retrieval-time lookup. The matrix only declares intent and current
  state.

## 3. Where it lives

| File                                                       | Purpose                                                                          |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `backend/data/eval/paradiso_coverage_matrix.json`          | Matrix data. Read by tooling only; not imported by `paradiso_backend.py`.        |
| `scripts/validate_coverage_matrix.py`                      | Structural validator. Exits non-zero on schema violations.                       |
| `backend/data/manual_grounding/stay_manual_grounding_2026_05.json` | Active grounding fixture. Only file `_select_grounding` actually consults.       |
| `backend/data/manual_grounding/candidates/`                | Draft candidates pending human review.                                           |

## 4. Row schema

Each row has these fields:

- `id` — stable string identifier (e.g. `d2_extension_general`).
- `visa_code` — top-level status code (`D-2`, `F-6`, …) or `*` for
  procedures that apply across statuses (address change, passport info,
  foreigner registration).
- `visa_sub_code` — sub-code (e.g. `F-6-3`) or `null`.
- `visa_name_ko` / `visa_name_en` — human-readable names.
- `procedure_type` — Korean procedure label or internal task label.
- `scenario` — finer scenario tag below procedure (e.g.
  `divorce_finalized_first_extension`).
- `language_scope` — currently `ko` for all rows.
- `risk_level` — `low` / `medium` / `high`. High-risk rows MUST carry
  non-empty `notes` or `next_action`.
- `coverage_status` — see §5.
- `source_status` — see §6.
- `active_grounding_ref` — `grounding_id` in the active fixture, or
  `null`.
- `candidate_ref` — repo-relative path to a candidate JSON, or `null`.
- `expected_task_type` — string returned by `_detect_task_type` for
  this row, or `null` when no task type maps yet.
- `requires_subcode` — true if a single top-level answer is unsafe.
- `requires_scenario` — true if scenario routing is mandatory.
- `notes` — short prose. Mandatory for high-risk rows with no
  `next_action`.
- `next_action` — short instruction for the next reviewer.

## 5. How to read `coverage_status`

| Value                  | Meaning                                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `active_grounded`      | The active fixture has a verified entry for this row. `/api/ask` will inject deterministic documents and caveats.  |
| `candidate_only`       | A draft candidate exists under `candidates/`. **Not active.** `/api/ask` falls through to the scoped fallback.     |
| `scoped_fallback`      | No grounding and no candidate. `/api/ask` answers within the scoped Korean-immigration fallback (PR #58 behavior). |
| `clarification_needed` | A single answer is unsafe; the user must be asked for sub-code / scenario before any document list is shown.        |
| `unsupported`          | Out of scope for now; the matrix records it so we don't claim coverage we don't have.                              |

`candidate_only` is **strictly weaker** than `active_grounded`:

- An active-grounded row has been through verification (PDF page
  extraction + page-footer match) and human review, and lives in the
  active fixture.
- A candidate-only row may have the same PDF verification but has
  **not** been reviewed for legal/scenario correctness, has **not**
  been wired into `_select_grounding`, and has **not** been promoted
  to the active fixture. Treating it as authoritative is exactly the
  failure mode the safe-automation architecture exists to prevent.

## 6. How to read `source_status`

| Value                       | Meaning                                                                                  |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| `verified_manual_active`    | Source is a committed manual PDF and the entry lives in the active fixture.              |
| `verified_manual_candidate` | Source is a committed manual PDF and a candidate exists; not yet active.                 |
| `source_needed`             | Manual reference believed to exist but no candidate has been verified yet.               |
| `law_api_needed`            | Answer must come from a primary statute (출입국관리법 / 시행령 / 시행규칙), not a manual. |
| `notice_needed`             | Answer depends on a 법무부 / 출입국·외국인정책본부 공지/시행지침 that must be sourced.   |
| `unsupported`               | Intentionally out of scope.                                                              |

## 7. How this supports automation (without auto-training)

The matrix is the first step of a pipeline; every later step stays
human-reviewed:

```
matrix row (gap declared)
  → source search (operator-driven, against committed PDFs / law API)
  → candidate generation (verbatim excerpt, page range, verification_note)
  → scripts/validate_manual_grounding_candidate.py (schema + provenance)
  → scripts/validate_coverage_matrix.py (matrix stays consistent)
  → draft PR with Korean immigration domain reviewer
  → human review
  → promotion to active fixture (separate PR)
  → matrix row flips to active_grounded
```

The arrows up to the draft PR may be automated. The reviewer step and
the promotion step stay human. The model is never updated from user
queries.

## 8. Why high-risk statuses require scenario / subcode routing

Top-level visa codes hide materially different document lists and
eligibility rules:

- **F-6** splits into F-6-1 (국민의 배우자), F-6-2 (자녀양육), F-6-3
  (혼인단절). The PR #59 candidate covers F-6-3 "국민 배우자와 이혼한
  후 최초 체류기간 연장허가" (p.498) only. F-6-1 별거·이혼소송 (p.495)
  and F-6-2 자녀양육 (p.496) and F-1-6 가사정리 (p.499) are separate
  procedures with separate `제출서류` and separate timing rules.
- **D-4** language-trainee (D-4-1, D-4-7) ships active; D-4-2K, D-4-3,
  D-4-5, D-4-6 are **not** covered and must not be answered with the
  D-4-1 list.
- **E-7** ships the general extension list; agreement-based tracks
  (한·인도 CEPA, 한·러, 외국법자문법률사무소) and E-7-4 숙련기능인력
  are not covered.
- **F-2** sub-codes diverge widely (점수제, 지역특화, etc.); a single
  "F-2" answer is unsafe.
- **F-5** is permanent residence — the procedure is 영주증 갱신, not
  체류기간 연장. The current `extension` task type is the wrong frame.

The matrix encodes these constraints in `requires_subcode` and
`requires_scenario` so the validator (and any future automation) can
refuse to claim flat top-level coverage for them.

## 9. Validator behavior

`scripts/validate_coverage_matrix.py`:

- Loads `paradiso_coverage_matrix.json`.
- Loads `stay_manual_grounding_2026_05.json` and collects every
  `grounding_id`.
- For each row, enforces required fields, enum values, and the rules
  above:
  - `active_grounded` ⇒ `active_grounding_ref` exists in the active
    fixture.
  - `candidate_only` ⇒ `candidate_ref` exists on disk.
  - `requires_subcode=true` ⇒ sub-code set OR `notes` explains why.
  - `risk_level=high` ⇒ `notes` or `next_action` non-empty.
  - F-6 / D-10 / F-2 / F-5 may not claim `active_grounded` until a
    matching active-fixture entry is committed.
- Exits non-zero on any violation. Wired into `scripts/check_repo.sh`.

## 10. What this PR intentionally does **not** change

- `backend/paradiso_backend.py` — untouched. `_select_grounding`
  behavior, `_GROUNDED_VISA_CODES`, fallback prompt, all unchanged.
- `backend/data/manual_grounding/stay_manual_grounding_2026_05.json` —
  untouched. No new active entry.
- `backend/data/manual_grounding/candidates/` — untouched. F-6
  candidate stays a draft.
- `visa_data.json` / `backend/data/visas.json` — untouched.
- `index.html` / `ai.html` — untouched.
- No law-API integration. No web scraping. No external fetch.
