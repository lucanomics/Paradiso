#!/usr/bin/env python3
"""Keep backend/data/visas.json in sync with the canonical visa_data.json.

Why this exists:
  The Railway service is deployed with Root Directory = backend, so the
  repo-root `visa_data.json` is not in the build context. The backend's
  loader prefers `backend/data/visas.json` (which IS in context) and
  falls back to a tiny DEFAULT_VISAS stub when that file is missing —
  which is exactly the production warning we are fixing.

Usage:
  scripts/sync_visa_data.py            # copy if drifted, else no-op
  scripts/sync_visa_data.py --check    # exit 1 if drifted (CI mode)
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "visa_data.json"
TARGET = REPO_ROOT / "backend" / "data" / "visas.json"


def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the two files differ, without copying.",
    )
    args = parser.parse_args(argv)

    if not SOURCE.is_file():
        return _fail(f"source missing: {SOURCE}")

    if TARGET.is_file() and filecmp.cmp(SOURCE, TARGET, shallow=False):
        print(f"OK: {TARGET.relative_to(REPO_ROOT)} matches "
              f"{SOURCE.relative_to(REPO_ROOT)}")
        return 0

    if args.check:
        return _fail(
            f"{TARGET.relative_to(REPO_ROOT)} is out of sync with "
            f"{SOURCE.relative_to(REPO_ROOT)}. "
            f"Run scripts/sync_visa_data.py to update."
        )

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, TARGET)
    print(f"Updated {TARGET.relative_to(REPO_ROOT)} from "
          f"{SOURCE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
