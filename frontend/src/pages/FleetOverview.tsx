import { useMemo } from "react";
import type { DriveStatus, DriveSummary } from "../api/types";
import { StatusBar } from "../components/charts/StatusBar";
import { Card, ErrorState, RiskBadge, Spinner, StatTile, StatusBadge } from "../components/ui";
import { useDrives } from "../hooks/useDrives";
import { formatPct } from "../lib/format";
import { STATUS_COLOR, riskBand } from "../lib/viz";

export function FleetOverview() {
  const { data, isLoading, isError } = useDrives({ limit: 200 });

  const stats = useMemo(() => {
    const items = data?.items ?? [];
    const counts = { healthy: 0, at_risk: 0, failed: 0, decommissioned: 0 } as Record<
      DriveStatus,
      number
    >;
    let highRisk = 0;
    let probSum = 0;
    let probN = 0;
    for (const d of items) {
      counts[d.status] += 1;
      if (d.latest_failure_probability != null) {
        probSum += d.latest_failure_probability;
        probN += 1;
        if (d.latest_failure_probability >= 0.7) highRisk += 1;
      }
    }
    const topRisk = [...items]
      .filter((d) => d.latest_failure_probability != null)
      .sort(
        (a, b) => (b.latest_failure_probability ?? 0) - (a.latest_failure_probability ?? 0),
      )
      .slice(0, 6);
    return {
      total: items.length,
      counts,
      highRisk,
      avgRisk: probN ? probSum / probN : null,
      topRisk,
    };
  }, [data]);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Fleet Overview</h1>
        <p className="mt-1 text-sm text-slate-400">
          Health, risk, and telemetry trends across {stats.total} SSDs.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Total drives" value={stats.total} />
        <StatTile label="Failed" value={stats.counts.failed} accent={STATUS_COLOR.critical} />
        <StatTile
          label="High risk (≥70%)"
          value={stats.highRisk}
          accent={STATUS_COLOR.warning}
          hint="latest prediction"
        />
        <StatTile label="Avg fleet risk" value={formatPct(stats.avgRisk)} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Drives by status">
          <StatusBar counts={stats.counts} />
        </Card>

        <Card title="Highest-risk drives">
          {stats.topRisk.length === 0 ? (
            <p className="text-sm text-slate-500">
              No predictions yet. Run <code>python -m app.ml.train --score</code>.
            </p>
          ) : (
            <ul className="divide-y divide-white/5">
              {stats.topRisk.map((d: DriveSummary) => (
                <li key={d.id} className="flex items-center justify-between py-2">
                  <div>
                    <div className="font-medium">{d.serial_number}</div>
                    <div className="text-xs text-slate-500">{d.model}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={d.status} />
                    <span className="tabular-nums text-sm text-slate-300">
                      {formatPct(d.latest_failure_probability)}
                    </span>
                    <RiskBadge band={riskBand(d.latest_failure_probability)} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
