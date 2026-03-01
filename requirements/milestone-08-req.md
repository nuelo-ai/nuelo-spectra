# Milestone v0.8 — Analysis Workspace + Spectra Pulse

## Overview

This milestone introduces the **Analysis Workspace** — a new frontend module separate from Chat — and **Spectra Pulse**, the proactive signal detection engine. Users create a Collection (workspace), select data sources, and run Pulse to surface Signals (findings) automatically. This is the "wow" moment: Spectra tells you what to pay attention to without being asked.

**Prerequisite:** UI/UX mockups for the Analysis Workspace and all 3 stages (Pulse, Explain, Model) must be reviewed and approved before engineering begins.

## 1. Analysis Workspace Module

### 1.1 Frontend Module
- New top-level route/module in Next.js app, separate from Chat
- Own navigation entry point (sidebar or top nav)
- Workspace landing page showing list of user's Collections
- Responsive layout — works on desktop and tablet

### 1.2 Collection Management
- Create new Collection with name and optional description
- List Collections with status, creation date, and signal count
- Open/resume an existing Collection
- Archive a Collection (soft delete)
- Collection is the persistent workspace — user can return anytime

### 1.3 Data Source Selection
- Select one or more files from user's uploaded files
- Upload new files directly from the Collection creation flow
- Show file summary (columns, row count, data types) before selection
- Support CSV and Excel files (existing file infrastructure)

## 2. Spectra Pulse — Signal Detection

### 2.1 Pulse Agent
- New agent type in the agent system — the Pulse Agent
- Triggered when user clicks "Run Detection" on a Collection
- Runs statistical analysis pipeline in E2B sandbox
- Returns structured Signal objects (not free-text)

### 2.2 Statistical Analysis Pipeline
- **Always run:** Descriptive profiling, missing value patterns, duplicate detection, IQR outlier detection
- **Numeric data:** Z-score outliers, distribution shape analysis, Isolation Forest (3+ numeric columns)
- **Categorical data:** Herfindahl-Hirschman Index (concentration), category distribution analysis
- **Time-series data (if time column exists):** Changepoint detection (PELT), STL decomposition, trend break detection
- **Small datasets (<30 rows):** Use Grubbs' test instead of Z-score; skip Isolation Forest, Monte Carlo
- **Graceful degradation:** Detect data shape first, only apply applicable methods

### 2.3 Signal Cards UI
- Display Signals as cards with: title (key finding), severity badge, description, visualization
- Severity classification: **opportunity** (green), **warning** (amber), **critical** (red), **info** (blue)
- Category labels: anomaly, trend, concentration, quality
- Each card has a supporting chart/visualization
- Cards ranked by impact/severity
- "Healthy data" state when no notable signals found — show health summary of checks performed

### 2.4 Signal Data Model
- Signal entity linked to Collection
- Fields: title, description, severity, category, visualization config, statistical evidence (method, values, confidence)
- Persisted to database — signals survive page refresh

## 3. Library & Infrastructure Requirements

### 3.1 E2B Sandbox Packages
- Verify `statsmodels` availability (needed for STL, ANOVA, OLS)
- Install `ruptures` package (needed for PELT changepoint detection)
- `pandas`, `numpy`, `scipy`, `scikit-learn` already available

### 3.2 Backend
- New API endpoints for Collection CRUD
- New API endpoint to trigger Pulse detection
- Signal storage and retrieval endpoints
- Credit cost for Pulse detection (define cost per run)

## 4. Out of Scope (Future Milestones)
- Report export / PDF download (v0.9)
- Guided Q&A / investigation — the Explain step (v0.10)
- Simulation / what-if modeling — the Model step (v1.0)
- Monitoring / recurring analysis (post-v1.0 backlog)
- Chat-to-Collection bridge (v0.9)

## 5. Success Criteria
- Upload 5 different real-world datasets → Pulse flags useful signals in at least 4 of them
- False positive rate < 20% (signals flagged should be genuinely interesting)
- "Healthy data" summary shown correctly when data has no notable patterns
- Collection persists — user can close browser and return to same Collection with Signals intact
- End-to-end flow works: create Collection → select data → run Pulse → see Signal cards
