# D-10 Candidate Generation Attempt — Failure Note

**Date:** 2026-05-15
**Branch:** feat/generate-d10-grounding-candidate
**Matrix rows attempted:** `d10_extension_general`, `d10_1_extension_general`
**Generator command:**
```
python3 scripts/generate_candidate_from_matrix.py \
  --row-id d10_extension_general \
  --manual docs/source-manuals/2026-05/stay_manual_2026_05.pdf \
  --dry-run
```

## Outcome

**No candidate was written.** Both row IDs (`d10_extension_general` and
`d10_1_extension_general`) produced clearly wrong dry-run output — the
generator mis-routed to content from a neighbouring chapter. The output
was NOT promoted and NOT written to disk.

## Root cause

### Bug 1 — TOC anchoring (fixed in this PR)

The original `_locate_page` function found the first page in the PDF
that contained any visa header string. For D-10 (`구직(D-10)`), the first
occurrence was **PDF page 2** — the table of contents — at character
position 959. The 80-page forward search window therefore ran from PDF
page 2 to page 82, which does not reach the actual D-10 chapter at PDF
page 142.

**Fix applied** (`scripts/generate_candidate_from_matrix.py`): replaced
the first-occurrence anchor with a chapter-title anchor. A chapter-title
page has the visa code in the very first characters of the
`pdftotext -layout` output (observed: `(D-10)` at char 6 on PDF page 142,
`구직(D-10)` at char 959 on the TOC page 2). The new helper
`_header_at_chapter_position` accepts only pages where any visa header
appears within the first `_CHAPTER_TITLE_MAX_OFFSET` (50) characters.

After the fix, `section_start` = PDF page 142 (correct D-10 chapter
opening: first line `구 직(D-10)`).

All 16 unit tests in `scripts/tests/test_generate_candidate_from_matrix.py`
continue to pass.

### Bug 2 (remaining limitation) — window spillover into E-7 chapter

With `section_start = 142`, the 80-page search window extends to PDF
page 222. The D-10 chapter occupies PDF pages 142–165 (~24 pages). The
E-7 chapter starts immediately after. Within pages 166–222, PDF page 190
(printed page 190) contains:

- The string `체류기간 연장허가` (in a sentence: "…별도의 **체류기간 연장허가**
  신청이 필요함") — a cross-reference explaining that E-7 workers who
  change workplaces still need a separate D-10 extension permit.
- A `제출서류` heading — for an E-1/E-3 status-change procedure (교수
  자격변경허가), unrelated to D-10 extension.

The generator selected PDF page 190 and extracted E-1/E-3 status-change
documents as the D-10 extension document list. The section label in the
dry-run preview read:

> `계속하여 취업하고자 하는 경우에는 구직(D-10) 체류자격으로 변경 허용`

This is clearly wrong for a D-10 체류기간 연장허가 candidate.

### Root cause 3 — content gap in the manual

A comprehensive scan of the committed PDF
(`docs/source-manuals/2026-05/stay_manual_2026_05.pdf`) confirms that
**no page in the D-10 chapter (PDF pages 142–165) contains both**:

- `체류기간 연장허가` (verbatim, not just `체류기간 연장‧조정`)
- `제출서류` heading

The D-10 chapter in this manual version documents:

| Section | Pages |
|---------|-------|
| 체류자격 변경허가 (status change TO D-10) | 144–155 |
| 시간제 취업 허가 | 143 |
| 외국인등록 (alien registration) | 159 |
| 연수개시/기관변경 신고 | 159–164 |
| 시간제취업 확인서 양식 | 165 |

There is no standalone `체류기간 연장허가` + `제출서류` page for D-10 in
this manual version. The matrix note for `d10_extension_general` already
flags this:

> "D-10 extension 제출서류 page is not yet verified inside
> stay_manual_2026_05.pdf."

## What was NOT done

- No `candidate.json` was written.
- No `REVIEW.md` was written.
- `backend/data/manual_grounding/stay_manual_grounding_2026_05.json` was
  not modified.
- `backend/data/eval/paradiso_coverage_matrix.json` was not modified.
- No active grounding was changed.
- No production behavior was changed.

## What was done

- Fixed the TOC-anchoring bug in `scripts/generate_candidate_from_matrix.py`
  (see "Bug 1" above).
- Confirmed via `pdftotext` scan that D-10 체류기간 연장허가 제출서류 is
  absent from the 2026-05 stay manual as a standalone section.

## Next steps for a human reviewer

1. Open `stay_manual_2026_05.pdf` and search for "구직(D-10)" + "체류기간
   연장허가".
2. If a dedicated extension page exists in a future manual edition,
   re-run the generator on that edition after updating `--manual`.
3. If the D-10 extension document list is embedded in a general section
   (e.g. a common renewal procedure page applicable across multiple visa
   types), a hand-written candidate may be needed; use the existing F-6
   candidate at `backend/data/manual_grounding/candidates/f6_divorce_status_change/`
   as a template.
4. The matrix rows `d10_extension_general` and `d10_1_extension_general`
   remain `scoped_fallback` until a verified candidate is available.

## Exact command needed when a source page is identified

```bash
pdftotext -layout -f <page> -l <page> \
  docs/source-manuals/2026-05/stay_manual_2026_05.pdf -
```

Verify that the printed footer matches `- <page> -` and that the section
header and 제출서류 bullet list are for D-10 체류기간 연장허가 specifically
before running:

```bash
python3 scripts/generate_candidate_from_matrix.py \
  --row-id d10_extension_general \
  --manual docs/source-manuals/2026-05/stay_manual_2026_05.pdf \
  --dry-run
```
