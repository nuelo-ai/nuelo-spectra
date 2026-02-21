# Phase 37: admin-seed-on-startup-and-mandatory-credentials - Research

**Researched:** 2026-02-21
**Domain:** Python startup validation, bash shell scripting, Pydantic settings, Docker entrypoint
**Confidence:** HIGH — all findings based on reading the actual codebase; no external libraries need researching

## Summary

Phase 37 closes a deployment safety gap: when `SPECTRA_MODE=dev` or `SPECTRA_MODE=admin`, the application currently boots without requiring `ADMIN_EMAIL` / `ADMIN_PASSWORD` to be set. An operator could accidentally deploy with these modes and then have no way to log into the admin panel. This phase adds two enforcement layers: (1) fail-fast validation at startup that refuses to boot if the required credentials are absent, and (2) automatic admin seeding in the Docker entrypoint so the admin user is always present after migrations.

The implementation is entirely internal — no new libraries are needed. All moving parts already exist in the codebase: `Settings` in `config.py` is the right place for validation logic, `docker-entrypoint.sh` is the right place for the seed call, the `seed_admin` service function already handles the idempotent upsert, and the CLI command already wraps it. The challenge is wiring these together correctly for all three deployment paths (manual `uv run`, `docker compose`, Dokploy/Dockerfile).

The `lru_cache` on `get_settings()` is a critical consideration: the cached instance is created once at import time in `main.py` (line 27), so any validator added to `Settings` via Pydantic's `model_validator` runs exactly once at startup — which is precisely the desired "fail fast" behavior. The `seed_admin` call in the entrypoint happens *after* `alembic upgrade head` and *before* `uvicorn` starts, so the user record exists before any request can be served.

**Primary recommendation:** Add a Pydantic `model_validator(mode="after")` on `Settings` that raises `ValueError` when `spectra_mode in ("dev", "admin")` and either `admin_email` or `admin_password` is empty. In `docker-entrypoint.sh`, add a conditional seed call after migrations using the venv Python. Update `.env.docker.example` to mark these fields as required. No new libraries or migration needed.

---

## Standard Stack

### Core (no new dependencies — all already in pyproject.toml)

| Component | Version in project | Purpose | Notes |
|-----------|-------------------|---------|-------|
| `pydantic-settings` | `>=2.0.0` | Settings class with env var loading | Already used; `model_validator` is the hook for startup validation |
| `click` | transitive (via `fastapi[standard]`) | CLI framework for `seed-admin` command | Already used in `backend/app/cli/__main__.py` |
| `bash` | system | docker-entrypoint.sh shell scripting | Already used; extend with seed call |
| `app.services.admin.auth.seed_admin` | in-codebase | Idempotent admin user upsert | Already exists and tested |

### No new packages required

This phase is pure configuration wiring and shell scripting. Do not add any new pip dependencies.

---

## Architecture Patterns

### Where Each Change Lives

```
backend/
├── app/
│   ├── config.py              # ADD: model_validator for ADMIN_EMAIL/ADMIN_PASSWORD requirement
│   └── cli/__main__.py        # READ-ONLY: already calls seed_admin correctly
├── docker-entrypoint.sh       # ADD: conditional seed-admin call after migrations
└── (no new files needed)
.env.docker.example            # EDIT: mark ADMIN_EMAIL/ADMIN_PASSWORD as REQUIRED
```

### Pattern 1: Pydantic model_validator for Fail-Fast Startup Validation

**What:** Use `@model_validator(mode="after")` on the `Settings` class to validate cross-field constraints. Pydantic v2 runs `mode="after"` validators after all individual fields are populated, so all env vars are already parsed when the validator fires.

**When to use:** When a constraint depends on the *combination* of two or more fields (e.g., "if field A has value X, field B must be non-empty").

**Critical detail:** `get_settings()` is decorated with `@lru_cache`, so `Settings()` is constructed exactly once. The validator fires at that construction point — which happens at module import time when `main.py` calls `get_settings()` at line 27. This means the process will refuse to start immediately, before any routes are registered.

**Example pattern (based on existing code style in config.py):**

