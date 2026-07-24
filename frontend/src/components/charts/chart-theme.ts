// Values sourced from the dataviz skill's reference palette
// (references/palette.md) — validated categorical order + chart chrome.
export const chartColors = {
  light: {
    surface: "#fcfcfb",
    primaryInk: "#0b0b0b",
    secondaryInk: "#52514e",
    mutedInk: "#898781",
    gridline: "#e1e0d9",
    baseline: "#c3c2b7",
    series1: "#2a78d6", // blue — default single-series hue
  },
  dark: {
    surface: "#1a1a19",
    primaryInk: "#ffffff",
    secondaryInk: "#c3c2b7",
    mutedInk: "#898781",
    gridline: "#2c2c2a",
    baseline: "#383835",
    series1: "#3987e5",
  },
} as const;

export type ChartMode = "light" | "dark";
