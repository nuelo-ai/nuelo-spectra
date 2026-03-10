"""Deterministic deep profiling script and E2B execution wrapper for Pulse Agent.

Provides:
- load_pulse_config(): Load pulse_config.yaml with caching
- PROFILING_SCRIPT: Python code that runs inside E2B sandbox to profile CSV/Excel data
- profile_files_in_sandbox(): Async wrapper that executes profiling with cache support
"""

import asyncio
import json
import logging
from functools import lru_cache
from pathlib import Path

import yaml

from app.services.sandbox.e2b_runtime import E2BSandboxRuntime

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_pulse_config() -> dict:
    """Load and cache pulse_config.yaml.

    Returns:
        dict: Parsed pulse configuration with thresholds and signals keys.

    Raises:
        FileNotFoundError: If pulse_config.yaml doesn't exist.
        yaml.YAMLError: If YAML is malformed.
    """
    config_dir = Path(__file__).parent.parent / "config"
    config_path = config_dir / "pulse_config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Deterministic profiling script (runs inside E2B sandbox)
# ---------------------------------------------------------------------------

PROFILING_SCRIPT = '''
import pandas as pd
import numpy as np
from scipy import stats
import json
import sys
import os
import glob

try:
    # Find the first CSV or Excel file in /home/user/
    data_dir = "/home/user/"
    files = (
        glob.glob(os.path.join(data_dir, "*.csv"))
        + glob.glob(os.path.join(data_dir, "*.xlsx"))
        + glob.glob(os.path.join(data_dir, "*.xls"))
    )

    if not files:
        print(json.dumps({"error": "No CSV or Excel file found in /home/user/"}))
        sys.exit(0)

    filepath = files[0]
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Handle empty dataframe
    if df.empty:
        print(json.dumps({
            "row_count": 0,
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "column_profiles": {},
            "correlations": {},
            "missing_patterns": [],
        }))
        sys.exit(0)

    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "column_profiles": {},
        "correlations": {},
        "missing_patterns": [],
    }

    # Per-column profiling
    for col in df.columns:
        col_data = df[col]
        cp = {
            "dtype": str(col_data.dtype),
            "non_null_count": int(col_data.notna().sum()),
            "null_pct": round(float(col_data.isna().mean() * 100), 2),
            "unique_count": int(col_data.nunique()),
            "cardinality_ratio": round(float(col_data.nunique() / max(len(col_data), 1)), 4),
        }

        # Numeric column stats
        if pd.api.types.is_numeric_dtype(col_data):
            valid = col_data.dropna()
            if len(valid) > 0:
                cp["mean"] = round(float(valid.mean()), 4)
                cp["median"] = round(float(valid.median()), 4)
                cp["std"] = round(float(valid.std()), 4) if len(valid) > 1 else 0.0
                cp["min"] = float(valid.min())
                cp["max"] = float(valid.max())
                cp["skewness"] = round(float(valid.skew()), 4) if len(valid) > 2 else 0.0
                cp["kurtosis"] = round(float(valid.kurtosis()), 4) if len(valid) > 3 else 0.0
                q1 = float(valid.quantile(0.25))
                q3 = float(valid.quantile(0.75))
                iqr = q3 - q1
                cp["q1"] = round(q1, 4)
                cp["q3"] = round(q3, 4)
                cp["iqr"] = round(iqr, 4)
                cp["outlier_count"] = int(((valid < (q1 - 1.5 * iqr)) | (valid > (q3 + 1.5 * iqr))).sum())
                if len(valid) > 1 and valid.std() > 0:
                    z_scores = np.abs(stats.zscore(valid, nan_policy="omit"))
                    cp["z_score_outliers"] = int((z_scores > 3).sum())
                else:
                    cp["z_score_outliers"] = 0

        # Datetime column stats
        if pd.api.types.is_datetime64_any_dtype(col_data):
            valid = col_data.dropna()
            if len(valid) > 0:
                cp["min_date"] = str(valid.min())
                cp["max_date"] = str(valid.max())
                date_range = (valid.max() - valid.min()).days
                cp["date_range_days"] = int(date_range)
                if len(valid) > 1:
                    diffs = valid.sort_values().diff().dropna()
                    cp["is_regular_interval"] = bool(diffs.nunique() <= 3)
                else:
                    cp["is_regular_interval"] = True

        # Top 5 sample values
        try:
            top_vals = col_data.dropna().value_counts().head(5)
            cp["top_values"] = {str(k): int(v) for k, v in top_vals.items()}
        except Exception:
            cp["top_values"] = {}

        profile["column_profiles"][col] = cp

    # Correlation matrix (numeric columns only, Pearson)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr(method="pearson")
        # Convert to nested dict, rounding values
        corr_dict = {}
        for c1 in corr_matrix.columns:
            corr_dict[c1] = {}
            for c2 in corr_matrix.columns:
                val = corr_matrix.loc[c1, c2]
                corr_dict[c1][c2] = round(float(val), 4) if not pd.isna(val) else None
        profile["correlations"] = corr_dict

    # Missing value patterns (columns with >5% nulls)
    for col in df.columns:
        null_pct = df[col].isna().mean() * 100
        if null_pct > 5:
            profile["missing_patterns"].append({
                "column": col,
                "null_pct": round(float(null_pct), 2),
                "null_count": int(df[col].isna().sum()),
            })

    print(json.dumps(profile))

except Exception as e:
    print(json.dumps({"error": str(e)}))
'''


async def profile_files_in_sandbox(
    file_data: list[dict],
    settings,
) -> list[tuple[str, dict]]:
    """Profile files using E2B sandbox, respecting deep_profile cache.

    Args:
        file_data: List of dicts with keys: file_id, filename, file_bytes, deep_profile.
            If deep_profile is not None, the cached profile is used and E2B is skipped.
        settings: Application settings instance (needs pulse_sandbox_timeout_seconds).

    Returns:
        List of (file_id, profile_dict) tuples.
    """
    results: list[tuple[str, dict]] = []

    for fd in file_data:
        file_id = fd["file_id"]
        filename = fd["filename"]
        file_bytes = fd["file_bytes"]
        cached_profile = fd.get("deep_profile")

        # Use cached profile if available
        if cached_profile is not None:
            logger.info("Using cached deep_profile for file %s (%s)", file_id, filename)
            results.append((file_id, cached_profile))
            continue

        # Run profiling in E2B sandbox
        logger.info("Profiling file %s (%s) in E2B sandbox", file_id, filename)
        runtime = E2BSandboxRuntime(
            timeout_seconds=settings.pulse_sandbox_timeout_seconds
        )

        execution_result = await asyncio.to_thread(
            runtime.execute,
            code=PROFILING_SCRIPT,
            timeout=float(settings.pulse_sandbox_timeout_seconds),
            data_files=[(file_bytes, filename)],
        )

        # Parse JSON from last stdout line
        profile = {"error": "No output from profiling script"}
        if execution_result.stdout:
            last_line = execution_result.stdout[-1].strip()
            try:
                profile = json.loads(last_line)
            except json.JSONDecodeError:
                profile = {"error": f"Failed to parse profiling output: {last_line[:200]}"}
        elif execution_result.error:
            profile = {"error": str(execution_result.error)}

        results.append((file_id, profile))

    return results
