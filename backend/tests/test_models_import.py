"""Smoke tests: all new Pulse workspace models importable from app.models."""


def test_collection_importable():
    """Collection model must be importable from app.models."""
    from app.models import Collection
    assert Collection.__tablename__ == "collections"


def test_collection_file_importable():
    """CollectionFile model must be importable from app.models."""
    from app.models import CollectionFile
    assert CollectionFile.__tablename__ == "collection_files"


def test_signal_importable():
    """Signal model must be importable from app.models."""
    from app.models import Signal
    assert Signal.__tablename__ == "signals"


def test_report_importable():
    """Report model must be importable from app.models."""
    from app.models import Report
    assert Report.__tablename__ == "reports"


def test_pulse_run_importable():
    """PulseRun model must be importable from app.models."""
    from app.models import PulseRun
    assert PulseRun.__tablename__ == "pulse_runs"


def test_pulse_run_files_importable():
    """pulse_run_files association table must be importable from app.models."""
    from app.models import pulse_run_files
    assert pulse_run_files.name == "pulse_run_files"


def test_no_tablename_collision():
    """CollectionFile tablename must not collide with File tablename."""
    from app.models import File, CollectionFile
    assert File.__tablename__ != CollectionFile.__tablename__
