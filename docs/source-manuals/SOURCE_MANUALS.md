# Source Manuals

The 2026.5 Ministry of Justice immigration manuals in this directory are Paradiso's current source-of-truth manuals for new extraction and grounding work.

- `2026-05/visa_manual_2026_05.pdf` - 사증발급 안내매뉴얼, 2026.5.
- `2026-05/stay_manual_2026_05.pdf` - 외국인체류 안내매뉴얼, 2026.5.

Older 2026.3 / 260414 manuals are superseded for future extraction work. Keep them available for audit history when they exist elsewhere in the project, but do not treat them as current for new extraction.

`visa_data.json` remains a structured fallback, audit, and display layer. It is useful for local rendering and compact grounding payloads, but it is not the ultimate source of truth.

User-facing decisions must still be verified with immigration offices, HiKorea, 1345, or a qualified professional. Paradiso provides reference information only and does not provide legal advice, filing services, or representation services.

This PR does not regenerate `visa_data.json` and does not perform full RAG ingestion, PDF chunking, or Supabase migration.
