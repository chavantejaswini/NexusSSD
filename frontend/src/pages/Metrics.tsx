import { API_BASE_URL } from "../api/client";
import { Card, Spinner, StatTile } from "../components/ui";
import { useDrives } from "../hooks/useDrives";
import { useHealth } from "../hooks/useHealth";
import { STATUS_COLOR } from "../lib/viz";

export function Metrics() {
  const health = useHealth();
  const drives = useDrives({ limit: 200 });

  const items = drives.data?.items ?? [];
  const scored = items.filter((d) => d.latest_failure_probability != null).length;

  const dbOk = health.data?.db === "ok";
  const apiOk = !health.isError && health.data?.status === "ok";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">System Metrics</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile
          label="API"
          value={apiOk ? "Online" : "Offline"}
          accent={apiOk ? STATUS_COLOR.good : STATUS_COLOR.critical}
        />
        <StatTile
          label="Database"
          value={dbOk ? "OK" : "Error"}
          accent={dbOk ? STATUS_COLOR.good : STATUS_COLOR.critical}
        />
        <StatTile label="Drives tracked" value={items.length} />
        <StatTile
          label="Drives scored"
          value={scored}
          hint={scored ? "predictions loaded" : "not scored yet"}
        />
      </div>

      <Card title="Service">
        {health.isLoading ? (
          <Spinner />
        ) : (
          <dl className="grid grid-cols-2 gap-y-2 text-sm sm:grid-cols-4">
            <dt className="text-slate-500">Version</dt>
            <dd className="text-slate-200">{health.data?.version ?? "—"}</dd>
            <dt className="text-slate-500">Environment</dt>
            <dd className="text-slate-200">{health.data?.environment ?? "—"}</dd>
            <dt className="text-slate-500">API base</dt>
            <dd className="col-span-3 truncate text-slate-200">{API_BASE_URL}</dd>
          </dl>
        )}
      </Card>
    </div>
  );
}
