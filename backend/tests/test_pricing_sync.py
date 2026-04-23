"""Tests for pricing_sync service."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Create a mock async DB session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def mock_stripe_client():
    """Create a mock Stripe client matching SubscriptionService._get_stripe_client()."""
    client = MagicMock()
    # Products
    mock_product = MagicMock()
    mock_product.id = "prod_test123"
    client.v1.products.create.return_value = mock_product
    # Prices
    mock_price = MagicMock()
    mock_price.id = "price_test123"
    client.v1.prices.create.return_value = mock_price
    client.v1.prices.update.return_value = MagicMock()
    return client


@pytest.fixture
def sample_tiers():
    """Sample tier config matching user_classes.yaml."""
    return {
        "free_trial": {"display_name": "Free Trial", "has_plan": False},
        "standard": {"display_name": "Standard", "has_plan": True, "price_cents": 2900},
        "premium": {"display_name": "Premium", "has_plan": True, "price_cents": 7900},
    }


@pytest.fixture
def sample_packages():
    """Sample credit packages matching user_classes.yaml."""
    return [
        {"name": "Starter Pack", "price_cents": 500, "credit_amount": 50, "display_order": 1},
        {"name": "Value Pack", "price_cents": 1500, "credit_amount": 200, "display_order": 2},
        {"name": "Pro Pack", "price_cents": 3500, "credit_amount": 500, "display_order": 3},
    ]


def _mock_scalar_none():
    """Return a mock result where scalar_one_or_none() returns None."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    return result


def _mock_scalar_existing(value=None):
    """Return a mock result where scalar_one_or_none() returns a row."""
    row = MagicMock()
    if value is not None:
        row.value = value
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    return result


# ---------------------------------------------------------------------------
# Test: YAML config shape (SUB-01, SUB-02, PKG-01)
# ---------------------------------------------------------------------------


def test_yaml_has_plan():
    """SUB-01: user_classes.yaml has has_plan flag per tier."""
    from app.services.user_class import get_user_classes

    tiers = get_user_classes()
    assert tiers["standard"]["has_plan"] is True
    assert tiers["free_trial"]["has_plan"] is False


def test_yaml_price_cents():
    """SUB-02: user_classes.yaml has price_cents per paid tier."""
    from app.services.user_class import get_user_classes

    tiers = get_user_classes()
    assert tiers["standard"]["price_cents"] == 2900
    assert tiers["premium"]["price_cents"] == 7900


def test_yaml_credit_packages():
    """PKG-01: user_classes.yaml has credit_packages list."""
    from app.services.user_class import get_credit_packages

    packages = get_credit_packages()
    assert isinstance(packages, list)
    assert len(packages) == 3
    names = [p["name"] for p in packages]
    assert "Starter Pack" in names
    assert "Value Pack" in names
    assert "Pro Pack" in names


# ---------------------------------------------------------------------------
# Test: Subscription seeding (SUB-03, SAFE-01)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.pricing_sync.upsert", new_callable=AsyncMock)
async def test_seed_subscription_pricing(mock_upsert, mock_db, sample_tiers):
    """SUB-03: Seeds subscription pricing to platform_settings on empty DB."""
    from app.services.pricing_sync import _seed_subscription_pricing

    # All DB queries return None (empty DB)
    mock_db.execute = AsyncMock(return_value=_mock_scalar_none())

    await _seed_subscription_pricing(mock_db, sample_tiers)

    # Should upsert price_cents and stripe_price keys for standard and premium
    upsert_keys = [c.args[1] for c in mock_upsert.call_args_list]
    assert "price_standard_monthly_cents" in upsert_keys
    assert "stripe_price_standard_monthly" in upsert_keys
    assert "price_premium_monthly_cents" in upsert_keys
    assert "stripe_price_premium_monthly" in upsert_keys

    # Verify values
    for c in mock_upsert.call_args_list:
        if c.args[1] == "price_standard_monthly_cents":
            assert c.args[2] == 2900
        if c.args[1] == "price_premium_monthly_cents":
            assert c.args[2] == 7900
        # All seeding uses admin_id=None
        assert c.kwargs.get("admin_id") is None or c.args[3] is None


