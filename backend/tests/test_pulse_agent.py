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


# ---------------------------------------------------------------------------
# Plan 02 Task 1 tests: LangGraph Pulse Agent pipeline
# ---------------------------------------------------------------------------

import json


def _make_signal_output_dict(idx: int = 1) -> dict:
    """Helper to build a valid SignalOutput dict."""
    return {
        "id": f"sig-{idx:03d}",
        "title": f"Test Signal {idx}",
        "severity": "warning",
        "category": "anomaly",
        "chartType": "bar",
        "analysis_text": f"Analysis text for signal {idx}.",
        "statistical_evidence": {
            "metric": "z-score = 2.5",
            "context": "Revenue column",
            "benchmark": "Industry average",
            "impact": "Moderate impact",
        },
        "chart_data": None,
    }


class TestBuildPulseGraph:
    """Verify build_pulse_graph returns a compiled LangGraph."""

    def test_build_pulse_graph_returns_compiled(self):
        """build_pulse_graph() returns a compiled LangGraph that has an ainvoke method."""
        from app.agents.pulse import build_pulse_graph

        graph = build_pulse_graph()
        assert hasattr(graph, "ainvoke"), "Compiled graph must have ainvoke method"


class TestProfileDataNode:
    """Verify profile_data_node calls profiler and returns file_profiles."""

    def test_profile_data_node_calls_profiler(self):
        """profile_data_node calls profile_files_in_sandbox with file_data."""
        from app.agents.pulse import profile_data_node

        mock_profiles = [("file-1", {"row_count": 100, "columns": ["a", "b"]})]

        state = {
            "collection_id": "col-1",
            "user_id": "user-1",
            "pulse_run_id": "run-1",
            "user_context": "",
            "file_data": [
                {"file_id": "file-1", "filename": "test.csv", "file_bytes": b"a,b\n1,2\n", "deep_profile": None}
            ],
            "file_profiles": [],
            "signal_candidates": [],
            "validated_signals": [],
            "signals_output": [],
            "report_content": "",
            "error": "",
        }

        with patch("app.agents.pulse.profile_files_in_sandbox", new_callable=AsyncMock, return_value=mock_profiles):
            with patch("app.agents.pulse.get_settings"):
                result = asyncio.get_event_loop().run_until_complete(
                    profile_data_node(state)
                )

        assert "file_profiles" in result
        assert len(result["file_profiles"]) == 1

    def test_profile_data_node_handles_error(self):
        """profile_data_node returns error on profiler failure."""
        from app.agents.pulse import profile_data_node

        state = {
            "collection_id": "col-1",
            "user_id": "user-1",
            "pulse_run_id": "run-1",
            "user_context": "",
            "file_data": [{"file_id": "file-1", "filename": "test.csv", "file_bytes": b"", "deep_profile": None}],
            "file_profiles": [],
            "signal_candidates": [],
            "validated_signals": [],
            "signals_output": [],
            "report_content": "",
            "error": "",
        }

        with patch("app.agents.pulse.profile_files_in_sandbox", new_callable=AsyncMock, side_effect=Exception("E2B timeout")):
            with patch("app.agents.pulse.get_settings"):
                result = asyncio.get_event_loop().run_until_complete(
                    profile_data_node(state)
                )

        assert result["error"] != ""
        assert result["file_profiles"] == []


class TestRunAnalysesNode:
    """Verify run_analyses_node produces validated_signals."""

    def test_run_analyses_node_produces_validated_signals(self):
        """run_analyses_node with mocked LLM and coding_agent produces validated_signals."""
        from app.agents.pulse import run_analyses_node

        # LLM returns JSON array of candidates
        candidates_json = json.dumps([
            {
                "title": "Revenue Spike",
                "severity_hint": "critical",
                "category": "anomaly",
                "code_instructions": "Compute z-scores for revenue column",
                "chart_hint": "bar chart of monthly revenue",
            }
        ])

        mock_llm_response = MagicMock()
        mock_llm_response.content = candidates_json

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

        # Mock validation result (sandbox execution)
        mock_sandbox_result = {
            "analysis_text": "Revenue z-score is 4.2",
            "statistical_evidence": {
                "metric": "z-score = 4.2",
                "context": "Revenue column Q4",
                "benchmark": "Expected range: $1M-$1.5M",
                "impact": "Affects 12% of records",
            },
            "chart_data": {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [100, 120, 110, 200]},
            "chart_type": "bar",
        }

        state = {
            "collection_id": "col-1",
            "user_id": "user-1",
            "pulse_run_id": "run-1",
            "user_context": "Check revenue",
            "file_data": [{"file_id": "f1", "filename": "data.csv", "data_summary": "Revenue data"}],
            "file_profiles": [{"row_count": 1000, "columns": ["revenue", "date"]}],
            "signal_candidates": [],
            "validated_signals": [],
            "signals_output": [],
            "report_content": "",
            "error": "",
        }

        with patch("app.agents.pulse.get_llm", return_value=mock_llm), \
             patch("app.agents.pulse.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.pulse.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.pulse.get_agent_temperature", return_value=0.3), \
             patch("app.agents.pulse.get_agent_max_tokens", return_value=8000), \
             patch("app.agents.pulse.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.pulse.get_agent_prompt", return_value="You are a data analyst."), \
             patch("app.agents.pulse.get_settings") as mock_settings, \
             patch("app.agents.pulse._validate_single_candidate", new_callable=AsyncMock, return_value=mock_sandbox_result):
            mock_settings.return_value.pulse_sandbox_timeout_seconds = 300
            result = asyncio.get_event_loop().run_until_complete(
                run_analyses_node(state)
            )

        assert len(result["validated_signals"]) == 1
        assert len(result["signal_candidates"]) == 1
        assert result.get("error", "") == ""

    def test_run_analyses_node_short_circuits_on_error(self):
        """run_analyses_node short-circuits if state has error."""
        from app.agents.pulse import run_analyses_node

        state = {
            "error": "Previous node failed",
            "file_profiles": [],
            "signal_candidates": [],
            "validated_signals": [],
        }

        result = asyncio.get_event_loop().run_until_complete(
            run_analyses_node(state)
        )
        # Should return empty -- not crash
        assert result.get("validated_signals", []) == []


