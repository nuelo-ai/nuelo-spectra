// ============================================================
// Mock Data — shared across the entire pulse-mockup application
// All plans import from here for consistent types and data.
// ============================================================

// --- Types ---

export type CollectionStatus = "active" | "archived";

export interface Collection {
  id: string;
  name: string;
  description: string;
  status: CollectionStatus;
  createdAt: string;
  signalCount: number;
  filesCount: number;
  creditsUsed: number;
}

export type ProfilingStatus = "profiling" | "ready" | "error";

export interface FileItem {
  id: string;
  name: string;
  type: "csv" | "xlsx" | "xls";
  size: string;
  uploadDate: string;
  profilingStatus: ProfilingStatus;
}

export type SignalSeverity = "critical" | "warning" | "info";
export type SignalCategory = "Anomaly" | "Trend" | "Correlation" | "Opportunity";
export type ChartType = "line" | "bar" | "scatter";

export interface Signal {
  id: string;
  title: string;
  description: string;
  severity: SignalSeverity;
  category: SignalCategory;
  statisticalEvidence: string;
  chartType: ChartType;
  chartData: Record<string, unknown>[];
}

// --- Constants ---

export const CREDIT_BALANCE = 47;
export const COST_PER_FILE = 2;

// --- Mock Collections ---

export const MOCK_COLLECTIONS: Collection[] = [
  {
    id: "col-001",
    name: "Q3 Revenue Analysis",
    description: "Quarterly revenue breakdown with anomaly detection across all product lines",
    status: "active",
    createdAt: "2026-02-15",
    signalCount: 6,
    filesCount: 4,
    creditsUsed: 8,
  },
  {
    id: "col-002",
    name: "Customer Churn Study",
    description: "Monthly churn rate analysis with predictive signals for at-risk segments",
    status: "active",
    createdAt: "2026-02-20",
    signalCount: 4,
    filesCount: 3,
    creditsUsed: 6,
  },
  {
    id: "col-003",
    name: "Supply Chain Metrics",
    description: "End-to-end supply chain performance analysis with bottleneck detection",
    status: "active",
    createdAt: "2026-03-01",
    signalCount: 8,
    filesCount: 5,
    creditsUsed: 10,
  },
  {
    id: "col-004",
    name: "2025 Marketing ROI",
    description: "Historical marketing spend vs. conversion analysis across channels",
    status: "archived",
    createdAt: "2025-12-10",
    signalCount: 3,
    filesCount: 2,
    creditsUsed: 4,
  },
  {
    id: "col-005",
    name: "Employee Engagement Survey",
    description: "Annual engagement metrics with department-level trend analysis",
    status: "archived",
    createdAt: "2025-11-05",
    signalCount: 5,
    filesCount: 3,
    creditsUsed: 6,
  },
];

// --- Mock Files ---

export const MOCK_FILES: FileItem[] = [
  {
    id: "file-001",
    name: "revenue_q3_2026.csv",
    type: "csv",
    size: "2.4 MB",
    uploadDate: "2026-02-15",
    profilingStatus: "ready",
  },
  {
    id: "file-002",
    name: "product_sales_breakdown.xlsx",
    type: "xlsx",
    size: "5.1 MB",
    uploadDate: "2026-02-15",
    profilingStatus: "ready",
  },
  {
    id: "file-003",
    name: "customer_segments.csv",
    type: "csv",
    size: "1.8 MB",
    uploadDate: "2026-02-20",
    profilingStatus: "ready",
  },
  {
    id: "file-004",
    name: "churn_monthly_2025.csv",
    type: "csv",
    size: "890 KB",
    uploadDate: "2026-02-20",
    profilingStatus: "ready",
  },
  {
    id: "file-005",
    name: "supply_chain_orders.xlsx",
    type: "xlsx",
    size: "12.3 MB",
    uploadDate: "2026-03-01",
    profilingStatus: "ready",
  },
  {
    id: "file-006",
    name: "logistics_performance.csv",
    type: "csv",
    size: "3.7 MB",
    uploadDate: "2026-03-01",
    profilingStatus: "ready",
  },
  {
    id: "file-007",
    name: "warehouse_inventory.xls",
    type: "xls",
    size: "8.2 MB",
    uploadDate: "2026-03-02",
    profilingStatus: "profiling",
  },
  {
    id: "file-008",
    name: "marketing_spend_2025.csv",
    type: "csv",
    size: "1.2 MB",
    uploadDate: "2025-12-10",
    profilingStatus: "ready",
  },
];

export type ReportType =
  | "Detection Summary"
  | "Investigation Report"
  | "What-If Scenario Report"
  | "Chat Report"
  | "Custom Report";

export interface RelatedSignal {
  signalId: string;
  signalTitle: string;
  rootCauseLink: string;       // short phrase explaining the connection
}

export interface Report {
  id: string;
  collectionId: string;
  type: ReportType;
  title: string;
  generatedAt: string; // ISO date string
  markdownContent: string; // Full markdown body for the report reader
  signalId?: string;             // which signal this investigation report originated from
  relatedSignals?: RelatedSignal[];   // cross-signal connections shown at bottom of report
}

export interface ActivityItem {
  id: string;
  collectionId: string;
  timestamp: string; // ISO date string, displayed as relative or formatted
  description: string; // e.g. "Detection ran — 6 signals found"
  icon: "pulse" | "file" | "report" | "chat"; // controls icon in feed
}

// --- Mock Signals ---

