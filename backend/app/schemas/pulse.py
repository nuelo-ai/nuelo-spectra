"""Pydantic schemas for Pulse Agent pipeline."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignalHypothesis(BaseModel):
    """Output from Pulse brain's hypothesis generation step."""

    title: str = Field(description="Business-language title, no statistical jargon")
    severity_hint: Literal["critical", "warning", "info"]
    category: str = Field(description="anomaly, trend, correlation, distribution")
    code_instructions: str = Field(
        description="Prescriptive: 'Calculate X, aggregate by Y, return Z as JSON'"
    )
    chart_hint: str = Field(description="What business story the chart should tell")


class HypothesisOutput(BaseModel):
    """Wrapper for structured output from hypothesis LLM call."""

    hypotheses: list[SignalHypothesis]


class CoderResult(BaseModel):
    """Expected JSON structure from sandbox stdout."""

    analysis_text: str = Field(description="Summary of what the code computed")
    statistical_evidence: dict = Field(
        description="Metrics dict with metric, context, benchmark, impact keys"
    )
    chart_data: dict | None = None
    chart_type: str | None = None


class BusinessFinding(BaseModel):
    """Output from interpretation LLM call."""

    title: str = Field(description="Business-language finding title")
    finding: str = Field(
        description="Business-language finding for leadership audience"
    )
    severity: Literal["critical", "warning", "info"]
    category: str
    evidence: "SignalEvidence"


class FindingsOutput(BaseModel):
    """Wrapper for batch interpretation."""

    findings: list[BusinessFinding]


class ChartInstruction(BaseModel):
    """Output from visualization LLM call."""

    chart_type: Literal["bar", "line", "scatter"]
    title: str
    description: str = Field(description="What business story the chart tells")
    code_instructions: str = Field(
        description="Prescriptive Plotly code generation instructions"
    )


class ReportOutput(BaseModel):
    """Output from report writer LLM call."""

    executive_summary: str
    content: str = Field(description="Full markdown report")


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


class SignalDetailResponse(BaseModel):
    """Response schema for a single Signal, serialized from the Signal ORM model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    severity: str
    category: str
    analysis: str | None
    evidence: dict | None
    chart_data: dict | None
    chart_type: str | None
    created_at: datetime


class PulseRunTriggerResponse(BaseModel):
    """202 response body returned when a Pulse detection run is triggered."""

    model_config = ConfigDict(from_attributes=True)

    pulse_run_id: UUID
    status: str
    credit_cost: float


class PulseRunDetailResponse(PulseRunResponse):
    """Extended response with signal count and full signal list."""

    signal_count: int
    signals: list[SignalDetailResponse] = []
