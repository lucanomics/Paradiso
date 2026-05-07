# Data Sources Overview

## Current Working Data in Paradiso
- `visa_data.json`
  - Runtime dataset used by the static search and guidance UI.
  - Should be validated for structure before releases.

- `data/jobcode_master.json`
  - Job code lookup data used by administrative helper features.

## Manual/Reference Documents
- Manual extracts used during curation (examples in prior workflow):
  - `docs/sajeung-manual.md`
  - `docs/ceryu-manual.md`

These materials are helpful for traceability and review, but should be treated as supporting references.

## Source Hierarchy Reminder
Data artifacts in this repository are audit targets and implementation inputs.
They are **not automatically definitive legal truth** by themselves.
Contributors should follow documented source hierarchy and verification rules when updating data.

## Compliance / Legal Review Context
A legal-review memo exists in the legacy repository as an additional reference point (for example, a draft review on submission/legal handling).
Use that review context during future data-refresh PR planning.