export const MOCK_SIGNALS: Signal[] = [
  {
    id: "sig-001",
    title: "Revenue Anomaly Detected Q3",
    description:
      "A statistically significant revenue spike was detected in the SaaS product line during weeks 8-10 of Q3, exceeding the 3-sigma threshold. This anomaly correlates with the launch of the enterprise tier pricing update and suggests a sustained uplift rather than a one-time event.",
    severity: "critical",
    category: "Anomaly",
    statisticalEvidence:
      "Z-score: 3.42 | p-value: 0.0006 | Confidence: 99.94% | Compared against 12-month rolling baseline",
    chartType: "line",
    chartData: [
      { week: "W1", revenue: 42000, baseline: 40000 },
      { week: "W2", revenue: 41500, baseline: 40200 },
      { week: "W3", revenue: 43000, baseline: 40400 },
      { week: "W4", revenue: 42800, baseline: 40600 },
      { week: "W5", revenue: 44200, baseline: 40800 },
      { week: "W6", revenue: 43500, baseline: 41000 },
      { week: "W7", revenue: 45000, baseline: 41200 },
      { week: "W8", revenue: 52000, baseline: 41400 },
      { week: "W9", revenue: 54500, baseline: 41600 },
      { week: "W10", revenue: 56200, baseline: 41800 },
      { week: "W11", revenue: 53800, baseline: 42000 },
      { week: "W12", revenue: 55100, baseline: 42200 },
    ],
  },
  {
    id: "sig-002",
    title: "Customer Churn Rate Spike",
    description:
      "Monthly churn rate increased from 2.1% to 4.8% in the SMB segment over the last 60 days. The acceleration pattern matches a known churn cascade signature where early departures trigger peer-effect churn in connected accounts.",
    severity: "critical",
    category: "Anomaly",
    statisticalEvidence:
      "Chi-squared: 18.7 | p-value: 0.0001 | Effect size (Cramer's V): 0.31 | SMB segment only",
    chartType: "bar",
    chartData: [
      { month: "Sep", churnRate: 2.1, segment: "SMB" },
      { month: "Oct", churnRate: 2.3, segment: "SMB" },
      { month: "Nov", churnRate: 2.0, segment: "SMB" },
      { month: "Dec", churnRate: 2.8, segment: "SMB" },
      { month: "Jan", churnRate: 3.5, segment: "SMB" },
      { month: "Feb", churnRate: 4.8, segment: "SMB" },
    ],
  },
  {
    id: "sig-003",
    title: "Seasonal Demand Pattern",
    description:
      "A recurring seasonal demand pattern was identified with a 90-day cycle in the consumer electronics category. Peak demand consistently occurs in the first 3 weeks of each quarter, followed by a predictable trough. This pattern holds across 8 quarters of data.",
    severity: "info",
    category: "Trend",
    statisticalEvidence:
      "Autocorrelation lag-90: 0.87 | Seasonal decomposition R-squared: 0.91 | 8 quarters validated",
    chartType: "line",
    chartData: [
      { day: 0, demand: 1200, trend: 1100 },
      { day: 15, demand: 1450, trend: 1120 },
      { day: 30, demand: 1100, trend: 1140 },
      { day: 45, demand: 980, trend: 1160 },
      { day: 60, demand: 920, trend: 1180 },
      { day: 75, demand: 1050, trend: 1200 },
      { day: 90, demand: 1250, trend: 1220 },
      { day: 105, demand: 1480, trend: 1240 },
      { day: 120, demand: 1150, trend: 1260 },
      { day: 135, demand: 1000, trend: 1280 },
      { day: 150, demand: 950, trend: 1300 },
      { day: 165, demand: 1100, trend: 1320 },
      { day: 180, demand: 1300, trend: 1340 },
    ],
  },
  {
    id: "sig-004",
    title: "Marketing Spend vs. Conversion Correlation",
    description:
      "Strong positive correlation identified between social media ad spend and conversion rate, but with diminishing returns above $15K/month. The relationship follows a logarithmic curve suggesting an optimal spend ceiling.",
    severity: "info",
    category: "Correlation",
    statisticalEvidence:
      "Pearson r: 0.89 | R-squared: 0.79 | Optimal spend threshold: $15,200/mo | Diminishing returns coefficient: -0.023",
    chartType: "scatter",
    chartData: [
      { spend: 5000, conversions: 120 },
      { spend: 7500, conversions: 185 },
      { spend: 9000, conversions: 220 },
      { spend: 10000, conversions: 250 },
      { spend: 12000, conversions: 290 },
      { spend: 13500, conversions: 310 },
      { spend: 15000, conversions: 325 },
      { spend: 17000, conversions: 330 },
      { spend: 20000, conversions: 338 },
      { spend: 22000, conversions: 340 },
      { spend: 25000, conversions: 342 },
    ],
  },
  {
    id: "sig-005",
    title: "Inventory Turnover Bottleneck",
    description:
      "Warehouse C consistently shows 40% slower inventory turnover compared to other facilities. Cross-referencing with logistics data reveals a correlation with the regional carrier scheduling delays in the Pacific Northwest corridor.",
    severity: "warning",
    category: "Anomaly",
    statisticalEvidence:
      "ANOVA F-statistic: 12.4 | p-value: 0.002 | Warehouse C turnover: 3.2x vs. network avg: 5.3x",
    chartType: "bar",
    chartData: [
      { warehouse: "A", turnover: 5.8 },
      { warehouse: "B", turnover: 5.4 },
      { warehouse: "C", turnover: 3.2 },
      { warehouse: "D", turnover: 5.1 },
      { warehouse: "E", turnover: 5.6 },
    ],
  },
  {
    id: "sig-006",
    title: "Cross-sell Opportunity in Enterprise Tier",
    description:
      "Enterprise accounts using the analytics module are 3.2x more likely to adopt the reporting add-on within 60 days. Currently 68% of eligible accounts have not been targeted for this cross-sell opportunity, representing an estimated $420K ARR expansion.",
    severity: "info",
    category: "Opportunity",
    statisticalEvidence:
      "Lift ratio: 3.2x | Untapped accounts: 68% (142/209) | Estimated ARR impact: $420K | Confidence: 95%",
    chartType: "bar",
    chartData: [
      { segment: "With Analytics", adoptionRate: 72 },
      { segment: "Without Analytics", adoptionRate: 22 },
      { segment: "Targeted", adoptionRate: 85 },
      { segment: "Not Targeted", adoptionRate: 18 },
    ],
  },
  {
    id: "sig-007",
    title: "Delivery Time Degradation Trend",
    description:
      "Average delivery time has increased by 18% over the past 4 months, from 3.2 days to 3.8 days. The trend is accelerating and, if unchecked, projects to exceed the 4.5-day SLA threshold within 6 weeks.",
    severity: "warning",
    category: "Trend",
    statisticalEvidence:
      "Linear regression slope: +0.15 days/month | R-squared: 0.94 | SLA breach projection: 6 weeks",
    chartType: "line",
    chartData: [
      { month: "Oct", avgDays: 3.2, sla: 4.5 },
      { month: "Nov", avgDays: 3.3, sla: 4.5 },
      { month: "Dec", avgDays: 3.4, sla: 4.5 },
      { month: "Jan", avgDays: 3.6, sla: 4.5 },
      { month: "Feb", avgDays: 3.8, sla: 4.5 },
      { month: "Mar (proj)", avgDays: 4.0, sla: 4.5 },
      { month: "Apr (proj)", avgDays: 4.3, sla: 4.5 },
      { month: "May (proj)", avgDays: 4.6, sla: 4.5 },
    ],
  },
  {
    id: "sig-008",
    title: "Employee Engagement Decline in Engineering",
    description:
      "Engineering department engagement scores dropped 12 points year-over-year, the largest decline of any department. Exit interview data correlates with concerns about tooling and on-call rotation burden.",
    severity: "warning",
    category: "Trend",
    statisticalEvidence:
      "YoY change: -12 pts (78 to 66) | Department rank: last of 8 | Correlation with attrition: r=0.76",
    chartType: "bar",
    chartData: [
      { department: "Engineering", score: 66 },
      { department: "Product", score: 78 },
      { department: "Sales", score: 82 },
      { department: "Marketing", score: 75 },
      { department: "Support", score: 71 },
      { department: "Finance", score: 80 },
      { department: "HR", score: 84 },
      { department: "Operations", score: 73 },
    ],
  },
];