```python
# Source: pydantic-settings v2 model_validator pattern
from pydantic import model_validator

class Settings(BaseSettings):
    # ... existing fields ...
    spectra_mode: str = "dev"
    admin_email: str = ""
    admin_password: str = ""

    @model_validator(mode="after")
    def validate_admin_credentials_for_admin_modes(self) -> "Settings":
        """Require ADMIN_EMAIL and ADMIN_PASSWORD when SPECTRA_MODE is dev or admin."""
        if self.spectra_mode in ("dev", "admin"):
            if not self.admin_email:
                raise ValueError(
                    "ADMIN_EMAIL is required when SPECTRA_MODE is 'dev' or 'admin'. "
                    "Set ADMIN_EMAIL in your .env file."
                )
            if not self.admin_password:
                raise ValueError(
                    "ADMIN_PASSWORD is required when SPECTRA_MODE is 'dev' or 'admin'. "
                    "Set ADMIN_PASSWORD in your .env file."
                )
        return self
```

**Startup behavior:** When validation fails, pydantic raises `ValidationError` → Python prints it and exits with non-zero code. uvicorn never starts. Docker container exits with error. Dokploy marks deployment as failed.

### Pattern 2: Conditional Seed Call in docker-entrypoint.sh

**What:** After the `alembic upgrade head` call, conditionally invoke the CLI seed command. "Conditional" on `ADMIN_EMAIL` being set — if it's empty, skip silently (this covers `SPECTRA_MODE=public` deployments where seeding is irrelevant).

**Why conditional, not always-run:** The public backend deployment does not set `ADMIN_EMAIL` (and the startup validator correctly doesn't require it for `public` mode). The entrypoint should not fail there.

**Example pattern (based on existing entrypoint style):**

```bash
# Source: existing docker-entrypoint.sh style
# --- Seed admin user (if ADMIN_EMAIL is set) ---
if [ -n "${ADMIN_EMAIL:-}" ]; then
    echo "[entrypoint] Seeding admin user (${ADMIN_EMAIL})..."
    /app/.venv/bin/python -m app.cli seed-admin
    echo "[entrypoint] Admin seed complete."
else
    echo "[entrypoint] ADMIN_EMAIL not set — skipping admin seed."
fi
```

**Placement:** Insert this block AFTER `alembic upgrade head` and BEFORE the `exec uvicorn ...` line. The seed function uses `async_session_maker` which connects to the same DB that Alembic just migrated — correct ordering ensures the schema exists before seed runs.

**Idempotency:** `seed_admin` in `app/services/admin/auth.py` already handles the upsert: if user exists it resets password and ensures `is_admin=True`; if user doesn't exist it creates it. Safe to call on every container restart.

### Pattern 3: .env.docker.example Required Fields Annotation

**What:** Update the comment on `ADMIN_EMAIL` and `ADMIN_PASSWORD` lines to clearly indicate they are REQUIRED for dev/admin modes, not optional.

**Current state (line 56-59 in .env.docker.example):**
```
# Admin Seed (optional — used by: uv run python -m app.cli seed-admin)
ADMIN_EMAIL=
ADMIN_PASSWORD=
```

**Target state:**
```
# Admin credentials (REQUIRED when SPECTRA_MODE=dev or SPECTRA_MODE=admin)
# The admin user is automatically seeded on startup when these are set.
# For SPECTRA_MODE=public, these can be left empty.
ADMIN_EMAIL=
ADMIN_PASSWORD=
```

### Pattern 4: Non-Docker Deployments (manual `uv run`)

**What:** For developers running `uv run uvicorn app.main:app` locally (not via Docker), the startup validator in `config.py` covers them. When `SPECTRA_MODE=dev` (the default) and `.env` doesn't have credentials, the app fails immediately with a clear message.

**No code needed here** beyond the `model_validator`. The developer then runs `uv run python -m app.cli seed-admin` manually after setting credentials — or they set `SPECTRA_MODE=public` to skip the requirement.

**Important:** This does NOT auto-seed for manual deployments. The additional context says "for non-Docker deployments via app startup validation". The validation (fail-fast) covers this — but auto-seeding on every uvicorn start would be dangerous for manual deployments (password reset on every restart). The `docker-entrypoint.sh` auto-seed is appropriate only for Docker because it runs once per container restart, gated by the immutable entrypoint script.

### Anti-Patterns to Avoid

- **Running seed in FastAPI lifespan:** Do NOT call `seed_admin` inside the `lifespan()` async context manager in `main.py`. This would run on every uvicorn restart in non-Docker deployments, resetting the admin password unexpectedly. Keep it in `docker-entrypoint.sh` for Docker, and as an explicit CLI command for manual deployments.
- **Checking mode at runtime instead of startup:** Do NOT add mode checks inside individual route handlers. The validator fires at startup — fail fast, not at first request.
- **Raising SystemExit instead of ValueError in model_validator:** Pydantic v2 expects validators to raise `ValueError` (or `ValidationError`). The CLI uses `SystemExit(1)` — that pattern is correct for Click commands but wrong for Pydantic validators.
- **Setting admin_email/admin_password as non-optional without defaults:** The current `str = ""` default is correct — it means Pydantic won't error on missing env vars by itself, and our explicit validator provides the clearer error message. Do not change the field type to `str` without default (that would cause a cryptic Pydantic error for `SPECTRA_MODE=public` deployments that legitimately don't set these vars).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Idempotent admin user creation | Custom INSERT ON CONFLICT | `seed_admin()` in `app/services/admin/auth.py` | Already exists, tested, handles all edge cases |
| Startup credential check | Custom startup code in lifespan | Pydantic `model_validator` on `Settings` | Runs before lifespan, better error messages, tested by pydantic |
| CLI invocation in bash | Inline Python in shell script | `python -m app.cli seed-admin` | CLI already exists with correct error handling |

