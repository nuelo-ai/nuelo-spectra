"""TDD tests for ApiKeyService and generate_api_key()."""
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.api_key import ApiKeyService, generate_api_key


class TestGenerateApiKey:
    def test_full_key_starts_with_spe_prefix(self):
        full_key, _, _ = generate_api_key()
        assert full_key.startswith("spe_")

    def test_token_hash_is_sha256_of_full_key(self):
        full_key, _, token_hash = generate_api_key()
        expected = hashlib.sha256(full_key.encode()).hexdigest()
        assert token_hash == expected

    def test_token_hash_is_64_hex_chars(self):
        _, _, token_hash = generate_api_key()
        assert len(token_hash) == 64
        assert all(c in "0123456789abcdef" for c in token_hash)

    def test_key_prefix_is_first_12_chars_of_full_key(self):
        full_key, key_prefix, _ = generate_api_key()
        assert key_prefix == full_key[:12]

    def test_keys_are_unique(self):
        keys = {generate_api_key()[0] for _ in range(10)}
        assert len(keys) == 10


class TestApiKeyServiceAuthenticate:
    @pytest.mark.asyncio
    async def test_authenticate_valid_active_key_returns_user(self):
        mock_db = AsyncMock()
        mock_api_key = MagicMock()
        mock_api_key.user_id = uuid4()
        mock_api_key.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_db.execute.return_value = mock_result
        mock_user = MagicMock()

        with patch("app.services.api_key.get_user_by_id", return_value=mock_user):
            result = await ApiKeyService.authenticate(mock_db, "spe_validkey")

        assert result is mock_user

    @pytest.mark.asyncio
    async def test_authenticate_invalid_key_returns_none(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await ApiKeyService.authenticate(mock_db, "spe_invalidkey")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_updates_last_used_at(self):
        mock_db = AsyncMock()
        mock_api_key = MagicMock()
        mock_api_key.user_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_db.execute.return_value = mock_result

        with patch("app.services.api_key.get_user_by_id", return_value=MagicMock()):
            await ApiKeyService.authenticate(mock_db, "spe_somekey")

        assert mock_api_key.last_used_at is not None
        mock_db.flush.assert_awaited_once()


class TestApiKeyServiceRevoke:
    @pytest.mark.asyncio
    async def test_revoke_owned_key_returns_true(self):
        mock_db = AsyncMock()
        user_id = uuid4()
        key_id = uuid4()
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_db.execute.return_value = mock_result

        result = await ApiKeyService.revoke(mock_db, key_id, user_id)

        assert result is True
        assert mock_api_key.is_active is False
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revoke_not_owned_key_returns_false(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await ApiKeyService.revoke(mock_db, uuid4(), uuid4())
        assert result is False


class TestApiKeyServiceCreate:
    @pytest.mark.asyncio
    async def test_create_returns_record_and_raw_key(self):
        mock_db = AsyncMock()
        user_id = uuid4()

        record, raw_key = await ApiKeyService.create(
            mock_db, user_id, "Test Key", "A test key"
        )

        assert raw_key.startswith("spe_")
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()


class TestApiKeyServiceListForUser:
    @pytest.mark.asyncio
    async def test_list_for_user_returns_keys(self):
        mock_db = AsyncMock()
        user_id = uuid4()
        mock_key1 = MagicMock()
        mock_key2 = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key1, mock_key2]
        mock_db.execute.return_value = mock_result

        result = await ApiKeyService.list_for_user(mock_db, user_id)

        assert len(result) == 2
