#!/usr/bin/env python3
"""Paradiso source monitoring — report-only skeleton.

Reads ``data/source_registry.json`` and reports the state of every
declared source. By default this script does **no** network I/O:

- ``pdf_manual`` entries are compared against their committed
  ``local_path`` via sha256. Result is one of:
  ``unchanged``, ``changed``, ``missing``, ``no_baseline``.
- ``law_api`` and ``notice_index`` entries are **skipped** unless
  ``--allow-network`` is passed. Even with ``--allow-network`` this
  PR's skeleton does not actually fetch — it reports
  ``network_skipped: HTTP not implemented in skeleton``. The flag is
  honored for future PRs.

The script never modifies ``source_registry.json``, never writes
state files, never opens issues, never opens PRs, and never touches
the active grounding fixture.

Exit codes:

- 0 by default in report mode, including when changes are detected.
- 0 when ``--strict`` is passed and all ``active`` local sources
  report ``unchanged``.
- 1 when ``--strict`` is passed and any ``active`` local source
  reports ``changed`` or ``missing``.
- 2 on registry parse / validation errors.

See ``docs/source_monitoring_pipeline.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "source_registry.json")

_VALID_TYPES = {"pdf_manual", "law_api", "notice_index"}
_VALID_STATUSES = {"active", "not_configured", "deprecated"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _load_registry(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise SystemExit(f"ERROR: source registry not found at {path}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: failed to read {path}: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise SystemExit(f"ERROR: {path} must be a JSON object with a 'sources' list")
    return data


def _validate_record(rec: Dict[str, Any], idx: int) -> List[str]:
    errors: List[str] = []
    required = ("id", "type", "title", "status")
    for field in required:
        if field not in rec:
            errors.append(f"sources[{idx}]: missing required field '{field}'")
    rec_type = rec.get("type")
    if rec_type not in _VALID_TYPES:
        errors.append(
            f"sources[{idx}] id={rec.get('id')!r}: invalid type {rec_type!r}; "
            f"expected one of {sorted(_VALID_TYPES)}"
        )
    rec_status = rec.get("status")
    if rec_status not in _VALID_STATUSES:
        errors.append(
            f"sources[{idx}] id={rec.get('id')!r}: invalid status "
            f"{rec_status!r}; expected one of {sorted(_VALID_STATUSES)}"
        )
    if rec_type == "pdf_manual" and not rec.get("local_path"):
        errors.append(
            f"sources[{idx}] id={rec.get('id')!r}: pdf_manual entries must "
            "declare local_path"
        )
    return errors


def _check_local(rec: Dict[str, Any]) -> Dict[str, Any]:
    local_path = rec.get("local_path")
    if not local_path:
        return {"state": "skipped", "reason": "no_local_path"}
    abs_path = local_path if os.path.isabs(local_path) else os.path.join(REPO_ROOT, local_path)
    if not os.path.isfile(abs_path):
        return {
            "state": "missing",
            "local_path": local_path,
            "reason": "file_not_found",
        }
    current_hash = _sha256_of_file(abs_path)
    baseline = rec.get("last_known_hash")
    if not baseline:
        return {
            "state": "no_baseline",
            "local_path": local_path,
            "current_hash": current_hash,
        }
    if baseline == current_hash:
        return {
            "state": "unchanged",
            "local_path": local_path,
            "current_hash": current_hash,
        }
    return {
        "state": "changed",
        "local_path": local_path,
        "current_hash": current_hash,
        "previous_hash": baseline,
    }


def _check_network_entry(rec: Dict[str, Any], allow_network: bool) -> Dict[str, Any]:
    if not allow_network:
        return {
            "state": "skipped",
            "reason": "network_disabled",
            "url": rec.get("url"),
        }
    # Even with --allow-network the skeleton does not fetch. Future PRs
    # may add a guarded fetcher here. For now, report a clear stub
    # state so operators know the flag was honored but no I/O happened.
    return {
        "state": "network_skipped",
        "reason": "HTTP fetch not implemented in skeleton",
        "url": rec.get("url"),
    }


def _check_source(rec: Dict[str, Any], allow_network: bool) -> Dict[str, Any]:
    rec_type = rec.get("type")
    rec_status = rec.get("status")
    base = {
        "id": rec.get("id"),
        "type": rec_type,
        "status": rec_status,
        "title": rec.get("title"),
        "checked_at": _now_iso(),
    }
    if rec_status == "deprecated":
        return {**base, "state": "skipped", "reason": "deprecated"}
    if rec_type == "pdf_manual":
        return {**base, **_check_local(rec)}
    if rec_type in ("law_api", "notice_index"):
        if rec_status == "not_configured":
            return {
                **base,
                "state": "skipped",
                "reason": "not_configured",
                "url": rec.get("url"),
            }
        return {**base, **_check_network_entry(rec, allow_network)}
    return {**base, "state": "skipped", "reason": f"unknown_type:{rec_type}"}


def _summarize(results: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in results:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    counts["total"] = len(results)
    return counts


def _format_human(results: List[Dict[str, Any]], summary: Dict[str, int]) -> str:
    lines: List[str] = []
    lines.append("Paradiso source monitor — report-only")
    lines.append("=" * 60)
    for r in results:
        bits = [
            r.get("state", "?"),
            r.get("id", "?"),
            f"({r.get('type', '?')})",
        ]
        if "local_path" in r:
            bits.append(f"local_path={r['local_path']}")
        if "url" in r and r["url"]:
            bits.append(f"url={r['url']}")
        if "reason" in r:
            bits.append(f"reason={r['reason']}")
        if r.get("state") == "changed":
            bits.append(f"previous_hash={r.get('previous_hash')}")
            bits.append(f"current_hash={r.get('current_hash')}")
        lines.append("  - " + " ".join(str(b) for b in bits))
    lines.append("")
    lines.append("Summary:")
    for k in sorted(summary):
        lines.append(f"  {k}: {summary[k]}")
    lines.append("")
    lines.append(
        "Note: This script never modifies the registry, never writes "
        "state files, and never edits production data."
    )
    return "\n".join(lines)


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Report-only source monitor for Paradiso AI."
    )
    p.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_PATH,
        help="Path to source_registry.json (default: %(default)s).",
    )
    p.add_argument(
        "--local-only",
        action="store_true",
        help="Force network-backed entries to be skipped (default behavior).",
    )
    p.add_argument(
        "--allow-network",
        action="store_true",
        help="Permit network-backed entries (this skeleton still does not fetch).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when any 'active' local source is changed/missing.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of human-readable report.",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    if args.allow_network and args.local_only:
        print("ERROR: --allow-network and --local-only are mutually exclusive", file=sys.stderr)
        return 2
    allow_network = bool(args.allow_network) and not args.local_only

    registry = _load_registry(args.registry)
    sources = registry.get("sources", [])

    validation_errors: List[str] = []
    for idx, rec in enumerate(sources):
        if not isinstance(rec, dict):
            validation_errors.append(f"sources[{idx}]: not an object")
            continue
        validation_errors.extend(_validate_record(rec, idx))
    if validation_errors:
        for err in validation_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2

    results = [_check_source(rec, allow_network) for rec in sources]
    summary = _summarize(results)

    if args.json:
        out = {
            "schema_version": "1.0",
            "checked_at": _now_iso(),
            "allow_network": allow_network,
            "results": results,
            "summary": summary,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(_format_human(results, summary))

    if args.strict:
        for r, rec in zip(results, sources):
            if rec.get("status") != "active":
                continue
            if r.get("state") in ("changed", "missing"):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
