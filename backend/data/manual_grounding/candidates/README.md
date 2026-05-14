# Manual grounding — candidates (draft only)

> **Nothing in this directory is read by `/api/ask`.**
> **Nothing in this directory is active grounding.**
> **Promotion to the active fixture requires human review and a separate PR.**

This directory holds **draft** manual-grounding candidates — proposed
`(visa_code, visa_sub_code, scenario, procedure_type)` entries that
have not yet been promoted into the active fixture
`backend/data/manual_grounding/stay_manual_grounding_2026_05.json`.

The Paradiso backend (`backend/paradiso_backend.py`) does **not** load
anything from this directory. `_load_stay_manual_grounding()` reads
exactly one file: `stay_manual_grounding_2026_05.json`. Candidates here
have **zero runtime effect**.

## Directory layout

```
backend/data/manual_grounding/candidates/
├── README.md                                    ← this file
└── <slug>/                                      ← one folder per candidate
    ├── candidate.json                           ← the proposed grounding entry
    ├── REVIEW.md                                ← required for promotion (human signoff)
    ├── law_excerpt.json     (optional)          ← verbatim 법령 조문, machine-fetched
    └── notice.json          (optional)          ← captured HiKorea/MOJ notice metadata
```

In this PR no candidate sub-folders are committed. The directory ships
with this README only.

## Candidate JSON contract

A `candidate.json` file must follow the schema 1.2 contract documented
in [`docs/manual_grounding_expansion_plan.md`](../../../../docs/manual_grounding_expansion_plan.md)
plus the candidate-specific fields below.

**Required fields:**

- `candidate_status` — `"draft"` or `"verified_candidate"`.
  `"draft"` means a reviewer has started the entry but it is not yet
  ready for promotion. `"verified_candidate"` means the page range,
  excerpt, and document list have been confirmed against the
  committed PDF and the reviewer has filled in `REVIEW.md`.
- `visa_code` — top-level visa code (e.g. `"D-10"`, `"F-6"`).
- `procedure_type` — currently only `"체류기간 연장허가"` is in scope.
- `section` — Korean section header from the source manual.
- `page_range` — string PDF-page range, e.g. `"226"` or `"43-44"`.
- `source_file` — path under `docs/source-manuals/...` to the
  committed PDF the candidate is verified against.
- `source_title`, `source_date`, `issuing_body` — provenance metadata
  matching the source manifest.
- `required_documents` — verbatim 제출서류 bullets, non-empty list.
- `source_excerpt` — verbatim 매뉴얼 발췌.
- `source_verification_status` — `"unverified"`,
  `"machine_extracted"`, or `"verified_locally"`. The validator
  refuses `"verified_locally"` unless a sibling `REVIEW.md` exists.
- `source_confidence` — `"low"`, `"medium"`, or `"high"`.
- `verification_note` — explicit description of the extraction step
  used to verify the entry (e.g. exact `pdftotext -f N -l M` command).

**Optional fields:**

- `visa_sub_code` — e.g. `"D-10-1"`. Must start with `visa_code + "-"`.
- `scenario` — e.g. `"general"`, `"initial"`, `"follow_up"`.
- `caveats` — list of caveat strings (manual disclaimers plus the
  standing "관할 출입국·외국인청에서 추가/면제 가능" line).
- `risk_notes` — list of strings describing known overreach risks
  (e.g. "must not be used for D-10-T; document list differs").
- `human_review` — object with `{ "decision": "approved" | "rejected"
  | "pending", "reviewer": "<name>", "reviewed_at": "<ISO-8601>" }`.

The validator (`scripts/validate_manual_grounding_candidate.py`)
enforces these rules. It refuses candidates that contain obvious
generic / global-immigration boilerplate (e.g. `USCIS`, `Home Office`,
`해당 국가`, `본인이 체류 중인 국가`) and refuses promotion of any
candidate whose `candidate_status` is not `verified_candidate`.

## Promotion

Promotion into the active fixture is handled by
`scripts/promote_grounding_candidate.py`. It is **dry-run by default**.
Even with `--apply`, it refuses to write unless:

1. `candidate_status == "verified_candidate"`,
2. the validator passes,
3. `human_review.decision == "approved"` with a non-empty `reviewer`
   field.

Promotion never pushes to `main`, never opens a PR, and never
auto-merges. Final promotion is a reviewed PR authored by a human.

## What this directory is NOT

- Not training data. Paradiso does not fine-tune any model.
- Not retrieval data. Paradiso does not run RAG, embeddings, or vector
  search over this directory.
- Not user-visible. Nothing here surfaces in `/api/ask` responses
  until a separate reviewed PR moves the content into the active
  fixture.
