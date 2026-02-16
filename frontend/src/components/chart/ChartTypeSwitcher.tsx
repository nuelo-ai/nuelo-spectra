'use client';

import { useState } from 'react';
import { BarChart3, TrendingUp, Circle } from 'lucide-react';
import Plotly from 'plotly.js-dist-min';
import {
  SwitchableChartType,
  getCompatibleChartTypes,
  detectCurrentChartType,
} from '@/lib/chartTypeCompatibility';

interface ChartTypeSwitcherProps {
  /** Function to get the Plotly chart DOM element */
  getChartElement: () => HTMLDivElement | null;
  /** JSON string of original chart data (for compatibility analysis) */
  chartDataJson: string;
}

/**
 * Chart type switcher component.
 * Allows switching between bar, line, and scatter chart types using Plotly.restyle().
 * Only visible for switchable chart types (hides for pie, histogram, box, etc.).
 */
export function ChartTypeSwitcher({ getChartElement, chartDataJson }: ChartTypeSwitcherProps) {
  // Detect initial chart type
  const initialType = detectCurrentChartType(chartDataJson);

  // If not switchable, don't render
  if (initialType === null) {
    return null;
  }

  // Get compatible types
  const compatibleTypes = getCompatibleChartTypes(chartDataJson);

  // If only one type available, no switching possible
  if (compatibleTypes.length <= 1) {
    return null;
  }

  const [currentType, setCurrentType] = useState<SwitchableChartType>(initialType);

  const handleTypeChange = (newType: SwitchableChartType) => {
    // No-op if same type
    if (newType === currentType) {
      return;
    }

    const element = getChartElement();
    if (!element) {
      console.error('Chart element not found');
      return;
    }

    try {
      // Use Plotly.restyle() to change trace type without full re-render
      if (newType === 'line') {
        Plotly.restyle(element, { type: 'scatter', mode: 'lines' }, [0]);
      } else if (newType === 'scatter') {
        Plotly.restyle(element, { type: 'scatter', mode: 'markers' }, [0]);
      } else if (newType === 'bar') {
        Plotly.restyle(element, { type: 'bar', mode: undefined }, [0]);
      }

      setCurrentType(newType);
    } catch (err) {
      console.error('Error changing chart type:', err);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <span className="text-xs text-muted-foreground mr-1">Chart type:</span>
      {compatibleTypes.map((type) => (
        <button
          key={type}
          onClick={() => handleTypeChange(type)}
          className={`flex items-center gap-1 px-2 py-1 text-xs rounded border transition-colors ${
            currentType === type
              ? 'bg-primary text-primary-foreground border-primary'
              : 'bg-background hover:bg-accent border-border'
          }`}
          title={`Switch to ${type} chart`}
        >
          {/* Icon per type */}
          {type === 'bar' && <BarChart3 className="h-3 w-3" />}
          {type === 'line' && <TrendingUp className="h-3 w-3" />}
          {type === 'scatter' && <Circle className="h-3 w-3" />}
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </button>
      ))}
    </div>
  );
}
