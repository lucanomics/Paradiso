# Privacy-safe coverage analytics

> Companion to [`docs/paradiso_ai_safe_automation_architecture.md`](paradiso_ai_safe_automation_architecture.md)
> §10 ("Privacy-safe coverage analytics flow") and §13 (safety policy
> table). This document defines what `scripts/analyze_coverage_gaps.py`
> accepts as input, what it refuses to read, and what it never does.

## Goal

Tell us **what kinds** of questions Paradiso AI cannot answer well
(by `(visa_code, visa_sub_code, task_type)` triple), **without**:

- training any model on user data,
- fine-tuning any model,
- computing embeddings on user data,
- storing raw user prompts on disk or in the repository,
- ingesting `/api/ask` logs,
- making a network call.

The script reads only a **local, already-redacted aggregate JSON
file** that an operator manually drops on disk. The repository does
not ingest, host, or commit that file.

## Input contract

`scripts/analyze_coverage_gaps.py <path-to-aggregate-json>` accepts a
JSON document of one of two shapes:

```jsonc
// Shape A: a top-level list of records
[
  { "visa_code": "F-6", "task_type": "extension", "count": 240,
    "grounding_used": false, "coverage_gap": true }
]

// Shape B: an object with a `records` / `by_triple` / `events` /
// `rows` list (the script picks the first one it finds).
{
  "schema_version": "1.0",
  "window": { "start": "2026-04-01", "end": "2026-04-30" },
  "by_triple": [
    { "visa_code": "F-6", "task_type": "extension", "count": 240,
      "grounding_used": false, "coverage_gap": true }
  ]
}
```

Per-record fields the script counts (everything else is ignored):

| Field                | Type           | Meaning                                                            |
| -------------------- | -------------- | ------------------------------------------------------------------ |
| `visa_code`          | string         | Top-level Korean visa code (`D-2`, `F-6`, ...).                    |
| `visa_sub_code`      | string \| null | Sub-code if known (`D-10-1`, `F-6-1`, ...).                        |
| `task_type`          | string         | `"extension"`, `"status_change"`, ... (free, but kept as a label). |
| `count`              | integer        | Pre-aggregated count of asks for this triple. Optional; default 1.  |
| `grounding_used`     | boolean        | Whether the active fixture grounded this triple's answer.          |
| `fallback_used`      | boolean        | Whether the LLM fallback path was used.                            |
| `coverage_gap`       | boolean        | Operator's manual flag that this triple is a known gap.            |

## Refused fields

The script refuses any record that contains a forbidden raw-PII key,
because such a key indicates the input was not redacted before being
passed in. The refused-key list (case-insensitive) is:

```
name, full_name, given_name, family_name,
email, email_address,
phone, phone_number, mobile,
passport, passport_number,
alien_registration_number, arn,
user_id, session_id, ip, ip_address,
prompt, question, query, message, text, body,
raw_text, user_input
```

Default behavior: a record containing any of the keys above is
**skipped** and counted in `skipped_due_to_pii`. The forbidden key
names themselves are reported as a histogram so the operator can fix
their export.

With `--redact`, the forbidden keys are dropped from the record and
the rest is counted. With `--strict`, the script exits non-zero if any
record contained a forbidden key, even when `--redact` is used.

## Output

The script prints a Markdown summary (or JSON with `--json`). The
summary contains only:

- counts (`total_records`, `grounding_used_false`, `fallback_used`,
  `coverage_gap`),
- per-`visa_code` / per-`visa_sub_code` / per-`task_type` counts,
- the top-N `(visa_code, visa_sub_code, task_type)` triples by count,
- the forbidden-field histogram for redacted/skipped records.

The script **never** echoes free-text fields. Even if a forbidden
field slipped past the redactor, the summary contains the field name
and a count — not the value.

## What this script does NOT do

- Does not read production logs.
- Does not connect to any database (Postgres, Supabase, etc.).
- Does not make any network call.
- Does not write any file by default (`stdout` only).
- Does not call any LLM provider.
- Does not compute embeddings or vector representations.
- Does not infer PII from text content; it looks only at field names.

## Where the input comes from

Operators generate the input file from their own environment, with
their own redaction tooling, and copy it to disk **outside** the
repository. The repository does not commit `data/coverage_input/` or
`data/coverage_reports/`; both are expected to be either ignored or
absent. The script does not create either directory.

## Future work (out of scope for PR A)

- A documented backend-side aggregation contract that emits records
  with no raw text. The backend today does not persist `/api/ask`
  prompts at all (see `backend/paradiso_backend.py`); the aggregation
  layer would be a separate, opt-in process under a future PR.
- A reviewer-facing report that links each top triple to the
  `candidates/` slug that should address it.
