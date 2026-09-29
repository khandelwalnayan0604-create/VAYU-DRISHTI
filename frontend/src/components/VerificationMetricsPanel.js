import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from "recharts";
import { BarChart3 } from "lucide-react";

const tt = { background: "#0F172A", border: "1px solid #1E293B", borderRadius: 8, fontSize: 11, color: "#E2E8F0" };

export default function VerificationMetricsPanel({ t, verification }) {
  if (!verification) return null;
  const leadData = verification.per_lead.map((l) => ({
    lead: l.model.lead_time_min,
    CSI: l.model.csi, POD: l.model.pod, FAR: l.model.far,
    "CSI·persist": l.persistence.csi, "CSI·optflow": l.optical_flow.csi,
  }));
  const rel = verification.reliability_curve.map((r) => ({ f: r.forecast_prob, o: r.observed_freq, perfect: r.forecast_prob }));

  return (
    <section data-testid="verification-metrics-panel" className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-center gap-2 mb-1">
        <BarChart3 className="w-4 h-4 text-cyan-400" />
        <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200">{t("verification")}</h3>
        <span className="text-[10px] font-mono text-slate-500">SIMULATED</span>
      </div>
      <p className="text-[10px] text-slate-500 mb-2">{verification.partition}</p>

      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          ["ROC-AUC", verification.roc_auc],
          ["PR-AUC", verification.pr_auc],
          ["Brier@60", verification.per_lead[3]?.model.brier],
        ].map(([k, v]) => (
          <div key={k} className="rounded-lg border border-slate-800 bg-slate-900/50 p-2 text-center">
            <div className="text-[9px] font-mono uppercase tracking-widest text-slate-500">{k}</div>
            <div className="font-mono text-lg font-bold text-cyan-300">{v}</div>
          </div>
        ))}
      </div>

      <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">CSI vs baselines by lead</div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={leadData} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" />
            <XAxis dataKey="lead" stroke="#64748B" fontSize={9} tickLine={false} />
            <YAxis stroke="#64748B" fontSize={9} domain={[0, 1]} tickLine={false} />
            <Tooltip contentStyle={tt} />
            <Legend wrapperStyle={{ fontSize: 9 }} />
            <Line type="monotone" dataKey="CSI" stroke="#22D3EE" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="CSI·optflow" stroke="#F59E0B" strokeWidth={1.5} dot={false} strokeDasharray="4 3" />
            <Line type="monotone" dataKey="CSI·persist" stroke="#94A3B8" strokeWidth={1.5} dot={false} strokeDasharray="2 4" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mt-3 mb-1">Reliability (calibration)</div>
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rel} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" />
            <XAxis dataKey="f" stroke="#64748B" fontSize={9} domain={[0, 1]} tickLine={false} />
            <YAxis stroke="#64748B" fontSize={9} domain={[0, 1]} tickLine={false} />
            <Tooltip contentStyle={tt} />
            <Line type="monotone" dataKey="perfect" stroke="#475569" strokeWidth={1} dot={false} strokeDasharray="4 4" />
            <Line type="monotone" dataKey="o" stroke="#22C55E" strokeWidth={2} dot={{ r: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="overflow-x-auto mt-3">
        <table className="w-full text-[10px] font-mono">
          <thead>
            <tr className="text-slate-500 border-b border-slate-800 text-left">
              <th className="py-1 pr-2">{t("leadMin")}</th><th className="py-1 pr-2">POD</th>
              <th className="py-1 pr-2">FAR</th><th className="py-1 pr-2">CSI</th>
              <th className="py-1 pr-2">ETS</th><th className="py-1 pr-2">HSS</th><th className="py-1">Trk km</th>
            </tr>
          </thead>
          <tbody>
            {verification.per_lead.map((l) => (
              <tr key={l.model.lead_time_min} className="border-b border-slate-800/60 text-slate-300">
                <td className="py-1 pr-2 text-slate-400">+{l.model.lead_time_min}</td>
                <td className="py-1 pr-2">{l.model.pod}</td>
                <td className="py-1 pr-2">{l.model.far}</td>
                <td className="py-1 pr-2 text-cyan-300">{l.model.csi}</td>
                <td className="py-1 pr-2">{l.model.ets}</td>
                <td className="py-1 pr-2">{l.model.hss}</td>
                <td className="py-1">{l.model.track_error_km}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
