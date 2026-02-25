# Spectra API Reference

Spectra exposes a REST API and an MCP server for programmatic data analysis. Both are served by the `spectra-api` service at `https://api.yourdomain.com`.

---

## Getting Started

### 1. Create an API Key

API keys are managed from within the Spectra web application:

1. Log in to Spectra at `https://app.yourdomain.com`
2. Go to **Settings → API Keys**
3. Click **Create Key**, enter a name and optional description
4. Copy the full key immediately — it is shown **once** and cannot be retrieved again

All API keys start with the prefix `spe_`.

### 2. Make Your First Request

```bash
# Check service health
curl https://api.yourdomain.com/api/v1/health

# List your files
curl -H "Authorization: Bearer spe_YOUR_KEY" \
  https://api.yourdomain.com/api/v1/files
```

### 3. Interactive API Docs

The full OpenAPI (Swagger) documentation is available at:

```
https://api.yourdomain.com/docs
```

---

## Authentication

All API endpoints (except `/health` and `/api/v1/health`) require an API key passed as a Bearer token:

```
Authorization: Bearer spe_YOUR_KEY
```

**Key management endpoints** (`GET/POST/DELETE /api/v1/keys`) use your Spectra account JWT instead of an API key. These are called by the web application on your behalf when you manage keys in Settings.

**Security notes:**
- Store API keys in environment variables, never in source code
- Revoked keys return `401` immediately on any request
- Keys are scoped to the account that created them — they only access that account's files and credits

---

## Response Format

All API responses use a consistent envelope:

### Success

```json
{
  "success": true,
  "data": { ... },
  "credits_used": 1.0
}
```

`credits_used` is only present on endpoints that consume credits (currently `POST /api/v1/chat/query`). It is `null` on all other endpoints.

### Error

```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "File not found. Verify the file_id exists and belongs to your account."
  }
}
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Access denied to the requested resource |
| `FILE_NOT_FOUND` | 404 | File ID does not exist or does not belong to your account |
| `INVALID_REQUEST` | 400 | Request body is malformed or missing required fields |
| `INVALID_FILE_TYPE` | 400 | File type not supported. Allowed: `.csv`, `.xlsx`, `.xls` |
| `FILE_TOO_LARGE` | 400 | File exceeds the 50 MB maximum |
| `FILE_VALIDATION_FAILED` | 400 | File could not be parsed as a valid CSV or Excel file |
| `FILE_NOT_ONBOARDED` | 400 | File was uploaded but AI analysis has not completed yet |
| `TOO_MANY_FILES` | 400 | More files provided than the platform limit allows per query |
| `INSUFFICIENT_CREDITS` | 402 | Account has no remaining credits |
| `ONBOARDING_FAILED` | 500 | AI analysis failed during upload. The file was saved — retry the upload |
| `ANALYSIS_FAILED` | 500 | Query execution failed. Credits are automatically refunded |
| `ANALYSIS_TIMEOUT` | 500 | Query exceeded the maximum execution time. Credits are automatically refunded |

---

## Credits

Credits are consumed when running analysis queries (`POST /api/v1/chat/query`). Each query deducts one credit unit from your account balance.

**Credit behaviour:**
- Credits are deducted **before** the query runs
- If the query fails or times out, credits are **automatically refunded**
- The `credits_used` field in the response confirms the amount deducted
- Credit balance and top-up are managed by your Spectra admin

---

## REST API Endpoints

### Health

#### `GET /health`

Basic service health check. No authentication required. No database query.

```bash
curl https://api.yourdomain.com/health
```

```json
{"status": "ok"}
```

#### `GET /api/v1/health`

Extended health check including database connectivity. No authentication required. Use this for external uptime monitoring.

```bash
curl https://api.yourdomain.com/api/v1/health
```

```json
{
  "status": "healthy",
  "service": "spectra-api",
  "version": "v0.7",
  "database": "connected"
}
```

`status` is `"healthy"` when the database is connected, `"degraded"` when it is not.

---

### Files

#### `POST /api/v1/files/upload`

Upload a CSV or Excel file. Triggers AI onboarding synchronously — the response is returned once onboarding completes. Use the returned `id` in all subsequent file and query requests.

**Supported formats:** `.csv`, `.xlsx`, `.xls` (max 50 MB)

```bash
curl -X POST https://api.yourdomain.com/api/v1/files/upload \
  -H "Authorization: Bearer spe_YOUR_KEY" \
  -F "file=@sales_data.csv"
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "filename": "sales_data.csv",
    "data_brief": "This dataset contains 1,200 rows of monthly sales records...",
    "query_suggestions": [
      "What is the total revenue by region?",
      "Which product category had the highest growth?"
    ],
    "created_at": "2026-02-25T10:00:00.000Z"
  }
}
```

---

#### `GET /api/v1/files`

List all files in your account.

```bash
curl https://api.yourdomain.com/api/v1/files \
  -H "Authorization: Bearer spe_YOUR_KEY"
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "filename": "sales_data.csv",
      "created_at": "2026-02-25T10:00:00.000Z",
      "updated_at": "2026-02-25T10:01:00.000Z"
    }
  ]
}
```

---

#### `DELETE /api/v1/files/{file_id}`

Delete a file by ID. The file and its stored data are permanently removed.

```bash
curl -X DELETE https://api.yourdomain.com/api/v1/files/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer spe_YOUR_KEY"
```

**Response:**

```json
{"success": true, "data": {"deleted": true}}
```

---

#### `GET /api/v1/files/{file_id}/download`

Download the original file as a binary stream.

```bash
curl -O -J https://api.yourdomain.com/api/v1/files/3fa85f64-5717-4562-b3fc-2c963f66afa6/download \
  -H "Authorization: Bearer spe_YOUR_KEY"