**Key insight:** Everything needed for this phase already exists. The task is wiring, not building.

---

## Common Pitfalls

### Pitfall 1: lru_cache and ValidationError message swallowed

**What goes wrong:** `get_settings()` is cached. If `Settings()` raises `ValidationError`, the exception propagates up. In `main.py`, `settings = get_settings()` is at module level (line 27), so the error occurs during module import. Python will print the traceback, but Docker logs may not show it clearly.

**Why it happens:** The `ValidationError` from pydantic is verbose and multi-line. Docker container exits immediately with code 1. The message is in stderr.

**How to avoid:** The validator should produce a single clear message. Use `raise ValueError("ADMIN_EMAIL is required when SPECTRA_MODE is 'dev' or 'admin'. ...")` — pydantic wraps this in `ValidationError` but the inner message is visible in logs.

**Warning signs:** Container exits immediately (code 1) without printing "Starting Spectra in DEV mode". Check `docker logs <container>` for `ValidationError`.

### Pitfall 2: Seed called before migrations complete

**What goes wrong:** If the seed call in `docker-entrypoint.sh` runs before `alembic upgrade head`, the `users` table may not exist. `seed_admin` will throw `sqlalchemy.exc.ProgrammingError: relation "users" does not exist`.

**Why it happens:** Ordering mistake in the entrypoint script.

**How to avoid:** The seed block MUST come after the `alembic upgrade head` line and the success echo. Verify by reading the final entrypoint script top-to-bottom.

**Warning signs:** `ProgrammingError: relation "users" does not exist` in container logs.

### Pitfall 3: ADMIN_EMAIL empty string vs unset env var

**What goes wrong:** In bash, `${ADMIN_EMAIL:-}` evaluates to empty string both when the var is unset AND when it's set to `""`. The check `[ -n "${ADMIN_EMAIL:-}" ]` correctly handles both cases (empty string has zero length, so `-n` is false). This is the correct behavior.

**Why it happens:** In Python (`config.py`), `admin_email: str = ""` means if `ADMIN_EMAIL` is not in the environment, it defaults to `""`. The validator checks `if not self.admin_email:` which is `True` for both `""` and unset. Consistent.

**How to avoid:** Use `[ -n "${ADMIN_EMAIL:-}" ]` in bash (not `[ -z ... ]` which inverts it). Use `if not self.admin_email:` in Python.

### Pitfall 4: docker compose sets SPECTRA_MODE inline (bypasses .env.docker)