// --- Mock Reports ---

export const MOCK_REPORTS: Report[] = [
  {
    id: "rep-001",
    collectionId: "col-001",
    type: "Detection Summary",
    title: "Q3 Revenue — Detection Summary",
    generatedAt: "2026-02-16",
    markdownContent: `# Detection Summary: Q3 Revenue Analysis\n\n**Generated:** February 16, 2026  \n**Collection:** Q3 Revenue Analysis  \n**Files analyzed:** 4  \n**Detection duration:** 28 seconds  \n**Credits used:** 8\n\n---\n\n## Overview\n\nPulse detection identified **6 signals** across the Q3 Revenue Analysis dataset. Two signals were rated critical severity, requiring immediate attention. Four signals were informational, highlighting patterns useful for forecasting.\n\n## Signals Detected\n\n### 1. Revenue Anomaly Detected Q3 ⚠️ Critical\n\nA statistically significant revenue spike was detected in the SaaS product line during weeks 8–10 of Q3, exceeding the 3-sigma threshold.\n\n- **Z-score:** 3.42\n- **p-value:** 0.0006\n- **Confidence:** 99.94%\n- **Baseline:** 12-month rolling average\n\nThis anomaly correlates with the launch of the enterprise tier pricing update and suggests a sustained uplift rather than a one-time event.\n\n### 2. Customer Churn Rate Spike ⚠️ Critical\n\nMonthly churn rate increased from 2.1% to 4.8% in the SMB segment over the last 60 days.\n\n- **Chi-squared:** 18.7\n- **p-value:** 0.0001\n- **Effect size (Cramer's V):** 0.31\n\n### 3. Seasonal Demand Pattern ℹ️ Informational\n\nA recurring 90-day seasonal demand cycle was confirmed with R-squared of 0.91 across 8 quarters.\n\n## Recommendations\n\n1. **Investigate the revenue spike** — Run Guided Investigation on Signal 1 to determine root cause and sustainability.\n2. **Act on churn signal** — SMB churn acceleration requires immediate retention intervention.\n3. **Use seasonal pattern for planning** — Adjust Q4 inventory and staffing based on confirmed 90-day cycle.\n\n## Raw Statistics\n\n| Signal | Severity | p-value | Confidence |\n|--------|----------|---------|------------|\n| Revenue Anomaly | Critical | 0.0006 | 99.94% |\n| Churn Rate Spike | Critical | 0.0001 | 99.99% |\n| Seasonal Pattern | Info | — | 91% R² |\n| Marketing Correlation | Info | — | 79% R² |\n`,
  },
  {
    id: "rep-002",
    collectionId: "col-001",
    type: "Investigation Report",
    title: "Revenue Spike — Root Cause Investigation",
    generatedAt: "2026-02-18",
    signalId: "sig-001",
    markdownContent: `# Investigation Report: Revenue Spike Root Cause\n\n**Generated:** February 18, 2026  \n**Signal investigated:** Revenue Anomaly Detected Q3  \n**Investigation exchanges:** 4  \n**Confidence:** High\n\n---\n\n## Root Cause\n\n> The Q3 revenue spike is attributable to a **successful enterprise tier pricing update** that triggered accelerated upgrades from mid-market accounts, combined with a seasonal enterprise budget flush in weeks 8–10.\n\n**Confidence:** High (87%)\n\n## Evidence Chain\n\n1. Enterprise tier launch date aligns exactly with spike onset (week 8)\n2. Mid-market upgrade rate increased 340% in the same period\n3. Pattern matches Q3 budget flush behavior from prior 3 years\n4. No external market event explains the magnitude independently\n\n## Supporting Data\n\n| Factor | Contribution | Confidence |\n|--------|-------------|------------|\n| Enterprise tier launch | 62% | High |\n| Budget flush timing | 28% | Medium |\n| Unknown factors | 10% | Low |\n\n## Next Steps\n\n- Model a What-If scenario: sustain enterprise pricing uplift into Q4\n- Monitor whether upgrade rate normalizes or sustains\n`,
  },
  {
    id: "rep-003",
    collectionId: "col-001",
    type: "Chat Report",
    title: "Chat Export — Revenue Breakdown Analysis",
    generatedAt: "2026-02-20",
    markdownContent: `# Chat Export: Revenue Breakdown Analysis\n\n**Saved from Chat:** February 20, 2026  \n**Added to collection by:** Demo User\n\n---\n\n## Analysis: Revenue by Product Line\n\nBased on the uploaded Q3 data, here is the revenue breakdown by product line for Q3 2026:\n\n| Product Line | Q3 Revenue | QoQ Change | YoY Change |\n|---|---|---|---|\n| SaaS Enterprise | $2,840,000 | +34% | +67% |\n| SaaS Mid-Market | $1,220,000 | +12% | +28% |\n| Professional Services | $480,000 | -5% | +3% |\n| Marketplace Fees | $195,000 | +8% | +22% |\n| **Total** | **$4,735,000** | **+19%** | **+41%** |\n\n## Key Observations\n\nThe SaaS Enterprise line shows a disproportionately large quarter-over-quarter jump of 34%, which is the primary driver of the overall revenue anomaly detected by Pulse. Mid-Market growth of 12% is healthy but within expected range. Professional Services contracted slightly, likely due to team capacity constraints in Q3.\n\n## Interpretation\n\nThe enterprise tier pricing change introduced in week 8 appears to have accelerated upgrade decisions from mid-market accounts, pulling them into the enterprise segment faster than the historical migration rate would predict.\n`,
  },
  {
    id: "rpt-inv-001",
    collectionId: "col-001",
    type: "Investigation Report",
    title: "Investigation — Enterprise Pricing Impact",
    generatedAt: "2026-03-01",
    signalId: "sig-001",
    relatedSignals: [
      {
        signalId: "sig-004",
        signalTitle: "Marketing Spend vs. Conversion Correlation",
        rootCauseLink: "Same enterprise pricing change drove both conversion improvement and revenue uplift",
      },
    ],
    markdownContent: `# Investigation Report: Enterprise Pricing Impact\n\n**Generated:** March 1, 2026  \n**Signal investigated:** Revenue Anomaly Detected Q3  \n**Investigation exchanges:** 3  \n**Confidence:** High\n\n---\n\n## Signal Summary\n\nA statistically significant revenue spike was detected in the SaaS product line during weeks 8–10 of Q3 2026, exceeding the 3-sigma threshold with a Z-score of 3.42. The anomaly persisted beyond the initial detection window, suggesting a structural shift rather than a transient event. Total revenue during the spike period was approximately 28% above the 12-month rolling baseline.\n\n## Signal Analysis\n\nPulse detection identified the revenue anomaly by comparing week-over-week SaaS revenue against a rolling 12-month baseline. The spike onset at week 8 coincides precisely with the enterprise tier pricing update rollout date. Statistical modeling confirms the anomaly is not attributable to seasonal variance or known cyclical patterns in the dataset.\n\n## Investigation Analysis\n\nBased on the guided investigation Q&A, the primary driver of the revenue spike is the enterprise tier pricing launch. User context confirmed that revenue remained elevated beyond the initial launch period, indicating that the pricing change drove permanent rather than one-time uplift. Enterprise accounts were identified as the segment with the strongest adoption of the new pricing tier.\n\nThe sustained nature of the revenue elevation is consistent with a structural demand shift: existing mid-market accounts accelerated their upgrade timeline to lock in the new enterprise feature set, while net-new enterprise deals closed at a faster rate due to the improved value proposition at the new price point.\n\nCross-referencing with segment data, enterprise account count grew 18% in the same period, confirming that account growth — not just per-account expansion — contributed to the revenue uplift. This dual driver (account growth + pricing uplift per account) explains the magnitude of the anomaly.\n\n## Supporting Evidence\n\n| Metric | Pre-Spike (W1–W7) | Spike Period (W8–W12) | Change |\n|--------|-------------------|----------------------|--------|\n| Weekly SaaS Revenue (avg) | $43,286 | $54,320 | +25.5% |\n| Enterprise Account Count | 142 | 168 | +18.3% |\n| Avg Revenue per Enterprise Account | $1,840 | $1,930 | +4.9% |\n\n## Recommendations\n\n- **Monitor sustainability:** Track enterprise revenue through Q4 to confirm the uplift is structural. If revenue normalizes, revisit the seasonal demand hypothesis.\n- **Replicate in other segments:** Evaluate whether a mid-market pricing tier update could produce similar uplift without cannibalizing existing enterprise growth.\n- **Run a What-If scenario:** Model projected Q4 revenue under three assumptions — sustained uplift, partial reversion, and full reversion — to inform board-level forecasting.\n`,
  },
  {
    id: "rpt-inv-002",
    collectionId: "col-001",
    type: "Investigation Report",
    title: "Investigation — Seasonal Demand Hypothesis",
    generatedAt: "2026-03-03",
    signalId: "sig-001",
    relatedSignals: [],
    markdownContent: `# Investigation Report: Seasonal Demand Hypothesis\n\n**Generated:** March 3, 2026  \n**Signal investigated:** Revenue Anomaly Detected Q3  \n**Investigation exchanges:** 2  \n**Confidence:** Medium\n\n---\n\n## Signal Summary\n\nThe Q3 revenue anomaly shows a 28% spike above the 12-month rolling baseline during weeks 8–10, with a Z-score of 3.42 and 99.94% confidence. The timing of this spike aligns with both the enterprise tier pricing launch and the historically observed Q3 enterprise budget flush window — creating two competing hypotheses for the root cause.\n\n## Signal Analysis\n\nPulse detection flagged the revenue event as statistically anomalous relative to prior quarters. The anomaly window is narrow (3 weeks), which is consistent with seasonal demand surges but also consistent with the adoption curve of a new pricing tier in its launch window. Distinguishing between the two requires analyst context.\n\n## Investigation Analysis\n\nThis investigation explored the seasonal demand hypothesis. User context identified seasonal demand increase as the primary driver, with SaaS subscriptions as the most correlated product category. This framing suggests the spike reflects a recurring Q3 enterprise budget cycle rather than a structural change driven by the pricing update.\n\nIf the seasonal hypothesis holds, the revenue uplift should partially or fully revert in Q4 as the budget flush cycle ends. The fact that SaaS subscriptions — rather than one-time professional services — drove the spike is consistent with a seasonal renewal and expansion pattern where enterprises renew annual contracts and add seats before fiscal year-end.\n\n## Supporting Evidence\n\n| Metric | Q1 2026 | Q2 2026 | Q3 2026 | YoY Q3 Change |\n|--------|---------|---------|---------|---------------|\n| SaaS Subscription Revenue | $3.8M | $3.6M | $4.7M | +38% |\n| Professional Services Revenue | $0.5M | $0.6M | $0.5M | +2% |\n| Enterprise Renewal Rate | 88% | 86% | 94% | +7pts |\n\n## Recommendations\n\n- **Compare to prior Q3 cycles:** Pull Q3 2024 and Q3 2025 SaaS revenue to test whether a similar seasonal spike appeared in those years.\n- **Separate renewal from expansion:** Isolate new ARR from renewal ARR in the Q3 data to determine whether the spike is driven by renewals (seasonal) or net new expansion (pricing change).\n- **Re-run investigation with pricing data:** If renewal data confirms seasonality, close this signal. If expansion ARR is the driver, the enterprise pricing launch hypothesis (inv-001) is more likely correct.\n`,
  },
  {
    id: "rep-whatif-001",
    collectionId: "col-001",
    type: "What-If Scenario Report",
    title: "What-If Scenario Report — Enterprise Revenue Q4",
    generatedAt: "2026-03-05",
    signalId: "sig-001",
    markdownContent: `# What-If Scenario Report: Enterprise Revenue Q4\n\n**Generated:** March 5, 2026  \n**Signal:** Revenue Anomaly Detected Q3  \n**Investigation basis:** Enterprise Pricing Impact (inv-001)  \n**Objective:** Sustain enterprise revenue growth into Q4 without over-relying on pricing changes\n\n---\n\n## Objective\n\nFollowing the root cause investigation that confirmed the Q3 revenue spike was driven by the enterprise tier pricing update, this What-If analysis explores three scenarios for sustaining growth into Q4 without creating pricing instability.\n\n## Root Cause Context\n\nThe investigation (inv-001) found that the Q3 revenue spike was primarily attributable to the enterprise tier pricing launch, which triggered accelerated upgrades from mid-market accounts. Confidence: High (87%). The risk for Q4 is that this growth is partly structural and partly a one-time cohort effect.\n\n## Evaluated Scenarios\n\n### Scenario 1: Enterprise Expansion Play\n*Confidence: High*\n\nAccelerate enterprise account expansion by targeting the 68% of eligible accounts not yet on the analytics add-on. A structured 90-day outreach campaign would capture latent upgrade potential before Q4 budget cycles close.\n\n**Estimated impact:** +14–20% Q4 enterprise revenue growth  \n**Key assumptions:**\n- 40%+ of targeted accounts respond within 90 days\n- Average expansion ARR per account remains near $4,200\n- Sales team capacity is available in parallel with renewals\n- No major competitive pricing disruption\n\n### Scenario 2: Mid-Market Tier Bridge\n*Confidence: Medium*\n\nIntroduce a mid-market pricing tier to retain accounts that upgraded opportunistically in Q3 before they churn back to a lower tier.\n\n**Estimated impact:** +8–13% reduction in post-Q3 revenue churn risk  \n**Key assumptions:**\n- 15–25% of Q3 enterprise upgrades came from opportunistic mid-market upgrades\n- A mid-market tier at 60–70% of enterprise price retains the at-risk cohort\n- Product team delivers feature differentiation within 6 weeks\n\n### Scenario 3: Seasonal Demand Lock-In\n*Confidence: Low*\n\nPursue annual contract renewals before Q4 budget freezes to lock in the Q3 revenue floor regardless of whether seasonal reversion occurs.\n\n**Estimated impact:** +5–9% annualized ARR stabilization  \n**Key assumptions:**\n- 60%+ of Q3 expanded accounts are not yet on annual contracts\n- One-time implementation credit (~$500) is sufficient to drive lock-in\n- Q4 seasonal reversion risk is real\n\n## AI-Recommended Approach\n\n**Recommended: Scenario 1 — Enterprise Expansion Play**\n\nScenario 1 is recommended as the primary Q4 strategy. The data backing is strongest (3.2x adoption lift ratio, 142 clearly identified target accounts), the revenue upside is largest (+14–20%), and the execution path is well-defined. The 90-day timeline fits within Q4 without requiring product or pricing changes.\n\nScenario 2 should be evaluated in parallel as a risk mitigation measure if analysis of Q3 upgrade cohort data confirms opportunistic mid-market upgrades. Scenario 3 is a contingency hedge if Q4 data shows early signs of seasonal reversion.\n`,
  },
];

