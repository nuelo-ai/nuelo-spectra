"""Tests for Phase 48 Plan 02: Collections router endpoints.

Tests cover:
- Workspace access gating (free tier 403, standard allowed)
- Collection CRUD (create, list, detail, update)
- Collection limit enforcement
- File operations (upload, link, duplicate link, remove)
- Report operations (list, detail, download)

All tests use unittest.mock — no database or live API required.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app.dependencies import require_workspace_access


# ============================================================================
# Helpers
# ============================================================================


def _make_mock_user(user_class: str = "standard", user_id=None):
    """Create a mock User object."""
    user = MagicMock()
    user.id = user_id or uuid4()
    user.user_class = user_class
    user.is_active = True
    return user


def _make_mock_collection(user_id=None, name="Test Collection", description=None):
    """Create a mock Collection object."""
    coll = MagicMock()
    coll.id = uuid4()
    coll.user_id = user_id or uuid4()
    coll.name = name
    coll.description = description
    coll.created_at = datetime.now(timezone.utc)
    coll.updated_at = datetime.now(timezone.utc)
    return coll


def _make_mock_file(user_id=None):
    """Create a mock File object."""
    f = MagicMock()
    f.id = uuid4()
    f.user_id = user_id or uuid4()
    f.original_filename = "test.csv"
    f.file_size = 1024
    f.data_summary = "10 rows, 3 columns"
    return f


def _make_mock_collection_file(collection_id=None, file_id=None):
    """Create a mock CollectionFile object."""
    cf = MagicMock()
    cf.id = uuid4()
    cf.collection_id = collection_id or uuid4()
    cf.file_id = file_id or uuid4()
    cf.added_at = datetime.now(timezone.utc)
    # Eagerly loaded file relationship
    cf.file = MagicMock()
    cf.file.original_filename = "test.csv"
    cf.file.file_size = 1024
    cf.file.data_summary = "10 rows, 3 columns"
    return cf


def _make_mock_report(collection_id=None, pulse_run_id=None):
    """Create a mock Report object."""
    r = MagicMock()
    r.id = uuid4()
    r.collection_id = collection_id or uuid4()
    r.title = "Detection Report"
    r.report_type = "pulse_detection"
    r.content = "# Report\n\nSome markdown content"
    r.created_at = datetime.now(timezone.utc)
    r.pulse_run_id = pulse_run_id or uuid4()
    return r


# ============================================================================
# Test Group 1: Workspace Access Gating
# ============================================================================


class TestWorkspaceAccessGating:
    """Test require_workspace_access dependency for tier-based access."""

    @pytest.mark.asyncio
    async def test_workspace_access_denied_free_tier(self):
        """Free tier user (workspace_access=False) should get 403."""
        user = _make_mock_user(user_class="free")

        with patch(
            "app.dependencies.get_class_config",
            return_value={"workspace_access": False, "max_active_collections": 0},
        ):
            with pytest.raises(HTTPException) as exc_info:
                await require_workspace_access(user)
            assert exc_info.value.status_code == 403
            assert "workspace access not available" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_workspace_access_allowed_standard(self):
        """Standard tier user (workspace_access=True) should be allowed."""
        user = _make_mock_user(user_class="standard")

        with patch(
            "app.dependencies.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": 5},
        ):
            result = await require_workspace_access(user)
            assert result == user


# ============================================================================
# Test Group 2: Collection CRUD
# ============================================================================


class TestCollectionCRUD:
    """Test collection create, list, detail, and update endpoints."""

    @pytest.mark.asyncio
    async def test_create_collection_success(self):
        """POST /collections should return 201 with correct JSON shape."""
        from app.routers.collections import create_collection
        from app.schemas.collection import CollectionCreate

        user = _make_mock_user()
        mock_db = AsyncMock()
        mock_collection = _make_mock_collection(user_id=user.id, name="My Collection")

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"max_active_collections": 5},
        ), patch(
            "app.routers.collections.CollectionService.count_user_collections",
            new_callable=AsyncMock,
            return_value=2,
        ), patch(
            "app.routers.collections.CollectionService.create_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ):
            body = CollectionCreate(name="My Collection")
            result = await create_collection(body, user, mock_db)

            assert result.id == mock_collection.id
            assert result.name == "My Collection"
            assert result.file_count == 0
            assert result.signal_count == 0
            assert result.report_count == 0

    @pytest.mark.asyncio
    async def test_create_collection_limit_reached(self):
        """POST /collections at max limit should return 403."""
        from app.routers.collections import create_collection
        from app.schemas.collection import CollectionCreate

        user = _make_mock_user()
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"max_active_collections": 5},
        ), patch(
            "app.routers.collections.CollectionService.count_user_collections",
            new_callable=AsyncMock,
            return_value=5,
        ):
            body = CollectionCreate(name="Over Limit")
            with pytest.raises(HTTPException) as exc_info:
                await create_collection(body, user, mock_db)
            assert exc_info.value.status_code == 403
            assert "Collection limit reached" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_collection_unlimited(self):
        """POST /collections with max_active_collections=-1 should always succeed."""
        from app.routers.collections import create_collection
        from app.schemas.collection import CollectionCreate

        user = _make_mock_user(user_class="premium")
        mock_db = AsyncMock()
        mock_collection = _make_mock_collection(user_id=user.id, name="Unlimited")

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"max_active_collections": -1},
        ), patch(
            "app.routers.collections.CollectionService.create_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ):
            body = CollectionCreate(name="Unlimited")
            result = await create_collection(body, user, mock_db)
            assert result.name == "Unlimited"

    @pytest.mark.asyncio
    async def test_list_collections(self):
        """GET /collections should return list with file_count/signal_count."""
        from app.routers.collections import list_collections

        user = _make_mock_user()
        mock_db = AsyncMock()
        coll1 = _make_mock_collection(user_id=user.id, name="Collection 1")
        coll2 = _make_mock_collection(user_id=user.id, name="Collection 2")

        with patch(
            "app.routers.collections.CollectionService.list_user_collections",
            new_callable=AsyncMock,
            return_value=[
                {"collection": coll1, "file_count": 3, "signal_count": 5},
                {"collection": coll2, "file_count": 1, "signal_count": 0},
            ],
        ):
            result = await list_collections(user, mock_db)
            assert len(result) == 2
            assert result[0].name == "Collection 1"
            assert result[0].file_count == 3
            assert result[0].signal_count == 5
            assert result[1].file_count == 1

    @pytest.mark.asyncio
    async def test_get_collection_detail(self):
        """GET /collections/{id} should return detail with all counts."""
        from app.routers.collections import get_collection

        user = _make_mock_user()
        mock_db = AsyncMock()
        coll = _make_mock_collection(user_id=user.id)

        with patch(
            "app.routers.collections.CollectionService.get_collection_detail",
            new_callable=AsyncMock,
            return_value={
                "collection": coll,
                "file_count": 2,
                "signal_count": 7,
                "report_count": 1,
            },
        ):
            result = await get_collection(coll.id, user, mock_db)
            assert result.file_count == 2
            assert result.signal_count == 7
            assert result.report_count == 1

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self):
        """GET /collections/{id} for nonexistent should return 404."""
        from app.routers.collections import get_collection

        user = _make_mock_user()
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.get_collection_detail",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_collection(uuid4(), user, mock_db)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_collection(self):
        """PATCH /collections/{id} should return updated detail."""
        from app.routers.collections import update_collection
        from app.schemas.collection import CollectionUpdate

        user = _make_mock_user()
        mock_db = AsyncMock()
        coll = _make_mock_collection(user_id=user.id, name="Updated Name")

        with patch(
            "app.routers.collections.CollectionService.update_collection",
            new_callable=AsyncMock,
            return_value=coll,
        ), patch(
            "app.routers.collections.CollectionService.get_collection_detail",
            new_callable=AsyncMock,
            return_value={
                "collection": coll,
                "file_count": 2,
                "signal_count": 3,
                "report_count": 0,
            },
        ):
            body = CollectionUpdate(name="Updated Name")
            result = await update_collection(coll.id, body, user, mock_db)
            assert result.name == "Updated Name"
            assert result.file_count == 2


# ============================================================================
# Test Group 3: File Operations
# ============================================================================


class TestFileOperations:
    """Test file upload, link, list, and remove endpoints."""

    @pytest.mark.asyncio
    async def test_upload_file_to_collection(self):
        """POST /collections/{id}/files should return 201 with file info."""
        from app.routers.collections import upload_file_to_collection

        user = _make_mock_user()
        mock_db = AsyncMock()
        coll = _make_mock_collection(user_id=user.id)
        file_record = _make_mock_file(user_id=user.id)
        cf = _make_mock_collection_file(collection_id=coll.id, file_id=file_record.id)

        mock_upload = MagicMock()
        mock_upload.filename = "data.csv"

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=coll,
        ), patch(
            "app.routers.collections.FileService.upload_file",
            new_callable=AsyncMock,
            return_value=file_record,
        ), patch(
            "app.routers.collections.CollectionService.add_file_to_collection",
            new_callable=AsyncMock,
            return_value=cf,
        ), patch(
            "app.routers.collections.asyncio.create_task",
        ):
            result = await upload_file_to_collection(coll.id, mock_upload, user, mock_db)
            assert result.file_id == file_record.id
            assert result.filename == file_record.original_filename

    @pytest.mark.asyncio
    async def test_link_file_to_collection(self):
        """POST /collections/{id}/files/link should return 201."""
        from app.routers.collections import link_file_to_collection
        from app.schemas.collection import FileLinkRequest

        user = _make_mock_user()
        mock_db = AsyncMock()
        coll = _make_mock_collection(user_id=user.id)
        file_record = _make_mock_file(user_id=user.id)
        cf = _make_mock_collection_file(collection_id=coll.id, file_id=file_record.id)

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=coll,
        ), patch(
            "app.routers.collections.FileService.get_user_file",
            new_callable=AsyncMock,
            return_value=file_record,
        ), patch(
            "app.routers.collections.CollectionService.get_collection_file",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "app.routers.collections.CollectionService.add_file_to_collection",
            new_callable=AsyncMock,
            return_value=cf,
        ):
            body = FileLinkRequest(file_id=file_record.id)
            result = await link_file_to_collection(coll.id, body, user, mock_db)
            assert result.file_id == file_record.id

    @pytest.mark.asyncio
    async def test_link_file_duplicate(self):
        """POST /collections/{id}/files/link for duplicate should return 409."""
        from app.routers.collections import link_file_to_collection
        from app.schemas.collection import FileLinkRequest

        user = _make_mock_user()
        mock_db = AsyncMock()
        coll = _make_mock_collection(user_id=user.id)
        file_record = _make_mock_file(user_id=user.id)
        existing_cf = _make_mock_collection_file(collection_id=coll.id, file_id=file_record.id)

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=coll,
        ), patch(
            "app.routers.collections.FileService.get_user_file",
            new_callable=AsyncMock,
            return_value=file_record,
        ), patch(
            "app.routers.collections.CollectionService.get_collection_file",
            new_callable=AsyncMock,
            return_value=existing_cf,
        ):
            body = FileLinkRequest(file_id=file_record.id)
            with pytest.raises(HTTPException) as exc_info:
                await link_file_to_collection(coll.id, body, user, mock_db)
            assert exc_info.value.status_code == 409
            assert "already linked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_remove_file_from_collection(self):
        """DELETE /collections/{id}/files/{file_id} should return 204."""
        from app.routers.collections import remove_file_from_collection

        user = _make_mock_user()
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.remove_file_from_collection",
            new_callable=AsyncMock,
            return_value=True,
        ):
            # Should not raise
            await remove_file_from_collection(uuid4(), uuid4(), user, mock_db)

    @pytest.mark.asyncio
    async def test_remove_file_not_found(self):
        """DELETE /collections/{id}/files/{file_id} for nonexistent returns 404."""
        from app.routers.collections import remove_file_from_collection

        user = _make_mock_user()
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.remove_file_from_collection",
            new_callable=AsyncMock,
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await remove_file_from_collection(uuid4(), uuid4(), user, mock_db)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_collection_files(self):
        """GET /collections/{id}/files should return files with data_summary."""
        from app.routers.collections import list_collection_files

        user = _make_mock_user()
        mock_db = AsyncMock()
        cf1 = _make_mock_collection_file()
        cf2 = _make_mock_collection_file()

        with patch(
            "app.routers.collections.CollectionService.list_collection_files",
            new_callable=AsyncMock,
            return_value=[cf1, cf2],
        ):
            result = await list_collection_files(uuid4(), user, mock_db)
            assert len(result) == 2
            assert result[0].filename == "test.csv"
            assert result[0].data_summary == "10 rows, 3 columns"


# ============================================================================
# Test Group 4: Report Operations
# ============================================================================


class TestReportOperations:
    """Test report list, detail, and download endpoints."""

    @pytest.mark.asyncio
    async def test_list_reports(self):
        """GET /collections/{id}/reports should return metadata list."""
        from app.routers.collections import list_collection_reports

        user = _make_mock_user()
        mock_db = AsyncMock()
        r1 = _make_mock_report()
        r2 = _make_mock_report()

        with patch(
            "app.routers.collections.CollectionService.list_collection_reports",
            new_callable=AsyncMock,
            return_value=[r1, r2],
        ):
            result = await list_collection_reports(uuid4(), user, mock_db)
            assert len(result) == 2
            assert result[0].title == "Detection Report"
            assert result[0].report_type == "pulse_detection"
            # List items should NOT have content field
            assert not hasattr(result[0], "content")

    @pytest.mark.asyncio
    async def test_report_detail(self):
        """GET /collections/{id}/reports/{report_id} should return content + signal_count."""
        from app.routers.collections import get_report_detail

        user = _make_mock_user()
        mock_db = AsyncMock()
        report = _make_mock_report()

        with patch(
            "app.routers.collections.CollectionService.get_report",
            new_callable=AsyncMock,
            return_value={"report": report, "signal_count": 5},
        ):
            result = await get_report_detail(uuid4(), report.id, user, mock_db)
            assert result.content == "# Report\n\nSome markdown content"
            assert result.signal_count == 5
            assert result.title == "Detection Report"

    @pytest.mark.asyncio
    async def test_report_detail_not_found(self):
        """GET /collections/{id}/reports/{report_id} for nonexistent returns 404."""
        from app.routers.collections import get_report_detail

        user = _make_mock_user()
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.get_report",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_report_detail(uuid4(), uuid4(), user, mock_db)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_download_report(self):
        """GET /collections/{id}/reports/{report_id}/download should have Content-Disposition."""
        from app.routers.collections import download_report

        user = _make_mock_user()
        mock_db = AsyncMock()
        report = _make_mock_report()

        with patch(
            "app.routers.collections.CollectionService.get_report_for_download",
            new_callable=AsyncMock,
            return_value=report,
        ):
            result = await download_report(uuid4(), report.id, user, mock_db)
            assert result.media_type == "text/markdown"
            assert "Content-Disposition" in result.headers
            assert "attachment" in result.headers["Content-Disposition"]
            assert "Detection_Report.md" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_download_report_not_found(self):
        """GET /collections/{id}/reports/{report_id}/download for nonexistent returns 404."""
        from app.routers.collections import download_report

        user = _make_mock_user()
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.get_report_for_download",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await download_report(uuid4(), uuid4(), user, mock_db)
            assert exc_info.value.status_code == 404
