# Milestone v1.0 — Simulation & What-If Modeling (Model)

## Overview

This milestone completes the Analysis Workspace with the **Model stage** — sensitivity analysis, lever playground with interactive sliders, and scenario comparison. Users go from root cause → "what happens if I change X?" with confidence intervals, not point estimates. This is where Spectra becomes a business optimization tool.

**Prerequisite:** UI/UX mockups for the Model stage (3a sensitivity overview → 3b lever playground → 3c scenario comparison) must be completed and reviewed before engineering.

## 1. Sensitivity Analysis (Step 3a)

### 1.1 Sensitivity Overview
- After a root cause is identified, Spectra identifies adjustable business levers from the data
- **Tornado chart** shows which variables have the most impact on the target KPI (±10% perturbation)
- Prevents users from wasting time on levers that don't matter
- Example: "Price has 3x more impact than headcount on operating margin"

### 1.2 Sensitivity Methods
- Systematic perturbation of regression inputs
- Linear regression to establish lever → outcome relationships
- Elasticity estimation (% change in outcome per % change in input)

## 2. Lever Playground (Step 3b)

### 2.1 Interactive Simulation UI
- Sliders and number inputs for top variables identified in sensitivity analysis
- Real-time projected outcome updates as user adjusts sliders
- **Always show confidence bands** — not just point estimates ("Revenue: $1.0M–$1.3M" not "$1.15M")
- Disclaimer: "Based on historical relationships in your data. Does not account for external factors."

### 2.2 Goal Seeking (Reverse Solve)
- User sets a target goal ("I want to reach $1.2M revenue")
- Spectra reverse-solves: "You'd need to reduce price by ~8% to hit that target"
- Breakeven analysis: "What value of X gets me to target Y?"

### 2.3 Simulation Methods
- **Linear regression** — default for all simulation (simple, interpretable)
- **Elasticity estimation** — log-log regression for intuitive % change metrics
- **Holt-Winters extrapolation** — baseline "current trajectory" projection with trend + seasonality
- **Monte Carlo simulation** — confidence intervals via thousands of random-variation reruns
- **Breakeven analysis** — algebraic inversion of regression equation

## 3. Scenario Comparison (Step 3c)

### 3.1 Scenario Management
- User names and saves different lever configurations as scenarios (e.g., "Conservative", "Moderate", "Aggressive")
- Each scenario stores: lever values, projected outcomes, confidence intervals
- Scenarios linked to root cause

### 3.2 Comparison UI
- **Comparison table:** columns = scenarios, rows = outcome metrics
- **Overlay chart:** all scenarios plotted on same axis, color-coded, with confidence bands
- User selects preferred scenario → Spectra auto-generates recommendation summary

### 3.3 Scenario Reports
- Each scenario comparison auto-generates a `scenario` type Report
- Report includes: sensitivity overview, lever settings, projected outcomes, comparison table, recommendation
- Added to Collection's reports list

## 4. Design Principles

1. **Always show confidence intervals, never just point estimates.** A range ("$0.9M–$1.3M at 90% confidence") is honest. A single number creates false precision.
2. **Start with linear regression, not complex ML.** Users need to understand *why* the model predicts what it does.
3. **Show model limitations explicitly.** "This projection assumes historical relationships continue. It does not account for competitor actions, market shifts, or capacity constraints."
4. **Sensitivity analysis before simulation.** Show which levers matter before letting users play with sliders.

## 5. Backend Requirements

### 5.1 Modeling Agent
- New agent type for the Model stage
- Runs regression, elasticity, Monte Carlo, Holt-Winters in E2B sandbox
- Returns structured results with confidence intervals

### 5.2 Scenario API
- Scenario CRUD within a Root Cause
- Scenario comparison endpoint
- Scenario → Report compilation

## 6. Out of Scope
- Complex ML models (neural networks, ensemble methods) — start simple
- Real-time data streaming simulation
- Multi-user collaborative scenarios
- Monitoring / recurring (post-v1.0 backlog)

## 7. Success Criteria
- 3 test scenarios → user can set up and run a meaningful simulation in < 2 minutes without help
- Confidence intervals shown on all projections — no bare point estimates
- Tornado chart correctly ranks variables by impact
- Goal seeking produces reasonable inverse solutions
- Scenario comparison table and overlay chart render correctly with 2-3 scenarios
- Users trust the simulation: model limitations are transparently communicated
