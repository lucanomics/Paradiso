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
