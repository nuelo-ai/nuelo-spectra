# Phase 2: File Upload & Management - Research

**Researched:** 2026-02-02
**Domain:** FastAPI file upload, pandas validation, async file I/O, user-isolated storage
**Confidence:** HIGH

## Summary

This phase adds file upload and management capabilities to the existing FastAPI backend. Users need to upload Excel (.xlsx, .xls) and CSV files up to 50MB, with server-side validation using pandas, user-isolated storage with UUID filenames, and per-file chat history support. The database schema (Files, ChatMessages tables with foreign keys and cascade deletes) already exists from Phase 1's Alembic migration, so this phase focuses on the API layer, service layer, file storage, and validation logic.

The standard approach uses FastAPI's `UploadFile` with chunked streaming via `aiofiles` for non-blocking disk writes, pandas `read_csv`/`read_excel` for structural validation, and Starlette's `MultiPartParser` configuration for the 50MB size limit. The existing codebase patterns (router -> service -> SQLAlchemy async, `CurrentUser` dependency for auth, `DbSession` for database) should be followed exactly.

Key finding: Starlette (FastAPI's underlying framework) defaults to a 1MB max part/file size since version 0.115.2+. This MUST be overridden to 50MB+ at application startup, otherwise all uploads over 1MB will fail with a 400 error. This is the single most common gotcha for this phase.

**Primary recommendation:** Use chunked async file writes with aiofiles, override Starlette's MultiPartParser size limits at startup, validate files with pandas in a try/except wrapper, and store files in a `uploads/{user_id}/{uuid}.{ext}` directory structure.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI UploadFile | (bundled with FastAPI 0.115+) | Receive multipart file uploads | Built-in, spooled temp files, async methods |
| python-multipart | >= 0.0.18 | Parse multipart form data | Required by FastAPI for file uploads; included in `fastapi[standard]` |
| aiofiles | 25.1.0 | Async file I/O (write uploads to disk) | Prevents blocking event loop during disk writes; Apache2 licensed |
| pandas | >= 2.0 | Validate CSV/Excel file structure | Industry standard for tabular data; `read_csv`/`read_excel` catch corrupted files |
| openpyxl | >= 3.1 | Engine for pandas to read .xlsx files | Default pandas engine for .xlsx; required optional dependency |
| xlrd | >= 2.0 | Engine for pandas to read .xls (legacy) files | Only engine supporting legacy .xls format |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | (Python 3.12+) | Path manipulation & directory creation | All file path operations; safer than string concatenation |
| uuid (stdlib) | (Python 3.12+) | Generate UUID4 for stored filenames | Every file upload to prevent enumeration |
| shutil (stdlib) | (Python 3.12+) | File cleanup/removal on delete | When deleting uploaded files from disk |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| aiofiles | shutil.copyfileobj | Simpler but blocks event loop; bad for async FastAPI under load |
| Local disk storage | S3/MinIO | More scalable but adds infrastructure complexity; overkill for MVP |
| pandas validation | Manual CSV parsing | Lighter but misses encoding issues, corrupt Excel detection, data type inference |
| filetype (magic numbers) | python-magic | python-magic needs libmagic system dep; filetype is pure Python but less thorough. For CSV/Excel, extension + pandas validation is sufficient |

**Installation:**
```bash
pip install aiofiles pandas openpyxl xlrd
```

**Note:** `python-multipart` is already included via `fastapi[standard]` in pyproject.toml. No separate install needed.

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── routers/
│   │   ├── auth.py          # Existing
│   │   ├── health.py        # Existing
│   │   └── files.py         # NEW: File upload/list/delete endpoints
│   ├── schemas/
│   │   ├── auth.py          # Existing
│   │   ├── user.py          # Existing
│   │   └── file.py          # NEW: FileUploadResponse, FileListResponse, etc.
│   ├── services/
│   │   ├── auth.py          # Existing
│   │   ├── email.py         # Existing
│   │   └── file.py          # NEW: File storage, validation, CRUD logic
│   ├── models/              # Already complete from Phase 1
│   │   ├── file.py          # EXISTS: File model with relationships
│   │   └── chat_message.py  # EXISTS: ChatMessage model with file_id FK
│   ├── config.py            # Add UPLOAD_DIR, MAX_FILE_SIZE settings
│   └── main.py              # Add files router, MultiPartParser config
├── uploads/                  # NEW: File storage root (gitignored)
│   └── {user_id}/           # Per-user directories
│       └── {uuid}.{ext}     # UUID-named files
└── pyproject.toml            # Add aiofiles, pandas, openpyxl, xlrd
```

### Pattern 1: Starlette MultiPartParser Size Override
**What:** Override default 1MB file size limit at application startup
**When to use:** Always -- required for any upload over 1MB
**Example:**
```python
# Source: https://github.com/fastapi/fastapi/discussions/12943
# In main.py, BEFORE creating the FastAPI app or at module level:
from starlette.formparsers import MultiPartParser

# 50MB in bytes + small buffer for form overhead
MultiPartParser.max_file_size = 1024 * 1024 * 50  # 50 MB
MultiPartParser.max_part_size = 1024 * 1024 * 50  # 50 MB
```

### Pattern 2: Chunked Async File Write
**What:** Stream uploaded file to disk in chunks using aiofiles
**When to use:** All file uploads (prevents memory exhaustion and event loop blocking)
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/request-files/
# Combined with aiofiles best practice from PyPI docs
import aiofiles
from pathlib import Path
from uuid import uuid4

CHUNK_SIZE = 1024 * 1024  # 1MB chunks

async def save_upload_file(
    upload_file: UploadFile,
    destination: Path,
) -> int:
    """Save uploaded file to disk in chunks. Returns total bytes written."""
    total_size = 0
    async with aiofiles.open(destination, "wb") as out_file:
        while chunk := await upload_file.read(CHUNK_SIZE):
            await out_file.write(chunk)
            total_size += len(chunk)
    return total_size
```

### Pattern 3: File Validation with Pandas
**What:** Validate CSV/Excel files can be parsed by pandas before accepting
**When to use:** After saving file to disk, before creating DB record
**Example:**
```python
import pandas as pd
from pathlib import Path

async def validate_file_structure(file_path: Path, file_type: str) -> dict:
    """Validate file can be read by pandas. Returns metadata or raises."""
    try:
        if file_type == "csv":
            # nrows=5 for fast validation without reading entire file
            df = pd.read_csv(file_path, nrows=5)
        elif file_type in ("xlsx", "xls"):
            df = pd.read_excel(file_path, nrows=5)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return {
            "columns": list(df.columns),
            "row_count_sample": len(df),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
    except Exception as e:
        raise ValueError(f"File validation failed: {str(e)}")
```

### Pattern 4: User-Isolated File Storage
**What:** Store files in per-user directories with UUID filenames
**When to use:** All file uploads
**Example:**
```python
from pathlib import Path
from uuid import UUID, uuid4

def get_user_upload_dir(base_upload_dir: Path, user_id: UUID) -> Path:
    """Get or create user-specific upload directory."""
    user_dir = base_upload_dir / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def generate_stored_filename(original_filename: str) -> str:
    """Generate UUID-based filename preserving original extension."""
    ext = Path(original_filename).suffix.lower()  # .csv, .xlsx, .xls
    return f"{uuid4()}{ext}"
```

### Pattern 5: Endpoint with Auth + File Upload
**What:** Combine CurrentUser dependency with UploadFile parameter
**When to use:** All file endpoints requiring authentication
**Example:**
```python
# Source: FastAPI docs + existing auth pattern from Phase 1
from fastapi import APIRouter, UploadFile, HTTPException, status
from app.dependencies import CurrentUser, DbSession

router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession,
):
    """Upload a data file (CSV, Excel) for analysis."""
    # 1. Validate content type / extension
    # 2. Save to disk with chunked write
    # 3. Validate with pandas
    # 4. Create DB record
    # 5. Return metadata
    ...
```

### Anti-Patterns to Avoid
- **Reading entire file into memory with `await file.read()`:** For 50MB files this wastes memory. Use chunked reads instead.
- **Trusting `file.content_type` for validation:** Client-supplied MIME type can be spoofed. Validate using file extension AND pandas parsing instead.
- **Storing files with original filenames:** Allows path traversal attacks and filename collisions. Always use UUID filenames.
- **Not resetting file pointer with `await file.seek(0)`:** After reading the file for validation, the pointer is at the end. Must seek(0) before any subsequent read.
- **Synchronous file I/O in async endpoints:** Using `open()` or `shutil` blocks the event loop. Use `aiofiles` for all disk operations.
- **Forgetting to delete file from disk when DB record deletion succeeds:** Must clean up both DB record AND physical file on delete. Handle partial failures.
- **Not configuring MultiPartParser limits:** Default 1MB limit in Starlette will reject any file over 1MB with a 400 error. Must override before first request.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV/Excel parsing | Custom file parsers | pandas read_csv / read_excel | Handles encoding, malformed data, multiple sheet formats, data types |
| Excel .xlsx reading | Direct XML parsing | openpyxl (via pandas engine) | Excel format is complex zipped XML; many edge cases |
| Excel .xls reading | Binary format parser | xlrd (via pandas engine) | Legacy binary format is notoriously complex |
| Async file writes | Thread pool executor wrapper | aiofiles | Already wraps thread pool; well-tested; mirrors stdlib API |
| Multipart form parsing | Manual boundary parsing | python-multipart (via FastAPI) | RFC 2388 compliance, streaming, security handled |
| File size enforcement | Custom middleware counting bytes | Starlette MultiPartParser.max_file_size | Built into the framework; enforced at parse level |
| UUID generation | Custom random strings | Python stdlib uuid4() | Cryptographically random, 122 bits of entropy, standard format |

**Key insight:** File format parsing (especially Excel) is deceptively complex. Pandas + openpyxl/xlrd handle thousands of edge cases (encoding, formula cells, merged cells, date formats, corrupt headers) that a custom parser would miss. Use them for validation even if you only need to confirm "file is readable."

## Common Pitfalls

### Pitfall 1: Starlette Default File Size Limit (1MB)
**What goes wrong:** All uploads over 1MB fail with HTTP 400 "Part exceeded maximum size of 1024KB"
**Why it happens:** Starlette 0.115.2+ introduced default size limits for DoS protection. FastAPI inherits these. The default `max_file_size` and `max_part_size` are both 1024 * 1024 (1MB).
**How to avoid:** Set `MultiPartParser.max_file_size` and `MultiPartParser.max_part_size` at module level in main.py BEFORE the app processes any requests.
**Warning signs:** File uploads work in tests with small files but fail with real-world files.

### Pitfall 2: Pandas Blocking the Event Loop
**What goes wrong:** `pd.read_csv()` and `pd.read_excel()` are synchronous operations that block the async event loop, causing request timeouts under load.
**Why it happens:** Pandas does not have an async API. When called in an async endpoint, it blocks the event thread.
**How to avoid:** Either (a) use `asyncio.to_thread()` to run pandas validation in a thread pool, or (b) keep the endpoint as `async def` but wrap the pandas call: `await asyncio.to_thread(pd.read_csv, file_path, nrows=5)`. Using `nrows=5` limits the read to just enough rows to validate structure.
**Warning signs:** Upload endpoint latency spikes when multiple users upload simultaneously.

### Pitfall 3: Cascade Delete Not Cleaning Up Physical Files
**What goes wrong:** Deleting a File record cascades to ChatMessage records in the database, but the physical file remains on disk forever, slowly consuming storage.
**Why it happens:** SQLAlchemy cascade only handles database records. Disk cleanup must be explicit in application code.
**How to avoid:** In the delete service function: (1) get file path from DB record, (2) delete DB record (cascades to chat_messages), (3) delete physical file from disk. Use try/except for disk delete -- log warning but don't fail if file is already gone.
**Warning signs:** Disk usage grows monotonically even as users delete files.

### Pitfall 4: Missing File Extension Validation Before Pandas
**What goes wrong:** Attempting `pd.read_excel()` on a renamed .txt file causes confusing error messages. Or worse, a crafted file triggers unexpected pandas behavior.
**Why it happens:** Relying solely on pandas to reject invalid files gives poor error messages.
**How to avoid:** Validate file extension (`.csv`, `.xlsx`, `.xls`) from the original filename BEFORE writing to disk. This is a fast, cheap first check. Then validate with pandas AFTER writing.
**Warning signs:** Error messages to users are pandas tracebacks instead of clear "Unsupported file format" messages.

### Pitfall 5: Not Cleaning Up Saved File on Validation Failure
**What goes wrong:** File is saved to disk, pandas validation fails, but the orphaned file is never deleted.
**Why it happens:** Error path doesn't include file cleanup.
**How to avoid:** Use try/finally or try/except to delete the saved file if validation or DB insertion fails. Pattern: save file -> validate -> create DB record. If step 2 or 3 fails, delete file from step 1.
**Warning signs:** `uploads/` directory contains files not referenced by any database record.

### Pitfall 6: Async Session and Eager Loading for Cascade Deletes
**What goes wrong:** Calling `session.delete(file_obj)` in async context may not trigger cascade if relationships aren't loaded.
**Why it happens:** SQLAlchemy async sessions use lazy="noload" by default, so related objects aren't available for cascade logic.
**How to avoid:** For cascade deletes, rely on the database-level `ON DELETE CASCADE` (already configured in the migration) rather than SQLAlchemy ORM cascade. Use `await db.execute(delete(File).where(File.id == file_id, File.user_id == user_id))` for simpler, more reliable deletes. The DB foreign key cascade handles ChatMessage cleanup.
**Warning signs:** Deleting files leaves orphaned chat_messages in the database.

## Code Examples

Verified patterns from official sources and the existing codebase:

### File Upload Endpoint (Complete Pattern)
```python
# Source: FastAPI docs + existing Phase 1 patterns (dependencies.py, routers/auth.py)
from fastapi import APIRouter, UploadFile, HTTPException, status
from app.dependencies import CurrentUser, DbSession
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["Files"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession,
):
    """Upload a data file for analysis."""
    # Validate extension
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Delegate to service layer
    file_record = await FileService.upload_file(
        db=db,
        user_id=current_user.id,
        upload_file=file,
        file_extension=ext,
    )
    return FileUploadResponse.model_validate(file_record)
```

### File List Endpoint
```python
# Source: Existing Phase 1 pattern (routers/auth.py get_current_user_info)
@router.get("/", response_model=list[FileListItem])
async def list_files(
    current_user: CurrentUser,
    db: DbSession,
):
    """List all files for the current user."""
    files = await FileService.list_user_files(db, current_user.id)
    return [FileListItem.model_validate(f) for f in files]
```

### File Delete Endpoint
```python
@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a file and its associated chat history."""
    deleted = await FileService.delete_file(db, file_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
```

### Pydantic Schemas for File Responses
```python
# Source: Existing Phase 1 pattern (schemas/user.py UserResponse)
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class FileUploadResponse(BaseModel):
    """Response after successful file upload."""
    id: UUID
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileListItem(BaseModel):
    """File metadata for list display."""
    id: UUID
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Service Layer: Upload with Validation
```python
# Source: Existing Phase 1 pattern (services/auth.py)
import asyncio
import aiofiles
import pandas as pd
from pathlib import Path
from uuid import UUID, uuid4
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.file import File

CHUNK_SIZE = 1024 * 1024  # 1MB

class FileService:
    @staticmethod
    async def upload_file(
        db: AsyncSession,
        user_id: UUID,
        upload_file: UploadFile,
        file_extension: str,
    ) -> File:
        """Upload, validate, and persist a file."""
        settings = get_settings()
        upload_dir = Path(settings.upload_dir)

        # Create user directory
        user_dir = upload_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate UUID filename
        stored_filename = f"{uuid4()}{file_extension}"
        file_path = user_dir / stored_filename

        # Save file to disk in chunks
        total_size = 0
        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                while chunk := await upload_file.read(CHUNK_SIZE):
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File exceeds 50MB limit"
                        )
                    await out_file.write(chunk)

            # Validate file structure with pandas (in thread pool)
            file_type = file_extension.lstrip(".")
            await asyncio.to_thread(
                _validate_file, str(file_path), file_type
            )

            # Create database record
            file_record = File(
                user_id=user_id,
                original_filename=upload_file.filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_size=total_size,
                file_type=file_type,
            )
            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)
            return file_record

        except Exception:
            # Clean up saved file on any failure
            if file_path.exists():
                file_path.unlink()
            raise