class TestPipelinePartialFailure:
    """Verify pipeline handles partial fan-out failures."""

    def test_pipeline_partial_failure(self):
        """3/5 candidates succeed, 2 fail. Pipeline completes with 3 signals."""
        from app.agents.pulse import run_analyses_node

        candidates = [
            {"title": f"Signal {i}", "severity_hint": "warning", "category": "trend",
             "code_instructions": f"test code {i}", "chart_hint": "line"}
            for i in range(5)
        ]
        candidates_json = json.dumps(candidates)

        mock_llm_response = MagicMock()
        mock_llm_response.content = candidates_json
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

        # 3 succeed, 2 return None (failure)
        valid_result = {
            "analysis_text": "Found trend",
            "statistical_evidence": {"metric": "r=0.8", "context": "x", "benchmark": "y", "impact": "z"},
            "chart_data": None, "chart_type": "line",
        }
        side_effects = [valid_result, None, valid_result, None, valid_result]

        state = {
            "collection_id": "col-1", "user_id": "user-1", "pulse_run_id": "run-1",
            "user_context": "", "file_data": [{"file_id": "f1", "filename": "d.csv", "data_summary": "data"}],
            "file_profiles": [{"row_count": 100}],
            "signal_candidates": [], "validated_signals": [], "signals_output": [],
            "report_content": "", "error": "",
        }

        with patch("app.agents.pulse.get_llm", return_value=mock_llm), \
             patch("app.agents.pulse.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.pulse.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.pulse.get_agent_temperature", return_value=0.3), \
             patch("app.agents.pulse.get_agent_max_tokens", return_value=8000), \
             patch("app.agents.pulse.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.pulse.get_agent_prompt", return_value="Prompt"), \
             patch("app.agents.pulse.get_settings") as mock_settings, \
             patch("app.agents.pulse._validate_single_candidate", new_callable=AsyncMock, side_effect=side_effects):
            mock_settings.return_value.pulse_sandbox_timeout_seconds = 300
            result = asyncio.get_event_loop().run_until_complete(
                run_analyses_node(state)
            )

        assert len(result["validated_signals"]) == 3
        assert result.get("error", "") == ""

    def test_pipeline_all_candidates_fail(self):
        """All candidates fail. Pipeline sets error."""
        from app.agents.pulse import run_analyses_node

        candidates_json = json.dumps([
            {"title": "Sig", "severity_hint": "info", "category": "trend",
             "code_instructions": "test", "chart_hint": "bar"}
        ])

        mock_llm_response = MagicMock()
        mock_llm_response.content = candidates_json
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

        state = {
            "collection_id": "col-1", "user_id": "user-1", "pulse_run_id": "run-1",
            "user_context": "", "file_data": [{"file_id": "f1", "filename": "d.csv", "data_summary": "data"}],
            "file_profiles": [{"row_count": 100}],
            "signal_candidates": [], "validated_signals": [], "signals_output": [],
            "report_content": "", "error": "",
        }

        with patch("app.agents.pulse.get_llm", return_value=mock_llm), \
             patch("app.agents.pulse.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.pulse.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.pulse.get_agent_temperature", return_value=0.3), \
             patch("app.agents.pulse.get_agent_max_tokens", return_value=8000), \
             patch("app.agents.pulse.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.pulse.get_agent_prompt", return_value="Prompt"), \
             patch("app.agents.pulse.get_settings") as mock_settings, \
             patch("app.agents.pulse._validate_single_candidate", new_callable=AsyncMock, return_value=None):
            mock_settings.return_value.pulse_sandbox_timeout_seconds = 300
            result = asyncio.get_event_loop().run_until_complete(
                run_analyses_node(state)
            )

        assert "error" in result
        assert result["error"] != ""


