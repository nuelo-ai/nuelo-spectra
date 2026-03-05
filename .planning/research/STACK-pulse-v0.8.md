# Stack Research: v0.8 Spectra Pulse (Detection)

**Domain:** Statistical analysis module (Pulse Agent) — additive additions to existing Spectra platform
**Researched:** 2026-03-05
**Confidence:** HIGH (libraries verified via PyPI, mockup source inspected directly)

> This is a v0.8-scoped stack document. The existing production stack (FastAPI, PostgreSQL, LangGraph,
> E2B, Next.js 16, React 19, shadcn/ui, TanStack Query, Zustand, Plotly.js) is locked and not
> re-evaluated here. Only new or changed items for v0.8 are documented.

---

## What Changes in v0.8

| Layer | Change | Notes |
|-------|--------|-------|
| Backend Python | Add `scipy`, `statsmodels`, `scikit-learn` | Statistical analysis for Pulse Agent |
| Backend data | 3 new SQLAlchemy models: `Collection`, `File` (pulse), `Signal` | New tables alongside existing schema |
| Backend API | 9 new FastAPI endpoints under `/collections/` | New router, no changes to existing routes |
| Backend config | New `user_classes.yaml` fields + 1 new `platform_settings` key | Config-only for tier gating; 1-row DB insert for credit cost |
| Frontend | Add `recharts` to main `frontend/` | Already in `pulse-mockup/` and `admin-frontend/`; missing from main app |
| Frontend | Migrate `pulse-mockup/` workspace components into `frontend/` | Copy-and-wire, not rebuild |

**Nothing else changes.** No new auth, no new infrastructure, no new database engine.

---

## Recommended Stack — New Additions Only

### Backend: Python Statistical Libraries

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `scipy` | `>=1.11.0` | Z-score and IQR-based anomaly detection; normality tests (Shapiro-Wilk); Pearson/Spearman correlation for concentration analysis; distribution fitting for data quality checks | Standard scientific Python library. Pre-installed in E2B's default sandbox environment. No custom sandbox config needed. Current stable: 1.17.1 (released 2026-02-22). |
| `statsmodels` | `>=0.14.0` | OLS regression for trend slopes with p-values and confidence intervals; `tsa.seasonal.seasonal_decompose` for seasonal trend detection; `tsa.stattools.adfuller` for stationarity testing | Best Python library for statistical modeling with interpretable outputs. Produces significance levels and confidence intervals — needed to populate `statistical_evidence` JSON in Signals. Current stable: 0.14.6 (released 2025-12-05). |
| `scikit-learn` | `>=1.3.0` | `IsolationForest` for multi-column anomaly detection; `StandardScaler` for preprocessing before anomaly detection; `KMeans` for segment concentration analysis | Industry-standard ML for detection tasks. Isolation Forest handles multi-dimensional datasets where per-column Z-score misses cross-column interactions. The `contamination` parameter gives tunable sensitivity. Current stable: 1.8.0. |

**Why all three, not just one:**

Each covers a distinct Pulse analysis category cleanly:

- `scipy.stats` — data quality checks (normality, distribution tests) and univariate anomaly detection (Z-score, IQR). Fast, no model fitting required.
- `statsmodels` — trend analysis with statistical significance. `adfuller` + OLS slope gives a p-value for "is this trend real?", which feeds directly into Signal severity and statistical evidence.
- `sklearn` — multi-column anomaly detection (Isolation Forest) for datasets where individual column stats miss the pattern. Also handles preprocessing and clustering for concentration analysis.

**E2B sandbox availability confirmed:** pandas, numpy, scipy, scikit-learn, and statsmodels are all included in E2B's default Python environment. Pulse Agent code runs in the same E2B sandbox as the existing Coding Agent — no sandbox configuration changes needed.

### Backend: No New Infrastructure Packages

The Pulse Agent reuses all existing infrastructure:

| Infrastructure | v0.8 Usage |
|----------------|-----------|
| E2B sandbox | Pulse Agent runs statistical analysis here — same execution environment as Coding Agent |
| LangGraph | New `PulseAgent` extends base agent class; no orchestration changes |
| FastAPI | New `collections` router follows same pattern as existing `sessions` and `files` routers |
| SQLAlchemy + Alembic | New models use existing async engine; migration follows three-step pattern |
| Credit system | `workspace_credit_cost_pulse` is a new `platform_settings` key — no schema change to credit tables |
| `get_current_user` dependency | Pulse endpoints reuse existing auth dependency unchanged |

