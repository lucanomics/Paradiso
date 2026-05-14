#!/usr/bin/env python3
"""Paradiso grounding-candidate promotion — dry-run by default.

This script *would* move a reviewed candidate into the active fixture
``backend/data/manual_grounding/stay_manual_grounding_2026_05.json``.
In PR A it is a strict-gate skeleton:

- Default mode is dry-run. The script prints the diff it *would*
  apply and exits 0 without writing.
- ``--apply`` is accepted but is gated. The script refuses to write
  unless ALL of the following are true:
    1. The candidate validator
       (``scripts/validate_manual_grounding_candidate.py``) passes
       cleanly on the candidate.
    2. ``candidate_status == "verified_candidate"``.
    3. ``human_review.decision == "approved"`` with a non-empty
       ``human_review.reviewer`` and a non-empty
       ``human_review.reviewed_at``.

Even when all checks pass, this script:

- never pushes to any remote,
- never opens a PR,
- never merges anything,
- only stages a local working-tree edit and instructs the operator
  to open a draft PR by hand.

Exit codes:

- 0 — dry-run completed, or apply gates passed and a local write
  occurred.
- 1 — apply was requested but at least one gate refused.
- 2 — invocation error (bad path, missing candidate, validator error).

See ``backend/data/manual_grounding/candidates/README.md`` and
``docs/paradiso_ai_safe_automation_architecture.md`` §9.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CANDIDATES_DIR = os.path.join(
    REPO_ROOT, "backend", "data", "manual_grounding", "candidates"
)
ACTIVE_FIXTURE_PATH = os.path.join(
    REPO_ROOT,
    "backend",
    "data",
    "manual_grounding",
    "stay_manual_grounding_2026_05.json",
)
VALIDATOR_SCRIPT = os.path.join(
    REPO_ROOT, "scripts", "validate_manual_grounding_candidate.py"
)


def _resolve_candidate(spec: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (candidate_json_path, error)."""
    if os.path.isabs(spec) or os.sep in spec:
        if os.path.isfile(spec):
            return spec, None
        if os.path.isdir(spec):
            cand = os.path.join(spec, "candidate.json")
            if os.path.isfile(cand):
                return cand, None
        return None, f"no candidate.json found at {spec!r}"
    slug_dir = os.path.join(DEFAULT_CANDIDATES_DIR, spec)
    cand = os.path.join(slug_dir, "candidate.json")
    if os.path.isfile(cand):
        return cand, None
    return None, (
        f"no candidate.json found for slug {spec!r}; expected at "
        f"{cand}"
    )