```

Returns the file with `Content-Disposition: attachment` and `Content-Type: application/octet-stream`.

---

### File Context

#### `GET /api/v1/files/{file_id}/context`

Retrieve the AI-generated data brief, user-provided context notes, and suggested questions for a file.

```bash
curl https://api.yourdomain.com/api/v1/files/3fa85f64-5717-4562-b3fc-2c963f66afa6/context \
  -H "Authorization: Bearer spe_YOUR_KEY"
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "filename": "sales_data.csv",
    "data_brief": "This dataset contains 1,200 rows of monthly sales records...",
    "data_summary": "This dataset contains 1,200 rows of monthly sales records...",
    "user_context": "Q1 2025 sales data for the APAC region",
    "query_suggestions": ["What is the total revenue by region?"],
    "created_at": "2026-02-25T10:00:00.000Z"
  }
}
```

---

#### `PUT /api/v1/files/{file_id}/context`

Add or update your own context notes for a file. This context is included when the AI runs analysis, helping it understand domain-specific nuances.

```bash
curl -X PUT https://api.yourdomain.com/api/v1/files/3fa85f64-5717-4562-b3fc-2c963f66afa6/context \
  -H "Authorization: Bearer spe_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_context": "Revenue figures are in USD thousands. Exclude Q4 outliers."}'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_context": "Revenue figures are in USD thousands. Exclude Q4 outliers."
  }
}
```

---

#### `GET /api/v1/files/{file_id}/suggestions`

Get the AI-generated query suggestions for a file.

```bash
curl https://api.yourdomain.com/api/v1/files/3fa85f64-5717-4562-b3fc-2c963f66afa6/suggestions \
  -H "Authorization: Bearer spe_YOUR_KEY"
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_suggestions": [
      "What is the total revenue by region?",
      "Which product category had the highest growth?"
    ]
  }
}
```

---

### Query

#### `POST /api/v1/chat/query`

Run a natural language analysis query against one or more uploaded files. This endpoint consumes credits.

The file must have completed onboarding (i.e. `data_brief` is populated in the upload response or context endpoint) before it can be queried.

```bash
curl -X POST https://api.yourdomain.com/api/v1/chat/query \
  -H "Authorization: Bearer spe_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total revenue by region for Q1?",
    "file_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    "web_search_enabled": false
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural language question about the data |
| `file_ids` | array of UUIDs | Yes | One or more file IDs to analyse. All files must belong to your account and have completed onboarding |
| `web_search_enabled` | boolean | No | Whether to allow the AI to search the web during analysis (default: `false`) |