class TestGenerateSignalsNode:
    """Verify generate_signals_node produces PulseAgentOutput-validated signals."""

    def test_generate_signals_validates_output(self):
        """generate_signals_node validates signals through PulseAgentOutput."""
        from app.agents.pulse import generate_signals_node

        validated_signals = [
            {
                "title": "Revenue Spike",
                "severity_hint": "critical",
                "category": "anomaly",
                "analysis_text": "Revenue z-score is 4.2",
                "statistical_evidence": {
                    "metric": "z-score = 4.2",
                    "context": "Revenue Q4",
                    "benchmark": "$1M-$1.5M",
                    "impact": "12% of records",
                },
                "chart_data": {"labels": ["Q1", "Q2"], "values": [100, 200]},
                "chart_type": "bar",
            }
        ]

        mock_llm_response = MagicMock()
        mock_llm_response.content = "# Detection Report\n\nRevenue spike detected."
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

        state = {
            "collection_id": "col-1", "user_id": "user-1", "pulse_run_id": "run-1",
            "user_context": "", "file_data": [],
            "file_profiles": [], "signal_candidates": [],
            "validated_signals": validated_signals,
            "signals_output": [], "report_content": "", "error": "",
        }

        with patch("app.agents.pulse.get_llm", return_value=mock_llm), \
             patch("app.agents.pulse.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.pulse.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.pulse.get_agent_temperature", return_value=0.3), \
             patch("app.agents.pulse.get_agent_max_tokens", return_value=8000), \
             patch("app.agents.pulse.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.pulse.get_agent_prompt", return_value="Prompt"), \
             patch("app.agents.pulse.get_settings"):
            result = asyncio.get_event_loop().run_until_complete(
                generate_signals_node(state)
            )

        assert len(result["signals_output"]) == 1
        assert result["report_content"] != ""

    def test_generate_signals_short_circuits_on_error(self):
        """generate_signals_node short-circuits if state has error."""
        from app.agents.pulse import generate_signals_node

        state = {
            "error": "Previous failure",
            "validated_signals": [],
            "signals_output": [],
            "report_content": "",
        }

        result = asyncio.get_event_loop().run_until_complete(
            generate_signals_node(state)
        )
        assert result.get("signals_output", []) == []


class TestPipelineEndToEnd:
    """Verify full pipeline end-to-end with mocked dependencies."""

    def test_pipeline_end_to_end(self):
        """Full pipeline: profile -> analyze -> generate with all mocks."""
        from app.agents.pulse import build_pulse_graph

        graph = build_pulse_graph()

        # Mock profile_files_in_sandbox
        mock_profiles = [("file-1", {"row_count": 100, "columns": ["revenue"]})]

        # Mock LLM responses
        candidates_json = json.dumps([
            {"title": "Revenue Spike", "severity_hint": "critical", "category": "anomaly",
             "code_instructions": "compute z-scores", "chart_hint": "bar chart"}
        ])
        report_content = "# Detection Report\n\nOne signal detected."

        mock_llm_response_candidates = MagicMock()
        mock_llm_response_candidates.content = candidates_json
        mock_llm_response_report = MagicMock()
        mock_llm_response_report.content = report_content

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=[
            mock_llm_response_candidates,
            mock_llm_response_report,
        ])

        mock_sandbox_result = {
            "analysis_text": "Z-score of 4.2 detected",
            "statistical_evidence": {
                "metric": "z-score = 4.2", "context": "Revenue Q4",
                "benchmark": "$1M-$1.5M", "impact": "12% of records",
            },
            "chart_data": None, "chart_type": "bar",
        }

        initial_state = {
            "collection_id": "col-1", "user_id": "user-1", "pulse_run_id": "run-1",
            "user_context": "Check revenue", "file_data": [
                {"file_id": "file-1", "filename": "data.csv", "file_bytes": b"rev\n100\n200\n",
                 "data_summary": "Revenue data", "deep_profile": None}
            ],
            "file_profiles": [], "signal_candidates": [], "validated_signals": [],
            "signals_output": [], "report_content": "", "error": "",
        }

        with patch("app.agents.pulse.profile_files_in_sandbox", new_callable=AsyncMock, return_value=mock_profiles), \
             patch("app.agents.pulse.get_settings"), \
             patch("app.agents.pulse.get_llm", return_value=mock_llm), \
             patch("app.agents.pulse.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.pulse.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.pulse.get_agent_temperature", return_value=0.3), \
             patch("app.agents.pulse.get_agent_max_tokens", return_value=8000), \
             patch("app.agents.pulse.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.pulse.get_agent_prompt", return_value="Prompt"), \
             patch("app.agents.pulse._validate_single_candidate", new_callable=AsyncMock, return_value=mock_sandbox_result):
            result = asyncio.get_event_loop().run_until_complete(
                graph.ainvoke(initial_state)
            )

        assert result.get("error", "") == ""
        assert len(result["signals_output"]) >= 1
        assert result["report_content"] != ""
