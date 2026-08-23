// Chart tokens (dark-surface values from the validated data-viz palette) and
// status/risk mappings. Status colors are the reserved status palette and are
// always paired with a text label — never color alone.

import type { DriveStatus, RiskBand } from "../api/types";

export const CHART = {
  series1: "#3987e5", // sequential/single-series blue (dark step)
  axis: "#898781", // muted ink
  grid: "rgba(255,255,255,0.08)", // recessive hairline grid
  tooltipBg: "#141d2e",
  tooltipBorder: "rgba(255,255,255,0.12)",
} as const;

export const STATUS_COLOR = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
  muted: "#898781",
} as const;

export const DRIVE_STATUS_META: Record<
  DriveStatus,
  { label: string; color: string }
> = {
  healthy: { label: "Healthy", color: STATUS_COLOR.good },
  at_risk: { label: "At risk", color: STATUS_COLOR.warning },
  failed: { label: "Failed", color: STATUS_COLOR.critical },
  decommissioned: { label: "Decommissioned", color: STATUS_COLOR.muted },
};

export function riskBand(probability: number | null): RiskBand | null {
  if (probability == null) return null;
  if (probability >= 0.7) return "high";
  if (probability >= 0.3) return "medium";
  return "low";
}

export const RISK_META: Record<RiskBand, { label: string; color: string }> = {
  low: { label: "Low", color: STATUS_COLOR.good },
  medium: { label: "Medium", color: STATUS_COLOR.warning },
  high: { label: "High", color: STATUS_COLOR.critical },
};
