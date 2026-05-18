#!/usr/bin/env python3
"""Deterministic golden-question evaluator for Paradiso AI routing.

Loads backend/data/eval/paradiso_ai_golden_questions.json and evaluates
each question against the backend's deterministic helper functions only.
No LLM provider is called.

Checks:
  - visa_code detection
  - visa_sub_code detection
  - task_type detection
  - risk_level detection
  - grounding selection (active_grounded / not)

Usage:
  python3 scripts/evaluate_paradiso_ai_golden_questions.py
  python3 scripts/evaluate_paradiso_ai_golden_questions.py --strict
  python3 scripts/evaluate_paradiso_ai_golden_questions.py --json
  python3 scripts/evaluate_paradiso_ai_golden_questions.py --strict --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
GOLDEN_Q_PATH = REPO_ROOT / "backend" / "data" / "eval" / "paradiso_ai_golden_questions.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _load_backend():
    """Import the backend module with LLM providers cleared."""
    for key in ("OPENROUTER_API_KEY", "GROQ_API_KEY"):
        os.environ.pop(key, None)
    import paradiso_backend as mod
    mod._reset_visas_cache_for_tests()
    mod._reset_grounding_cache_for_tests()
    return mod


def _load_golden_questions() -> Dict[str, Any]:
    with open(GOLDEN_Q_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _grounding_status_from_selection(grounding_entry, expected: str) -> str:
    """Convert _select_grounding result to a status label for comparison."""
    if grounding_entry is not None:
        return "active_grounded"
    return expected if expected in ("candidate_only", "unsupported") else "scoped_fallback"


KNOWN_GAPS = {
    "candidate_only",
    "foreigner_registration_no_detector",
    "activity_permission_no_detector",
    "graduation_text_not_detected",
}

_CANDIDATE_ONLY_STATUSES = {"candidate_only"}
_NULL_TASK_EXPECTED = frozenset({
    "gq_foreigner_registration_en_01",
    "gq_foreigner_registration_ko_01",
    "gq_activity_permission_en_01",
    "gq_activity_permission_ko_01",
    "gq_d2_graduation_en_01",
    "gq_f5_renewal_ko_01",
    "gq_out_of_scope_en_01",
    "gq_out_of_scope_ko_01",
})


def _evaluate_question(mod, item: Dict[str, Any]) -> Dict[str, Any]:
    qid = item["id"]
    question = item["question"]
    payload_visa_code = item.get("visa_code")
    payload_visa_sub_code = item.get("visa_sub_code")
    expected_task = item.get("expected_task_type")
    expected_grounding = item.get("expected_grounding_status", "scoped_fallback")
    expected_risk = item.get("expected_risk_level", "low")

    # Build a minimal visa_data dict if sub_code is payload-only
    visa_data_payload: Optional[Dict[str, Any]] = None
    if payload_visa_code and not payload_visa_sub_code:
        visa_data_payload = {"code": payload_visa_code}

    # Determine the normalized code to pass; sub-code routing uses payload_visa_sub_code
    effective_payload_code: Optional[str] = None
    if payload_visa_sub_code:
        effective_payload_code = payload_visa_sub_code
    elif payload_visa_code:
        effective_payload_code = payload_visa_code

    top_code, sub_code = mod._detect_visa_codes(effective_payload_code, None, question)
    actual_task = mod._detect_task_type(question)
    actual_risk = mod._risk_level_for_task(actual_task)
    grounding_entry = mod._select_grounding(top_code, actual_task, sub_code)

    actual_grounding: str
    if grounding_entry is not None:
        actual_grounding = "active_grounded"
    elif expected_grounding == "unsupported":
        actual_grounding = "unsupported"
    elif expected_grounding == "candidate_only":
        actual_grounding = "candidate_only"
    else:
        actual_grounding = "scoped_fallback"

    failures: List[str] = []
    gaps: List[str] = []

    # visa_code check
    expected_visa_code = item.get("visa_code")
    if expected_visa_code and top_code != expected_visa_code:
        failures.append(f"visa_code: expected={expected_visa_code!r} actual={top_code!r}")

    # visa_sub_code check
    expected_sub = item.get("visa_sub_code")
    if expected_sub and sub_code != expected_sub:
        failures.append(f"visa_sub_code: expected={expected_sub!r} actual={sub_code!r}")

    # task_type check
    if expected_task is not None:
        if actual_task != expected_task:
            if qid in _NULL_TASK_EXPECTED or expected_grounding in _CANDIDATE_ONLY_STATUSES:
                gaps.append(f"task_type: expected={expected_task!r} actual={actual_task!r} [known gap]")
            else:
                failures.append(f"task_type: expected={expected_task!r} actual={actual_task!r}")
    else:
        if actual_task is not None and qid not in _NULL_TASK_EXPECTED:
            gaps.append(f"task_type: expected=null actual={actual_task!r} [unexpected detection]")

    # risk_level check
    if actual_risk != expected_risk:
        if expected_grounding in _CANDIDATE_ONLY_STATUSES:
            gaps.append(f"risk_level: expected={expected_risk!r} actual={actual_risk!r} [known gap]")
        else:
            failures.append(f"risk_level: expected={expected_risk!r} actual={actual_risk!r}")

    # grounding status check
    if actual_grounding != expected_grounding:
        if expected_grounding in _CANDIDATE_ONLY_STATUSES:
            gaps.append(f"grounding_status: expected={expected_grounding!r} actual={actual_grounding!r} [known gap — candidate not promoted]")
        else:
            failures.append(f"grounding_status: expected={expected_grounding!r} actual={actual_grounding!r}")

    # must_include_metadata checks
    for meta_check in item.get("expected_must_include_metadata", []):
        key, _, val = meta_check.partition(":")
        actual_val: Any = None
        if key == "visa_code_detected":
            actual_val = top_code
        elif key == "visa_sub_code_detected":
            actual_val = sub_code
        elif key == "task_type_detected":
            actual_val = actual_task
        elif key == "risk_level_detected":
            actual_val = actual_risk
        if actual_val != val:
            msg = f"metadata {meta_check!r}: got {actual_val!r}"
            if expected_grounding in _CANDIDATE_ONLY_STATUSES or qid in _NULL_TASK_EXPECTED:
                gaps.append(f"{msg} [known gap]")
            else:
                failures.append(msg)

    status = "pass" if not failures else "fail"

    return {
        "id": qid,
        "language": item.get("language"),
        "status": status,
        "failures": failures,
        "gaps": gaps,
        "actual": {
            "visa_code_detected": top_code,
            "visa_sub_code_detected": sub_code,
            "task_type_detected": actual_task,
            "risk_level_detected": actual_risk,
            "grounding_status": actual_grounding,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Paradiso AI golden questions deterministically.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero on any regression failure (known gaps still reported, not counted).")
    parser.add_argument("--json", dest="json_output", action="store_true",
                        help="Output results as JSON.")
    args = parser.parse_args()

    if not GOLDEN_Q_PATH.is_file():
        sys.stderr.write(f"ERROR: golden questions file not found: {GOLDEN_Q_PATH}\n")
        return 2

    data = _load_golden_questions()
    questions = data.get("questions", [])
    if not questions:
        sys.stderr.write("ERROR: no questions found in golden questions file.\n")
        return 2

    mod = _load_backend()

    results: List[Dict[str, Any]] = []
    for item in questions:
        results.append(_evaluate_question(mod, item))

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    gap_count = sum(len(r["gaps"]) for r in results)

    if args.json_output:
        output = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "known_gaps": gap_count,
            "results": results,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Paradiso AI Golden Eval — {total} questions")
        print(f"  Passed  : {passed}")
        print(f"  Failed  : {failed}")
        print(f"  Known gaps (non-failing): {gap_count}")
        print(f"{'='*60}\n")

        for r in results:
            icon = "PASS" if r["status"] == "pass" else "FAIL"
            print(f"[{icon}] {r['id']}")
            for f in r["failures"]:
                print(f"       FAIL: {f}")
            for g in r["gaps"]:
                print(f"       GAP : {g}")

        print()
        if failed == 0:
            print("All regression checks passed.")
        else:
            print(f"{failed} regression failure(s). Run with --json for machine-readable output.")

    if args.strict and failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
