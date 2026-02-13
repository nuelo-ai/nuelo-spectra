/**
 * Chart type compatibility utility.
 * Analyzes Plotly chart JSON to determine switchable chart types and current type.
 */

export type SwitchableChartType = 'bar' | 'line' | 'scatter';

/**
 * Detects the current chart type from Plotly JSON.
 * Returns null if chart is not switchable (pie, histogram, box, etc.).
 */
export function detectCurrentChartType(chartDataJson: string): SwitchableChartType | null {
  try {
    const chartData = JSON.parse(chartDataJson);
    const trace = chartData.data?.[0];

    if (!trace) {
      return null;
    }

    const traceType = trace.type;
    const traceMode = trace.mode;

    // Bar chart
    if (traceType === 'bar') {
      return 'bar';
    }

    // Scatter-based charts (line and scatter)
    if (traceType === 'scatter') {
      // Line chart: mode includes 'lines'
      if (traceMode && traceMode.includes('lines')) {
        return 'line';
      }
      // Scatter chart: mode includes 'markers' or mode is undefined/null
      if (traceMode && traceMode.includes('markers')) {
        return 'scatter';
      }
      // Default scatter when mode is unspecified
      if (!traceMode) {
        return 'scatter';
      }
    }

    // Non-switchable types (pie, histogram, box, etc.)
    return null;
  } catch (err) {
    console.error('Error detecting chart type:', err);
    return null;
  }
}

/**
 * Returns array of compatible chart types for the given chart data.
 * Empty array means chart type is not switchable.
 */
export function getCompatibleChartTypes(chartDataJson: string): SwitchableChartType[] {
  try {
    // First check if current type is switchable
    const currentType = detectCurrentChartType(chartDataJson);
    if (currentType === null) {
      return [];
    }

    // Parse to analyze data shape
    const chartData = JSON.parse(chartDataJson);
    const trace = chartData.data?.[0] as Record<string, unknown>;

    if (!trace) {
      return [];
    }

    // Check if both x and y exist and are arrays
    const hasXY = Array.isArray(trace.x) && Array.isArray(trace.y);

    if (!hasXY) {
      // If data shape is unusual, only allow current type
      return [currentType];
    }

    // Determine if x-axis is numeric or categorical
    const xArray = trace.x as unknown[];
    const firstXValue = xArray.find((val) => val !== null && val !== undefined);

    if (firstXValue === undefined) {
      // No valid x values, return only current type
      return [currentType];
    }

    const xIsNumeric = typeof firstXValue === 'number';

    if (xIsNumeric) {
      // Numeric x-axis: all three types are compatible
      return ['bar', 'line', 'scatter'];
    } else {
      // Categorical x-axis: bar and line work, scatter doesn't make sense
      return ['bar', 'line'];
    }
  } catch (err) {
    console.error('Error getting compatible chart types:', err);
    return [];
  }
}
