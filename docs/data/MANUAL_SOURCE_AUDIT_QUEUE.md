# Manual Source Audit Queue

## Source Manual Placement

The repository currently does not include the expected source manual files under `docs/source-manuals`.

This PR assumes the user will place:

- `docs/source-manuals/visa/사증민원_0504.pdf`
- `docs/source-manuals/stay/체류민원_0504.pdf`

Local attachments confirm the expected page counts:

- 사증민원_0504.pdf: 2026.5 Ministry of Justice visa issuance manual, 484 pages
- 체류민원_0504.pdf: 2026.5 Ministry of Justice foreigner stay/sojourn manual, 774 pages

## Audit Priority

1. `F-6`
2. `D-2` / `D-4`
3. `E-7` / Top-Tier / `K-STAR`
4. `F-2` / `F-5`
5. `C-3` / `C-4`
6. Remaining `A` / `B` / `C` / `D` / `E` / `F` / `G` / `H` categories

## Required Verification

Every required document list must be manually checked against the 2026.5 source manuals before it can be marked verified.

For each category, the audit should capture:

- base code and all manual-listed subcodes
- visa issuance availability and documents
- certificate of visa issuance availability and documents
- status grant, status change, extension, registration, re-entry, activities outside status, and workplace change rules
- common warnings and category-specific caveats
- manual page ranges and confidence level

Representative records in the interface rebuild are schema samples only. They should remain marked `needsManualReview: true` until the manual page audit is complete.

## 2026.5 Required Document Audit Pass

On 2026-05-07, `visa_data.json` received a conservative first pass for all current stay-status records that map to the `체류민원_0504.pdf` manual.

This pass added or refreshed:

- `procedures.extension`
- `procedures.registration`
- `manualRequiredDocAudit`
- 2026.5 stay-manual references

Important limitation: this pass used PDF text extraction and does not replace human legal/source review. Records remain `needsManualReview: true`. If a procedure section could not be safely structured, the UI-facing required document list intentionally says `매뉴얼 확인 필요` instead of exposing a possibly mixed or misleading list.

See `docs/data/MANUAL_REQUIRED_DOC_AUDIT_2026_05.md` for the audit scope and follow-up hotspots.
