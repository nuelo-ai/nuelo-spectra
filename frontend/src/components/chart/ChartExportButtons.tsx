'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Plotly from 'plotly.js-dist-min';

interface ChartExportButtonsProps {
  /** Function that returns the chart DOM element (from ChartRendererHandle.getElement) */
  getChartElement: () => HTMLDivElement | null;
  /** Base filename for downloads (without extension) */
  filename?: string;
}

/**
 * Chart Export Buttons
 * Provides PNG and SVG download buttons for Plotly charts using Plotly.downloadImage().
 */
export function ChartExportButtons({ getChartElement, filename }: ChartExportButtonsProps) {
  const [exportingFormat, setExportingFormat] = useState<'png' | 'svg' | null>(null);

  const handleExport = async (format: 'png' | 'svg') => {
    const element = getChartElement();
    if (!element) {
      console.error('Chart element not available for export');
      return;
    }

    setExportingFormat(format);

    try {
      const sanitizedFilename = filename || 'spectra-chart';
      await Plotly.downloadImage(element, {
        format,
        width: 1200,
        height: 800,
        filename: sanitizedFilename,
      });
    } catch (error) {
      console.error(`Failed to export chart as ${format}:`, error);
    } finally {
      setExportingFormat(null);
    }
  };

  const isExporting = exportingFormat !== null;

  return (
    <div className="flex gap-2 items-center">
      <span className="text-xs text-muted-foreground">Export:</span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('png')}
        disabled={isExporting}
        className="gap-2"
      >
        <Download className="h-4 w-4" />
        {exportingFormat === 'png' ? 'Exporting...' : 'PNG'}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('svg')}
        disabled={isExporting}
        className="gap-2"
      >
        <Download className="h-4 w-4" />
        {exportingFormat === 'svg' ? 'Exporting...' : 'SVG'}
      </Button>
    </div>
  );
}
