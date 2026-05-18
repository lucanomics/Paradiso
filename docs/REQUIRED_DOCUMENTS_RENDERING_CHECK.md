# Required Documents Rendering Coverage Check

## What this check does

`scripts/check_required_documents_coverage.py` performs a deterministic sanity check against the visa data used by the frontend renderer.

It:
- loads `visa_data.json` (or `backend/data/visas.json` if needed),
- scans each status code for known required-document/procedure fields expected by `index.html`,
- reports:
  - statuses with document fields,
  - statuses without document fields,
  - statuses likely to rely on fallback display,
  - suspicious document-like fields not covered by the renderer mapping inventory,
- explicitly inspects priority statuses:
  - `F-1`, `F-2`, `F-3`, `F-5`, `F-6`, `D-2`, `D-4`, `D-10`, `E-2`, `E-7`, `G-1`, `H-2`.

The script fails only for clear regressions:
- a document-like field exists with renderable data but is not covered by the renderer mapping inventory,
- malformed document field type that renderer normalization cannot handle,
- priority status missing both document data and fallback classification metadata.

## What this check does **not** verify

This is not a legal/content verification tool. It does **not**:
- verify correctness/completeness of document policy,
- verify manual-grounding truthfulness,
- guarantee UX details in browser rendering,
- assert that every status must have manually verified documents.

## Why missing data is not automatically an error

Some statuses intentionally rely on conservative fallback text pending manual expansion. A status with no direct document fields is reported, but not failed, unless it also lacks fallback-relevant metadata (for priority statuses).

## How to add fields safely

If a new document field is introduced in data:
1. Add frontend renderer support in `index.html` mapping/normalization aliases.
2. Add the new alias to `RENDERER_DOC_FIELDS` in `scripts/check_required_documents_coverage.py`.
3. Re-run:
   - `python3 scripts/check_required_documents_coverage.py`
   - `bash scripts/check_repo.sh`

This keeps renderer assumptions and data schema evolution synchronized.

## Connection to manual-grounding expansion

As manual-grounded coverage grows, more statuses/procedures can move from fallback-heavy states to explicit structured document groups. This check guards against accidental schema drift during that expansion, without forcing unverified statuses to be treated as errors.
