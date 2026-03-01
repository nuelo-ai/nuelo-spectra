# Milestone v0.10 — Guided Q&A Investigation (Explain)

## Overview

This milestone adds the **Explain stage** — a guided, doctor-style Q&A investigation flow. When a user taps a Signal, Spectra walks them through structured questions to identify root causes. This is not freeform chat — it's a structured flow with discrete choices and progressive narrowing. One Signal can be investigated multiple times with different outcomes.

## 1. Investigation Flow

### 1.1 Investigation Initiation
- User clicks "Investigate" on a Signal card within a Collection
- Creates a new Investigation record linked to the Signal
- Spectra opens the guided Q&A interface

### 1.2 Guided Q&A UX
- **Not a chatbot.** Structured interface with discrete choice options + optional free-text input
- Spectra presents hypotheses; user confirms, challenges, or provides additional context
- 3-5 exchanges, progressively narrowing to root cause
- Each exchange shows: Spectra's question/hypothesis, evidence from data, choice options
- Think: doctor interview — start broad, narrow systematically

### 1.3 Q&A Exchange Flow
| Exchange | What Spectra Does | Statistical Method |
|----------|-------------------|--------------------|
| 1 | "Which dimension matters most?" — ranked options | Variance decomposition (ANOVA F-statistic) |
| 2 | "The change is concentrated in [segment]. Dig deeper?" | Contribution analysis + Pareto (80/20) |
| 3 | "Here's how [problem segment] differs from others." | Welch's t-test + Chi-squared |
| 4 | "These metrics also moved: [list]. Any relevant?" | Pearson/Spearman correlation scan |
| 5 | "Summary: [root cause hypothesis with confidence]" | Decision tree summary + all above |

### 1.4 Adaptive Flow
- If data lacks categorical dimensions → skip dimension selection, focus on temporal/correlation analysis
- If fewer than 3 exchanges needed → conclude early (don't pad)
- If user provides unexpected input → Spectra adapts (not rigidly scripted)
- If investigation reaches dead end → acknowledge it, suggest alternative angles

## 2. Root Cause System

### 2.1 Root Cause Identification
- Investigation produces one or more Root Cause hypotheses
- Each has: hypothesis statement, confidence level (high/medium/low), supporting evidence
- Root Causes can link across Signals — one root cause may explain multiple findings

### 2.2 Multi-Signal Linking
- After identifying a root cause, Spectra checks if it explains other Signals in the same Collection
- Presents cross-links: "This root cause may also explain Signal X and Signal Y"
- User confirms or dismisses suggested links

### 2.3 Re-Investigation
- User can investigate the same Signal again — creates a new Investigation
- Different choices → different root cause → different report
- Previous investigations are preserved (not overwritten)

## 3. Statistical Methods (Explain Stage)

### 3.1 Required Methods
- **Contribution analysis** — decomposes KPI change into per-segment contributions
- **Welch's t-test** — tests statistical significance between two groups
- **Chi-squared test** — tests independence of categorical variables
- **Pearson/Spearman correlation** — finds co-movement with other metrics
- **Decision tree (shallow, depth-2)** — identifies most discriminating factor combinations
- **Period-over-period comparison** — structured diff by dimension when time data exists
- **Variance decomposition (ANOVA)** — ranks dimensions by explanatory power
- **Pareto analysis (80/20)** — identifies the vital few segments

### 3.2 Method Selection
- Methods are selected based on data shape (same approach as Pulse)
- Not all methods apply to all datasets — graceful degradation
- Agent decides which methods to run based on the investigation context

## 4. Investigation Reports

### 4.1 Report Generation
- Each completed Investigation auto-generates an `investigation` type Report
- Report includes: Signal summary, Q&A trail, evidence visualizations, root cause conclusion
- Saved to the Collection's reports list
- Downloadable as Markdown/PDF (using v0.9 export infrastructure)

## 5. Backend Requirements

### 5.1 Investigation API
- Create Investigation from a Signal
- Store Q&A exchanges as structured trail
- Root Cause CRUD with cross-signal linking
- Investigation → Report compilation

### 5.2 Diagnostic Agent
- New agent type (or Pulse Agent extension) for the Explain stage
- Runs statistical methods in E2B based on investigation context
- Returns structured responses with evidence + choices for the Q&A flow

## 6. Out of Scope
- Simulation / what-if modeling (v1.0)
- Uploading additional documents (PDF, PPTX) as investigation context (future)
- Monitoring / recurring (post-v1.0 backlog)

## 7. Success Criteria
- 5 test scenarios with known root causes → guided flow identifies correct driver in at least 4
- Guided flow is demonstrably faster than freeform Chat for reaching root cause
- Q&A feels guided, not scripted — adapts to different data shapes
- Cross-signal linking works: one root cause correctly links to multiple related Signals
- Re-investigation works: same Signal, different choices, different outcome preserved