**What goes wrong:** `compose.yaml` sets `SPECTRA_MODE` and `DATABASE_URL` as inline `environment:` overrides (noted in `.env.docker.example` comment: "NOTE: DATABASE_URL and SPECTRA_MODE are set inline in compose.yaml"). An operator might set these vars in `.env.docker` thinking they take effect, but compose inline overrides win.

**Why it happens:** This is by design (see Phase 35-01 decision: "env_file for secrets with inline environment overrides for non-secret config").

**Impact for this phase:** When testing Docker Compose locally, `ADMIN_EMAIL` and `ADMIN_PASSWORD` must be in `.env.docker`. The validator will fire and require them because `SPECTRA_MODE=dev` is set inline in `compose.yaml`.

**How to avoid:** When testing, ensure `.env.docker` has non-empty `ADMIN_EMAIL` and `ADMIN_PASSWORD`. Document this in the env file comment.

### Pitfall 5: seed_admin resets password on every Docker container restart

**What goes wrong:** By design, `seed_admin` resets the hashed_password to the value from `ADMIN_PASSWORD` env var on every call. This means if an admin manually changed their password in the admin panel, a container restart will reset it.

**Why it happens:** The current `seed_admin` implementation always does `user.hashed_password = hash_password(password)` if user exists.

**Implication:** This is actually the intended behavior — the env var is the source of truth for the admin password. Operators should be aware: **changing admin password via the admin UI is not persistent across container restarts** if a different password is in the env var. Document this behavior clearly.

**How to avoid:** Accept this trade-off (env var = source of truth). Document in `.env.docker.example` that changing the password via UI will be reset on restart.

---

## Code Examples

### Pydantic model_validator (v2 syntax)

```python
# Source: pydantic-settings v2 — https://docs.pydantic.dev/latest/concepts/validators/#model-validators
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    spectra_mode: str = "dev"
    admin_email: str = ""
    admin_password: str = ""

    @model_validator(mode="after")
    def validate_admin_credentials_for_admin_modes(self) -> "Settings":
        if self.spectra_mode in ("dev", "admin"):
            missing = []
            if not self.admin_email:
                missing.append("ADMIN_EMAIL")
            if not self.admin_password:
                missing.append("ADMIN_PASSWORD")
            if missing:
                raise ValueError(
                    f"{', '.join(missing)} must be set when SPECTRA_MODE is "
                    f"'{self.spectra_mode}'. Add {'them' if len(missing) > 1 else 'it'} "
                    f"to your .env file and restart."
                )
        return self
```

### docker-entrypoint.sh seed block (to be inserted after migrations)

```bash
# --- Seed admin user (if ADMIN_EMAIL is set) ---
if [ -n "${ADMIN_EMAIL:-}" ]; then
    echo "[entrypoint] Seeding admin user (${ADMIN_EMAIL})..."
    /app/.venv/bin/python -m app.cli seed-admin
    echo "[entrypoint] Admin seed complete."
else
    echo "[entrypoint] ADMIN_EMAIL not set — skipping admin seed (public mode)."
fi
```

### Existing seed_admin function (already correct — no changes needed)

