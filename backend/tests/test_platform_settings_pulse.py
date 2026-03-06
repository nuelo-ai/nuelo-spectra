"""Tests for ADMIN-02: workspace_credit_cost_pulse platform setting."""

import json

from app.services.platform_settings import DEFAULTS, VALID_KEYS, validate_setting


def test_workspace_credit_cost_pulse_in_defaults():
    """workspace_credit_cost_pulse must be in DEFAULTS dict."""
    assert "workspace_credit_cost_pulse" in DEFAULTS


def test_workspace_credit_cost_pulse_default_value():
    """Default value must parse to '5.0' string."""
    raw = DEFAULTS["workspace_credit_cost_pulse"]
    parsed = json.loads(raw)
    assert parsed == "5.0", f"Expected '5.0', got {parsed!r}"


def test_workspace_credit_cost_pulse_in_valid_keys():
    """workspace_credit_cost_pulse must be in VALID_KEYS set."""
    assert "workspace_credit_cost_pulse" in VALID_KEYS


def test_validate_setting_valid_positive_float():
    """validate_setting should accept valid positive float."""
    result = validate_setting("workspace_credit_cost_pulse", 10.0)
    assert result is None, f"Expected None, got {result!r}"


def test_validate_setting_valid_small_float():
    """validate_setting should accept small positive float."""
    result = validate_setting("workspace_credit_cost_pulse", 0.5)
    assert result is None, f"Expected None, got {result!r}"


def test_validate_setting_negative_rejected():
    """validate_setting should reject negative values."""
    result = validate_setting("workspace_credit_cost_pulse", -1)
    assert isinstance(result, str), "Expected error string for negative value"


def test_validate_setting_zero_rejected():
    """validate_setting should reject zero."""
    result = validate_setting("workspace_credit_cost_pulse", 0)
    assert isinstance(result, str), "Expected error string for zero"


def test_validate_setting_string_rejected():
    """validate_setting should reject string values."""
    result = validate_setting("workspace_credit_cost_pulse", "abc")
    assert isinstance(result, str), "Expected error string for string value"


def test_validate_setting_bool_rejected():
    """validate_setting should reject boolean values."""
    result = validate_setting("workspace_credit_cost_pulse", True)
    assert isinstance(result, str), "Expected error string for boolean value"
