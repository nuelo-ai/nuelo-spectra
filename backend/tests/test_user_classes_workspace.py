"""Tests for ADMIN-01: workspace tier config in user_classes.yaml.

Covers tiers: free_trial, on_demand, standard, premium, internal.
"""

from app.services.user_class import get_user_classes, invalidate_cache


def test_workspace_access_exists_for_all_tiers():
    """All tiers must have workspace_access key."""
    invalidate_cache()
    classes = get_user_classes()
    expected_tiers = ["free_trial", "on_demand", "standard", "premium", "internal"]
    for tier in expected_tiers:
        assert tier in classes, f"Tier '{tier}' missing from user_classes.yaml"
        assert "workspace_access" in classes[tier], (
            f"Tier '{tier}' missing workspace_access key"
        )


def test_workspace_access_correct_values():
    """workspace_access boolean values must match specification."""
    invalidate_cache()
    classes = get_user_classes()
    expected = {
        "free_trial": True,
        "on_demand": True,
        "standard": True,
        "premium": True,
        "internal": True,
    }
    for tier, value in expected.items():
        assert classes[tier]["workspace_access"] is value, (
            f"Tier '{tier}' workspace_access should be {value}, "
            f"got {classes[tier]['workspace_access']}"
        )


def test_max_active_collections_exists_for_all_tiers():
    """All tiers must have max_active_collections key."""
    invalidate_cache()
    classes = get_user_classes()
    expected_tiers = ["free_trial", "on_demand", "standard", "premium", "internal"]
    for tier in expected_tiers:
        assert "max_active_collections" in classes[tier], (
            f"Tier '{tier}' missing max_active_collections key"
        )


def test_max_active_collections_correct_values():
    """max_active_collections integer values must match specification."""
    invalidate_cache()
    classes = get_user_classes()
    expected = {
        "free_trial": 1,
        "on_demand": 3,
        "standard": 5,
        "premium": -1,
        "internal": -1,
    }
    for tier, value in expected.items():
        assert classes[tier]["max_active_collections"] == value, (
            f"Tier '{tier}' max_active_collections should be {value}, "
            f"got {classes[tier]['max_active_collections']}"
        )
