# Backend Deployment Reference Files (Documentation)

## Scope
This page explains the role of typical backend deployment/config files from the legacy service repository.

## File Roles
- `Procfile`
  - Declares process startup command for platform runtimes.
  - Usually points to an ASGI/WSGI launch command.

- `railway.json`
  - Platform deployment metadata (build/start/runtime controls).
  - Used by managed deployment tooling.

- `requirements.txt`
  - Python dependency lock/reference for backend runtime.
  - Includes framework, DB driver, and utility libraries.

- Architecture notes (example: pipeline architecture markdown)
  - Describes ingestion/normalization path for visa guidance data.
  - Helps contributors reason about reproducibility and compliance.

## Contributor Guidance
- Treat these files as backend-only context, not static-site dependencies.
- Do not add runtime backend files to production static root in mixed PRs.
- Reintroduce backend artifacts only in isolated backend-focused PR phases.