def _validate_file(file_path: str, file_type: str) -> None:
    """Synchronous file validation (called via asyncio.to_thread)."""
    try:
        if file_type == "csv":
            pd.read_csv(file_path, nrows=5)
        elif file_type in ("xlsx", "xls"):
            pd.read_excel(file_path, nrows=5)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        raise ValueError(f"Invalid file: could not parse as {file_type}. {str(e)}")
```

### Settings Extension
```python
# Add to existing app/config.py Settings class:
class Settings(BaseSettings):
    # ... existing fields ...

    # File Upload
    upload_dir: str = "uploads"
    max_file_size_mb: int = 50
```

### Main.py MultiPartParser Configuration
```python
# Add to top of main.py, BEFORE FastAPI app creation:
from starlette.formparsers import MultiPartParser

# Override Starlette default 1MB limit for file uploads
MultiPartParser.max_file_size = 1024 * 1024 * 50  # 50MB
MultiPartParser.max_part_size = 1024 * 1024 * 50  # 50MB
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `shutil.copyfileobj` for file saves | `aiofiles` chunked writes | 2023+ (async-first FastAPI) | Non-blocking I/O, better concurrency |
| No default upload size limit | Starlette MultiPartParser 1MB default | Starlette 0.115.2+ (late 2024) | Must explicitly override for any uploads >1MB |
| `xlrd` for all Excel formats | `openpyxl` for .xlsx, `xlrd` only for .xls | xlrd 2.0 (2020) | xlrd dropped .xlsx support; openpyxl is now default |
| Synchronous pandas in async endpoints | `asyncio.to_thread()` wrapper | Python 3.9+ pattern | Prevents event loop blocking |
| `passlib` for password hashing | `pwdlib` (already in project) | 2024+ | passlib is abandoned; project already uses pwdlib |

