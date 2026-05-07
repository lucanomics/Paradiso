# Moonshot to Paradiso Remaining Migration Audit

## Current State
- Paradiso currently contains the expected static production surface: `index.html`, `ai.html`, `visa_data.json`, `assets/`, `data/`, and `scripts/check_repo.sh`.
- Recent PRs already landed static migration + Figma-inspired hero/UI updates.
- Validation guardrails are present (`scripts/check_repo.sh`) including JSON validity and legacy-brand regression scanning.
- **Constraint during this audit:** source repo clone from `https://github.com/lucanomics/moonshot.git` failed in this environment (`CONNECT tunnel failed, response 403`), so this document is a cautious **phase plan audit** with explicit manual-review items.

## Migration Principles
1. Preserve working production behavior first (search, render, direct-search toggles, AI page navigation).
2. Prefer smallest safe PRs by concern (automation/docs/backend/data) rather than bulk copy.
3. Do not import React/Vite/Tailwind runtime paths into production static app.
4. Exclude build artifacts (`node_modules`, caches, virtual envs, temp outputs).
5. Enforce branding safety: no Moonshot / Paradiso 39 / P/39 restoration.

## File Comparison Summary
- **Target inventory exists and is coherent** for static app delivery.
- **Source inventory unavailable in this runtime** (network clone blocked), so direct one-to-one diff classification is partially deferred.
- We can still identify likely remaining migration zones from target signals:
  - backend/API references (`moonshot_backend_fastapi.py` referenced by checker but absent)
  - deployment/ops docs (not visible at root)
  - structured migration documentation for future contributors
  - CI validation hardening for missing optional files

## Migration Candidates

| Category | Source path | Target path | Recommendation | Risk | Reason |
|---|---|---|---|---|---|
| Production app files | `/index.html`, `/ai.html`, `/visa_data.json`, `/assets/**`, `/data/**`, `/scripts/**` | already present in Paradiso root | Already migrated | Low | Core static app is in place and currently operational. |
| Backend/API | `/moonshot_backend_fastapi.py` | `moonshot_backend_fastapi.py` (or `backend/moonshot_backend_fastapi.py`) | Needs manual review | Medium | Checker references this file but it is absent; verify whether backend should be restored as optional support or checker updated. |
| Backend/API deps | `/requirements*.txt`, `/pyproject.toml` (if any) | `backend/requirements*.txt` | Should migrate later | Medium | Only if backend endpoint strategy is still planned; avoid mixing into static-only PRs now. |
| API run/deploy docs | `README backend sections`, `deploy/*.md`, `Procfile`, compose files | `docs/backend/` | Should migrate now | Low | Documentation-only migration is safe and helps future backend reactivation. |
| Data source/truth artifacts | visa extraction notes, PDF-derived mappings, jobcode source files, generation scripts | `docs/data-sources/`, `data/`, `scripts/` | Should migrate now | Medium | Improves maintainability/auditability without changing production behavior if docs-only first. |
| AI guidance support docs | prompt templates, evaluation notes, policy docs | `docs/ai/` | Should migrate later | Medium | Useful but not required for current static production stability. |
| Validation automation | source shell validators / CI workflows | `.github/workflows/`, `scripts/` | Should migrate now | Low | Add CI parity for JSON validation + branding scans; reduce manual regression risk. |
| Checker robustness | n/a (target improvement from audit finding) | `scripts/check_repo.sh` | Should migrate now | Low | Make optional-file checks non-failing/noisy for absent backend file. |
| Documentation (public/internal split) | Moonshot README/CLAUDE/strategy/audit docs | `docs/archive/moonshot/` + curated `README.md` updates | Should migrate later | Low | Valuable history; must curate to avoid reviving deprecated branding. |
| Legacy branding assets | old Moonshot/Paradiso39/P39 logos and copy | **none** | Should not migrate | High | Violates current branding constraints and can leak into UI copy/assets. |
| Build/runtime artifacts | `node_modules`, `.venv`, cache/output dirs | **none** | Should not migrate | Low | Non-source artifacts; unsafe/noisy in repo. |

## Do Not Migrate
- `node_modules/`, `.venv/`, `__pycache__/`, build caches, temporary outputs, local IDE folders.
- Deprecated branding assets/copy containing Moonshot, Paradiso 39, Paradiso39, P/39 variants.
- Broken placeholder image names or externally hosted image dependencies.
- Unvetted React/Vite/Tailwind/shadcn/motion runtime files into static production path.

## Recommended PR Sequence
1. **PR-1 (Docs + Auditability, safest):**
   - Add curated `docs/backend/` and `docs/data-sources/` from Moonshot (documentation-only).
   - Add migration provenance notes (what generated `visa_data.json`, job code provenance, legal/source caveats).
2. **PR-2 (Validation hardening):**
   - Improve `scripts/check_repo.sh` to gracefully handle optional backend files and keep strict branding/data checks.
   - Add CI workflow for `json.tool`, `git diff --check`, branding grep scans.
3. **PR-3 (Optional backend recovery, if still needed):**
   - Reintroduce backend code in isolated `backend/` folder with pinned deps and run instructions.
   - No production `index.html` rewiring in the same PR.
4. **PR-4 (Data pipeline reproducibility):**
   - Bring source extraction scripts + normalization docs so future `visa_data.json` refreshes are reproducible.

## Immediate Next PR Recommendation
**Safest immediate implementation PR:**
- Documentation + validation hardening only.
- Specifically: migrate backend/data provenance docs from Moonshot and adjust validation tooling to remove noisy missing-file errors while preserving strict branding and JSON checks.
- This gives immediate contributor clarity with near-zero production behavior risk.