// --- Chat Types and Mock Data ---

export type ChatMessageRole = "user" | "assistant";
export type ChatResultType = "table" | "chart" | "text";

export interface ChatResultCard {
  id: string;
  type: ChatResultType;
  title: string;
  content: string; // Markdown text for "text" type; description for table/chart
  tableData?: { headers: string[]; rows: string[][] }; // For type="table"
  chartDescription?: string; // For type="chart" — describe the chart shown
}

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string; // User message text or assistant prose text
  resultCards?: ChatResultCard[]; // Assistant messages may have result cards
}

export const MOCK_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: "msg-001",
    role: "user",
    content: "Show me a breakdown of revenue by product line for Q3 2026",
  },
  {
    id: "msg-002",
    role: "assistant",
    content: "Here's the Q3 2026 revenue breakdown by product line based on your uploaded data:",
    resultCards: [
      {
        id: "card-001",
        type: "table",
        title: "Revenue by Product Line — Q3 2026",
        content: "Quarterly revenue table showing performance across all product lines.",
        tableData: {
          headers: ["Product Line", "Q3 Revenue", "QoQ Change", "YoY Change"],
          rows: [
            ["SaaS Enterprise", "$2,840,000", "+34%", "+67%"],
            ["SaaS Mid-Market", "$1,220,000", "+12%", "+28%"],
            ["Professional Services", "$480,000", "-5%", "+3%"],
            ["Marketplace Fees", "$195,000", "+8%", "+22%"],
            ["Total", "$4,735,000", "+19%", "+41%"],
          ],
        },
      },
    ],
  },
  {
    id: "msg-003",
    role: "user",
    content: "Can you chart the SaaS enterprise revenue trend over the past 6 months?",
  },
  {
    id: "msg-004",
    role: "assistant",
    content: "Here's the SaaS Enterprise revenue trend for the past 6 months. The upward trajectory starting in September aligns with the enterprise tier pricing update.",
    resultCards: [
      {
        id: "card-002",
        type: "chart",
        title: "SaaS Enterprise Revenue — 6-Month Trend",
        content: "Line chart showing month-over-month SaaS Enterprise revenue from Sep 2025 to Feb 2026, with a steep upturn visible from Dec 2025 onward.",
        chartDescription: "Line chart: Sep $1.8M → Oct $1.9M → Nov $2.0M → Dec $2.3M → Jan $2.6M → Feb $2.84M",
      },
      {
        id: "card-003",
        type: "text",
        title: "Key Insight",
        content: "**Enterprise revenue growth is accelerating**, not decelerating. The +34% QoQ jump is the largest single-quarter increase in the past 8 quarters. If this trend sustains into Q4, annual enterprise ARR could reach $12.8M — a 58% YoY increase. This growth appears structural (driven by the pricing tier change) rather than seasonal.",
      },
    ],
  },
];

