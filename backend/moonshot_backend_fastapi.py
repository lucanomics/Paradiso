"""Optional legacy-style FastAPI backend reference for Paradiso.
Not wired into the static production app.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Paradiso Optional Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_from_json_fallback() -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "visa_data.json"
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("visa_data.json must contain a list")
    return data


def _load_from_postgres() -> list[dict[str, Any]]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    # Optional import path for environments that have psycopg available.
    import psycopg  # type: ignore

    query = "SELECT row_to_json(v) FROM visas v"
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    return [r[0] for r in rows]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/visas")
def get_visas() -> list[dict[str, Any]]:
    source = os.getenv("PARADISO_DATA_SOURCE", "json").lower()
    try:
        if source == "postgres":
            return _load_from_postgres()
        return _load_from_json_fallback()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load visa data: {exc}") from exc
