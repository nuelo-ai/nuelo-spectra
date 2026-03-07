"""Tests for Pulse Agent foundation: config, schemas, profiling."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Task 1 tests: Config, Schemas, YAML config, prompts entry
# ---------------------------------------------------------------------------


class TestPulseTimeoutConfig:
    """Verify PULSE_SANDBOX_TIMEOUT_SECONDS setting."""

    def test_pulse_timeout_config(self):
        """Settings has pulse_sandbox_timeout_seconds=300, distinct from sandbox_timeout_seconds=60."""
        with patch.dict("os.environ", {
            "DATABASE_URL": "sqlite:///test.db",
            "SECRET_KEY": "test-secret",
            "ADMIN_EMAIL": "admin@test.com",
            "ADMIN_PASSWORD": "testpass123",
        }):
            from app.config import Settings
            s = Settings()
            assert s.pulse_sandbox_timeout_seconds == 300
            assert s.sandbox_timeout_seconds == 60
            assert s.pulse_sandbox_timeout_seconds != s.sandbox_timeout_seconds


class TestPydanticSchemas:
    """Verify PulseAgentOutput / SignalOutput / SignalEvidence validation."""

    def test_pydantic_validation(self):
        """Valid SignalOutput passes Pydantic validation."""
        from app.schemas.pulse import SignalOutput, SignalEvidence, PulseAgentOutput

        evidence = SignalEvidence(
            metric="z-score = 4.2",
            context="Revenue column",
            benchmark="Industry average",
            impact="High revenue volatility",
        )
        signal = SignalOutput(
            id="sig-001",
            title="Revenue Spike Detected",
            severity="critical",
            category="anomaly",
            chartType="bar",
            analysis_text="Significant revenue spike in Q4.",
            statistical_evidence=evidence,
            chart_data=None,
        )
        output = PulseAgentOutput(signals=[signal])
        assert len(output.signals) == 1
        assert output.signals[0].severity == "critical"

    def test_pydantic_rejects_invalid_severity(self):
        """SignalOutput rejects severity='Critical' (wrong case)."""
        from app.schemas.pulse import SignalOutput, SignalEvidence

        evidence = SignalEvidence(
            metric="z=3", context="col", benchmark="avg", impact="high"
        )
        with pytest.raises(Exception):  # ValidationError
            SignalOutput(
                id="sig-001",
                title="Test",
                severity="Critical",  # wrong case
                category="anomaly",
                chartType="bar",
                analysis_text="test",
                statistical_evidence=evidence,
            )

    def test_pydantic_rejects_invalid_chart_type(self):
        """SignalOutput rejects chartType='pie' (invalid literal)."""
        from app.schemas.pulse import SignalOutput, SignalEvidence

        evidence = SignalEvidence(
            metric="z=3", context="col", benchmark="avg", impact="high"
        )
        with pytest.raises(Exception):  # ValidationError
            SignalOutput(
                id="sig-001",
                title="Test",
                severity="info",
                category="anomaly",
                chartType="pie",  # invalid
                analysis_text="test",
                statistical_evidence=evidence,
            )

    def test_pydantic_case_normalization(self):
        """Show that .lower() fixes case issues for severity."""
        from app.schemas.pulse import SignalOutput, SignalEvidence

        evidence = SignalEvidence(
            metric="z=3", context="col", benchmark="avg", impact="high"
        )
        # This should work because .lower() normalizes "Critical" -> "critical"
        signal = SignalOutput(
            id="sig-001",
            title="Test",
            severity="Critical".lower(),
            category="anomaly",
            chartType="bar",
            analysis_text="test",
            statistical_evidence=evidence,
        )
        assert signal.severity == "critical"


class TestPulseConfigYaml:
    """Verify pulse_config.yaml loads with expected keys."""

    def test_pulse_config_yaml_loads(self):
        """pulse_config.yaml loads with expected keys."""
        config_path = Path(__file__).parent.parent / "app" / "config" / "pulse_config.yaml"
        assert config_path.exists(), f"pulse_config.yaml not found at {config_path}"

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert "thresholds" in config
        assert "signals" in config
        thresholds = config["thresholds"]
        assert "z_score_critical" in thresholds
        assert "z_score_warning" in thresholds
        assert "p_value_threshold" in thresholds
        assert "correlation_strong" in thresholds
        assert config["signals"]["max_per_run"] == 8


class TestPulseAgentPromptsEntry:
    """Verify pulse_agent entry in prompts.yaml."""

    def test_pulse_agent_prompts_entry(self):
        """pulse_agent entry exists in prompts.yaml with required fields."""
        from app.agents.config import load_prompts

        # Clear cache to pick up new entry
        load_prompts.cache_clear()
        prompts = load_prompts()

        assert "pulse_agent" in prompts["agents"], "pulse_agent not in prompts.yaml"
        agent = prompts["agents"]["pulse_agent"]
        assert "provider" in agent
        assert "model" in agent
        assert "temperature" in agent
        assert "max_tokens" in agent
        assert "system_prompt" in agent
        assert agent["provider"] == "anthropic"
        assert agent["temperature"] == 0.3
        assert agent["max_tokens"] == 8000
