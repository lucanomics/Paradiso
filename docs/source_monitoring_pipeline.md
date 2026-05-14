# Source monitoring pipeline

> Companion to [`docs/paradiso_ai_safe_automation_architecture.md`](paradiso_ai_safe_automation_architecture.md)
> §5 ("Source monitoring flow") and the
> [Codex implementation brief](CODEX_SAFE_AUTOMATION_IMPLEMENTATION_BRIEF.md).
> This document describes what the source-monitoring skeleton shipped
> in PR A does and, just as importantly, what it does **not** do.

## Goal

Detect when the official Korean immigration sources Paradiso relies on
(법무부 매뉴얼 PDFs, 국가법령정보센터 법령, HiKorea / 법무부 공지) have
changed, so a human reviewer can decide whether the change should
flow into the active grounding fixture.

The pipeline is **report-only** by default and **never** modifies
production data.

## Components

| File                                              | Purpose                                                          |
| ------------------------------------------------- | ---------------------------------------------------------------- |
| `data/source_registry.json`                       | Allow-list of monitored sources and their last-known hashes.     |
| `scripts/check_source_updates.py`                 | Walks the registry, reports state. Network is opt-in.            |
| `backend/data/manual_grounding/candidates/`       | Draft candidates only. Not read by `/api/ask`.                   |
| `scripts/validate_manual_grounding_candidate.py`  | Structural + provenance validator for candidate JSON files.      |
| `scripts/promote_grounding_candidate.py`          | Dry-run-by-default promotion with strict review gates.           |
| `.github/workflows/source-monitoring.yml`         | Optional `workflow_dispatch`-only CI job.                        |

## Source registry

`data/source_registry.json` lists every monitored source. Each record
declares its `type` (`pdf_manual`, `law_api`, `notice_index`), its
`status` (`active`, `not_configured`, `deprecated`), the `local_path`
or `url`, a `last_known_hash` (for committed PDFs), and free-form
`notes`. The registry is the only file `check_source_updates.py`
reads; nothing in production code reads it.

## `check_source_updates.py`

CLI flags:

- `--registry <path>` — override the registry path.
- `--local-only` — explicitly disable network handling (default).
- `--allow-network` — permit network-backed entries. The PR A
  skeleton still does **not** make HTTP calls even with this flag; it
  reports `network_skipped` so the flag plumbing is testable.
- `--strict` — exit non-zero when any `active` local source is
  `changed` or `missing`. Without `--strict` the script always exits
  0 in report mode.
- `--json` — emit JSON instead of the human-readable report.

`--local-only` and `--allow-network` are mutually exclusive.

For each `pdf_manual` entry the script computes a sha256 of the file
at `local_path` and compares it to `last_known_hash`. The result is
one of:

- `unchanged` — hashes match.
- `changed` — file is present but hash differs (a reviewer must
  triage whether the new file is the same authoritative manual or a
  different document).
- `missing` — `local_path` does not exist (a reviewer must locate or
  re-commit the file).
- `no_baseline` — `last_known_hash` is missing in the registry; the
  reported `current_hash` is what should be added once a human has
  verified the file is the right version.

For `law_api` and `notice_index` entries, the script reports
`skipped: not_configured` for placeholders and `network_skipped` for
configured entries (HTTP fetch is intentionally out of scope for
PR A).

The script **never** rewrites `source_registry.json`, never writes a
state file, never opens GitHub issues, and never opens PRs.

## Candidate flow (downstream of monitoring)

When monitoring reports `changed` on a committed PDF, a human
reviewer:

1. Confirms what changed (typically by `pdftotext`-ing the new file
   against the previous version's extraction).
2. Updates `last_known_hash` in `data/source_registry.json` (in a
   separate PR) once the new file is confirmed authoritative.
3. If a section's document list changed, creates a candidate folder
   under `backend/data/manual_grounding/candidates/<slug>/` with a
   `candidate.json` (and, when ready, a `REVIEW.md`) per the schema
   documented in [`backend/data/manual_grounding/candidates/README.md`](../backend/data/manual_grounding/candidates/README.md)
   and [`docs/manual_grounding_expansion_plan.md`](manual_grounding_expansion_plan.md).
4. Runs `scripts/validate_manual_grounding_candidate.py` to confirm
   structural / provenance correctness.
5. Runs `scripts/promote_grounding_candidate.py <slug>` to inspect
   the proposed diff. Promotion to the active fixture requires
   `--apply` plus a non-empty `human_review.decision == "approved"`
   block in `candidate.json` and `candidate_status ==
   "verified_candidate"`.
6. Even when all gates pass, the human still authors the draft PR
   manually. Nothing auto-pushes.

## What this pipeline does NOT do

- Does not scrape any external website. Network fetching is opt-in
  and, in the PR A skeleton, not yet implemented.
- Does not fine-tune any model.
- Does not run RAG, embeddings, or vector search.
- Does not write to `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
  from any script (the validator refuses to touch it; the promoter
  refuses without explicit gates).
- Does not push commits or open PRs.
- Does not store secrets. `LAW_API_KEY` and other keys are read from
  the operator's environment only and are not used by the PR A
  skeleton.
- Does not store raw user logs.

## CI integration

`scripts/check_repo.sh` runs the source monitor in default
(local-only, non-strict, non-JSON) mode and the candidate validator
in default mode. Both are report-only and never fail CI by themselves
unless the registry is malformed or a candidate file is invalid.

A separate `workflow_dispatch`-only GitHub Actions workflow
(`.github/workflows/source-monitoring.yml`) runs the same two
commands on demand and uploads no artifacts. It has no `cron`
schedule, takes no secrets, and makes no network calls.
