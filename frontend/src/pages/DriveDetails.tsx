import { useEffect, useState } from "react";
import { TelemetryChart } from "../components/charts/TelemetryChart";
import { Card, ErrorState, RiskBadge, Spinner, StatusBadge } from "../components/ui";
import { useDrive, useDrives } from "../hooks/useDrives";
import { formatBytes, formatPct } from "../lib/format";
import { riskBand } from "../lib/viz";

export function DriveDetails() {
  const { data: list, isLoading, isError } = useDrives({ limit: 200 });
  const [selected, setSelected] = useState<number | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (selected == null && list?.items.length) setSelected(list.items[0].id);
  }, [list, selected]);

  const detail = useDrive(selected);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState />;

  const drives = (list?.items ?? []).filter((d) =>
    d.serial_number.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Drive Details</h1>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        <Card title="Drives" className="h-fit">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search serial…"
            className="mb-2 w-full rounded-md border border-white/10 bg-black/20 px-2 py-1 text-sm outline-none focus:border-nexus-accent"
          />
          <ul className="max-h-[70vh] space-y-1 overflow-auto">
            {drives.map((d) => (
              <li key={d.id}>
                <button
                  onClick={() => setSelected(d.id)}
                  className={`flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm ${
                    selected === d.id ? "bg-nexus-accent/20 text-white" : "hover:bg-white/5"
                  }`}
                >
                  <span className="truncate">{d.serial_number}</span>
                  <StatusBadge status={d.status} />
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <div className="space-y-4">
          {detail.isLoading && <Spinner />}
          {detail.data && (
            <>
              <Card>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-lg font-semibold">{detail.data.serial_number}</div>
                    <div className="text-sm text-slate-400">
                      {detail.data.model} · {formatBytes(detail.data.capacity_bytes)}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      Seen {detail.data.first_seen} → {detail.data.last_seen}
                    </div>
                  </div>
                  <div className="text-right">
                    <StatusBadge status={detail.data.status} />
                    <div className="mt-2 text-2xl font-semibold tabular-nums">
                      {formatPct(detail.data.latest_failure_probability)}
                    </div>
                    <div className="flex items-center justify-end gap-2 text-xs text-slate-500">
                      failure risk
                      <RiskBadge band={riskBand(detail.data.latest_failure_probability)} />
                    </div>
                    {detail.data.latest_prediction && (
                      <div className="mt-1 text-[11px] text-slate-600">
                        {detail.data.latest_prediction.horizon_days}-day ·{" "}
                        {detail.data.latest_prediction.model_version}
                      </div>
                    )}
                  </div>
                </div>
              </Card>

              <Card title="Telemetry">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <TelemetryChart data={detail.data.telemetry} dataKey="temperature" label="Temperature (°C)" />
                  <TelemetryChart data={detail.data.telemetry} dataKey="reallocated_sectors" label="Reallocated sectors" />
                  <TelemetryChart data={detail.data.telemetry} dataKey="media_wearout_indicator" label="Wear consumed (%)" />
                  <TelemetryChart data={detail.data.telemetry} dataKey="power_on_hours" label="Power-on hours" />
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
