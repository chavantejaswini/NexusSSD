import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TelemetryPoint } from "../../api/types";
import { CHART } from "../../lib/viz";
import { ChartTooltip } from "./ChartTooltip";

interface TelemetryChartProps {
  data: TelemetryPoint[];
  dataKey: keyof TelemetryPoint;
  label: string;
  color?: string;
}

// Single-series line chart (small-multiple). Title names the series, so no legend.
export function TelemetryChart({ data, dataKey, label, color = CHART.series1 }: TelemetryChartProps) {
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-slate-300">{label}</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid stroke={CHART.grid} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: CHART.axis, fontSize: 10 }}
            tickFormatter={(v: string) => v.slice(5)}
            minTickGap={28}
            stroke={CHART.grid}
          />
          <YAxis
            tick={{ fill: CHART.axis, fontSize: 10 }}
            width={44}
            stroke={CHART.grid}
            allowDecimals={false}
          />
          <Tooltip content={<ChartTooltip />} />
          <Line
            type="monotone"
            dataKey={dataKey}
            name={label}
            stroke={color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
