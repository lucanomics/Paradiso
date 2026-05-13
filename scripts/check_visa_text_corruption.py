#!/usr/bin/env python3
"""Fail fast if visa data files contain replacement characters.

The U+FFFD REPLACEMENT CHARACTER (`�`) appears when text was decoded
under the wrong codec at some earlier stage of a pipeline; once it is
written into a JSON file the original character is lost. We refuse to
ship that to production silently — this check is wired into
scripts/check_repo.sh.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    REPO_ROOT / "visa_data.json",
    REPO_ROOT / "backend" / "data" / "visas.json",
)
REPLACEMENT_CHAR = "�"


def main() -> int:
    failures: list[str] = []
    for path in TARGETS:
        if not path.is_file():
            failures.append(f"missing: {path.relative_to(REPO_ROOT)}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(
                f"{path.relative_to(REPO_ROOT)}: not valid UTF-8 ({exc})"
            )
            continue
        count = text.count(REPLACEMENT_CHAR)
        if count:
            failures.append(
                f"{path.relative_to(REPO_ROOT)}: contains {count} U+FFFD "
                f"replacement character(s) — Korean text is corrupted at the "
                f"source. Restore from a clean source instead of guessing."
            )
    if failures:
        for line in failures:
            print(f"ERROR: {line}", file=sys.stderr)
        return 1
    print(
        f"OK: visa data files are valid UTF-8 with no replacement characters "
        f"({', '.join(p.relative_to(REPO_ROOT).as_posix() for p in TARGETS)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