**Response:**

```json
{
  "success": true,
  "credits_used": 1.0,
  "data": {
    "analysis": "The total revenue for Q1 breaks down as follows: APAC $4.2M (38%), EMEA $3.8M (34%), Americas $3.1M (28%)...",
    "generated_code": "import pandas as pd\n\ndf = pd.read_csv('sales_data.csv')\nresult = df[df['quarter'] == 'Q1'].groupby('region')['revenue'].sum()\nprint(result)",
    "chart_specs": "{\"data\":[{\"type\":\"bar\",\"x\":[\"APAC\",\"EMEA\",\"Americas\"],\"y\":[4200000,3800000,3100000],\"name\":\"Revenue\"}],\"layout\":{\"title\":\"Q1 Revenue by Region\",\"xaxis\":{\"title\":\"Region\"},\"yaxis\":{\"title\":\"Revenue (USD)\"},\"height\":400}}"
  }
}
```

**Response data fields:**

| Field | Type | Description |
|-------|------|-------------|
| `analysis` | string | Narrative analysis answering your question |
| `generated_code` | string | The Python code generated and executed to produce the analysis |
| `chart_specs` | string \| null | JSON string containing a Plotly figure spec. `null` when the query does not produce a visualisation (e.g. a single-number answer) |

---

#### Data Visualisation — Rendering `chart_specs`