No new Python packages beyond `scipy`, `statsmodels`, and `scikit-learn`.

### Frontend: Recharts Addition

| Package | Version | Purpose | Why |
|---------|---------|---------|-----|
| `recharts` | `^2.15.3` | Signal visualizations in `SignalDetailPanel` — `AreaChart` for trend/line signals, `BarChart` for category/concentration signals, `ScatterChart` for correlation signals | Already in `pulse-mockup/` at this version and in `admin-frontend/`. Adding to `frontend/` brings it in sync. The `signal-chart.tsx` component from the mockup uses exactly these three chart types. |

**Chart types used by Signal visualizations** (verified from `pulse-mockup/src/components/workspace/signal-chart.tsx`):

| `signal.chartType` | Recharts component | Signal categories it serves |
|-------------------|--------------------|----------------------------|
| `"line"` | `AreaChart` + `Area` | Trend signals (revenue over time, churn rate over quarters) |
| `"bar"` | `BarChart` + `Bar` | Concentration/anomaly signals (sales by region, count by segment) |
| `"scatter"` | `ScatterChart` + `Scatter` | Correlation signals (two numeric dimensions, outlier positioning) |

The mockup defines `ChartType = "line" | "bar" | "scatter"` — no other Recharts types are needed for v0.8 Signals.

### Frontend: No Other New Packages

Comparing `pulse-mockup/package.json` against `frontend/package.json` directly:

| Package | In pulse-mockup | In frontend | Action |
|---------|----------------|-------------|--------|
| `recharts ^2.15.3` | YES | NO | **Add to frontend** |
| `react-dropzone ^14.4.0` | NO (mocked) | YES | Already present — handles `FileUploadZone` drag/drop |
| `zustand ^5.0.11` | NO (local state) | YES | Already present — handles workspace state |
| `@tanstack/react-query ^5.90.20` | NO (mock data) | YES | Already present — handles API calls |
| `@tanstack/react-table ^8.21.3` | NO (mock data) | YES | Already present — handles `FileTable` sorting |
| All shadcn/ui, lucide-react, clsx, etc. | Same versions | Same versions | No action needed |

The mockup omits `react-dropzone`, `zustand`, and TanStack packages because it uses hardcoded mock data. The real implementation uses these existing `frontend/` packages when wiring up API calls and file uploads.

---

## Installation Commands

```bash
# Backend — add to backend/pyproject.toml [project] dependencies, then:
cd backend
uv add scipy statsmodels scikit-learn

# Frontend — run in frontend/ directory:
cd frontend
npm install recharts@^2.15.3
```

---

## Database Migration Considerations

**New tables (v0.8 Alembic migration):**

| Table | Notes |
|-------|-------|
| `collections` | No collision with existing tables |
| `pulse_files` | Use `pulse_files` (not `files`) — existing user upload model likely occupies `files`. Verify before naming the migration. |
| `signals` | No collision with existing tables |

**JSON columns:** `column_profile`, `visualization`, and `statistical_evidence` use SQLAlchemy `JSON` type. asyncpg handles `JSON` columns correctly — same pattern already used in LangGraph checkpoint storage.

**Migration pattern:** Follow the existing three-step pattern (add nullable → backfill → apply NOT NULL). Used in v0.3 and v0.5; apply the same here.

**`platform_settings` extension:** Add `workspace_credit_cost_pulse` (default `5.0`) as a new row `INSERT` in the Alembic migration data migration step. No schema change — same as how `default_credit_cost` was added.

**`user_classes.yaml` extension:** Add `workspace_access: bool` and `max_active_collections: int` to each tier entry. Config-file change only — no DB migration needed. Same mechanism as existing `credits` and `reset_policy` fields.

---

## Signal Visualization JSON Format

The `Signal.visualization` JSON column should store the shape that `signal-chart.tsx` consumes directly:

```json
{
  "chartType": "bar",
  "chartData": [
    { "region": "APAC", "revenue": 420000 },
    { "region": "EMEA", "revenue": 310000 },
    { "region": "Americas", "revenue": 890000 }
  ]
}
```

**Do NOT store Plotly figure JSON here.** Chat DataCards use Plotly format. Pulse Signals use Recharts format. Mixing these formats creates a maintenance burden and confuses future developers.

