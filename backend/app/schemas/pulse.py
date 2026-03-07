"""Pydantic schemas for Pulse Agent pipeline."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SignalEvidence(BaseModel):
    """Statistical evidence supporting a signal."""

    metric: str
    context: str
    benchmark: str
    impact: str


class SignalOutput(BaseModel):
    """A single signal candidate produced by the Pulse Agent."""

    id: str
    title: str
    severity: Literal["critical", "warning", "info"]
    category: str
    chartType: Literal["bar", "line", "scatter"]
    analysis_text: str
    statistical_evidence: SignalEvidence
    chart_data: dict | None = None


class PulseAgentOutput(BaseModel):
    """Top-level output from the Pulse Agent: a list of signals."""

    signals: list[SignalOutput]


class PulseRunCreate(BaseModel):
    """Request body for creating a new Pulse run."""

    file_ids: list[UUID]
    user_context: str | None = None


class PulseRunResponse(BaseModel):
    """Response schema for a Pulse run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collection_id: UUID
    status: str
    credit_cost: float
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class PulseRunDetailResponse(PulseRunResponse):
    """Extended response with signal count."""

    signal_count: int
