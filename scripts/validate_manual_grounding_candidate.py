#!/usr/bin/env python3
"""Paradiso manual-grounding candidate validator.

Validates JSON candidate files under
``backend/data/manual_grounding/candidates/`` for structural and
provenance correctness. **Does not** validate legal or factual
correctness — that is a human reviewer's job.

The validator:

- Refuses to validate the active fixture
  (``stay_manual_grounding_2026_05.json``); the active fixture is
  out of scope.
- Walks ``backend/data/manual_grounding/candidates/`` looking for
  ``candidate.json`` files (or a single explicit path passed on the
  CLI).
- Passes cleanly when no candidate JSON files exist (PR A ships no
  candidates).
- Refuses ``source_verification_status = "verified_locally"`` unless
  a sibling ``REVIEW.md`` exists.
- Refuses candidates that contain obvious generic / global-immigration
  boilerplate (``USCIS``, ``Home Office``, ``해당 국가``,
  ``본인이 체류 중인 국가``) in any string field.

Exit codes:

- 0 — all discovered candidates passed, or there are no candidates.
- 1 — one or more candidates failed validation.
- 2 — invocation error (bad path, refused target).

See ``backend/data/manual_grounding/candidates/README.md`` and
``docs/manual_grounding_expansion_plan.md`` for the schema contract.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CANDIDATES_DIR = os.path.join(
    REPO_ROOT, "backend", "data", "manual_grounding", "candidates"
)
ACTIVE_FIXTURE_NAME = "stay_manual_grounding_2026_05.json"

_REQUIRED_FIELDS = (
    "candidate_status",
    "visa_code",
    "procedure_type",
    "section",
    "page_range",
    "source_file",
    "source_title",
    "source_date",
    "issuing_body",
    "required_documents",
    "source_excerpt",
    "source_verification_status",
    "source_confidence",
    "verification_note",
)
_OPTIONAL_FIELDS = (
    "visa_sub_code",
    "scenario",
    "caveats",
    "risk_notes",
    "human_review",
    "sub_codes_covered",
    "scenarios_covered",
    "requires_clarification_when_missing_subcode",
)

_VALID_CANDIDATE_STATUS = {"draft", "verified_candidate"}
_VALID_VERIFICATION_STATUS = {
    "unverified",
    "machine_extracted",
    "verified_locally",
}
_VALID_CONFIDENCE = {"low", "medium", "high"}

# Generic / global-immigration boilerplate that must not appear in a
# Korea-specific candidate. The list is deliberately small and
# specific; broader natural-language correctness is a human task.
_FORBIDDEN_STRINGS = (
    "USCIS",
    "Home Office",
    "해당 국가",
    "본인이 체류 중인 국가",
)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)


def _find_forbidden(candidate: Dict[str, Any]) -> List[Tuple[str, str]]:
    hits: List[Tuple[str, str]] = []
    for needle in _FORBIDDEN_STRINGS:
        for s in _iter_strings(candidate):
            if needle in s:
                hits.append((needle, s.strip()[:140]))
                break
    return hits


def _discover_candidates(root: str) -> List[str]:
    if not os.path.isdir(root):
        return []
    paths: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name == "candidate.json":
                paths.append(os.path.join(dirpath, name))
    paths.sort()
    return paths


def _refuse_active_fixture(path: str) -> Optional[str]:
    abs_path = os.path.abspath(path)
    base = os.path.basename(abs_path)
    if base == ACTIVE_FIXTURE_NAME:
        return (
            f"refusing to validate active fixture {abs_path!r}; this script "
            "is for candidate files only. The active fixture is reviewed by "
            "scripts/check_repo.sh and by human reviewers."
        )
    return None


def _validate_one(path: str) -> List[str]:
    errors: List[str] = []

    refusal = _refuse_active_fixture(path)
    if refusal:
        errors.append(refusal)
        return errors

    try:
        with open(path, "r", encoding="utf-8") as fh:
            candidate = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: failed to read JSON: {exc}")
        return errors

    if not isinstance(candidate, dict):
        errors.append(f"{path}: top-level JSON value must be an object")
        return errors

    for field in _REQUIRED_FIELDS:
        if field not in candidate:
            errors.append(f"{path}: missing required field '{field}'")

    # candidate_status
    cs = candidate.get("candidate_status")
    if cs is not None and cs not in _VALID_CANDIDATE_STATUS:
        errors.append(
            f"{path}: candidate_status must be one of "
            f"{sorted(_VALID_CANDIDATE_STATUS)}, got {cs!r}"
        )

    # source_verification_status
    svs = candidate.get("source_verification_status")
    if svs is not None and svs not in _VALID_VERIFICATION_STATUS:
        errors.append(
            f"{path}: source_verification_status must be one of "
            f"{sorted(_VALID_VERIFICATION_STATUS)}, got {svs!r}"
        )

    # source_confidence
    sc = candidate.get("source_confidence")
    if sc is not None and sc not in _VALID_CONFIDENCE:
        errors.append(
            f"{path}: source_confidence must be one of "
            f"{sorted(_VALID_CONFIDENCE)}, got {sc!r}"
        )

    # page_range presence and basic shape
    pr = candidate.get("page_range")
    if not isinstance(pr, str) or not pr.strip():
        errors.append(f"{path}: page_range must be a non-empty string")

    # source_file must exist on disk (relative to repo root or absolute)
    src = candidate.get("source_file")
    if not isinstance(src, str) or not src.strip():
        errors.append(f"{path}: source_file must be a non-empty string")
    else:
        abs_src = src if os.path.isabs(src) else os.path.join(REPO_ROOT, src)
        if not os.path.isfile(abs_src):
            errors.append(
                f"{path}: source_file references missing path: {src!r}"
            )

    # source_excerpt
    excerpt = candidate.get("source_excerpt")
    if not isinstance(excerpt, str) or not excerpt.strip():
        errors.append(f"{path}: source_excerpt must be a non-empty string")

    # required_documents must be a non-empty list
    docs = candidate.get("required_documents")
    if not isinstance(docs, list) or len(docs) == 0:
        errors.append(f"{path}: required_documents must be a non-empty list")

    # verified_locally requires sibling REVIEW.md
    if svs == "verified_locally":
        review_path = os.path.join(os.path.dirname(path), "REVIEW.md")
        if not os.path.isfile(review_path):
            errors.append(
                f"{path}: source_verification_status='verified_locally' "
                f"requires sibling REVIEW.md at {review_path!r}"
            )

    # sub-code shape
    visa_code = candidate.get("visa_code")
    sub = candidate.get("visa_sub_code")
    if isinstance(sub, str) and sub and isinstance(visa_code, str):
        if not sub.startswith(f"{visa_code}-"):
            errors.append(
                f"{path}: visa_sub_code {sub!r} must start with "
                f"'{visa_code}-'"
            )
    covered = candidate.get("sub_codes_covered")
    if isinstance(covered, list) and isinstance(visa_code, str):
        for item in covered:
            if not isinstance(item, str) or not item.startswith(f"{visa_code}-"):
                errors.append(
                    f"{path}: sub_codes_covered entry {item!r} must start "
                    f"with '{visa_code}-'"
                )

    # Forbidden generic / global-immigration boilerplate
    for needle, sample in _find_forbidden(candidate):
        errors.append(
            f"{path}: contains forbidden generic-immigration string "
            f"{needle!r} (excerpt: {sample!r})"
        )

    return errors


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Validate manual-grounding candidate JSON files. "
            "Does not validate legal correctness."
        )
    )
    p.add_argument(
        "path",
        nargs="?",
        default=None,
        help=(
            "Optional explicit path to a single candidate.json. "
            "If omitted, the candidates/ directory is walked."
        ),
    )
    p.add_argument(
        "--candidates-dir",
        default=DEFAULT_CANDIDATES_DIR,
        help="Override the candidates directory (default: %(default)s).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of human-readable report.",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    if args.path:
        refusal = _refuse_active_fixture(args.path)
        if refusal:
            print(f"ERROR: {refusal}", file=sys.stderr)
            return 2
        if not os.path.isfile(args.path):
            print(f"ERROR: candidate file not found: {args.path}", file=sys.stderr)
            return 2
        candidate_paths = [args.path]
    else:
        candidate_paths = _discover_candidates(args.candidates_dir)

    if not candidate_paths:
        msg = (
            "No candidate.json files found under "
            f"{args.candidates_dir!r}. Nothing to validate."
        )
        if args.json:
            print(json.dumps({"status": "ok", "message": msg, "candidates": []}, indent=2))
        else:
            print(msg)
        return 0

    all_errors: Dict[str, List[str]] = {}
    for p in candidate_paths:
        errs = _validate_one(p)
        if errs:
            all_errors[p] = errs

    summary = {
        "total": len(candidate_paths),
        "passed": len(candidate_paths) - len(all_errors),
        "failed": len(all_errors),
    }

    if args.json:
        print(
            json.dumps(
                {
                    "status": "fail" if all_errors else "ok",
                    "summary": summary,
                    "errors": all_errors,
                    "candidates": candidate_paths,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print("Paradiso manual-grounding candidate validator")
        print("=" * 60)
        for p in candidate_paths:
            if p in all_errors:
                print(f"FAIL  {p}")
                for err in all_errors[p]:
                    print(f"   - {err}")
            else:
                print(f"OK    {p}")
        print("")
        print(
            f"Summary: total={summary['total']} "
            f"passed={summary['passed']} failed={summary['failed']}"
        )

    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
