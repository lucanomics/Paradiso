#!/usr/bin/env python3
"""Paradiso coverage matrix validator.

Validates ``backend/data/eval/paradiso_coverage_matrix.json`` — the
machine-readable control plane that describes every visa-status /
procedure / scenario combination Paradiso AI is expected to answer
about and which deterministic answer path (if any) backs it today.

The validator enforces structural rules only. It does **not** validate
legal or factual correctness — that is a human reviewer's job.

Hard rules enforced here:

- Top-level shape: ``schema_version``, ``rows`` (list).
- Each row carries every required field.
- ``coverage_status`` and ``source_status`` use their declared enums.
- If ``coverage_status == 'active_grounded'`` then
  ``active_grounding_ref`` must be a non-empty string AND must resolve
  to a ``grounding_id`` in the active fixture
  ``backend/data/manual_grounding/stay_manual_grounding_2026_05.json``.
- If ``coverage_status == 'candidate_only'`` then ``candidate_ref``
  must point to an existing file on disk.
- If ``requires_subcode`` is true, then ``visa_sub_code`` must be set
  OR ``notes`` must explain why top-level routing is unsafe.
- If ``risk_level == 'high'`` then ``notes`` or ``next_action`` must
  be non-empty.
- F-6 may not claim ``active_grounded`` yet (PR #59 only added a
  candidate; promotion is out of scope for this matrix).
- D-10 / F-2 / F-5 may not claim ``active_grounded`` unless a matching
  active fixture entry actually exists.

Exit codes:

- 0 — matrix is structurally valid.
- 1 — one or more rows failed validation.
- 2 — invocation error (missing matrix, malformed JSON, missing
  active fixture).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MATRIX_PATH = os.path.join(
    REPO_ROOT, "backend", "data", "eval", "paradiso_coverage_matrix.json"
)
ACTIVE_FIXTURE_PATH = os.path.join(
    REPO_ROOT,
    "backend",
    "data",
    "manual_grounding",
    "stay_manual_grounding_2026_05.json",
)

_REQUIRED_ROW_FIELDS: Tuple[str, ...] = (
    "id",
    "visa_code",
    "visa_sub_code",
    "visa_name_ko",
    "procedure_type",
    "scenario",
    "language_scope",
    "risk_level",
    "coverage_status",
    "source_status",
    "active_grounding_ref",
    "candidate_ref",
    "expected_task_type",
    "requires_subcode",
    "requires_scenario",
    "notes",
    "next_action",
)

_COVERAGE_STATUS_VALUES: Set[str] = {
    "active_grounded",
    "candidate_only",
    "scoped_fallback",
    "clarification_needed",
    "unsupported",
}
_SOURCE_STATUS_VALUES: Set[str] = {
    "verified_manual_active",
    "verified_manual_candidate",
    "source_needed",
    "law_api_needed",
    "notice_needed",
    "unsupported",
}
_RISK_LEVELS: Set[str] = {"low", "medium", "high"}

# Visa codes whose extension grounding is not yet active. They may not
# claim coverage_status='active_grounded' until a matching entry exists
# in the active fixture.
_NOT_YET_ACTIVE_VISA_CODES: Set[str] = {"F-6", "D-10", "F-2", "F-5"}


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_active_grounding_ids() -> Set[str]:
    if not os.path.isfile(ACTIVE_FIXTURE_PATH):
        raise SystemExit(
            f"ERROR: active grounding fixture missing at {ACTIVE_FIXTURE_PATH!r}"
        )
    fixture = _load_json(ACTIVE_FIXTURE_PATH)
    groundings = fixture.get("groundings") if isinstance(fixture, dict) else None
    if not isinstance(groundings, list):
        raise SystemExit(
            f"ERROR: active fixture at {ACTIVE_FIXTURE_PATH!r} is missing 'groundings' list"
        )
    ids: Set[str] = set()
    for g in groundings:
        if isinstance(g, dict):
            gid = g.get("grounding_id")
            if isinstance(gid, str) and gid:
                ids.add(gid)
    return ids


def _validate_row(
    row: Any,
    index: int,
    active_grounding_ids: Set[str],
) -> List[str]:
    errors: List[str] = []
    prefix = f"row[{index}]"

    if not isinstance(row, dict):
        return [f"{prefix}: must be an object"]

    rid = row.get("id")
    if isinstance(rid, str) and rid:
        prefix = f"row[{index}]({rid})"

    for field in _REQUIRED_ROW_FIELDS:
        if field not in row:
            errors.append(f"{prefix}: missing required field '{field}'")

    coverage_status = row.get("coverage_status")
    if coverage_status not in _COVERAGE_STATUS_VALUES:
        errors.append(
            f"{prefix}: coverage_status must be one of "
            f"{sorted(_COVERAGE_STATUS_VALUES)}, got {coverage_status!r}"
        )

    source_status = row.get("source_status")
    if source_status not in _SOURCE_STATUS_VALUES:
        errors.append(
            f"{prefix}: source_status must be one of "
            f"{sorted(_SOURCE_STATUS_VALUES)}, got {source_status!r}"
        )

    risk_level = row.get("risk_level")
    if risk_level not in _RISK_LEVELS:
        errors.append(
            f"{prefix}: risk_level must be one of "
            f"{sorted(_RISK_LEVELS)}, got {risk_level!r}"
        )

    visa_code = row.get("visa_code")
    if not isinstance(visa_code, str) or not visa_code:
        errors.append(f"{prefix}: visa_code must be a non-empty string")

    active_ref = row.get("active_grounding_ref")
    candidate_ref = row.get("candidate_ref")
    notes = row.get("notes") or ""
    next_action = row.get("next_action") or ""

    if coverage_status == "active_grounded":
        if not isinstance(active_ref, str) or not active_ref.strip():
            errors.append(
                f"{prefix}: coverage_status='active_grounded' requires "
                "non-empty active_grounding_ref"
            )
        elif active_ref not in active_grounding_ids:
            errors.append(
                f"{prefix}: active_grounding_ref={active_ref!r} not found "
                f"in active fixture {os.path.relpath(ACTIVE_FIXTURE_PATH, REPO_ROOT)!r}"
            )

    if coverage_status == "candidate_only":
        if not isinstance(candidate_ref, str) or not candidate_ref.strip():
            errors.append(
                f"{prefix}: coverage_status='candidate_only' requires "
                "candidate_ref"
            )
        else:
            abs_candidate = (
                candidate_ref
                if os.path.isabs(candidate_ref)
                else os.path.join(REPO_ROOT, candidate_ref)
            )
            if not os.path.isfile(abs_candidate):
                errors.append(
                    f"{prefix}: candidate_ref={candidate_ref!r} does not "
                    "exist on disk"
                )

    requires_subcode = row.get("requires_subcode")
    if requires_subcode is True:
        sub = row.get("visa_sub_code")
        sub_set = isinstance(sub, str) and sub.strip()
        if not sub_set and not (isinstance(notes, str) and notes.strip()):
            errors.append(
                f"{prefix}: requires_subcode=true requires either "
                "visa_sub_code or notes explaining why top-level routing "
                "is unsafe"
            )

    if risk_level == "high":
        if not (isinstance(notes, str) and notes.strip()) and not (
            isinstance(next_action, str) and next_action.strip()
        ):
            errors.append(
                f"{prefix}: risk_level='high' requires non-empty notes "
                "or next_action"
            )

    if (
        isinstance(visa_code, str)
        and visa_code in _NOT_YET_ACTIVE_VISA_CODES
        and coverage_status == "active_grounded"
    ):
        errors.append(
            f"{prefix}: visa_code={visa_code!r} may not claim "
            "active_grounded yet (no active fixture entry promoted)"
        )

    return errors


def main(argv: Optional[List[str]] = None) -> int:
    if not os.path.isfile(MATRIX_PATH):
        print(
            f"ERROR: coverage matrix not found at {MATRIX_PATH!r}",
            file=sys.stderr,
        )
        return 2

    try:
        matrix = _load_json(MATRIX_PATH)
    except json.JSONDecodeError as exc:
        print(f"ERROR: matrix is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(matrix, dict):
        print("ERROR: matrix top-level value must be an object", file=sys.stderr)
        return 2

    rows = matrix.get("rows")
    if not isinstance(rows, list) or not rows:
        print("ERROR: matrix.rows must be a non-empty list", file=sys.stderr)
        return 2

    try:
        active_grounding_ids = _load_active_grounding_ids()
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2

    seen_ids: Dict[str, int] = {}
    all_errors: List[str] = []
    for i, row in enumerate(rows):
        if isinstance(row, dict):
            rid = row.get("id")
            if isinstance(rid, str) and rid:
                if rid in seen_ids:
                    all_errors.append(
                        f"row[{i}]({rid}): duplicate id, first seen at "
                        f"row[{seen_ids[rid]}]"
                    )
                else:
                    seen_ids[rid] = i
        all_errors.extend(_validate_row(row, i, active_grounding_ids))

    print("Paradiso coverage matrix validator")
    print("=" * 60)
    print(f"matrix:          {os.path.relpath(MATRIX_PATH, REPO_ROOT)}")
    print(f"rows:            {len(rows)}")
    print(f"active fixtures: {sorted(active_grounding_ids)}")
    print("")

    if all_errors:
        print(f"FAIL ({len(all_errors)} error(s)):")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print("OK: matrix is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
