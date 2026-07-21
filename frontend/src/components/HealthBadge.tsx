import { useHealth } from "../hooks/useHealth";

export function HealthBadge() {
  const { data, isLoading, isError } = useHealth();

  const online = !isError && data?.status === "ok";
  const label = isLoading
    ? "checking…"
    : isError
      ? "API offline"
      : `API ${data?.status} · db ${data?.db}`;

  const dotColor = isLoading
    ? "bg-amber-400"
    : online
      ? "bg-emerald-400"
      : "bg-rose-500";

  return (
    <div className="flex items-center gap-2 rounded-full bg-nexus-panel px-3 py-1 text-xs text-slate-300 ring-1 ring-white/10">
      <span className={`h-2 w-2 rounded-full ${dotColor}`} />
      <span>{label}</span>
      {data?.version && <span className="text-slate-500">v{data.version}</span>}
    </div>
  );
}
