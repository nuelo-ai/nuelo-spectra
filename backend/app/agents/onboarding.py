"""Onboarding Agent for data profiling and summarization."""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.config import (
    get_agent_prompt,
    get_agent_max_tokens,
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm
from app.config import get_settings


@dataclass
class OnboardingResult:
    """Result from Onboarding Agent execution."""

    data_summary: str
    """LLM-generated natural language summary of the dataset."""

    data_profile: dict
    """Pandas profiling output (structure, types, stats)."""

    sample_data: str
    """First few rows formatted for user verification."""

    query_suggestions: dict | None = None
    """LLM-generated categorized query suggestions for the dataset."""


class OnboardingAgent:
    """Agent that profiles uploaded data and generates natural language summaries.

    The Onboarding Agent has two phases:
    1. Data profiling (pure Python/pandas, no LLM)
    2. LLM summarization (takes profile + user context, generates summary)
    """

    def __init__(self):
        """Initialize the Onboarding Agent."""
        self.settings = get_settings()

    async def profile_data(self, file_path: str, file_type: str) -> dict:
        """Profile the dataset using pandas analysis.

        Args:
            file_path: Absolute path to the uploaded file
            file_type: File type (csv, xlsx, xls)

        Returns:
            dict: Data profile containing:
                - shape: {rows: int, columns: int}
                - columns: {col_name: {dtype, missing_count, missing_pct, unique_count, ...stats}}
                - sample_data: first 5 rows as list of dicts
                - quality_issues: list of issue descriptions

        Raises:
            Exception: If file cannot be read or profiled
        """
        def _profile():
            """Blocking pandas profiling function."""
            # Read file based on type
            if file_type == "csv":
                df = pd.read_csv(file_path)
            elif file_type in ("xlsx", "xls"):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Build profile
            profile = {
                "shape": {
                    "rows": len(df),
                    "columns": len(df.columns)
                },
                "columns": {},
                "sample_data": df.head(5).to_dict(orient="records"),
                "quality_issues": []
            }

            # Profile each column
            for col in df.columns:
                col_data = df[col]
                missing_count = int(col_data.isna().sum())
                missing_pct = (missing_count / len(df)) * 100

                col_profile = {
                    "dtype": str(col_data.dtype),
                    "missing_count": missing_count,
                    "missing_pct": round(missing_pct, 2),
                    "unique_count": int(col_data.nunique())
                }

                # Add numeric stats if applicable
                if pd.api.types.is_numeric_dtype(col_data):
                    stats = col_data.describe()
                    col_profile.update({
                        "min": float(stats["min"]) if not pd.isna(stats["min"]) else None,
                        "max": float(stats["max"]) if not pd.isna(stats["max"]) else None,
                        "mean": float(stats["mean"]) if not pd.isna(stats["mean"]) else None,
                        "median": float(stats["50%"]) if not pd.isna(stats["50%"]) else None,
                        "std": float(stats["std"]) if not pd.isna(stats["std"]) else None
                    })

                profile["columns"][col] = col_profile

                # Quality issue detection
                if missing_pct > 50:
                    profile["quality_issues"].append(
                        f"Column '{col}' has {missing_pct:.1f}% missing values"
                    )

            # Check for duplicate rows
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                duplicate_pct = (duplicate_count / len(df)) * 100
                profile["quality_issues"].append(
                    f"Found {duplicate_count} duplicate rows ({duplicate_pct:.1f}%)"
                )

            return profile

        # Run pandas profiling in thread pool to avoid blocking event loop
        try:
            return await asyncio.to_thread(_profile)
        except Exception as e:
            # Return minimal profile on error
            return {
                "shape": {"rows": 0, "columns": 0},
                "columns": {},
                "sample_data": [],
                "quality_issues": [f"Profiling error: {str(e)}"]
            }

    async def generate_summary(
        self, profile: dict, user_context: str
    ) -> tuple[str, dict | None]:
        """Generate natural language summary and query suggestions using LLM.

        Args:
            profile: Data profile dict from profile_data()
            user_context: Optional user-provided context

        Returns:
            tuple[str, dict | None]: (summary text, suggestions dict or None)

        Raises:
            Exception: If LLM invocation fails
        """
        # Initialize LLM using per-agent config
        provider = get_agent_provider("onboarding")
        model = get_agent_model("onboarding")
        temperature = get_agent_temperature("onboarding")
        api_key = get_api_key_for_provider(provider, self.settings)
        max_tokens = get_agent_max_tokens("onboarding")

        # Build kwargs for provider-specific options
        kwargs = {"max_tokens": max_tokens, "temperature": temperature}
        if provider == "ollama":
            kwargs["base_url"] = self.settings.ollama_base_url

        llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

        # Load system prompt from YAML
        system_prompt = get_agent_prompt("onboarding")

        # Build user message with profile and context
        user_message = f"""Data Profile (JSON):
{json.dumps(profile, indent=2)}
"""
        if user_context:
            user_message += f"\nUser-provided context: {user_context}"

        # Invoke LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        response = await asyncio.to_thread(llm.invoke, messages)

        # Parse JSON response with fallback for non-JSON responses
        # Strip markdown code fences if LLM wrapped response in ```json...```
        content = response.content.strip()
        if content.startswith("```"):
            # Remove opening fence (```json or ```)
            first_newline = content.index("\n")
            content = content[first_newline + 1:]
            # Remove closing fence
            if content.endswith("```"):
                content = content[:-3].strip()

        try:
            parsed = json.loads(content)
            summary = parsed.get("summary", response.content)
            suggestions = parsed.get("suggestions", None)
            return (summary, suggestions)
        except json.JSONDecodeError:
            # Fallback: treat entire response as summary, no suggestions
            return (response.content, None)

    async def run(
        self,
        file_path: str,
        file_type: str,
        user_context: str = ""
    ) -> OnboardingResult:
        """Execute the Onboarding Agent workflow.

        Args:
            file_path: Absolute path to the uploaded file
            file_type: File type (csv, xlsx, xls)
            user_context: Optional user-provided context

        Returns:
            OnboardingResult: Contains data_summary, data_profile, and sample_data

        Raises:
            Exception: If profiling or summarization fails
        """
        # Phase 1: Profile data
        profile = await self.profile_data(file_path, file_type)

        # Phase 2: Generate LLM summary and query suggestions
        summary, suggestions = await self.generate_summary(profile, user_context)

        # Format sample data for display
        sample_data = json.dumps(profile.get("sample_data", []), indent=2)

        return OnboardingResult(
            data_summary=summary,
            data_profile=profile,
            sample_data=sample_data,
            query_suggestions=suggestions,
        )
