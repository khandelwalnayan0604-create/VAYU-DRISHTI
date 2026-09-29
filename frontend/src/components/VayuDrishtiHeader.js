import React from "react";
import { CloudLightning, Clock } from "lucide-react";
import { DataStateBadge } from "./DataStateBadge";

export default function VayuDrishtiHeader({
  t, lang, setLang, role, setRole, domain, setDomain, domains, istClock,
}) {
  return (
    <header className="sticky top-0 z-[1200] h-16 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md px-3 sm:px-5 flex items-center justify-between gap-2">
      <div className="flex items-center gap-3 min-w-0">
        <div className="grid place-items-center w-9 h-9 rounded-lg bg-cyan-500/15 border border-cyan-500/40 shrink-0">
          <CloudLightning className="w-5 h-5 text-cyan-400" />
        </div>
        <div className="min-w-0">
          <div data-testid="header-brand-title" className="font-display text-lg sm:text-xl font-black uppercase tracking-tight text-slate-50 leading-none truncate">
            {t("brand")}
          </div>
          <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 truncate">
            SIH26072 · {t("tagline")}
          </div>
        </div>
        <DataStateBadge state="simulated" className="ml-1 hidden sm:inline-flex" testid="header-sim-badge" />
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <div className="hidden md:flex items-center gap-1.5 font-mono text-xs text-slate-300 px-2 py-1 rounded-md bg-slate-900/70 border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span data-testid="ist-clock">{istClock}</span>
          <span className="text-slate-500">{t("ist")}</span>
        </div>

        <select
          data-testid="domain-select-dropdown"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          className="bg-slate-900/80 border border-slate-800 text-slate-200 text-xs sm:text-sm rounded-md px-2 py-1.5 font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
        >
          {domains.map((d) => (
            <option key={d.id} value={d.id}>{lang === "hi" ? d.name_hi : d.name}</option>
          ))}
        </select>

        <div className="flex rounded-md border border-slate-800 overflow-hidden">
          <button
            data-testid="role-toggle-operator"
            onClick={() => setRole("operator")}
            className={`px-2.5 py-1.5 text-xs font-semibold uppercase tracking-wide transition-colors ${role === "operator" ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-900/60 text-slate-400 hover:text-slate-200"}`}
          >
            {t("operator")}
          </button>
          <button
            data-testid="role-toggle-public"
            onClick={() => setRole("public")}
            className={`px-2.5 py-1.5 text-xs font-semibold uppercase tracking-wide transition-colors ${role === "public" ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-900/60 text-slate-400 hover:text-slate-200"}`}
          >
            {t("public")}
          </button>
        </div>

        <button
          data-testid="lang-toggle-btn"
          onClick={() => setLang(lang === "en" ? "hi" : "en")}
          className="px-2.5 py-1.5 text-xs font-bold rounded-md bg-slate-900/80 border border-slate-800 text-slate-200 hover:border-cyan-500/50 transition-colors"
        >
          {lang === "en" ? "हिं" : "EN"}
        </button>
      </div>
    </header>
  );
}
