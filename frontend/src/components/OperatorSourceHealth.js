import React from "react";
import { Activity, CheckCircle2, AlertTriangle, PowerOff, Lock } from "lucide-react";
import { DataStateBadge } from "./DataStateBadge";

const STATUS_ICON = {
  ok: { Icon: CheckCircle2, cls: "text-emerald-400" },
  simulated: { Icon: Activity, cls: "text-amber-400" },
  stale: { Icon: AlertTriangle, cls: "text-amber-400" },
  disabled: { Icon: PowerOff, cls: "text-slate-500" },
};

export default function OperatorSourceHealth({ t, connectors }) {
  return (
    <section data-testid="source-health-panel" className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-center gap-2 mb-3">
        <Activity className="w-4 h-4 text-cyan-400" />
        <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200">{t("sources")}</h3>
        <span className="ml-auto text-[9px] font-mono text-slate-500 uppercase tracking-widest">mixed state</span>
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
                    {c.real && <span className="text-[8px] font-mono font-bold px-1 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/50">REAL</span>}
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
              {!c.real && c.authorized_status && (
                <div data-testid={`connector-authorized-${c.key}`} className="mt-2 flex items-start gap-1.5 text-[10px] rounded-md bg-slate-950/60 border border-slate-800 px-2 py-1.5">
                  <Lock className="w-3 h-3 mt-0.5 text-slate-500 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-slate-300">Authorized feed: <span className="text-amber-300">{c.authorized_status}</span></div>
                    <div className="text-slate-500 truncate">{c.authorized_provider} · {c.access_route}</div>
                  </div>
                </div>
              )}
              {c.attribution && (
                <div className="mt-1.5 text-[9px] font-mono text-slate-500 truncate">
                  Data source: <span className={c.real ? "text-emerald-400" : "text-slate-400"}>{c.attribution}</span>
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
