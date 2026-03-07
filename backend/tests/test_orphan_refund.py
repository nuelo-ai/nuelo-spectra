"""Orphan refund job tests — Wave 0 stubs.

These tests are skipped until Wave 2 implements the orphan cleanup job in
backend/app/scheduler.py. The stubs let the test runner discover and report
them without import errors.
"""

import pytest


@pytest.mark.skip(reason="endpoint not yet implemented")
def test_orphan_refund_job():
    """Orphan job marks stuck runs failed and refunds credits."""
    pass
