#!/usr/bin/env python3
"""Generate PostgreSQL seed SQL from visa_data.json.

Usage:
  python3 scripts/generate_seed.py [input_json] [output_sql]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def esc(v: str) -> str:
    return v.replace("'", "''")


def main() -> int:
    input_json = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("visa_data.json")
    output_sql = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/seed_visas.sql")

    rows = json.loads(input_json.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        print("ERROR: input JSON must be an array", file=sys.stderr)
        return 1

    output_sql.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "BEGIN;",
        "CREATE TABLE IF NOT EXISTS visas (code text primary key, name text, cat text, raw jsonb not null);",
    ]

    for item in rows:
        code = esc(str(item.get("code", "")))
        name = esc(str(item.get("name", "")))
        cat = esc(str(item.get("cat", "")))
        raw = esc(json.dumps(item, ensure_ascii=False))
        lines.append(
            f"INSERT INTO visas (code, name, cat, raw) VALUES ('{code}','{name}','{cat}','{raw}'::jsonb) "
            "ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, cat=EXCLUDED.cat, raw=EXCLUDED.raw;"
        )

    lines.append("COMMIT;")
    output_sql.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_sql}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