// --- Investigation Types ---

export type InvestigationStatus = "none" | "in-progress" | "complete";

export interface QAExchange {
  id: string;
  question: string;
  choices: string[];          // 3-4 radio-button choices
  selectedChoice: string | null;  // null = not yet answered
  freeTextAnswer: string | null;  // null = used a choice
}

export interface InvestigationSession {
  id: string;
  signalId: string;
  collectionId: string;
  status: InvestigationStatus;
  startedAt: string;           // ISO date string
  completedAt: string | null;
  reportId: string | null;     // links to a Report with type "Investigation Report"
  exchanges: QAExchange[];
}

// --- Mock Investigation Sessions ---

export const MOCK_INVESTIGATION_SESSIONS: InvestigationSession[] = [
  {
    id: "inv-001",
    signalId: "sig-001",
    collectionId: "col-001",
    status: "complete",
    startedAt: "2026-03-01T08:00:00Z",
    completedAt: "2026-03-01",
    reportId: "rpt-inv-001",
    exchanges: [
      {
        id: "exc-001-1",
        question: "What is the primary driver you believe caused the revenue spike?",
        choices: [
          "Enterprise tier pricing launch",
          "Seasonal demand increase",
          "One-time bulk order",
          "Marketing campaign",
        ],
        selectedChoice: "Enterprise tier pricing launch",
        freeTextAnswer: null,
      },
      {
        id: "exc-001-2",
        question: "Did the spike persist beyond the initial launch period?",
        choices: [
          "Yes, revenue remained elevated",
          "No, it returned to baseline",
          "Partially — some retained, some reverted",
          "Unclear from the data",
        ],
        selectedChoice: "Yes, revenue remained elevated",
        freeTextAnswer: null,
      },
      {
        id: "exc-001-3",
        question: "Which customer segment showed the strongest uptake?",
        choices: [
          "Enterprise accounts",
          "Mid-market",
          "SMB",
          "All segments equally",
        ],
        selectedChoice: "Enterprise accounts",
        freeTextAnswer: null,
      },
    ],
  },
  {
    id: "inv-002",
    signalId: "sig-001",
    collectionId: "col-001",
    status: "complete",
    startedAt: "2026-03-03T09:00:00Z",
    completedAt: "2026-03-03",
    reportId: "rpt-inv-002",
    exchanges: [
      {
        id: "exc-002-1",
        question: "What is the primary driver you believe caused the revenue spike?",
        choices: [
          "Enterprise tier pricing launch",
          "Seasonal demand increase",
          "One-time bulk order",
          "Marketing campaign",
        ],
        selectedChoice: "Seasonal demand increase",
        freeTextAnswer: null,
      },
      {
        id: "exc-002-2",
        question: "Is this spike correlated with a specific product category?",
        choices: [
          "SaaS subscriptions",
          "Professional services",
          "Hardware",
          "Multiple categories",
        ],
        selectedChoice: "SaaS subscriptions",
        freeTextAnswer: null,
      },
    ],
  },
  {
    id: "inv-003",
    signalId: "sig-002",
    collectionId: "col-001",
    status: "in-progress",
    startedAt: "2026-03-04T10:00:00Z",
    completedAt: null,
    reportId: null,
    exchanges: [
      {
        id: "exc-003-1",
        question: "What is the primary cause of the SMB churn spike?",
        choices: [
          "Pricing increase",
          "Product gap vs competitor",
          "Support quality decline",
          "Market contraction",
        ],
        selectedChoice: "Pricing increase",
        freeTextAnswer: null,
      },
      {
        id: "exc-003-2",
        question: "How long has the pricing differential existed?",
        choices: [
          "Less than 1 month",
          "1-3 months",
          "3-6 months",
          "More than 6 months",
        ],
        selectedChoice: null,
        freeTextAnswer: null,
      },
      {
        id: "exc-003-3",
        question: "Which customer cohorts are churning first?",
        choices: [
          "Newer accounts (< 6 months)",
          "Tenured accounts (> 2 years)",
          "Both cohorts equally",
          "Recent mid-market downgrades",
        ],
        selectedChoice: null,
        freeTextAnswer: null,
      },
    ],
  },
];