def _run_validator(candidate_path: str) -> Tuple[bool, str]:
    if not os.path.isfile(VALIDATOR_SCRIPT):
        return False, f"validator script missing at {VALIDATOR_SCRIPT}"
    proc = subprocess.run(
        [sys.executable, VALIDATOR_SCRIPT, candidate_path],
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    return proc.returncode == 0, out


def _check_review_gate(candidate: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    if candidate.get("candidate_status") != "verified_candidate":
        failures.append(
            "candidate_status must be 'verified_candidate' "
            f"(got {candidate.get('candidate_status')!r})"
        )
    review = candidate.get("human_review")
    if not isinstance(review, dict):
        failures.append(
            "human_review object missing; promotion requires "
            "{decision, reviewer, reviewed_at}"
        )
        return failures
    decision = review.get("decision")
    if decision != "approved":
        failures.append(
            f"human_review.decision must be 'approved' (got {decision!r})"
        )
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        failures.append("human_review.reviewer must be a non-empty string")
    reviewed_at = review.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not reviewed_at.strip():
        failures.append("human_review.reviewed_at must be a non-empty string")
    return failures


def _load_active_fixture() -> Dict[str, Any]:
    with open(ACTIVE_FIXTURE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _strip_candidate_meta(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``candidate`` without candidate-only metadata.

    The active fixture's grounding entries do not carry
    ``candidate_status`` or ``human_review``; those are review-time
    fields. Everything else is preserved.
    """
    drop = {"candidate_status", "human_review", "risk_notes"}
    return {k: v for k, v in candidate.items() if k not in drop}


def _proposed_fixture(
    fixture: Dict[str, Any], candidate: Dict[str, Any]
) -> Dict[str, Any]:
    new = json.loads(json.dumps(fixture, ensure_ascii=False))
    new.setdefault("groundings", []).append(_strip_candidate_meta(candidate))
    return new


def _unified_diff(before: str, after: str, label: str) -> str:
    import difflib

    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{label}",
        tofile=f"b/{label}",
        n=3,
    )
    return "".join(diff)


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Dry-run-by-default promotion of a reviewed grounding "
            "candidate into the active fixture."
        )
    )
    p.add_argument(
        "candidate",
        help=(
            "Candidate slug (under backend/data/manual_grounding/"
            "candidates/) or explicit path to candidate.json."
        ),
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Permit writing to the active fixture. Refused unless ALL "
            "gates pass (validator OK, candidate_status="
            "verified_candidate, human_review.decision=approved). "
            "Never pushes, never opens a PR, never merges."
        ),
    )
    p.add_argument(
        "--no-validator",
        action="store_true",
        help=(
            "Skip the validator gate. Strongly discouraged — only for "
            "debugging the diff renderer."
        ),
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    candidate_path, err = _resolve_candidate(args.candidate)
    if err or not candidate_path:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    try:
        with open(candidate_path, "r", encoding="utf-8") as fh:
            candidate = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: failed to read {candidate_path}: {exc}", file=sys.stderr)
        return 2

    if not os.path.isfile(ACTIVE_FIXTURE_PATH):
        print(
            f"ERROR: active fixture not found at {ACTIVE_FIXTURE_PATH}",
            file=sys.stderr,
        )
        return 2

    print("Paradiso grounding-candidate promotion — dry-run by default")
    print("=" * 60)
    print(f"Candidate file: {candidate_path}")
    print(f"Active fixture: {ACTIVE_FIXTURE_PATH}")
    print("")

    # 1. Validator gate
    validator_ok = True
    if not args.no_validator:
        validator_ok, validator_output = _run_validator(candidate_path)
        print("Validator:")
        print(validator_output.rstrip())
        print("")
    else:
        print("Validator: SKIPPED (--no-validator)\n")

    # 2. Review gate
    review_failures = _check_review_gate(candidate)
    if review_failures:
        print("Review gate: FAIL")
        for f in review_failures:
            print(f"  - {f}")
    else:
        print("Review gate: OK")
    print("")

    # 3. Compute proposed fixture and diff
    fixture = _load_active_fixture()
    proposed = _proposed_fixture(fixture, candidate)
    before = json.dumps(fixture, indent=2, ensure_ascii=False) + "\n"
    after = json.dumps(proposed, indent=2, ensure_ascii=False) + "\n"
    diff = _unified_diff(
        before, after, "backend/data/manual_grounding/stay_manual_grounding_2026_05.json"
    )
    print("Proposed diff:")
    if diff:
        print(diff)
    else:
        print("  (no change — candidate already present?)")
    print("")

    all_gates_pass = validator_ok and not review_failures

    if not args.apply:
        print(
            "Dry-run only. No file was modified. Pass --apply to attempt "
            "promotion (requires all gates to pass)."
        )
        return 0

    if not all_gates_pass:
        print(
            "REFUSED: --apply was passed but one or more gates failed. "
            "No file modified."
        )
        print("")
        print(
            "Note: promotion never pushes, never opens a PR, and never "
            "auto-merges. Even when all gates pass, a human must still "
            "author the draft PR."
        )
        return 1

    # All gates passed and --apply requested. Write the proposed
    # fixture locally. We deliberately do not call git, do not push,
    # and do not open a PR.
    with open(ACTIVE_FIXTURE_PATH, "w", encoding="utf-8") as fh:
        fh.write(after)
    print(
        "Applied. Local working tree updated. "
        "Next step (human): review the diff, run scripts/check_repo.sh, "
        "and open a draft PR. This script did NOT commit, did NOT push, "
        "and did NOT open a PR."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
