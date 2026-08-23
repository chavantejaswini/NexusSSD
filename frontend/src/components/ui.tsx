import type { ReactNode } from "react";
import type { DriveStatus, RiskBand } from "../api/types";
import { DRIVE_STATUS_META, RISK_META } from "../lib/viz";

export function Card({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-white/10 bg-nexus-panel/60 p-4 ${className}`}
    >
      {(title || action) && (
        <header className="mb-3 flex items-center justify-between">
          {title && <h2 className="text-sm font-medium text-slate-300">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function StatTile({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-nexus-panel/60 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-3xl font-semibold" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium text-slate-200">
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

export function StatusBadge({ status }: { status: DriveStatus }) {
  const meta = DRIVE_STATUS_META[status];
  return <Pill label={meta.label} color={meta.color} />;
}

export function RiskBadge({ band }: { band: RiskBand | null }) {
  if (band == null) return <span className="text-xs text-slate-500">—</span>;
  const meta = RISK_META[band];
  return <Pill label={meta.label} color={meta.color} />;
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return <div className="py-8 text-center text-sm text-slate-500">{label}</div>;
}

export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="rounded-md border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
      {message ?? "Something went wrong. Is the API running?"}
    </div>
  );
}
