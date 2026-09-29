import React from "react";
import { Bell, Download, Check } from "lucide-react";
import { severityColor, SEVERITY } from "../lib/colors";
import { capUrl } from "../lib/api";

export default function AlertPanel({ t, lang, domain, alerts, onFocusAlert, onAck }) {
  return (
    <section data-testid="alert-panel" className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-center gap-2 mb-3">
        <Bell className="w-4 h-4 text-rose-400" />
        <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200">{t("alerts")}</h3>
        <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/50">
          CAP status=Test
        </span>
      </div>

      {alerts.length === 0 && <div className="text-xs text-slate-500 py-4 text-center">{t("noWarning")}</div>}

      <div className="space-y-2">
        {alerts.map((a) => {
          const col = severityColor(a.severity);
          return (
            <div key={a.id} data-testid={`alert-card-${a.cell_id}`}
              className="rounded-lg border p-2.5" style={{ borderColor: col + "66", background: col + "14" }}>
              <div className="flex items-start justify-between gap-2">
                <button data-testid={`alert-focus-${a.cell_id}`} onClick={() => onFocusAlert(a)} className="text-left min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ background: col }} />
                    <span className="text-xs font-bold uppercase tracking-wide" style={{ color: col }}>
                      {lang === "hi" ? a.severity_label_hi : a.severity_label}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">{a.cell_id}</span>
                  </div>
                  <div className="text-[11px] text-slate-300 mt-1">
                    {t("onsetIn")} <span className="font-mono font-bold text-slate-100">~{a.lead_time_min} {t("minutes")}</span>
                    <span className="text-slate-500"> · {t("probability")} {Math.round(a.probability * 100)}% · {t("confidence")} {Math.round(a.confidence * 100)}%</span>
                  </div>
                </button>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <a data-testid={`cap-download-${a.cell_id}`} href={capUrl(a.id, domain)} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:border-cyan-500/50">
                  <Download className="w-3 h-3" /> {t("downloadCap")}
                </a>
                <button data-testid={`alert-ack-${a.cell_id}`} onClick={() => onAck(a)} disabled={a.acknowledged}
                  className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-1 rounded border transition-colors ${a.acknowledged ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300" : "bg-slate-900 border-slate-700 text-slate-300 hover:border-emerald-500/50"}`}>
                  <Check className="w-3 h-3" /> {a.acknowledged ? t("acknowledged") : t("acknowledge")}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
