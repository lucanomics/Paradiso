#!/usr/bin/env python3
"""Deterministic integrity checks for visa JSON text fields."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

TARGETS = [Path("visa_data.json"), Path("backend/data/visas.json")]
REPLACEMENT_CHAR = "\uFFFD"
MOJIBAKE_PATTERNS = [
    re.compile(r"Ã.|Â.|Ð.|Ñ.|Ø.|Ù.|æ.|ç.|ì.|ë.|ï¿½"),
]


def _iter_strings(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _iter_strings(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _iter_strings(item, f"{path}[{i}]")


def _find_code_context(path: str) -> str:
    m = re.search(r"\$\[(\d+)\]", path)
    if not m:
        return ""
    idx = int(m.group(1))
    return f"record_index={idx}"


def main() -> int:
    errors: list[str] = []
    for target in TARGETS:
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{target}: failed to parse as UTF-8 JSON: {exc}")
            continue

        for jpath, text in _iter_strings(payload):
            if REPLACEMENT_CHAR in text:
                errors.append(f"{target}:{jpath} contains replacement char U+FFFD {_find_code_context(jpath)}")
            for pat in MOJIBAKE_PATTERNS:
                if pat.search(text):
                    errors.append(f"{target}:{jpath} matches mojibake-like pattern {_find_code_context(jpath)}")
                    break

    if errors:
        print("FAIL: visa data text integrity check found possible corruption:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("PASS: visa data text integrity check passed for visa_data.json and backend/data/visas.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
