# Optional Legacy Backend Reference

This directory contains an optional backend reference and is **not wired into** the production static site.

## What it does
- Provides a FastAPI service.
- Exposes `GET /api/visas` for visa dataset reads.
- Supports two data-source modes:
  - `PARADISO_DATA_SOURCE=json` (default): reads local `visa_data.json`.
  - `PARADISO_DATA_SOURCE=postgres`: reads from PostgreSQL using `DATABASE_URL`.

## Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.moonshot_backend_fastapi:app --reload
```

Then open:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/visas`

## Production impact
None. This backend is reference-only in the current repository state.
