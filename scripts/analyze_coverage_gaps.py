#!/usr/bin/env python3
"""Paradiso privacy-safe coverage analytics — local-only skeleton.

This script processes **pre-redacted, locally-supplied aggregate
JSON** to summarize which `(visa_code, task_type, sub_code)` triples
are under-served by current grounding. It is a skeleton for future
privacy-safe analytics.

Hard rules (also enforced in code):

- Reads only a local JSON file given on the CLI. Does not read
  ``/api/ask`` logs. Does not connect to any database. Does not make
  network calls.
- Refuses any input record that contains obvious raw-PII fields
  (``name``, ``email``, ``phone``, ``passport``, ``passport_number``,
  ``alien_registration_number``, ``arn``, ``user_id``, ``session_id``,
  ``ip``, ``ip_address``, ``prompt``, ``question``, ``query``,
  ``message``, ``text``, ``body``). A refused record is either
  skipped (default) or redacted (``--redact``).
- Output is counts and codes only — no free-text fields are echoed
  back, even from the input file.

See ``docs/privacy_safe_coverage_analytics.md`` for the full input
contract.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Fields whose mere presence in an input record indicates the file
# was not redacted before being passed in. The script refuses such
# records by default.
_FORBIDDEN_RAW_FIELDS = frozenset(
    [
        "name",
        "full_name",
        "given_name",
        "family_name",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "mobile",
        "passport",
        "passport_number",
        "alien_registration_number",
        "arn",
        "user_id",
        "session_id",
        "ip",
        "ip_address",
        "prompt",
        "question",
        "query",
        "message",
        "text",
        "body",
        "raw_text",
        "user_input",
    ]
)

# Aggregate keys we count. Anything else is ignored at summary time —
# the script never echoes back free-text fields.
_COUNTABLE_KEYS = (
    "visa_code",
    "visa_sub_code",
    "task_type",
    "grounding_used",
    "fallback_used",
    "coverage_gap",
)


def _scan_pii(record: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    for key in record.keys():
        if not isinstance(key, str):
            continue
        if key.lower() in _FORBIDDEN_RAW_FIELDS:
            hits.append(key)
    return hits


def _redact_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        k: v
        for k, v in record.items()
        if isinstance(k, str) and k.lower() not in _FORBIDDEN_RAW_FIELDS
    }


def _iter_records(data: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        for key in ("records", "by_triple", "events", "rows"):
            section = data.get(key)
            if isinstance(section, list):
                for item in section:
                    if isinstance(item, dict):
                        yield item
                return


def _count(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    visa_codes: Counter = Counter()
    sub_codes: Counter = Counter()
    task_types: Counter = Counter()
    grounding_used_false = 0
    fallback_used = 0
    coverage_gap = 0
    triples: Counter = Counter()
    total = 0

    for rec in records:
        total += 1
        vc = rec.get("visa_code") or "UNKNOWN"
        sub = rec.get("visa_sub_code")
        tt = rec.get("task_type") or "UNKNOWN"
        visa_codes[vc] += int(rec.get("count", 1)) if isinstance(rec.get("count"), int) else 1
        if sub:
            sub_codes[sub] += 1
        task_types[tt] += 1
        if rec.get("grounding_used") is False:
            grounding_used_false += 1
        if rec.get("fallback_used") is True:
            fallback_used += 1
        if rec.get("coverage_gap") is True:
            coverage_gap += 1
        triples[(vc, sub or "", tt)] += int(rec.get("count", 1)) if isinstance(rec.get("count"), int) else 1

    return {
        "total_records": total,
        "visa_code_counts": dict(visa_codes.most_common()),
        "visa_sub_code_counts": dict(sub_codes.most_common()),
        "task_type_counts": dict(task_types.most_common()),
        "grounding_used_false": grounding_used_false,
        "fallback_used": fallback_used,
        "coverage_gap": coverage_gap,
        "top_triples": [
            {
                "visa_code": vc,
                "visa_sub_code": sub or None,
                "task_type": tt,
                "count": cnt,
            }
            for (vc, sub, tt), cnt in triples.most_common(20)
        ],
    }


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Privacy-safe coverage analytics over a locally-supplied "
            "aggregate JSON file. Counts and codes only — never echoes "
            "free-text fields."
        )
    )
    p.add_argument(
        "input_path",
        help="Path to a local aggregate JSON file (already PII-redacted).",
    )
    p.add_argument(
        "--redact",
        action="store_true",
        help=(
            "Drop forbidden raw-PII fields from each record instead of "
            "skipping the record entirely. Off by default — by default "
            "the script skips suspect records and prints a warning."
        ),
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit nonzero if any record contained a forbidden raw-PII "
            "field, even with --redact."
        ),
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable Markdown.",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    if not os.path.isfile(args.input_path):
        print(f"ERROR: input file not found: {args.input_path}", file=sys.stderr)
        return 2

    try:
        with open(args.input_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: failed to read {args.input_path}: {exc}", file=sys.stderr)
        return 2

    accepted: List[Dict[str, Any]] = []
    skipped = 0
    pii_records = 0
    pii_fields: Counter = Counter()
    for rec in _iter_records(data):
        hits = _scan_pii(rec)
        if hits:
            pii_records += 1
            for h in hits:
                pii_fields[h] += 1
            if args.redact:
                accepted.append(_redact_record(rec))
            else:
                skipped += 1
                continue
        else:
            accepted.append(rec)

    summary = _count(accepted)
    summary["skipped_due_to_pii"] = skipped
    summary["records_with_pii_fields_detected"] = pii_records
    summary["pii_field_counts"] = dict(pii_fields)

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("# Paradiso coverage gaps — privacy-safe summary")
        print("")
        print(f"- input: `{args.input_path}`")
        print(f"- total accepted records: {summary['total_records']}")
        print(f"- skipped due to raw-PII fields: {skipped}")
        print(f"- records with PII fields detected: {pii_records}")
        if pii_fields:
            print("- PII field counts (from input, dropped/redacted before counting):")
            for k, v in pii_fields.most_common():
                print(f"    - `{k}`: {v}")
        print("")
        print("## Counts")
        print(f"- grounding_used=false: {summary['grounding_used_false']}")
        print(f"- fallback_used=true: {summary['fallback_used']}")
        print(f"- coverage_gap=true: {summary['coverage_gap']}")
        print("")
        print("## Top visa codes")
        for k, v in summary["visa_code_counts"].items():
            print(f"- `{k}`: {v}")
        print("")
        print("## Top sub-codes")
        if summary["visa_sub_code_counts"]:
            for k, v in summary["visa_sub_code_counts"].items():
                print(f"- `{k}`: {v}")
        else:
            print("- (none)")
        print("")
        print("## Top task types")
        for k, v in summary["task_type_counts"].items():
            print(f"- `{k}`: {v}")
        print("")
        print("## Top (visa_code, sub_code, task_type) triples")
        for triple in summary["top_triples"]:
            print(
                f"- `{triple['visa_code']}` "
                f"sub=`{triple['visa_sub_code']}` "
                f"task=`{triple['task_type']}`: {triple['count']}"
            )

    if args.strict and pii_records > 0:
        print(
            f"\nSTRICT: refusing to exit 0 — {pii_records} record(s) "
            "contained forbidden raw-PII fields.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
