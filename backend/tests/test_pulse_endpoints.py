"""Pulse endpoint tests — Wave 0 stubs.

These tests are skipped until Wave 2 wires up the HTTP endpoints in
backend/app/routers/collections.py. The stubs let the test runner
discover and report them without import errors.
"""

import pytest


@pytest.mark.skip(reason="endpoint not yet implemented")
def test_trigger_pulse_202():
    """POST /collections/{id}/pulse returns 202 with pulse_run_id, status, credit_cost."""
    pass


@pytest.mark.skip(reason="endpoint not yet implemented")
def test_trigger_pulse_402():
    """POST with 0 credits returns 402 with 'required' and 'available' keys in body."""
    pass


@pytest.mark.skip(reason="endpoint not yet implemented")
def test_trigger_pulse_409():
    """POST with active run returns 409 with 'active_run_id' key in body."""
    pass


@pytest.mark.skip(reason="endpoint not yet implemented")
def test_poll_pulse_run():
    """GET /collections/{id}/pulse-runs/{run_id} returns a status field."""
    pass


@pytest.mark.skip(reason="endpoint not yet implemented")
def test_poll_pulse_run_completed():
    """GET returns signals list when status=completed."""
    pass
