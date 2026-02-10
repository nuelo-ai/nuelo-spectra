"""Test scenarios for multi-LLM provider infrastructure (LLM-06).

This test suite verifies the multi-provider LLM infrastructure covering:
- LLM factory (get_llm) for all 5 providers (Anthropic, OpenAI, Google, Ollama, OpenRouter)
- Per-agent configuration loading (provider, model, temperature)
- Provider registry validation
- Startup validation (missing keys, unreachable providers, unknown references)
- Error classification for LLM failures
- Health endpoint functionality and caching

All tests are fully mocked and do not require live API keys.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import time
from app.agents.llm_factory import get_llm, classify_llm_error, invoke_with_logging
from app.agents.config import (
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_default_provider,
    load_provider_registry,
    load_prompts,
)


# ============================================================================
# Test Group 1: LLM Factory (get_llm)
# ============================================================================


class TestLLMFactory:
    """Test the LLM factory creates correct provider instances."""

    @patch("langchain_anthropic.ChatAnthropic")
    def test_factory_creates_anthropic(self, mock_anthropic):
        """Test factory creates ChatAnthropic instance."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance

        result = get_llm("anthropic", "claude-sonnet-4-20250514", "test-key")

        assert result == mock_instance
        mock_anthropic.assert_called_once_with(
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

    @patch("langchain_openai.ChatOpenAI")
    def test_factory_creates_openai(self, mock_openai):
        """Test factory creates ChatOpenAI instance."""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance

        result = get_llm("openai", "gpt-4o", "test-key")

        assert result == mock_instance
        mock_openai.assert_called_once_with(
            model="gpt-4o",
            api_key="test-key"
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_factory_creates_google(self, mock_google):
        """Test factory creates ChatGoogleGenerativeAI instance."""
        mock_instance = MagicMock()
        mock_google.return_value = mock_instance

        result = get_llm("google", "gemini-2.0-flash", "test-key")

        assert result == mock_instance
        mock_google.assert_called_once_with(
            model="gemini-2.0-flash",
            google_api_key="test-key"
        )

    @patch("langchain_ollama.ChatOllama")
    def test_factory_creates_ollama(self, mock_ollama):
        """Test factory creates ChatOllama instance with base_url."""
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance

        result = get_llm("ollama", "llama3.1", "", base_url="http://localhost:11434")

        assert result == mock_instance
        mock_ollama.assert_called_once_with(
            model="llama3.1",
            base_url="http://localhost:11434"
        )

    @patch("langchain_openai.ChatOpenAI")
    def test_factory_creates_openrouter(self, mock_openai):
        """Test factory creates ChatOpenAI instance for OpenRouter with correct config."""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance

        result = get_llm("openrouter", "anthropic/claude-3.5-sonnet", "test-key")

        assert result == mock_instance
        mock_openai.assert_called_once_with(
            model="anthropic/claude-3.5-sonnet",
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://spectra.app",
                "X-Title": "Spectra"
            }
        )

    def test_factory_rejects_unknown_provider(self):
        """Test factory raises ValueError for unknown provider."""
        with pytest.raises(ValueError) as exc_info:
            get_llm("unknown", "model", "key")

        error_msg = str(exc_info.value)
        assert "Unsupported LLM provider: unknown" in error_msg
        assert "anthropic" in error_msg
        assert "openai" in error_msg
        assert "google" in error_msg
        assert "ollama" in error_msg
        assert "openrouter" in error_msg

    @patch("langchain_anthropic.ChatAnthropic")
    def test_factory_passes_temperature(self, mock_anthropic):
        """Test factory passes temperature parameter to provider constructor."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance

        result = get_llm("anthropic", "claude-sonnet-4-20250514", "test-key", temperature=0.7)

        assert result == mock_instance
        mock_anthropic.assert_called_once_with(
            model="claude-sonnet-4-20250514",
            api_key="test-key",
            temperature=0.7
        )


# ============================================================================
# Test Group 2: Per-Agent Config Loading
# ============================================================================


class TestAgentConfig:
    """Test per-agent configuration loading from prompts.yaml."""

    def test_get_agent_provider_explicit(self):
        """Test get_agent_provider returns explicit provider when specified."""
        with patch("app.agents.config.load_prompts") as mock_load:
            mock_load.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "ollama",
                        "model": "llama3.1",
                    }
                }
            }

            provider = get_agent_provider("test_agent")
            assert provider == "ollama"

    def test_get_agent_provider_fallback_to_default(self):
        """Test get_agent_provider falls back to default when not specified."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry:
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "model": "claude-sonnet-4-20250514",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True},
                    "openai": {"type": "openai"}
                }
            }

            provider = get_agent_provider("test_agent")
            assert provider == "anthropic"

    def test_get_agent_model(self):
        """Test get_agent_model returns model from agent config."""
        with patch("app.agents.config.load_prompts") as mock_load:
            mock_load.return_value = {
                "agents": {
                    "test_agent": {
                        "model": "llama3.1",
                    }
                }
            }

            model = get_agent_model("test_agent")
            assert model == "llama3.1"

    def test_get_agent_model_missing_raises(self):
        """Test get_agent_model raises KeyError when model field is missing."""
        with patch("app.agents.config.load_prompts") as mock_load:
            mock_load.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "anthropic",
                    }
                }
            }

            with pytest.raises(KeyError) as exc_info:
                get_agent_model("test_agent")

            assert "has no 'model' field" in str(exc_info.value)

    def test_get_agent_temperature_explicit(self):
        """Test get_agent_temperature returns explicit temperature when specified."""
        with patch("app.agents.config.load_prompts") as mock_load:
            mock_load.return_value = {
                "agents": {
                    "test_agent": {
                        "model": "gpt-4",
                        "temperature": 0.7,
                    }
                }
            }

            temperature = get_agent_temperature("test_agent")
            assert temperature == 0.7

    def test_get_agent_temperature_default(self):
        """Test get_agent_temperature returns 0.0 when not specified."""
        with patch("app.agents.config.load_prompts") as mock_load:
            mock_load.return_value = {
                "agents": {
                    "test_agent": {
                        "model": "gpt-4",
                    }
                }
            }

            temperature = get_agent_temperature("test_agent")
            assert temperature == 0.0

    def test_get_default_provider(self):
        """Test get_default_provider returns provider marked as default."""
        with patch("app.agents.config.load_provider_registry") as mock_load:
            mock_load.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True},
                    "openai": {"type": "openai"},
                    "google": {"type": "google"}
                }
            }

            default = get_default_provider()
            assert default == "anthropic"

    def test_get_default_provider_missing_raises(self):
        """Test get_default_provider raises ValueError when no default is marked."""
        with patch("app.agents.config.load_provider_registry") as mock_load:
            mock_load.return_value = {
                "providers": {
                    "openai": {"type": "openai"},
                    "google": {"type": "google"}
                }
            }

            with pytest.raises(ValueError) as exc_info:
                get_default_provider()

            assert "No default provider found" in str(exc_info.value)