```python
# Source: backend/app/services/admin/auth.py
# Already idempotent: creates or updates, always sets is_admin=True
async def seed_admin(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.hashed_password = hash_password(password)
        user.is_admin = True
        if not user.first_name:
            user.first_name = first_name
        if not user.last_name:
            user.last_name = last_name
    else:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            ...
            is_admin=True,
        )
        db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

---

## Implementation Scope: All Three Deployment Methods

| Deployment Method | Validation (fail-fast) | Auto-seed | How |
|-------------------|----------------------|-----------|-----|
| `uv run uvicorn app.main:app` (manual) | YES — `model_validator` in `config.py` fires at startup | NO — manual: `uv run python -m app.cli seed-admin` | Startup error if missing; dev runs CLI once to seed |
| `docker compose up` | YES — `model_validator` fires when uvicorn starts | YES — `docker-entrypoint.sh` seeds after migrations | Both layers active |
| Dockerfile / Dokploy | YES — `model_validator` fires when uvicorn starts | YES — `docker-entrypoint.sh` seeds after migrations | Both layers active |

**Note for SPECTRA_MODE=public:** Both validation and seed are skipped. The validator only fires for `dev` and `admin` modes. The entrypoint seed is conditional on `ADMIN_EMAIL` being set. Public mode sets neither.

---

## Files to Change (Complete List)

| File | Change Type | What |
|------|------------|------|
| `backend/app/config.py` | Edit | Add `@model_validator(mode="after")` method to `Settings` class |
| `backend/docker-entrypoint.sh` | Edit | Add conditional `python -m app.cli seed-admin` block after migrations |
| `.env.docker.example` | Edit | Update `ADMIN_EMAIL` / `ADMIN_PASSWORD` comment from "optional" to "required for dev/admin" |

**Files NOT to change:**
- `backend/app/cli/__main__.py` — already correct
- `backend/app/services/admin/auth.py` — `seed_admin` is already idempotent and correct
- `backend/app/main.py` — mode validation already exists; do not add seed logic here

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No credential enforcement — admin_email/admin_password optional everywhere | Fail-fast validation for dev/admin modes | Phase 37 | Container refuses to start with clear message instead of booting with inaccessible admin |
| Manual `uv run python -m app.cli seed-admin` required after every deploy | Auto-seed in docker-entrypoint.sh | Phase 37 | Docker/Dokploy deployments always have admin user without manual step |
| `.env.docker.example` comments "optional" for ADMIN_EMAIL/ADMIN_PASSWORD | Comments updated to "required" for dev/admin | Phase 37 | Operator documentation matches enforcement behavior |

---

## Open Questions

1. **Should the validator also check SPECTRA_MODE validity?**
   - What we know: `main.py` already has `if mode not in ("public", "admin", "dev"): raise ValueError(...)` at module level
   - What's unclear: Should this be moved into the `model_validator` for cleaner centralization?
   - Recommendation: Leave the existing mode check in `main.py` as-is — it runs before lifespan, which is correct. The new validator is additive. Avoid refactoring existing working code.

2. **Should seed failure in entrypoint abort startup?**
   - What we know: `set -euo pipefail` is already in the entrypoint, so any Python exit code != 0 will abort the entrypoint
   - What's unclear: Is aborting startup on seed failure the right UX? (e.g., if DB connection fails during seed after successful migration)
   - Recommendation: Yes — abort. If seed fails, the admin user doesn't exist and the deployment is broken. Better to fail fast and let the orchestrator retry.

3. **First_name / last_name defaults for seeded admin**
   - What we know: `seed_admin` defaults to "Admin" / "User". `config.py` has `admin_first_name: str = "Admin"` and `admin_last_name: str = "User"`. The CLI already passes these.
   - What's unclear: Should the entrypoint-invoked seed use env var overrides for first/last name?
   - Recommendation: The CLI already reads `settings.admin_first_name` / `settings.admin_last_name` and passes them to `seed_admin`. Since the entrypoint calls `python -m app.cli seed-admin`, this is automatically handled — no change needed.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `backend/app/config.py` — Settings class, existing fields, lru_cache pattern
- Direct codebase inspection: `backend/app/main.py` — startup sequence, lifespan, mode validation
- Direct codebase inspection: `backend/docker-entrypoint.sh` — pg_isready + alembic + uvicorn pattern
- Direct codebase inspection: `backend/app/cli/__main__.py` — seed-admin CLI implementation
- Direct codebase inspection: `backend/app/services/admin/auth.py` — seed_admin idempotent upsert
- Direct codebase inspection: `.env.docker.example` — current env var documentation
- Direct codebase inspection: `backend/pyproject.toml` — pydantic-settings >=2.0.0 confirmed

### Secondary (MEDIUM confidence)
- pydantic-settings v2 `model_validator(mode="after")` pattern — well-established, matches project's existing pydantic-settings usage

---

## Metadata

**Confidence breakdown:**
- What needs to change: HIGH — all from direct codebase reading
- How to implement (model_validator): HIGH — pydantic-settings v2 is already in use, pattern is established
- How to implement (bash entrypoint): HIGH — extending existing shell script with known-working Python invocation
- Pitfalls: HIGH — identified from reading actual code and known bash/pydantic behavior

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable domain — pydantic-settings, bash; no fast-moving libraries involved)