@pytest.mark.asyncio
@patch("app.services.pricing_sync.upsert", new_callable=AsyncMock)
async def test_no_overwrite_existing(mock_upsert, mock_db, sample_tiers):
    """SAFE-01: Existing DB rows are never overwritten during seeding."""
    from app.services.pricing_sync import _seed_subscription_pricing

    # All DB queries return an existing row
    mock_db.execute = AsyncMock(return_value=_mock_scalar_existing(json.dumps(2900)))

    await _seed_subscription_pricing(mock_db, sample_tiers)

    # upsert should NOT have been called (all keys already exist)
    mock_upsert.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Credit package seeding (PKG-02, SAFE-01)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seed_credit_packages(mock_db, sample_packages):
    """PKG-02: Seeds credit packages to credit_packages table on empty DB."""
    from app.services.pricing_sync import _seed_credit_packages

    # All DB queries return None (no matching package)
    mock_db.execute = AsyncMock(return_value=_mock_scalar_none())

    await _seed_credit_packages(mock_db, sample_packages)

    # Should add 3 new packages
    assert mock_db.add.call_count == 3


@pytest.mark.asyncio
async def test_seed_credit_packages_idempotent(mock_db, sample_packages):
    """SAFE-01: Existing credit packages are not re-inserted."""
    from app.services.pricing_sync import _seed_credit_packages

    # All DB queries return an existing row
    mock_db.execute = AsyncMock(return_value=_mock_scalar_existing())

    await _seed_credit_packages(mock_db, sample_packages)

    # Should NOT add any packages
    mock_db.add.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Stripe sync (SUB-04, PKG-03, D-05)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.pricing_sync.upsert", new_callable=AsyncMock)
@patch("app.services.subscription.SubscriptionService._get_stripe_client")
async def test_stripe_sync_subscription(mock_get_client, mock_upsert, mock_db, mock_stripe_client, sample_tiers):
    """SUB-04: Creates Stripe Products/Prices for subscription tiers."""
    from app.services.pricing_sync import _sync_stripe_prices

    mock_get_client.return_value = mock_stripe_client

    # DB returns empty stripe_price_id
    mock_db.execute = AsyncMock(return_value=_mock_scalar_existing(json.dumps("")))

    await _sync_stripe_prices(mock_db, sample_tiers)

    # Should create products for standard and premium (not free_trial)
    assert mock_stripe_client.v1.products.create.call_count == 2

    # Verify recurring subscription pricing
    price_calls = mock_stripe_client.v1.prices.create.call_args_list
    assert len(price_calls) == 2
    for c in price_calls:
        params = c.kwargs.get("params", c.args[0] if c.args else {})
        assert params.get("recurring") == {"interval": "month"}

    # Should store price IDs via upsert
    assert mock_upsert.call_count == 2


