# Matrix-driven candidate generation

> **Status:** scripting helper only.
> Running `scripts/generate_candidate_from_matrix.py` does not change
> any production behavior. It cannot promote a candidate, cannot
> modify the active grounding fixture, and cannot modify the coverage
> matrix. It writes one folder under
> `backend/data/manual_grounding/candidates/<row_id>/`.

## 1. What this script does

Given a row id in
[`backend/data/eval/paradiso_coverage_matrix.json`](../backend/data/eval/paradiso_coverage_matrix.json),
the script:

1. Looks up the row.
2. Refuses to proceed if the row is `active_grounded` or `unsupported`.
3. Refuses to proceed if the row already has a `candidate_ref` on
   disk (a reviewer must reconcile the existing candidate first).
4. Requires `pdftotext` (poppler-utils) to be installed. If it is
   missing the script exits non-zero with install instructions — it
   does **not** invent page numbers or document lists.
5. Extracts the cited source manual PDF with
   `pdftotext -layout`.
6. Searches the extracted text for the row's visa-header strings
   (e.g. `구직(D-10)`, `결혼이민(F-6)`) and the row's procedure
   signals (e.g. `체류기간 연장허가`, `이혼`, `근무처 변경`).
7. Picks the first page that contains BOTH the visa header context
   (or the bare `(visa_code)` token) AND a `제출서류` heading AND a
   printed page footer `- N -`.
8. Extracts the verbatim `제출서류` bullet block on that page.
9. Writes a draft `candidate.json` + a `REVIEW.md` placeholder.

If any of steps 5–8 fail to produce a clean result, the script exits
non-zero **without writing anything**.

## 2. What this script does NOT do

- Does **not** modify
  `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`.
- Does **not** modify
  `backend/data/eval/paradiso_coverage_matrix.json`. Flipping a row to
  `candidate_only` is a reviewer-authored step in a follow-up PR.
- Does **not** promote a candidate. Promotion lives in
  `scripts/promote_grounding_candidate.py` and is gated on
  `candidate_status == "verified_candidate"`,
  `human_review.decision == "approved"`, and a non-empty `reviewer`.
- Does **not** fine-tune any model, build embeddings, or run RAG.
- Does **not** make HTTP requests. The only source is the committed
  PDF passed via `--manual`.
- Does **not** fabricate document lists. Every bullet in
  `required_documents` is parsed from a line on the cited PDF page
  that begins with a manual-style bullet marker
  (`①–⑳`, `❍`, `가.`, `1.`, `⑴`, `a.`). Prose paragraphs are never
  converted into bullets.
- Does **not** mark the candidate `verified_locally`. Output is
  always `candidate_status == "draft"` and
  `source_verification_status == "machine_extracted"` with
  `source_confidence == "low"`.

## 3. Usage

```
python3 scripts/generate_candidate_from_matrix.py \
    --row-id d10_extension_general \
    [--manual docs/source-manuals/2026-05/stay_manual_2026_05.pdf] \
    [--out-dir backend/data/manual_grounding/candidates] \
    [--dry-run]
```

- `--row-id` — required. Must match an `id` in the coverage matrix.
- `--manual` — path to a committed PDF. Defaults to the 2026-05 stay
  manual.
- `--out-dir` — root candidates directory. Defaults to
  `backend/data/manual_grounding/candidates`.
- `--dry-run` — print what would be written; do not write files.

## 4. Eligibility rules

| Row `coverage_status`     | Generator behavior                                                                  |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `active_grounded`         | **Refused.** Active grounding is owned by the active fixture; never auto-edit it.   |
| `unsupported`             | **Refused.** Out of scope by design.                                                |
| `source_needed`           | Eligible.                                                                           |
| `clarification_needed`    | Eligible (the resulting draft will likely need sub-code / scenario routing notes).  |
| `scoped_fallback`         | Eligible.                                                                           |
| `candidate_only`          | Eligible **only if** the row's existing `candidate_ref` is missing on disk.         |

## 5. Output contract

The script writes two files:

```
backend/data/manual_grounding/candidates/<row_id>/candidate.json
backend/data/manual_grounding/candidates/<row_id>/REVIEW.md
```

The candidate JSON conforms to the schema enforced by
[`scripts/validate_manual_grounding_candidate.py`](../scripts/validate_manual_grounding_candidate.py):

- `candidate_status`: `"draft"`.
- `source_verification_status`: `"machine_extracted"` (never
  `"verified_locally"`; that flag is reserved for human-reviewed
  candidates with a hand-written REVIEW.md).
- `source_confidence`: `"low"`.
- `human_review.decision`: `"pending"`.
- `required_documents`: a non-empty list of bullets parsed verbatim
  from the source page.
- `source_excerpt`: the verbatim text block beginning at `제출서류`.
- `verification_note`: a human-readable description of the extraction,
  explicitly labelling the output as **machine extract only**.
- `caveats` and `risk_notes`: machine-generated guard text that tells
  the next reader the candidate is unreviewed.

The generated `REVIEW.md` is a placeholder checklist. It explicitly
labels every reviewer action that must precede promotion.

## 6. Pipeline position

The script slots into the safe-automation pipeline from
[`docs/paradiso_ai_safe_automation_architecture.md`](paradiso_ai_safe_automation_architecture.md):

```
matrix row (coverage gap declared)
  → generate_candidate_from_matrix.py  ← THIS SCRIPT
  → scripts/validate_manual_grounding_candidate.py
  → human reviewer fills in REVIEW.md
  → reviewer flips candidate_status to verified_candidate
  → reviewer flips source_verification_status to verified_locally
  → reviewer sets human_review.decision = "approved"
  → scripts/promote_grounding_candidate.py --apply  (separate PR)
  → matrix row flips coverage_status to active_grounded (separate PR)
```

Only the first arrow is automated by this script. Every subsequent
arrow is human-authored.

## 7. Known limitations

- Korean visa headers in `_VISA_HEADERS_KO` are limited to the codes
  already seen in the committed stay manual. Adding a new code
  requires a one-line entry; it is intentionally explicit so the
  script does not silently search for headers that do not exist.
- Cross-status / `visa_code == "*"` rows (address change, passport
  info report, foreigner registration, status change) cannot be
  generated by this script — they need a hand-picked page hint from
  a primary source. The script refuses these rows cleanly.
- Bullet parsing relies on regex over `pdftotext -layout` output.
  Multi-line bullets, inline parentheticals, and adjacent 특칙 boxes
  may be dropped or merged. This is the main reason the script always
  marks output `source_confidence: "low"` and never `verified_locally`.
- The script picks the **first** page that satisfies the visa-header +
  procedure-signal + `제출서류` + page-footer constraint. If the
  manual repeats `제출서류` in adjacent sub-sections (e.g. F-6-1 vs
  F-6-3), the first hit may not be the intended one. The reviewer is
  responsible for confirming the scope before promotion.

## 8. Tests

`scripts/tests/test_generate_candidate_from_matrix.py` covers the pure
Python logic (matrix lookup, refusal rules, page location, bullet
extraction, candidate-shape conformance with the existing validator)
using a synthetic `pdftotext`-style fixture. The tests do **not**
require `pdftotext` to be installed.
