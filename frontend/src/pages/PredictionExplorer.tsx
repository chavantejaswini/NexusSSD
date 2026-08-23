import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { predictDrive } from "../api/predict";
import type { DriveSummary, PredictResponse } from "../api/types";
import { Card, ErrorState, RiskBadge, Spinner, StatusBadge } from "../components/ui";
import { useDrives } from "../hooks/useDrives";
import { formatPct } from "../lib/format";
import { riskBand } from "../lib/viz";

type SortKey = "serial_number" | "risk";

export function PredictionExplorer() {
  const { data, isLoading, isError } = useDrives({ limit: 200 });
  const [sortKey, setSortKey] = useState<SortKey>("risk");
  const [asc, setAsc] = useState(false);
  const [explained, setExplained] = useState<Record<number, PredictResponse>>({});

  const predict = useMutation({
    mutationFn: predictDrive,
    onSuccess: (res) => {
      if (res.drive_id != null) setExplained((prev) => ({ ...prev, [res.drive_id!]: res }));
    },
  });

  const rows = useMemo(() => {
    const items = [...(data?.items ?? [])];
    items.sort((a, b) => {
      let cmp: number;
      if (sortKey === "serial_number") {
        cmp = a.serial_number.localeCompare(b.serial_number);
      } else {
        cmp = (a.latest_failure_probability ?? -1) - (b.latest_failure_probability ?? -1);
      }
      return asc ? cmp : -cmp;
    });
    return items;
  }, [data, sortKey, asc]);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState />;

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) setAsc((v) => !v);
    else {
      setSortKey(key);
      setAsc(key === "serial_number");
    }
  };

  const arrow = (key: SortKey) => (key === sortKey ? (asc ? " ▲" : " ▼") : "");

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Prediction Explorer</h1>
      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="cursor-pointer py-2" onClick={() => toggleSort("serial_number")}>
                Serial{arrow("serial_number")}
              </th>
              <th className="py-2">Model</th>
              <th className="py-2">Status</th>
              <th className="cursor-pointer py-2 text-right" onClick={() => toggleSort("risk")}>
                Failure risk{arrow("risk")}
              </th>
              <th className="py-2 text-right">Band</th>
              <th className="py-2 text-right">Explain</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((d: DriveSummary) => {
              const exp = explained[d.id];
              return (
                <tr key={d.id} className="border-b border-white/5 align-top">
                  <td className="py-2 font-medium">{d.serial_number}</td>
                  <td className="py-2 text-slate-400">{d.model}</td>
                  <td className="py-2">
                    <StatusBadge status={d.status} />
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {formatPct(d.latest_failure_probability, 1)}
                  </td>
                  <td className="py-2 text-right">
                    <RiskBadge band={riskBand(d.latest_failure_probability)} />
                  </td>
                  <td className="py-2 text-right">
                    <button
                      onClick={() => predict.mutate(d.id)}
                      className="rounded-md border border-white/10 px-2 py-1 text-xs hover:bg-white/5"
                    >
                      {exp ? "↻" : "Predict"}
                    </button>
                    {exp && (
                      <div className="mt-1 text-left text-[11px] text-slate-500">
                        {exp.top_features.slice(0, 3).map((f) => (
                          <div key={f.name}>
                            {f.name}: {f.value.toFixed(1)}
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
