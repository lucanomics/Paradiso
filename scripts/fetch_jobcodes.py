#!/usr/bin/env python3
"""Fetch KSCO/KSIC job and industry codes from an external API.

Requires:
  JOBCODE_API_KEY environment variable.

This utility is for reproducibility/documentation workflows and is not used by
production static runtime directly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = os.getenv("JOBCODE_API_BASE", "https://api.example.invalid/jobcodes")


def fetch(endpoint: str, api_key: str) -> dict:
    query = urlencode({"apiKey": api_key})
    url = f"{API_BASE}/{endpoint}?{query}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:  # nosec B310 - controlled endpoint
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    api_key = os.getenv("JOBCODE_API_KEY")
    if not api_key:
        print("ERROR: JOBCODE_API_KEY is required.", file=sys.stderr)
        return 1

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)

    payload = {
        "ksco": fetch("ksco", api_key),
        "ksic": fetch("ksic", api_key),
    }

    out_file = out_dir / "jobcode_master.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
