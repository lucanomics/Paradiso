# Backend Service Overview (Reference Only)

## Purpose
This document captures the architecture of the legacy backend service for contributor reference.

The legacy backend was used to:
- connect to a PostgreSQL database,
- load visa/residence records,
- expose normalized records through an HTTP API,
- support retrieval flows for guidance features.

## High-level Architecture
1. **Application layer**: FastAPI app with route handlers.
2. **Data access layer**: PostgreSQL connection and query execution.
3. **Serialization layer**: response normalization into API-friendly JSON.
4. **API surface**: endpoint pattern equivalent to `/api/visas` for visa list reads.

## Operational Notes
- This repository currently runs as a static app in production.
- Backend implementation is intentionally not reintroduced in this PR.
- Any backend reactivation should be isolated in a dedicated `backend/` path and reviewed separately.

## Why this is documentation-only
- Keeps production stable while preserving architecture context.
- Allows phased reactivation work without coupling to UI/UX changes.
