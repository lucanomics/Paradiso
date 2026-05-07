# Data Pipeline Reproducibility

This folder documents helper scripts for reproducing data preparation workflows.

## `scripts/fetch_jobcodes.py`
- Purpose: collect job/industry code data (KSCO + KSIC API pattern) and produce `data/jobcode_master.json`.
- Requires: `JOBCODE_API_KEY` environment variable.
- Optional: `JOBCODE_API_BASE` can override the API base URL.

Run locally:
```bash
export JOBCODE_API_KEY="..."
python3 scripts/fetch_jobcodes.py
```

## `scripts/generate_seed.py`
- Purpose: convert `visa_data.json` into a PostgreSQL seed SQL file for backend reference environments.
- Default output: `data/seed_visas.sql`.

Run locally:
```bash
python3 scripts/generate_seed.py
# or
python3 scripts/generate_seed.py visa_data.json data/seed_visas.sql
```

## Safety / Operational Notes
- These scripts are reproducibility helpers and are not part of production static runtime.
- `fetch_jobcodes.py` uses external network requests and requires valid credentials.
- Do not commit secrets or API keys.