**Deprecated/outdated:**
- `xlrd` for .xlsx files: xlrd >= 2.0 only supports .xls. Do NOT use xlrd for .xlsx -- openpyxl is the correct engine.
- `File(bytes)` parameter type: Reads entire file into memory. Use `UploadFile` instead for any non-trivial file size.
- `python-multipart` as separate install: Already bundled with `fastapi[standard]` since FastAPI 0.100+.

## Open Questions

Things that couldn't be fully resolved:

1. **Exact Starlette version in project with MultiPartParser defaults**
   - What we know: Starlette 0.115.2+ has 1MB defaults. FastAPI 0.115+ uses this Starlette version.
   - What's unclear: The exact Starlette version installed may vary with fastapi[standard] version pin.
   - Recommendation: Always set MultiPartParser limits explicitly regardless. It's a no-op if defaults are already higher but prevents breakage if they're lower.

2. **Whether to store file column metadata in the File record**
   - What we know: The File model has no column for storing parsed column names or data types.
   - What's unclear: Whether Phase 3 (chat/analysis) needs pre-stored column metadata or will re-parse files on demand.
   - Recommendation: Validate file structure on upload (to reject corrupted files) but don't persist column metadata yet. Phase 3 can add metadata storage if needed. Keeps Phase 2 simpler.

