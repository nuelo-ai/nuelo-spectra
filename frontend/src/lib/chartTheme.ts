import type { Layout, PlotData } from 'plotly.js-dist-min';

/**
 * Nord palette — 16 color constants
 * https://www.nordtheme.com/docs/colors-and-palettes
 */
export const NORD_PALETTE = {
  // Polar Night (dark backgrounds)
  nord0: '#2e3440',
  nord1: '#3b4252',
  nord2: '#434c5e',
  nord3: '#4c566a',
  // Snow Storm (light text on dark backgrounds)
  nord4: '#d8dee9',
  nord5: '#e5e9f0',
  nord6: '#eceff4',
  // Frost (blue tones)
  nord7: '#8fbcbb',
  nord8: '#88c0d0',
  nord9: '#81a1c1',
  nord10: '#5e81ac',
  // Aurora (accent colors for data visualization)
  nord11: '#bf616a', // red
  nord12: '#d08770', // orange
  nord13: '#ebcb8b', // yellow
  nord14: '#a3be8c', // green
  nord15: '#b48ead', // purple
} as const;

/**
 * Darkened Aurora variants for light mode.
 * Pure Aurora colors wash out on white backgrounds, so we deepen them for contrast.
 */
export const LIGHT_AURORA = {
  red: '#a54e56',
  orange: '#b86f5d',
  yellow: '#c9a956',
  green: '#8a9d78',
  purple: '#9a7a96',
} as const;

/**
 * Get Plotly layout configuration for the current theme.
 * Applies Nord palette colors and layout properties to match platform theme.
 *
 * @param theme - 'light' or 'dark'
 * @returns Partial Plotly layout object with theme-specific colors
 */
export function getChartThemeConfig(theme: 'light' | 'dark'): Partial<Layout> {
  if (theme === 'dark') {
    return {
      paper_bgcolor: NORD_PALETTE.nord1, // subtle card-like tint
      plot_bgcolor: NORD_PALETTE.nord0, // slightly darker chart area for depth
      colorway: [
        NORD_PALETTE.nord11,
        NORD_PALETTE.nord12,
        NORD_PALETTE.nord13,
        NORD_PALETTE.nord14,
        NORD_PALETTE.nord15,
      ],
      font: {
        color: NORD_PALETTE.nord4,
      },
      title: {
        font: {
          color: NORD_PALETTE.nord5, // brighter for titles
        },
      },
      xaxis: {
        gridcolor: 'rgba(67, 76, 94, 0.3)', // Nord 2 at 30% opacity
        gridwidth: 1,
        title: {
          font: {
            color: NORD_PALETTE.nord4,
          },
        },
        tickfont: {
          color: NORD_PALETTE.nord3, // one step dimmer than axis labels
        },
        zerolinecolor: 'rgba(67, 76, 94, 0.3)',
      },
      yaxis: {
        gridcolor: 'rgba(67, 76, 94, 0.3)',
        gridwidth: 1,
        title: {
          font: {
            color: NORD_PALETTE.nord4,
          },
        },
        tickfont: {
          color: NORD_PALETTE.nord3,
        },
        zerolinecolor: 'rgba(67, 76, 94, 0.3)',
      },
      legend: {
        orientation: 'h',
        y: -0.2,
        xanchor: 'center',
        x: 0.5,
        font: {
          color: NORD_PALETTE.nord4,
        },
        bgcolor: 'rgba(0,0,0,0)',
      },
      hoverlabel: {
        bgcolor: NORD_PALETTE.nord1,
        font: {
          color: NORD_PALETTE.nord6,
        },
        bordercolor: NORD_PALETTE.nord3,
      },
    };
  } else {
    // Light mode
    return {
      paper_bgcolor: '#f9fafb', // Tailwind gray-50
      plot_bgcolor: '#ffffff',
      colorway: [
        LIGHT_AURORA.red,
        LIGHT_AURORA.orange,
        LIGHT_AURORA.yellow,
        LIGHT_AURORA.green,
        LIGHT_AURORA.purple,
      ],
      font: {
        color: '#374151', // Tailwind gray-700
      },
      title: {
        font: {
          color: '#1f2937', // Tailwind gray-800
        },
      },
      xaxis: {
        gridcolor: '#e5e7eb', // Tailwind gray-200
        gridwidth: 1,
        title: {
          font: {
            color: '#374151',
          },
        },
        tickfont: {
          color: '#9ca3af', // Tailwind gray-400 — dimmer than labels
        },
        zerolinecolor: '#e5e7eb',
      },
      yaxis: {
        gridcolor: '#e5e7eb',
        gridwidth: 1,
        title: {
          font: {
            color: '#374151',
          },
        },
        tickfont: {
          color: '#9ca3af',
        },
        zerolinecolor: '#e5e7eb',
      },
      legend: {
        orientation: 'h',
        y: -0.2,
        xanchor: 'center',
        x: 0.5,
        font: {
          color: '#374151',
        },
        bgcolor: 'rgba(0,0,0,0)',
      },
      hoverlabel: {
        bgcolor: '#ffffff',
        font: {
          color: '#1f2937',
        },
        bordercolor: '#e5e7eb',
      },
    };
  }
}

/**
 * Get pie/donut chart text overrides for the current theme.
 * Ensures white text on colored slices, theme-appropriate outside text.
 *
 * @param theme - 'light' or 'dark'
 * @returns Partial Plotly trace data for pie charts
 */
export function getPieChartOverrides(theme: 'light' | 'dark'): Record<string, unknown> {
  return {
    textfont: {
      color: '#ffffff', // white text on colored slices
      size: 14,
    },
    insidetextfont: {
      color: '#ffffff',
    },
    outsidetextfont: {
      color: theme === 'dark' ? NORD_PALETTE.nord4 : '#374151',
    },
  };
}