# ============================================================================
# Test Group 3: Provider Registry
# ============================================================================


class TestProviderRegistry:
    """Test provider registry loading and validation."""

    def test_load_provider_registry_returns_5_providers(self):
        """Test actual llm_providers.yaml contains all 5 providers."""
        registry = load_provider_registry()

        assert "providers" in registry
        providers = registry["providers"]

        # Check all 5 providers exist
        assert "anthropic" in providers
        assert "google" in providers
        assert "openai" in providers
        assert "ollama" in providers
        assert "openrouter" in providers

    def test_registry_has_one_default(self):
        """Test registry has exactly one provider marked as default."""
        registry = load_provider_registry()
        providers = registry["providers"]

        defaults = [name for name, config in providers.items() if config.get("default", False)]
        assert len(defaults) == 1, f"Expected exactly 1 default provider, found {len(defaults)}: {defaults}"

    def test_registry_anthropic_is_default(self):
        """Test anthropic is the default provider."""
        registry = load_provider_registry()
        assert registry["providers"]["anthropic"].get("default", False) is True


# ============================================================================
# Test Group 4: Startup Validation
# ============================================================================


class TestStartupValidation:
    """Test startup validation catches configuration errors."""

    def test_validation_catches_unknown_provider_reference(self):
        """Test validation raises error when agent references unknown provider."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry:
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "unknown_provider",
                        "model": "some-model",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True},
                    "openai": {"type": "openai"}
                }
            }

            # Import validation function locally to use mocked configs
            from app.main import validate_llm_configuration

            # Use pytest.raises with async context
            import asyncio
            with pytest.raises(ValueError) as exc_info:
                asyncio.run(validate_llm_configuration())

            error_msg = str(exc_info.value)
            assert "test_agent" in error_msg
            assert "unknown_provider" in error_msg
            assert "not in llm_providers.yaml" in error_msg

    @pytest.mark.asyncio
    async def test_validation_catches_missing_api_key(self):
        """Test validation fails when API key is missing for active provider."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry, \
             patch("app.main.settings") as mock_settings:
            # Mock configs
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-20250514",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True}
                }
            }

            # Mock settings with empty anthropic API key
            mock_settings.anthropic_api_key = ""

            from app.main import validate_llm_configuration

            with pytest.raises(ValueError) as exc_info:
                await validate_llm_configuration()

            error_msg = str(exc_info.value)
            assert "ANTHROPIC_API_KEY is not set" in error_msg
            assert "test_agent" in error_msg

    @pytest.mark.asyncio
    async def test_validation_catches_ollama_unreachable(self):
        """Test validation fails when Ollama is unreachable."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry, \
             patch("app.main.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:
            # Mock configs
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "ollama",
                        "model": "llama3.1",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "ollama": {"type": "ollama", "default": True}
                }
            }

            # Mock settings
            mock_settings.ollama_base_url = "http://localhost:11434"

            # Mock httpx client to raise ConnectError
            mock_http_instance = AsyncMock()
            mock_http_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value.__aenter__.return_value = mock_http_instance

            from app.main import validate_llm_configuration

            with pytest.raises(ValueError) as exc_info:
                await validate_llm_configuration()

            error_msg = str(exc_info.value)
            assert "Cannot connect to Ollama" in error_msg
            assert "http://localhost:11434" in error_msg

    @pytest.mark.asyncio
    async def test_validation_catches_openrouter_invalid_key(self):
        """Test validation fails when OpenRouter API key is invalid."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry, \
             patch("app.main.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:
            # Mock configs
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "openrouter",
                        "model": "anthropic/claude-3.5-sonnet",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "openrouter": {"type": "openrouter", "default": True}
                }
            }

            # Mock settings
            mock_settings.openrouter_api_key = "invalid-key"

            # Mock httpx client to return 401
            mock_http_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_http_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_http_instance

            from app.main import validate_llm_configuration

            with pytest.raises(ValueError) as exc_info:
                await validate_llm_configuration()

            error_msg = str(exc_info.value)
            assert "Invalid OPENROUTER_API_KEY" in error_msg

    @pytest.mark.asyncio
    async def test_validation_skips_unused_providers(self):
        """Test validation only tests providers actually used by agents."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry, \
             patch("app.main.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:
            # Mock configs - all agents use anthropic only
            mock_load_prompts.return_value = {
                "agents": {
                    "agent1": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-20250514",
                    },
                    "agent2": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-20250514",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True},
                    "ollama": {"type": "ollama"},
                    "openrouter": {"type": "openrouter"}
                }
            }

            # Mock settings
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.openrouter_api_key = ""

            # Mock httpx client - anthropic succeeds
            mock_http_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_http_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_http_instance

            from app.main import validate_llm_configuration

            # Should not raise - ollama/openrouter are not tested
            await validate_llm_configuration()

            # Verify only anthropic endpoint was called
            assert mock_http_instance.get.call_count == 1
            call_args = mock_http_instance.get.call_args
            assert "anthropic.com" in call_args[0][0]


# ============================================================================
# Test Group 5: Error Classification
# ============================================================================


class TestErrorClassification:
    """Test LLM error classification logic."""

    def test_classify_connection_error(self):
        """Test ConnectionError is classified as network_error."""
        error = ConnectionError("Connection refused")
        classification = classify_llm_error(error, "ollama")
        assert classification == "network_error"

    def test_classify_timeout_error(self):
        """Test TimeoutError is classified as network_error."""
        error = TimeoutError("Request timeout")
        classification = classify_llm_error(error, "anthropic")
        assert classification == "network_error"

    def test_classify_auth_error(self):
        """Test 401 Unauthorized is classified as auth_error."""
        error = Exception("401 Unauthorized")
        classification = classify_llm_error(error, "openai")
        assert classification == "auth_error"

    def test_classify_rate_limit(self):
        """Test 429 rate limit is classified as rate_limit."""
        error = Exception("429 rate limit exceeded")
        classification = classify_llm_error(error, "anthropic")
        assert classification == "rate_limit"

    def test_classify_model_not_found(self):
        """Test model not found error is classified as model_not_found."""
        error = Exception("404 model not found")
        classification = classify_llm_error(error, "openrouter")
        assert classification == "model_not_found"

    def test_classify_generic_error(self):
        """Test generic errors are classified as provider_error."""
        error = Exception("Something went wrong")
        classification = classify_llm_error(error, "google")
        assert classification == "provider_error"


# ============================================================================
# Test Group 6: Health Endpoint
# ============================================================================


class TestHealthEndpoint:
    """Test LLM health endpoint functionality."""

    def test_health_llm_endpoint_exists(self):
        """Test /health/llm route is registered on health router."""
        from app.routers.health import router

        # Check route exists
        route_paths = [route.path for route in router.routes]
        assert "/health/llm" in route_paths

    @pytest.mark.asyncio
    async def test_health_returns_provider_status(self):
        """Test health endpoint returns provider status structure."""
        # Import inside function to mock settings at runtime
        import app.routers.health

        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry, \
             patch("app.config.get_settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:
            # Mock configs
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-20250514",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True}
                }
            }

            # Mock settings
            mock_settings_instance = MagicMock()
            mock_settings_instance.anthropic_api_key = "test-key"
            mock_settings.return_value = mock_settings_instance

            # Mock httpx client
            mock_http_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_http_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_http_instance

            # Clear health cache
            from app.routers import health
            health._health_cache["result"] = None
            health._health_cache["timestamp"] = 0

            result = await health.llm_health_check()

            # Verify response structure
            assert "status" in result
            assert "providers" in result
            assert "checked_at" in result
            assert "anthropic" in result["providers"]
            assert result["providers"]["anthropic"]["status"] == "healthy"
            assert "latency_ms" in result["providers"]["anthropic"]

    @pytest.mark.asyncio
    async def test_health_caches_results(self):
        """Test health endpoint caches results for 60 seconds."""
        with patch("app.agents.config.load_prompts") as mock_load_prompts, \
             patch("app.agents.config.load_provider_registry") as mock_load_registry, \
             patch("app.config.get_settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:
            # Mock configs
            mock_load_prompts.return_value = {
                "agents": {
                    "test_agent": {
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-20250514",
                    }
                }
            }
            mock_load_registry.return_value = {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": True}
                }
            }

            # Mock settings
            mock_settings_instance = MagicMock()
            mock_settings_instance.anthropic_api_key = "test-key"
            mock_settings.return_value = mock_settings_instance

            # Mock httpx client
            mock_http_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_http_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_http_instance

            # Import and clear health cache
            from app.routers import health

            # First call - cache miss
            health._health_cache["result"] = None
            health._health_cache["timestamp"] = 0

            result1 = await health.llm_health_check()

            # Verify httpx was called
            assert mock_http_instance.get.call_count == 1

            # Second call within 60 seconds - cache hit
            health._health_cache["result"] = result1
            health._health_cache["timestamp"] = time.time()

            result2 = await health.llm_health_check()

            # Verify httpx was not called again (cache hit)
            assert mock_http_instance.get.call_count == 1
            assert result2 == result1


# ============================================================================
# Test Group 7: Invoke with Logging
# ============================================================================


class TestInvokeWithLogging:
    """Test LLM invocation with structured logging."""

    @pytest.mark.asyncio
    async def test_invoke_logs_success(self):
        """Test successful LLM invocation logs metadata."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="test response")

        with patch("app.agents.llm_factory.logger") as mock_logger:
            result = await invoke_with_logging(
                llm=mock_llm,
                messages=[{"role": "user", "content": "test"}],
                agent_name="test_agent",
                provider="anthropic",
                model="claude-sonnet-4-20250514"
            )

            # Verify LLM was invoked
            assert mock_llm.ainvoke.called
            assert result.content == "test response"

            # Verify logger.info was called
            assert mock_logger.info.called
            log_call = mock_logger.info.call_args[0][0]
            assert "llm_call" in log_call
            assert "test_agent" in log_call
            assert "anthropic" in log_call
            assert "success" in log_call

    @pytest.mark.asyncio
    async def test_invoke_logs_error(self):
        """Test failed LLM invocation logs error metadata."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("401 Unauthorized")

        with patch("app.agents.llm_factory.logger") as mock_logger:
            with pytest.raises(Exception):
                await invoke_with_logging(
                    llm=mock_llm,
                    messages=[{"role": "user", "content": "test"}],
                    agent_name="test_agent",
                    provider="openai",
                    model="gpt-4o"
                )

            # Verify logger.error was called
            assert mock_logger.error.called
            log_call = mock_logger.error.call_args[0][0]
            assert "llm_call" in log_call
            assert "test_agent" in log_call
            assert "openai" in log_call
            assert "error" in log_call
            assert "auth_error" in log_call


# ============================================================================
# Test Group 8: Empty Response Validation (UAT Gap Closure)
# ============================================================================


class TestEmptyResponseValidation:
    """Tests for empty LLM response validation (UAT gap closure)."""

    def test_validate_llm_response_returns_content_on_valid(self):
        """validate_llm_response returns content when response has non-empty content."""
        from app.agents.llm_factory import validate_llm_response

        response = MagicMock()
        response.content = "Hello, this is a valid response."
        result = validate_llm_response(response, "openai", "gpt-4o", "onboarding")
        assert result == "Hello, this is a valid response."

    def test_validate_llm_response_raises_on_empty_string(self):
        """validate_llm_response raises EmptyLLMResponseError on empty string."""
        from app.agents.llm_factory import validate_llm_response, EmptyLLMResponseError

        response = MagicMock()
        response.content = ""
        with pytest.raises(EmptyLLMResponseError) as exc_info:
            validate_llm_response(response, "openai", "gpt-5-nano", "onboarding")
        assert "gpt-5-nano" in str(exc_info.value)
        assert "onboarding" in str(exc_info.value)

    def test_validate_llm_response_raises_on_whitespace_only(self):
        """validate_llm_response raises EmptyLLMResponseError on whitespace-only content."""
        from app.agents.llm_factory import validate_llm_response, EmptyLLMResponseError

        response = MagicMock()
        response.content = "   \n\t  "
        with pytest.raises(EmptyLLMResponseError):
            validate_llm_response(response, "openai", "o3", "coding")

    def test_validate_llm_response_raises_on_none_content(self):
        """validate_llm_response raises EmptyLLMResponseError when content is None."""
        from app.agents.llm_factory import validate_llm_response, EmptyLLMResponseError

        response = MagicMock()
        response.content = None
        with pytest.raises(EmptyLLMResponseError):
            validate_llm_response(response, "openai", "gpt-5-nano", "data_analysis")

    def test_validate_llm_response_handles_non_string_content(self):
        """validate_llm_response converts non-string content to string."""
        from app.agents.llm_factory import validate_llm_response

        response = MagicMock()
        response.content = ["some", "list", "content"]
        result = validate_llm_response(response, "anthropic", "claude-sonnet-4-20250514", "coding")
        assert isinstance(result, str)
        assert "some" in result


# ============================================================================
# Test Group 9: Reasoning Model Configuration (UAT Gap Closure)
# ============================================================================


class TestReasoningModelConfig:
    """Tests for OpenAI reasoning model configuration (UAT gap closure)."""

    @patch("langchain_openai.ChatOpenAI")
    def test_reasoning_model_gets_reasoning_effort(self, mock_openai):
        """OpenAI reasoning models automatically receive reasoning_effort='low'."""
        get_llm("openai", "gpt-5-nano-2025-08-07", "test-key", max_tokens=4096)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args
        model_kwargs = call_kwargs.kwargs.get("model_kwargs", {})
        assert model_kwargs.get("reasoning_effort") == "low"

    @patch("langchain_openai.ChatOpenAI")
    def test_o3_model_gets_reasoning_effort(self, mock_openai):
        """o3 models automatically receive reasoning_effort='low'."""
        get_llm("openai", "o3-mini-2025-01-31", "test-key", max_tokens=4096)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args
        model_kwargs = call_kwargs.kwargs.get("model_kwargs", {})
        assert model_kwargs.get("reasoning_effort") == "low"

    @patch("langchain_openai.ChatOpenAI")
    def test_o1_model_gets_reasoning_effort(self, mock_openai):
        """o1 models automatically receive reasoning_effort='low'."""
        get_llm("openai", "o1-2024-12-17", "test-key", max_tokens=4096)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args
        model_kwargs = call_kwargs.kwargs.get("model_kwargs", {})
        assert model_kwargs.get("reasoning_effort") == "low"

    @patch("langchain_openai.ChatOpenAI")
    def test_o4_mini_model_gets_reasoning_effort(self, mock_openai):
        """o4-mini models automatically receive reasoning_effort='low'."""
        get_llm("openai", "o4-mini-2025-04-16", "test-key", max_tokens=4096)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args
        model_kwargs = call_kwargs.kwargs.get("model_kwargs", {})
        assert model_kwargs.get("reasoning_effort") == "low"

    @patch("langchain_openai.ChatOpenAI")
    def test_non_reasoning_model_no_reasoning_effort(self, mock_openai):
        """Standard OpenAI models (gpt-4o) do NOT receive reasoning_effort."""
        get_llm("openai", "gpt-4o", "test-key", max_tokens=4096)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args
        model_kwargs = call_kwargs.kwargs.get("model_kwargs", {})
        assert "reasoning_effort" not in model_kwargs

    @patch("langchain_openai.ChatOpenAI")
    def test_explicit_reasoning_effort_not_overridden(self, mock_openai):
        """User-provided reasoning_effort is NOT overridden by auto-detection."""
        get_llm(
            "openai", "gpt-5-nano-2025-08-07", "test-key",
            max_tokens=4096,
            model_kwargs={"reasoning_effort": "high"},
        )
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args
        model_kwargs = call_kwargs.kwargs.get("model_kwargs", {})
        assert model_kwargs.get("reasoning_effort") == "high"
