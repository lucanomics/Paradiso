# AI Grounding with 2026.5 Manuals

This PR registers the May 2026 Ministry of Justice visa issuance and stay/residence manuals as Paradiso's current source-of-truth manuals and hardens `ai.html` so local `visa_data` is sent to `/api/ask` when a visa code or subcode appears in the user question.

## What changed

- `docs/source-manuals/source_manifest.json` now declares exactly one current visa issuance manual and one current stay/residence manual.
- `scripts/check_source_manuals.py` validates the manifest, declared PDF paths, required metadata, current roles, and page counts when `pdfinfo` is available.
- `ai.html` detects top-level visa codes and subcodes such as `F-6-1`, `E-7-4`, `D-4-2K`, `D-10-T`, and `K-STAR`.
- When a match is found, `ai.html` sends a compact real local `visa_data` payload with `matched_code`, optional `matched_subcode`, `source_manual_version: "2026.5"`, and `source_manuals`.

## What this PR does not change

- It does not regenerate `visa_data.json`.
- It does not perform full PDF-to-RAG ingestion or chunking.
- It does not change the backend API contract.
- It does not change Railway, Supabase, or environment settings.

## Why local visa_data matters

The deployed backend's grounding layer can use `visa_data` to build a visa-specific context block. Sending placeholder values such as `N/A` prevents that block from anchoring the answer to the user's actual visa code. The new payload keeps backend compatibility while giving the backend a real local record when the browser can identify one.

## Relationship between visa_data.json and the PDFs

`visa_data.json` remains a structured fallback, audit, and display layer. The registered 2026.5 PDFs are the source-of-truth manuals for future extraction and grounding work, but this PR intentionally does not rewrite existing structured data from those PDFs.

## Remaining work

- Verify Railway environment settings.
- Verify Supabase pgvector/RPC configuration.
- Verify public-data and law API connectivity.
- Extract and chunk text from the 2026.5 PDFs for future RAG ingestion.
- Plan eventual backend parity and cutover work.