// --- What-If Types ---

export type WhatIfConfidence = "high" | "medium" | "low";

export interface WhatIfScenario {
  id: string;
  name: string;
  narrative: string;                // 2-3 sentences describing the scenario
  estimatedImpact: string;          // e.g. "+12–18% reduction in lead time"
  assumptions: string[];            // 3-4 bullet points
  confidence: WhatIfConfidence;
  confidenceRationale: string;      // why the AI assigned this confidence
  dataBacking: string;              // what data supports this scenario
}

export interface WhatIfChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface WhatIfSession {
  id: string;
  signalId: string;
  collectionId: string;
  investigationSessionId: string;   // which investigation session prompted this
  objective: string;                // the stated objective
  scenarios: WhatIfScenario[];      // always 3 in mock data
  chatHistory: Record<string, WhatIfChatMessage[]>; // keyed by scenarioId
  reportId: string | null;          // links to a Report with type "What-If Scenario Report"
  createdAt: string;
}

// --- Mock What-If Sessions ---

export const MOCK_WHATIF_SESSIONS: WhatIfSession[] = [
  {
    id: "wif-001",
    signalId: "sig-001",
    collectionId: "col-001",
    investigationSessionId: "inv-001",
    objective: "Sustain enterprise revenue growth into Q4 without over-relying on pricing changes",
    scenarios: [
      {
        id: "wif-sc-001",
        name: "Enterprise Expansion Play",
        narrative: "Accelerate enterprise account expansion by targeting the 68% of eligible accounts not yet on the analytics add-on. A structured outreach campaign with a 90-day window would capture latent upgrade potential before Q4 budget cycles close.",
        estimatedImpact: "+14–20% Q4 enterprise revenue growth",
        assumptions: [
          "At least 40% of targeted accounts respond to outreach within 90 days",
          "Average expansion ARR per account remains near current $4,200",
          "Sales team has capacity to run structured outreach in parallel with renewals",
          "No major competitive pricing shift disrupts upgrade decisions",
        ],
        confidence: "high",
        confidenceRationale: "Strong historical data on analytics add-on adoption (3.2x lift ratio) and a clearly defined addressable pool of 142 accounts make this scenario well-supported by existing evidence.",
        dataBacking: "Cross-sell analysis (sig-006) shows 72% adoption rate among analytics users vs. 22% baseline. 142 of 209 eligible enterprise accounts have not been targeted. Historical Q3 expansion ARR data from revenue_q3_2026.csv.",
      },
      {
        id: "wif-sc-002",
        name: "Mid-Market Tier Bridge",
        narrative: "Introduce a mid-market pricing tier that bridges the gap between SMB and enterprise, capturing the accounts that upgraded opportunistically during Q3 before they churn back to a lower tier. A retention-focused pricing structure preserves the Q3 uplift.",
        estimatedImpact: "+8–13% reduction in post-Q3 revenue churn risk",
        assumptions: [
          "15–25% of Q3 enterprise upgrades came from mid-market accounts upgrading to lock in pricing",
          "A mid-market tier at 60–70% of enterprise price would retain the majority of at-risk accounts",
          "Product team can deliver feature differentiation within 6 weeks",
          "Pricing change does not cannibalize existing enterprise accounts",
        ],
        confidence: "medium",
        confidenceRationale: "The scenario logic is sound but depends on segment-level data not yet isolated in the current dataset. Confidence improves if mid-market upgrade cohort data is extracted separately.",
        dataBacking: "SMB churn spike signal (sig-002) and enterprise revenue anomaly (sig-001) together suggest pricing sensitivity. Q3 revenue breakdown from rep-001 shows enterprise growth was the primary driver.",
      },
      {
        id: "wif-sc-003",
        name: "Seasonal Demand Lock-In",
        narrative: "Treat Q3's elevated revenue as a seasonal window and aggressively pursue annual contract renewals before Q4 budget freezes. Locking accounts into 12-month terms at current pricing preserves the revenue floor regardless of whether Q4 shows a seasonal reversion.",
        estimatedImpact: "+5–9% annualized ARR stabilization",
        assumptions: [
          "At least 60% of Q3 expanded accounts are not yet on annual contracts",
          "Annual contract incentive (e.g., 5% discount) is sufficient to drive lock-in decisions",
          "Q4 seasonal reversion risk is real — the seasonal hypothesis from inv-002 may be partially correct",
          "Legal and finance can process contract amendments within 45 days",
        ],
        confidence: "low",
        confidenceRationale: "This scenario hedges against the seasonal reversion hypothesis (inv-002), but the data does not yet confirm whether Q3 growth was structural or seasonal. Lower confidence until renewal vs. expansion ARR is separated.",
        dataBacking: "Competing investigation conclusions from rpt-inv-001 (pricing change) and rpt-inv-002 (seasonal demand). Enterprise renewal rate data from Q1–Q3 in rep-003.",
      },
    ],
    chatHistory: {
      "wif-sc-001": [
        {
          id: "chat-sc1-001",
          role: "user",
          content: "Can you make the timeline for this scenario more specific — how does the 90-day outreach window break down?",
        },
        {
          id: "chat-sc1-002",
          role: "assistant",
          content: "Updated the scenario. The 90-day window now breaks into three phases: weeks 1–4 for identifying and prioritizing the 142 target accounts by expansion readiness score, weeks 5–10 for outreach and discovery calls, and weeks 11–13 for close and onboarding. The estimated impact range remains +14–20% but is now front-loaded toward the high end if the priority tier (top 40 accounts by usage signal) converts first.",
        },
      ],
      "wif-sc-002": [],
      "wif-sc-003": [
        {
          id: "chat-sc3-001",
          role: "user",
          content: "Change the discount assumption from 5% to a free implementation credit instead — we don't want to set a discount precedent.",
        },
        {
          id: "chat-sc3-002",
          role: "assistant",
          content: "Updated assumption 2: the incentive is now a one-time implementation credit (valued at ~$500) rather than a recurring discount, avoiding pricing precedent concerns. The estimated impact range is unchanged — the credit cost is absorbed within existing customer success budget.",
        },
      ],
    },
    reportId: "rep-whatif-001",
    createdAt: "2026-03-05T14:00:00Z",
  },
];