Keep `chartData` arrays small — 20–50 data points maximum. A Signal highlights a finding, not the full dataset. Large arrays belong in the full file, not in the Signal JSON.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `scipy` Z-score + IQR | `PyOD` (Python Outlier Detection) | PyOD is comprehensive but heavy (~20 transitive deps). E2B availability unverified. scipy covers univariate anomaly detection adequately. |
| `statsmodels` for trends | `prophet` (Meta time-series forecasting) | Prophet requires pystan backend, C++ build toolchain, significantly heavier install. `statsmodels.tsa` covers trend detection without forecasting requirements. |
| `sklearn` IsolationForest | `PyOD IForest wrapper` | sklearn's IsolationForest is the reference implementation. PyOD wraps it with extra overhead. Use directly. |
| `recharts ^2.15.3` (v2) | Recharts v3 alpha | Recharts v3 was in alpha as of March 2026. Mockup uses v2.15.x. Same major version eliminates API migration risk. |
| Migrate mockup components | Rebuild from scratch | Mockup is production-ready (correct stack, routing, interactions). Rebuilding spends milestone time on work already done. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `prophet` | Requires Stan/PyMC backend. Heavy install. v0.8 is detection, not forecasting. | `statsmodels.tsa.seasonal.seasonal_decompose` |
| `pyod` | Wraps sklearn, adds ~15 transitive deps. Overkill when sklearn's Isolation Forest is available directly. | `sklearn.ensemble.IsolationForest` |
| `plotly` in Signal `visualization` JSON | Chat DataCards use Plotly format. Pulse Signals use Recharts format. Mixing formats creates confusion and couples modules. | Store `{chartType, chartData}` as Recharts-compatible shape |
| `react-plotly.js` for Signal charts | Plotly is already in frontend for Chat. Signal charts in Pulse use Recharts per the mockup design. Don't add Plotly rendering to the Signal component. | `recharts` `BarChart`/`AreaChart`/`ScatterChart` |
| Any new auth or middleware | Pulse endpoints use existing `get_current_user` dependency and existing credit check pattern. | Existing `get_current_user` + `CreditService` |
| `celery` or task queues | Pulse Agent runs async in FastAPI's async context via `await`. E2B execution is the bottleneck; a task queue adds infrastructure without improving UX. | `await pulse_agent.run(...)` in the endpoint |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `scipy>=1.11.0` | `pandas>=2.0.0`, numpy (transitive) | pandas already in pyproject.toml. scipy and pandas share numpy — no conflict. statsmodels 0.14.6 requires scipy<2.0; scipy 1.17.1 satisfies this. |
| `statsmodels>=0.14.0` | `scipy>=1.11.0`, `pandas>=2.0.0` | 0.14.6 requires scipy<2.0. 1.17.1 satisfies this. |
| `scikit-learn>=1.3.0` | `scipy>=1.11.0`, numpy (transitive) | sklearn 1.8.0 requires scipy>=1.3.2; 1.17.1 satisfies this. All three libraries share the same numpy transitive dependency with no conflicts. |
| `recharts@^2.15.3` | `react@19.2.3`, `react-dom@19.2.3` | Recharts 2.x supports React 18+. React 19 compatibility is confirmed — the pulse-mockup runs this exact combination. |

---

## Sources

- `pulse-mockup/src/components/workspace/signal-chart.tsx` — Confirmed chart types: `AreaChart` (for `"line"`), `BarChart` (for `"bar"`), `ScatterChart` (for `"scatter"`). No other Recharts types used.
- `pulse-mockup/src/lib/mock-data.ts` — `ChartType = "line" | "bar" | "scatter"` type definition confirmed.
- `pulse-mockup/package.json` — `recharts ^2.15.3` (resolved to 2.15.4 per package-lock.json).
- `frontend/package.json` — Confirmed `recharts` is NOT present in main frontend.
- `admin-frontend/package.json` — `recharts ^2` already present.
- `backend/pyproject.toml` — Confirmed `scipy`, `statsmodels`, `scikit-learn` NOT present.
- [SciPy 1.17.1 on PyPI](https://pypi.org/project/SciPy/) — Current version 1.17.1 (released 2026-02-22) — HIGH confidence.
- [statsmodels 0.14.6 on PyPI](https://pypi.org/project/statsmodels/) — Current version 0.14.6 (released 2025-12-05) — HIGH confidence.
- [scikit-learn 1.8.0 documentation](https://scikit-learn.org/stable/index.html) — Current stable version 1.8.0 — HIGH confidence.
- [Recharts API documentation](https://recharts.github.io/en-US/api/) — `AreaChart`, `BarChart`, `ScatterChart` API verified stable in v2.x — HIGH confidence.

---

*Stack research for: v0.8 Spectra Pulse (Detection) — additive changes to existing Spectra platform*
*Researched: 2026-03-05*
