import React from "react";
import { ShieldAlert, Timer, Download, CheckCircle2, Info } from "lucide-react";
import { severityColor } from "../lib/colors";
import { capUrl } from "../lib/api";
import { DataStateBadge } from "./DataStateBadge";

export default function PublicSafetyAlertView({ t, lang, domain, domainName, safety, heroUrl }) {
  if (!safety) return null;
  const col = severityColor(safety.severity);
  const a = safety.latest_alert;
  const rules = safety.rules[lang] || safety.rules.en;
  return (
    <div className="max-w-4xl mx-auto p-4 space-y-5">
      {/* Hero risk card */}
      <div data-testid="public-safety-card" className="relative overflow-hidden rounded-2xl border" style={{ borderColor: col + "80" }}>
        <div className="absolute inset-0">
          <img src={heroUrl} alt="storm" className="w-full h-full object-cover opacity-25" />
          <div className="absolute inset-0" style={{ background: `linear-gradient(180deg, rgba(5,8,17,0.75), ${col}22)` }} />
        </div>
        <div className="relative p-5 sm:p-7">
          <div className="flex items-center justify-between">
            <DataStateBadge state="simulated" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-300">{domainName}</span>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <div className="grid place-items-center w-14 h-14 rounded-2xl" style={{ background: col + "33", border: `1px solid ${col}` }}>
              <ShieldAlert className="w-7 h-7" style={{ color: col }} />
            </div>
            <div>
              <div className="text-[11px] font-mono uppercase tracking-widest text-slate-300">{t("severity")}</div>
              <div className="font-display text-3xl sm:text-4xl font-black uppercase tracking-tight" style={{ color: col }}>
                {lang === "hi" ? safety.severity_label_hi : safety.severity_label}
              </div>
            </div>
          </div>

          {safety.minutes_to_onset != null && (
            <div className="mt-4 inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-700">
              <Timer className="w-4 h-4 text-amber-400" />
              <span className="text-sm text-slate-200">{t("onsetIn")}</span>
              <span data-testid="onset-countdown" className="font-mono text-xl font-bold text-amber-300">~{safety.minutes_to_onset} {t("minutes")}</span>
            </div>
          )}

          <p className="mt-4 text-base sm:text-lg font-medium text-slate-100 max-w-2xl">
            {safety.advice[lang] || safety.advice.en}
          </p>
        </div>
      </div>

      {/* Latest verified alert + CAP */}
      {a && (
        <div data-testid="cap-alert-broadcast-box" className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200">{t("latestAlert")}</h3>
            <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/50">CAP 1.2 · Test</span>
          </div>
          <p className="text-sm text-slate-300">{a.description}</p>
          <a href={capUrl(a.id, domain)} target="_blank" rel="noreferrer"
            className="mt-3 inline-flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:border-cyan-500/50">
            <Download className="w-3.5 h-3.5" /> {t("downloadCap")}
          </a>
        </div>
      )}

      {/* Safety rules */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
        <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200 mb-3">{t("safetyRules")}</h3>
        <ul className="space-y-2">
          {rules.map((r, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
        <div className="mt-3 flex items-start gap-1.5 text-[10px] text-slate-500">
          <Info className="w-3 h-3 mt-0.5 shrink-0" />
          <span>{safety.source}</span>
        </div>
      </div>
    </div>
  );
}
