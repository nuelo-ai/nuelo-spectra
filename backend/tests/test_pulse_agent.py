"""Tests for Pulse Agent foundation: config, schemas, profiling."""

import pytest
import yaml
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock


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


# ---------------------------------------------------------------------------
# Task 2 tests: Profiling script, E2B wrapper, config loader
# ---------------------------------------------------------------------------


class TestProfilingScript:
    """Verify PROFILING_SCRIPT is valid Python."""

    def test_profiling_script_is_valid_python(self):
        """PROFILING_SCRIPT compiles without SyntaxError."""
        from app.agents.pulse_profiler import PROFILING_SCRIPT

        # Should not raise SyntaxError
        compile(PROFILING_SCRIPT, "<profiling_script>", "exec")

    def test_profiling_script_imports(self):
        """PROFILING_SCRIPT imports pandas, numpy, scipy."""
        from app.agents.pulse_profiler import PROFILING_SCRIPT

        assert "import pandas" in PROFILING_SCRIPT
        assert "import numpy" in PROFILING_SCRIPT
        assert "scipy" in PROFILING_SCRIPT


class TestProfileFilesInSandbox:
    """Verify profile_files_in_sandbox behavior."""

    def test_profile_files_skips_cached(self):
        """Files with deep_profile already set are skipped (E2B not called)."""
        from app.agents.pulse_profiler import profile_files_in_sandbox

        file_data = [
            {
                "file_id": "abc-123",
                "filename": "test.csv",
                "file_bytes": b"col1,col2\n1,2\n",
                "deep_profile": {"row_count": 1, "columns": ["col1", "col2"]},
            }
        ]

        mock_settings = MagicMock()
        mock_settings.pulse_sandbox_timeout_seconds = 300

        # Run async function
        with patch("app.agents.pulse_profiler.E2BSandboxRuntime") as mock_e2b:
            result = asyncio.get_event_loop().run_until_complete(
                profile_files_in_sandbox(file_data, mock_settings)
            )

        # E2B should NOT have been called
        mock_e2b.assert_not_called()
        # Should return the cached profile
        assert len(result) == 1
        assert result[0][0] == "abc-123"
        assert result[0][1]["row_count"] == 1


class TestLoadPulseConfig:
    """Verify load_pulse_config returns dict with expected structure."""

    def test_load_pulse_config(self):
        """load_pulse_config returns dict with thresholds and signals keys."""
        from app.agents.pulse_profiler import load_pulse_config

        # Clear cache
        load_pulse_config.cache_clear()
        config = load_pulse_config()

        assert isinstance(config, dict)
        assert "thresholds" in config
        assert "signals" in config
        assert config["thresholds"]["z_score_critical"] == 3.0
        assert config["signals"]["max_per_run"] == 8