`chart_specs` is a **JSON string** containing a complete [Plotly](https://plotly.com/javascript/) figure specification. Parse it before use:

```js
const figure = JSON.parse(response.data.chart_specs);
// figure.data   → array of trace objects (the datasets)
// figure.layout → chart title, axis labels, height, colors
```

**Figure structure:**

```json
{
  "data": [
    {
      "type": "bar",
      "x": ["APAC", "EMEA", "Americas"],
      "y": [4200000, 3800000, 3100000],
      "name": "Revenue"
    }
  ],
  "layout": {
    "title": "Q1 Revenue by Region",
    "xaxis": { "title": "Region", "type": "category" },
    "yaxis": { "title": "Revenue (USD)" },
    "height": 400,
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)"
  }
}
```

**Supported chart types** — the `data[].type` field will be one of:

| Type | When generated |
|------|---------------|
| `bar` | Categorical comparisons (≤ 8 categories: vertical, > 8: horizontal) |
| `pie` | Part-of-whole with ≤ 8 categories |
| `scatter` | Two numeric columns, or with `mode: "lines"` for time series |
| `histogram` | Single numeric column with many unique values |
| `box` | Distribution or spread queries |

---

**Rendering with Plotly.js (recommended)**

Plotly.js is the direct target format — no data conversion required.

```bash
npm install plotly.js-dist-min
# or for TypeScript types:
npm install plotly.js @types/plotly.js
```

**Vanilla JS:**

```html
<div id="chart"></div>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script>
  const figure = JSON.parse(response.data.chart_specs);

  Plotly.newPlot('chart', figure.data, figure.layout, {
    responsive: true,
    displayModeBar: false,
  });
</script>
```

**React:**

```bash
npm install react-plotly.js plotly.js
```

```tsx
import Plot from 'react-plotly.js';

function SpectraChart({ chartSpecs }: { chartSpecs: string }) {
  const figure = JSON.parse(chartSpecs);

  return (
    <Plot
      data={figure.data}
      layout={{ ...figure.layout, autosize: true }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%' }}
    />
  );
}
```

**Next.js** — import dynamically to avoid SSR errors:

```tsx
import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });
```

---

**Rendering with Chart.js**

Chart.js uses a different data model — you need to map Plotly traces manually. Use this when you already have Chart.js in your stack and prefer not to add Plotly.

```bash
npm install chart.js react-chartjs-2
```

```tsx
import { Bar, Line, Pie, Scatter } from 'react-chartjs-2';
import {
  Chart,
  BarElement, LineElement, PointElement, ArcElement,
  CategoryScale, LinearScale, Title, Tooltip, Legend,
} from 'chart.js';

Chart.register(
  BarElement, LineElement, PointElement, ArcElement,
  CategoryScale, LinearScale, Title, Tooltip, Legend
);

function plotlyToChartJs(chartSpecs: string) {
  const figure = JSON.parse(chartSpecs);
  const trace = figure.data[0];
  const layout = figure.layout ?? {};

  return {
    type: trace.type === 'scatter' && trace.mode?.includes('lines') ? 'line' : trace.type,
    data: {
      labels: trace.x ?? [],
      datasets: figure.data.map((t: any) => ({
        label: t.name ?? '',
        data: t.type === 'scatter' && !t.mode?.includes('lines')
          ? t.x.map((x: number, i: number) => ({ x, y: t.y[i] }))
          : t.y ?? t.values ?? [],
        backgroundColor: 'rgba(99, 132, 255, 0.6)',
        borderColor: 'rgb(99, 132, 255)',
        borderWidth: 1,
      })),
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: figure.data.length > 1 },
        title: { display: !!layout.title, text: layout.title },
      },
      scales: trace.type !== 'pie' ? {
        x: { title: { display: !!layout.xaxis?.title, text: layout.xaxis?.title } },
        y: { title: { display: !!layout.yaxis?.title, text: layout.yaxis?.title } },
      } : undefined,
    },
  };
}
```

---

**Rendering with Recharts**

Recharts is React-only and requires extracting `x`/`y` arrays into the `[{ key: value }]` record format it expects.

```bash
npm install recharts
```

```tsx
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function SpectraRecharts({ chartSpecs }: { chartSpecs: string }) {
  const figure = JSON.parse(chartSpecs);
  const trace = figure.data[0];
  const layout = figure.layout ?? {};

  // Convert Plotly x/y arrays to Recharts record format
  const chartData = (trace.x ?? []).map((xVal: any, i: number) => ({
    name: xVal,
    [trace.name ?? 'value']: trace.y?.[i],
  }));

  const isLine = trace.type === 'scatter' && trace.mode?.includes('lines');

  if (isLine) {
    return (
      <ResponsiveContainer width="100%" height={layout.height ?? 400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" label={{ value: layout.xaxis?.title, position: 'insideBottom' }} />
          <YAxis label={{ value: layout.yaxis?.title, angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          {figure.data.map((t: any) => (
            <Line key={t.name} type="monotone" dataKey={t.name ?? 'value'} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={layout.height ?? 400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" label={{ value: layout.xaxis?.title, position: 'insideBottom' }} />
        <YAxis label={{ value: layout.yaxis?.title, angle: -90, position: 'insideLeft' }} />
        <Tooltip />
        <Legend />
        {figure.data.map((t: any) => (
          <Bar key={t.name} dataKey={t.name ?? 'value'} fill="#6366f1" />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
```

> **Note:** Recharts does not support `pie`, `histogram`, or `box` chart types natively in the same way Plotly does. For those types, fall back to Plotly.js or Chart.js, or use Recharts' `PieChart` with an additional type check.

---

**Library comparison**

| Library | Best for | `chart_specs` compatibility | Bundle size |
|---------|----------|----------------------------|-------------|
| [Plotly.js](https://plotly.com/javascript/) | Full fidelity, all chart types | Native — no conversion needed | ~3 MB (use `plotly.js-dist-min`) |
| [react-plotly.js](https://github.com/plotly/react-plotly.js) | React apps with Plotly | Native | ~3 MB |
| [Chart.js](https://www.chartjs.org/) + [react-chartjs-2](https://react-chartjs-2.js.org/) | Lightweight, already in your stack | Manual trace mapping required | ~200 KB |
| [Recharts](https://recharts.org/) | React-only, simple bar/line | Manual data reshaping required; no pie/histogram/box | ~300 KB |
| [Vega-Lite](https://vega.github.io/vega-lite/) | Declarative grammars | Not compatible — full reimplementation needed | ~900 KB |

**Recommendation:** Use **Plotly.js** or **react-plotly.js** for the most accurate rendering with zero data conversion. Use Chart.js or Recharts only if you are already using them and need to keep bundle size minimal, noting that some chart types require additional handling.

---

### API Key Management

These endpoints are used by the Spectra web application. They require a valid **JWT** (not an API key) — authenticated via the standard web login session.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/keys` | List all your API keys (active and revoked) |
| `POST` | `/api/v1/keys` | Create a new API key |
| `DELETE` | `/api/v1/keys/{key_id}` | Revoke an API key immediately |

**Create key request body:**

```json
{
  "name": "My Integration",
  "description": "Used by my data pipeline"
}
```

**Create key response** — the `full_key` field is returned **once only**:

```json
{
  "id": "uuid",
  "name": "My Integration",
  "key_prefix": "spe_abc1",
  "full_key": "spe_abc1xxxxxxxxxxxxxxxxxxxxxxxx",
  "created_at": "2026-02-25T10:00:00.000Z"
}
```

---

## MCP Server

The Spectra MCP server lets AI assistants (Claude Desktop, Cursor, and any MCP-compatible client) interact with your data directly using natural language.

**Endpoint:** `https://api.yourdomain.com/mcp/`

**Transport:** Streamable HTTP (MCP spec 2025-03-26)

### Connecting to Claude Desktop

Add this to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "spectra": {
      "url": "https://api.yourdomain.com/mcp/",
      "headers": {
        "Authorization": "Bearer spe_YOUR_KEY"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

### Connecting to Cursor

In Cursor settings, add an MCP server with:
- **URL:** `https://api.yourdomain.com/mcp/`
- **Header:** `Authorization: Bearer spe_YOUR_KEY`

### Available MCP Tools

All tools require a valid `spe_` API key passed in the `Authorization` header of the MCP connection.

---

#### `spectra_upload_file`

Upload a CSV or Excel file to your Spectra account.

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | string | Name of the file including extension (e.g. `sales_data.csv`) |
| `file_content_base64` | string | Raw file bytes encoded as base64 |

Returns the file ID, AI-generated data brief, and suggested questions.

**Example prompt to Claude:**
> "Upload the file sales_data.csv to Spectra and tell me what it contains."

---

#### `spectra_run_analysis`

Ask a natural language question about an uploaded file. Consumes one credit per call.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | The UUID of the uploaded file |
| `question` | string | Natural language question about the data |

Returns the analysis narrative, the Python code that was executed, and any chart specification.

**Example prompt to Claude:**
> "Using Spectra, analyse the sales file and tell me which region had the highest revenue growth."

---

#### `spectra_list_files`

List all files in your Spectra account. No parameters required.

Returns a table of file IDs, filenames, and upload dates.

**Example prompt to Claude:**
> "Show me all the files I have in Spectra."

---

#### `spectra_delete_file`

Delete a file from your Spectra account.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | The UUID of the file to delete |

**Example prompt to Claude:**
> "Delete the old sales file from Spectra."

---

#### `spectra_download_file`

Download a file's content. For CSV files the content is returned as text directly in the conversation. Binary files (Excel) show file size and type metadata.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | The UUID of the file to download |

---

#### `spectra_get_context`

Get the AI-generated data brief, user context notes, and suggested questions for a file. Use this before running an analysis to understand what the file contains.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | The UUID of the file |

**Example prompt to Claude:**
> "Before we start, get the context for the Q1 sales file from Spectra."

---

### Recommended MCP Workflow

```
1. spectra_list_files          → find the file you want to work with
2. spectra_get_context         → understand what the data contains
3. spectra_run_analysis        → ask your question
```

Or, to start fresh with new data:

```
1. spectra_upload_file         → upload and onboard a new file
2. spectra_run_analysis        → ask your question immediately
```

### Security Notes

- Enable **"Ask before running tools"** in your MCP client to review tool calls before execution
- Each tool call is authenticated against your API key and consumes the same credits as the REST API
- API keys grant access to all data in your account — treat them as secrets
