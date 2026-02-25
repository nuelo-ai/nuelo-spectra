---
status: testing
phase: 35-docker-compose-local-validation
source: 35-01-SUMMARY.md
started: 2026-02-21T00:00:00Z
updated: 2026-02-21T00:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 2
name: Stack starts with docker compose up --build
expected: |
  Running `docker compose up --build` builds and starts all 4 services without errors. No immediate crashes or missing image errors.
awaiting: user response

## Tests

### 1. compose.yaml and .env.docker.example exist
expected: compose.yaml is present at the repo root. .env.docker.example is also present with documented vars (SECRET_KEY, CORS_ORIGINS, API keys, DATABASE_URL, SPECTRA_MODE).
result: pass

### 2. Stack starts with docker compose up --build
expected: Running `docker compose up --build` builds and starts all 4 services without errors. No immediate crashes or missing image errors.
result: [pending]

### 3. All 4 services are running
expected: After startup, `docker compose ps` shows db, backend, public-frontend, and admin-frontend all in a running/healthy state.
result: [pending]

### 4. Healthcheck-ordered startup
expected: Services start in order: db first (must reach healthy), then backend, then the two frontends. No frontend or backend starts before db is healthy.
result: [pending]

### 5. Public frontend is accessible
expected: http://localhost:3000 loads the public frontend without errors.
result: [pending]

### 6. Admin frontend is accessible on port 3001
expected: http://localhost:3001 loads the admin frontend. It maps host port 3001 to container port 3000.
result: [pending]

### 7. Backend is accessible
expected: http://localhost:8000 (or configured port) responds — e.g., health endpoint or API root returns a response.
result: [pending]

### 8. Data persists across restarts
expected: After `docker compose down` and `docker compose up` (without --volumes), previously created data (e.g., a DB record or uploaded file) is still present.
result: [pending]

## Summary

total: 8
passed: 1
issues: 0
pending: 7
skipped: 0

## Gaps

[none yet]
