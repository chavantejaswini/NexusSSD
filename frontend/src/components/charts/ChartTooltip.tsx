import type { TooltipProps } from "recharts";
import { CHART } from "../../lib/viz";

// Themed tooltip shared by the charts.
export function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      className="rounded-md px-3 py-2 text-xs shadow-lg"
      style={{ background: CHART.tooltipBg, border: `1px solid ${CHART.tooltipBorder}` }}
    >
      {label != null && <div className="mb-1 text-slate-400">{label}</div>}
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: entry.color }}
          />
          <span className="text-slate-300">{entry.name}</span>
          <span className="ml-auto font-medium tabular-nums text-slate-100">
            {typeof entry.value === "number" ? entry.value.toLocaleString() : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}