// --- Admin Workspace Management mock data ---

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  tier: "free" | "pro" | "enterprise";
  status: "active" | "suspended";
  credits: number;
}

export const ADMIN_USERS: AdminUser[] = [
  { id: "u1", name: "Alice Chen", email: "alice@acmecorp.com", tier: "pro", status: "active", credits: 142 },
  { id: "u2", name: "Bob Martinez", email: "bob@acmecorp.com", tier: "enterprise", status: "active", credits: 389 },
  { id: "u3", name: "Carol Smith", email: "carol@acmecorp.com", tier: "free", status: "active", credits: 27 },
  { id: "u4", name: "David Kim", email: "david@acmecorp.com", tier: "pro", status: "suspended", credits: 0 },
];

// Line chart: Collections created per month
export const COLLECTIONS_OVER_TIME = [
  { month: "Oct", count: 4 },
  { month: "Nov", count: 7 },
  { month: "Dec", count: 5 },
  { month: "Jan", count: 11 },
  { month: "Feb", count: 9 },
  { month: "Mar", count: 14 },
];

// Donut chart: active vs. archived
export const COLLECTION_STATUS_BREAKDOWN = [
  { name: "Active", value: 38, color: "#10b981" },
  { name: "Archived", value: 12, color: "#6b7280" },
];

// Bar charts: activity counts by month
export const ACTIVITY_BY_TYPE = [
  { month: "Oct", pulse: 18, investigation: 9, whatif: 4, report: 12 },
  { month: "Nov", pulse: 24, investigation: 14, whatif: 7, report: 18 },
  { month: "Dec", pulse: 19, investigation: 11, whatif: 5, report: 14 },
  { month: "Jan", pulse: 31, investigation: 19, whatif: 11, report: 23 },
  { month: "Feb", pulse: 28, investigation: 16, whatif: 9, report: 19 },
  { month: "Mar", pulse: 37, investigation: 22, whatif: 13, report: 27 },
];

// Funnel chart: pipeline adoption
export const PIPELINE_ADOPTION = [
  { stage: "Pulse Detection", count: 157, color: "#3b82f6" },
  { stage: "Explain (Investigation)", count: 89, color: "#8b5cf6" },
  { stage: "What-If Scenarios", count: 41, color: "#a78bfa" },
];

// Credit usage stacked bar by activity type over time
export const CREDIT_USAGE_OVER_TIME = [
  { month: "Oct", pulse: 36, investigation: 45, whatif: 16, report: 24 },
  { month: "Nov", pulse: 48, investigation: 70, whatif: 28, report: 36 },
  { month: "Dec", pulse: 38, investigation: 55, whatif: 20, report: 28 },
  { month: "Jan", pulse: 62, investigation: 95, whatif: 44, report: 46 },
  { month: "Feb", pulse: 56, investigation: 80, whatif: 36, report: 38 },
  { month: "Mar", pulse: 74, investigation: 110, whatif: 52, report: 54 },
];

// Per-user Workspace tab data (keyed by user id)
export interface UserCollectionSummary {
  id: string;
  name: string;
  status: "active" | "archived";
  signals: number;
  credits: number;
}

