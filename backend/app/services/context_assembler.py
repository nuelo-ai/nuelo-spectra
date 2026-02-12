"""Multi-file context assembly service with progressive token budget management.

Assembles compact multi-file context from file IDs by profiling each file,
detecting join hints across files, and progressively reducing detail to fit
within the configured token budget.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import tiktoken
import yaml
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_session_settings() -> dict:
    """Load session and context assembler settings from settings.yaml.

    Follows the same pattern as load_prompts() in backend/app/agents/config.py
    -- loads YAML from backend/app/config/ directory and caches with lru_cache.

    Returns:
        dict: Parsed settings with 'session' and 'context_assembler' keys.

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist.
        yaml.YAMLError: If YAML is malformed.
    """
    config_dir = Path(__file__).parent.parent / "config"
    settings_path = config_dir / "settings.yaml"

    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ContextAssembler:
    """Assembles multi-file context with progressive token budget management.

    Takes file IDs, profiles each file using the existing OnboardingAgent,
    detects join hints across files, and builds a compact context string
    that fits within the configured token budget via progressive reduction.

    Reduction levels (tried in order):
        1. "full"       - dtype + stats (mean, min, max) + sample data (first 3 rows)
        2. "no_samples" - dtype + stats, no sample data
        3. "no_stats"   - dtype only, no stats, no samples
        4. "minimal"    - column names + types only, one line per column
    """

    def __init__(self) -> None:
        """Initialize ContextAssembler with settings from settings.yaml.

        Loads token_budget and safety_margin from configuration, creates
        tiktoken encoder using gpt-4 model (same pattern as TiktokenCounter
        in backend/app/agents/memory/token_counter.py).
        """
        settings = load_session_settings()
        ca_settings = settings["context_assembler"]

        self.token_budget: int = ca_settings["token_budget"]
        self.safety_margin: float = ca_settings["safety_margin"]
        self.effective_budget: int = int(self.token_budget * (1 - self.safety_margin))

        # Use tiktoken for token counting (same as TiktokenCounter)
        self.encoder = tiktoken.encoding_for_model("gpt-4")

    async def assemble(
        self,
        db: AsyncSession,
        file_ids: list[UUID],
        user_id: UUID,
    ) -> dict:
        """Assemble multi-file context with token budget management.

        Loads file records, profiles each file, detects join hints, and
        progressively reduces detail level until context fits within the
        effective token budget.

        Args:
            db: Async database session.
            file_ids: List of file UUIDs to include in context.
            user_id: User UUID for access control verification.

        Returns:
            dict with keys:
                - files: list of file metadata dicts (id, name, var_name, profile, size_bytes)
                - join_hints: list of join hint strings
                - context_string: formatted context string for LLM prompt
                - total_tokens: token count of the context string
                - reduction_level: which reduction level was used

        Raises:
            ValueError: If any file is missing, not owned by user, or not yet onboarded.
        """
        # Import inside method to avoid circular imports (same pattern as agent_service.py)
        from app.agents.onboarding import OnboardingAgent
        from app.services.file import FileService

        # Load and validate all file records
        file_records = []
        for file_id in file_ids:
            file_record = await FileService.get_user_file(db, file_id, user_id)
            if file_record is None:
                raise ValueError(
                    f"File {file_id} not found or does not belong to user."
                )
            if file_record.data_summary is None:
                raise ValueError(
                    f"File '{file_record.original_filename}' ({file_id}) has not been "
                    f"onboarded yet. Please wait for onboarding to complete."
                )
            file_records.append(file_record)

        # Profile each file using OnboardingAgent (reuse existing profiling logic)
        onboarding_agent = OnboardingAgent()
        used_names: set[str] = set()
        file_metadata: list[dict] = []

        for file_record in file_records:
            profile = await onboarding_agent.profile_data(
                file_record.file_path,
                file_record.file_type,
            )

            var_name = self._sanitize_var_name(
                file_record.original_filename, used_names
            )

            file_metadata.append({
                "id": str(file_record.id),
                "name": file_record.original_filename,
                "var_name": var_name,
                "profile": profile,
                "size_bytes": file_record.file_size,
            })

        # Detect join hints across files
        join_hints = self._detect_join_hints(file_metadata)

        # Progressive reduction loop: try each level until within budget
        reduction_levels = ["full", "no_samples", "no_stats", "minimal"]
        context_string = ""
        total_tokens = 0

        for level in reduction_levels:
            context_string = self._build_context_string(
                file_metadata, join_hints, level
            )
            total_tokens = self._count_tokens(context_string)

            if total_tokens <= self.effective_budget:
                logger.info(
                    "Context assembled at '%s' level: %d tokens (budget: %d)",
                    level, total_tokens, self.effective_budget,
                )
                return {
                    "files": file_metadata,
                    "join_hints": join_hints,
                    "context_string": context_string,
                    "total_tokens": total_tokens,
                    "reduction_level": level,
                }

        # Even minimal exceeds budget -- return minimal with warning
        logger.warning(
            "Context exceeds budget even at 'minimal' level: %d tokens (budget: %d)",
            total_tokens, self.effective_budget,
        )
        return {
            "files": file_metadata,
            "join_hints": join_hints,
            "context_string": context_string,
            "total_tokens": total_tokens,
            "reduction_level": "minimal_exceeded",
        }

    def _sanitize_var_name(self, filename: str, used_names: set[str]) -> str:
        """Convert filename to a valid Python DataFrame variable name.

        Sanitization steps:
            1. Remove file extension using Path.stem
            2. Lowercase, replace non-alphanumeric chars with underscore
            3. Strip leading/trailing underscores
            4. Prepend 'data_' if starts with digit
            5. Add 'df_' prefix
            6. Handle collisions by appending '_2', '_3', etc.

        Args:
            filename: Original filename (e.g., "Sales Data 2024.csv").
            used_names: Set of already-used variable names for collision tracking.

        Returns:
            Valid Python identifier with df_ prefix (e.g., "df_sales_data_2024").

        Examples:
            "Sales Data 2024.csv"  -> "df_sales_data_2024"
            "customer-info.xlsx"   -> "df_customer_info"
            "123_data.csv"         -> "df_data_123_data"
            "sales.csv" (collision)-> "df_sales_2"
        """
        # Remove extension
        stem = Path(filename).stem

        # Lowercase, replace non-alphanumeric with underscore
        sanitized = re.sub(r"[^a-z0-9_]", "_", stem.lower())

        # Strip leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Handle empty string edge case
        if not sanitized:
            sanitized = "data"

        # Prepend 'data_' if starts with digit
        if sanitized[0].isdigit():
            sanitized = f"data_{sanitized}"

        # Add df_ prefix
        var_name = f"df_{sanitized}"

        # Handle collisions
        if var_name in used_names:
            counter = 2
            while f"{var_name}_{counter}" in used_names:
                counter += 1
            var_name = f"{var_name}_{counter}"

        used_names.add(var_name)
        return var_name

    def _detect_join_hints(self, profiles: list[dict]) -> list[str]:
        """Detect shared column names across files for join suggestions.

        For each pair of files (i, j where i < j), finds column name
        intersections and builds hint strings including dtype information.
        Appends a type mismatch warning when dtypes differ.

        Args:
            profiles: List of file metadata dicts, each containing a 'profile'
                      key with 'columns' mapping column names to their metadata.

        Returns:
            List of join hint strings, e.g.:
                "Possible join: sales.csv.customer_id (int64) <-> customers.csv.id (int64)"
                "Possible join: a.csv.name (object) <-> b.csv.name (int64) [WARNING: Type mismatch]"
        """
        hints: list[str] = []

        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                file_a = profiles[i]
                file_b = profiles[j]

                cols_a = file_a["profile"]["columns"]
                cols_b = file_b["profile"]["columns"]

                # Find shared column names via set intersection
                shared = set(cols_a.keys()) & set(cols_b.keys())

                for col in sorted(shared):
                    dtype_a = cols_a[col]["dtype"]
                    dtype_b = cols_b[col]["dtype"]

                    hint = (
                        f"Possible join: {file_a['name']}.{col} ({dtype_a}) "
                        f"<-> {file_b['name']}.{col} ({dtype_b})"
                    )

                    if dtype_a != dtype_b:
                        hint += " [WARNING: Type mismatch]"

                    hints.append(hint)

        return hints

    def _build_context_string(
        self,
        profiles: list[dict],
        join_hints: list[str],
        level: str,
    ) -> str:
        """Build markdown-formatted context string at the specified reduction level.

        Levels:
            - "full":       dtype + stats (mean, min, max) + sample data (first 3 rows)
            - "no_samples": dtype + stats, omit sample data
            - "no_stats":   dtype only, no stats, no samples
            - "minimal":    column names + types only, one line per column

        Args:
            profiles: List of file metadata dicts with profile data.
            join_hints: List of join hint strings.
            level: Reduction level to use.

        Returns:
            Formatted markdown string for inclusion in LLM prompt.
        """
        lines: list[str] = ["# Multi-File Dataset Context", ""]

        for profile in profiles:
            p = profile["profile"]
            shape = p["shape"]

            lines.append(f"## File: {profile['name']}")
            lines.append(f"Variable name: `{profile['var_name']}`")
            lines.append(f"Rows: {shape['rows']}, Columns: {shape['columns']}")
            lines.append("")
            lines.append("### Columns:")

            for col_name, col_meta in p["columns"].items():
                dtype = col_meta["dtype"]

                if level == "minimal":
                    lines.append(f"- `{col_name}`: {dtype}")
                elif level == "no_stats":
                    line = f"- `{col_name}`: {dtype}"
                    lines.append(line)
                elif level == "no_samples":
                    line = f"- `{col_name}`: {dtype}"
                    # Add stats if numeric
                    if "mean" in col_meta and col_meta["mean"] is not None:
                        line += (
                            f" (mean={col_meta['mean']:.2f}, "
                            f"min={col_meta['min']}, max={col_meta['max']})"
                        )
                    lines.append(line)
                else:
                    # level == "full"
                    line = f"- `{col_name}`: {dtype}"
                    if "mean" in col_meta and col_meta["mean"] is not None:
                        line += (
                            f" (mean={col_meta['mean']:.2f}, "
                            f"min={col_meta['min']}, max={col_meta['max']})"
                        )
                    lines.append(line)

            # Include sample data only for "full" level
            if level == "full" and p.get("sample_data"):
                lines.append("")
                lines.append("### Sample Data (first 3 rows):")
                samples = p["sample_data"][:3]
                for row in samples:
                    lines.append(f"  {row}")

            lines.append("")

        # Add join hints section if any exist
        if join_hints:
            lines.append("## Detected Join Opportunities")
            lines.append("")
            for hint in join_hints:
                lines.append(f"- {hint}")
            lines.append("")

        return "\n".join(lines)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken encoder.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens.
        """
        return len(self.encoder.encode(text))
