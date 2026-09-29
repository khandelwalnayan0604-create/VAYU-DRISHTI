import React from "react";
import { Activity, CheckCircle2, AlertTriangle, PowerOff } from "lucide-react";
import { DataStateBadge } from "./DataStateBadge";

const STATUS_ICON = {
  ok: { Icon: CheckCircle2, cls: "text-emerald-400" },
  stale: { Icon: AlertTriangle, cls: "text-amber-400" },
  disabled: { Icon: PowerOff, cls: "text-slate-500" },
};

export default function OperatorSourceHealth({ t, connectors }) {
  return (
    <section data-testid="source-health-panel" className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-center gap-2 mb-3">
        <Activity className="w-4 h-4 text-cyan-400" />
        <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200">{t("sources")}</h3>
      </div>
      <div className="space-y-2">
        {connectors.map((c) => {
          const si = STATUS_ICON[c.status] || STATUS_ICON.ok;
          return (
            <div key={c.key} data-testid={`connector-${c.key}`} className="rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <si.Icon className={`w-3.5 h-3.5 ${si.cls}`} />
                    <span className="text-xs font-semibold text-slate-100 truncate">{c.name}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5 truncate">{c.product}</div>
                </div>
                <DataStateBadge state={c.data_state} testid={`connector-badge-${c.key}`} />
              </div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-2 text-[10px] font-mono">
                <div className="text-slate-500">{t("latency")}: <span className="text-slate-300">{c.latency_s}s</span></div>
                <div className="text-slate-500">Cadence: <span className="text-slate-300">{c.cadence_min}m</span></div>
                <div className="col-span-2 text-slate-500 truncate">{t("coverage")}: <span className="text-slate-300">{c.coverage}</span></div>
                <div className="col-span-2 text-slate-500 truncate">
                  Src: <span className="text-slate-400">{(c.source_time_ist || "").replace("T", " ").slice(0, 16)} IST</span>
                </div>
              </div>
              {c.quality_flags && c.quality_flags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {c.quality_flags.map((q) => (
                    <span key={q} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">{q}</span>
                  ))}
                </div>
              )}
              {c.error && <div className="text-[10px] text-rose-400 mt-1">{c.error}</div>}
            </div>
          );
        })}
      </div>
    </section>
  );
}
