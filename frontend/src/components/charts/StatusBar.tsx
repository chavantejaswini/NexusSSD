import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DriveStatus } from "../../api/types";
import { CHART, DRIVE_STATUS_META } from "../../lib/viz";
import { ChartTooltip } from "./ChartTooltip";

// Drive counts by status. Color is the reserved status palette; the x-axis
// category label + value label carry identity, so meaning is never color-alone.
export function StatusBar({ counts }: { counts: Record<DriveStatus, number> }) {
  const data = (Object.keys(DRIVE_STATUS_META) as DriveStatus[])
    .map((status) => ({
      status,
      label: DRIVE_STATUS_META[status].label,
      color: DRIVE_STATUS_META[status].color,
      count: counts[status] ?? 0,
    }))
    .filter((d) => d.count > 0);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 12, right: 8, bottom: 0, left: -16 }}>
        <XAxis dataKey="label" tick={{ fill: CHART.axis, fontSize: 11 }} stroke={CHART.grid} />
        <YAxis tick={{ fill: CHART.axis, fontSize: 10 }} stroke={CHART.grid} allowDecimals={false} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Bar dataKey="count" name="Drives" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.status} fill={d.color} />
          ))}
          <LabelList dataKey="count" position="top" fill={CHART.axis} fontSize={11} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