@pytest.mark.asyncio
@patch("app.services.subscription.SubscriptionService._get_stripe_client")
async def test_stripe_sync_packages(mock_get_client, mock_db, mock_stripe_client):
    """PKG-03: Creates Stripe Products/Prices for credit packages (one-time, no recurring)."""
    from app.services.pricing_sync import _sync_stripe_packages

    mock_get_client.return_value = mock_stripe_client

    # Create mock packages with stripe_price_id=None
    pkg1 = MagicMock()
    pkg1.name = "Starter Pack"
    pkg1.price_cents = 500
    pkg1.credit_amount = 50
    pkg1.stripe_price_id = None

    pkg2 = MagicMock()
    pkg2.name = "Value Pack"
    pkg2.price_cents = 1500
    pkg2.credit_amount = 200
    pkg2.stripe_price_id = None

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [pkg1, pkg2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    mock_db.execute = AsyncMock(return_value=result_mock)

    await _sync_stripe_packages(mock_db)

    # Should create products
    assert mock_stripe_client.v1.products.create.call_count == 2

    # Prices should NOT have recurring (one-time purchase)
    price_calls = mock_stripe_client.v1.prices.create.call_args_list
    for c in price_calls:
        params = c.kwargs.get("params", c.args[0] if c.args else {})
        assert "recurring" not in params

    # stripe_price_id should be set
    assert pkg1.stripe_price_id == "price_test123"
    assert pkg2.stripe_price_id == "price_test123"


@pytest.mark.asyncio
@patch("app.services.pricing_sync.upsert", new_callable=AsyncMock)
@patch("app.services.subscription.SubscriptionService._get_stripe_client")
async def test_stripe_sync_graceful_failure(mock_get_client, mock_upsert, mock_db, sample_tiers):
    """D-05: Stripe failures are graceful -- logged but not raised."""
    from app.services.pricing_sync import _sync_stripe_prices

    mock_get_client.side_effect = Exception("Stripe error")

    # DB returns empty stripe_price_id
    mock_db.execute = AsyncMock(return_value=_mock_scalar_existing(json.dumps("")))

    # Should NOT raise
    await _sync_stripe_prices(mock_db, sample_tiers)

    # upsert should NOT have been called (Stripe failed before storing)
    mock_upsert.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Stripe readiness check (D-07)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.pricing_sync.get_user_classes")
@patch("app.services.pricing_sync.get_settings")
async def test_check_stripe_readiness_all_ready(mock_settings, mock_tiers, mock_db):
    """D-07: Returns ready=True when all Stripe Price IDs are configured."""
    from app.services.pricing_sync import check_stripe_readiness

    mock_settings.return_value.stripe_secret_key = "sk_test_123"
    mock_tiers.return_value = {
        "standard": {"has_plan": True},
        "premium": {"has_plan": True},
    }

    # Platform settings have stripe price IDs
    stripe_row = MagicMock()
    stripe_row.value = json.dumps("price_abc123")

    # Credit packages all have stripe_price_id
    pkg = MagicMock()
    pkg.stripe_price_id = "price_pkg123"
    pkg.name = "Starter"

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [pkg]

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Subscription tier checks
            result = MagicMock()
            result.scalar_one_or_none.return_value = stripe_row
            return result
        else:
            # Credit package check
            result = MagicMock()
            result.scalars.return_value = scalars_mock
            return result

    mock_db.execute = AsyncMock(side_effect=side_effect)

    result = await check_stripe_readiness(mock_db)
    assert result["ready"] is True
    assert result["missing"] == []


@pytest.mark.asyncio
@patch("app.services.pricing_sync.get_user_classes")
@patch("app.services.pricing_sync.get_settings")
async def test_check_stripe_readiness_missing(mock_settings, mock_tiers, mock_db):
    """D-07: Returns ready=False with details when Stripe Price IDs are missing."""
    from app.services.pricing_sync import check_stripe_readiness

    mock_settings.return_value.stripe_secret_key = "sk_test_123"
    mock_tiers.return_value = {
        "standard": {"has_plan": True},
    }

    # Platform settings: empty stripe price
    empty_row = MagicMock()
    empty_row.value = json.dumps("")

    # No credit packages
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            result = MagicMock()
            result.scalar_one_or_none.return_value = empty_row
            return result
        else:
            result = MagicMock()
            result.scalars.return_value = scalars_mock
            return result

    mock_db.execute = AsyncMock(side_effect=side_effect)

    result = await check_stripe_readiness(mock_db)
    assert result["ready"] is False
    assert any("standard" in m for m in result["missing"])


# ---------------------------------------------------------------------------
# Test: Mode guard (D-09)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.pricing_sync.invalidate_platform_cache")
@patch("app.services.pricing_sync.get_settings")
@patch("app.services.pricing_sync.get_credit_packages")
@patch("app.services.pricing_sync.get_user_classes")
@patch("app.services.pricing_sync._sync_stripe_packages", new_callable=AsyncMock)
@patch("app.services.pricing_sync._sync_stripe_prices", new_callable=AsyncMock)
@patch("app.services.pricing_sync._seed_credit_packages", new_callable=AsyncMock)
@patch("app.services.pricing_sync._seed_subscription_pricing", new_callable=AsyncMock)
async def test_spectra_mode_guard(
    mock_seed_sub, mock_seed_pkg, mock_sync_prices, mock_sync_pkgs,
    mock_tiers, mock_pkgs, mock_settings, mock_invalidate, mock_db,
):
    """D-09: Stripe sync is skipped in admin mode."""
    from app.services.pricing_sync import seed_pricing_from_config

    mock_tiers.return_value = {"standard": {"has_plan": True, "price_cents": 2900}}
    mock_pkgs.return_value = []
    mock_settings.return_value.spectra_mode = "admin"
    mock_settings.return_value.stripe_secret_key = "sk_test_123"

    await seed_pricing_from_config(mock_db)

    # DB seeding should run
    mock_seed_sub.assert_called_once()
    mock_seed_pkg.assert_called_once()

    # Stripe sync should NOT run (mode=admin)
    mock_sync_prices.assert_not_called()
    mock_sync_pkgs.assert_not_called()


# ---------------------------------------------------------------------------
# Test: monetization_enabled default (D-06)
# ---------------------------------------------------------------------------


def test_monetization_default_false():
    """D-06: monetization_enabled defaults to false on first startup."""
    from app.services.platform_settings import DEFAULTS

    assert DEFAULTS["monetization_enabled"] == json.dumps(False)