export interface UserActivityEvent {
  timestamp: string;
  event: string;
}

export interface UserWorkspaceData {
  collections: UserCollectionSummary[];
  creditBreakdown: { name: string; value: number; color: string }[];
  activityTimeline: UserActivityEvent[];
  creditsUsed: number;
  creditLimit: number;
}

export const USER_WORKSPACE_DATA: Record<string, UserWorkspaceData> = {
  u1: {
    collections: [
      { id: "c1", name: "Q3 Revenue Anomaly", status: "active", signals: 7, credits: 48 },
      { id: "c2", name: "Churn Risk Analysis", status: "active", signals: 4, credits: 31 },
      { id: "c3", name: "Product Usage Trends", status: "archived", signals: 12, credits: 63 },
    ],
    creditBreakdown: [
      { name: "Pulse", value: 48, color: "#3b82f6" },
      { name: "Investigation", value: 60, color: "#8b5cf6" },
      { name: "What-If", value: 20, color: "#a78bfa" },
      { name: "Reports", value: 14, color: "#6366f1" },
    ],
    activityTimeline: [
      { timestamp: "Mar 5, 10:42 AM", event: "Detection ran — 7 signals found" },
      { timestamp: "Mar 4, 3:18 PM", event: "Investigation completed — root cause identified" },
      { timestamp: "Mar 3, 11:05 AM", event: "What-If session started" },
      { timestamp: "Mar 2, 2:30 PM", event: "Report generated and saved" },
      { timestamp: "Feb 28, 9:14 AM", event: "New collection created: Churn Risk Analysis" },
    ],
    creditsUsed: 142,
    creditLimit: 500,
  },
  u2: {
    collections: [
      { id: "c4", name: "Enterprise Expansion", status: "active", signals: 9, credits: 72 },
      { id: "c5", name: "Pricing Model Review", status: "active", signals: 6, credits: 54 },
      { id: "c6", name: "Q4 Forecast Analysis", status: "active", signals: 11, credits: 98 },
      { id: "c7", name: "Competitor Benchmarking", status: "archived", signals: 8, credits: 65 },
      { id: "c8", name: "Market Share Trends", status: "active", signals: 5, credits: 44 },
    ],
    creditBreakdown: [
      { name: "Pulse", value: 100, color: "#3b82f6" },
      { name: "Investigation", value: 150, color: "#8b5cf6" },
      { name: "What-If", value: 80, color: "#a78bfa" },
      { name: "Reports", value: 59, color: "#6366f1" },
    ],
    activityTimeline: [
      { timestamp: "Mar 5, 9:30 AM", event: "Detection ran — 9 signals found" },
      { timestamp: "Mar 5, 8:15 AM", event: "What-If scenario finalized" },
      { timestamp: "Mar 4, 4:00 PM", event: "Investigation started on pricing anomaly" },
      { timestamp: "Mar 3, 1:22 PM", event: "Collection created: Competitor Benchmarking" },
    ],
    creditsUsed: 389,
    creditLimit: 1000,
  },
  u3: {
    collections: [
      { id: "c9", name: "Sales Pipeline Review", status: "active", signals: 3, credits: 27 },
    ],
    creditBreakdown: [
      { name: "Pulse", value: 18, color: "#3b82f6" },
      { name: "Investigation", value: 9, color: "#8b5cf6" },
    ],
    activityTimeline: [
      { timestamp: "Mar 4, 2:10 PM", event: "Detection ran — 3 signals found" },
      { timestamp: "Mar 1, 11:00 AM", event: "Collection created: Sales Pipeline Review" },
    ],
    creditsUsed: 27,
    creditLimit: 100,
  },
  u4: {
    collections: [],
    creditBreakdown: [],
    activityTimeline: [],
    creditsUsed: 0,
    creditLimit: 500,
  },
};

// Credit cost configuration
export interface CreditCostConfig {
  activity: string;
  costPerUnit: number;
  description: string;
}

export const CREDIT_COST_CONFIG: CreditCostConfig[] = [
  { activity: "Pulse Detection", costPerUnit: 5, description: "Per detection run" },
  { activity: "Investigation (Explain)", costPerUnit: 8, description: "Per investigation session" },
  { activity: "What-If Scenario", costPerUnit: 2, description: "Per scenario generated" },
  { activity: "Report Generation", costPerUnit: 3, description: "Per report saved" },
  { activity: "Chat Analysis", costPerUnit: 1, description: "Per chat session" },
  { activity: "File Profiling", costPerUnit: 2, description: "Per file uploaded" },
  { activity: "Data Export", costPerUnit: 1, description: "Per export action" },
  { activity: "API Call", costPerUnit: 1, description: "Per API request" },
];

// Alert items
export type AlertSeverity = "warning" | "critical";

export interface AlertItem {
  id: string;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
}

export const MOCK_ALERTS: AlertItem[] = [
  {
    id: "a1",
    severity: "critical",
    message: "Bob Martinez exceeded 350 credits in the last 30 days (limit: 300)",
    timestamp: "Mar 5, 2026 — 8:42 AM",
  },
  {
    id: "a2",
    severity: "warning",
    message: "Alice Chen is at 85% of monthly credit limit (142 / 500)",
    timestamp: "Mar 4, 2026 — 3:15 PM",
  },
  {
    id: "a3",
    severity: "warning",
    message: "3 users have not run any detection in the past 14 days",
    timestamp: "Mar 3, 2026 — 9:00 AM",
  },
];

// --- Mock Activity ---

export const MOCK_ACTIVITY: ActivityItem[] = [
  {
    id: "act-001",
    collectionId: "col-001",
    timestamp: "2026-02-16T10:24:00Z",
    description: "Detection ran — 6 signals found",
    icon: "pulse",
  },
  {
    id: "act-002",
    collectionId: "col-001",
    timestamp: "2026-02-15T14:10:00Z",
    description: "4 files uploaded",
    icon: "file",
  },
  {
    id: "act-003",
    collectionId: "col-001",
    timestamp: "2026-02-18T09:05:00Z",
    description: "Investigation report generated",
    icon: "report",
  },
  {
    id: "act-004",
    collectionId: "col-001",
    timestamp: "2026-02-20T16:33:00Z",
    description: "Chat result saved as report",
    icon: "chat",
  },
  {
    id: "act-005",
    collectionId: "col-001",
    timestamp: "2026-03-01T11:00:00Z",
    description: "1 new file uploaded",
    icon: "file",
  },
];