3. **Upload directory persistence in Docker**
   - What we know: PostgreSQL runs in Docker. The app may also run in Docker eventually.
   - What's unclear: Whether to use a Docker volume for uploads now or defer to production setup.
   - Recommendation: Use a local `uploads/` directory relative to project root for now. Add to `.gitignore`. Docker volume mapping can be added when containerizing the app.

## Sources

### Primary (HIGH confidence)
- [FastAPI Request Files docs](https://fastapi.tiangolo.com/tutorial/request-files/) - UploadFile API, python-multipart requirement, async methods
- [FastAPI UploadFile reference](https://fastapi.tiangolo.com/reference/uploadfile/) - UploadFile attributes and methods
- [pandas.read_excel() docs (2.3.3)](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html) - Engine selection logic, supported formats, parameters
- [aiofiles PyPI (25.1.0)](https://pypi.org/project/aiofiles/) - Current version, API, async file operations
- [Starlette MultiPartParser discussion](https://github.com/fastapi/fastapi/discussions/12943) - max_file_size and max_part_size configuration
- Existing codebase inspection - models/file.py, models/chat_message.py, dependencies.py, services/auth.py, alembic migration

### Secondary (MEDIUM confidence)
- [FastAPI file size limiting strategies](https://github.com/fastapi/fastapi/issues/362) - Community patterns for size enforcement
- [BetterStack FastAPI file upload guide](https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/) - Security best practices, UUID naming
- [FastAPI best practices GitHub](https://github.com/zhanymkanov/fastapi-best-practices) - Project structure patterns
- [FastAPI + async SQLAlchemy patterns](https://chaoticengineer.hashnode.dev/fastapi-sqlalchemy) - Service layer and cascade delete patterns

### Tertiary (LOW confidence)
- [Chunked file upload discussion](https://github.com/fastapi/fastapi/discussions/9828) - Large file upload approaches
- [aiofiles vs shutil discussion](https://github.com/fastapi/fastapi/discussions/9618) - Async vs sync file writes comparison

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official docs (FastAPI, pandas, aiofiles PyPI)
- Architecture: HIGH - Patterns derived from existing Phase 1 codebase + FastAPI official docs
- Pitfalls: HIGH - MultiPartParser limit verified via FastAPI GitHub discussion; cascade delete issue documented in SQLModel issue tracker
- Code examples: HIGH - Derived from existing codebase patterns (auth.py router/service/schema structure)

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (30 days - stable libraries, no fast-moving changes expected)
