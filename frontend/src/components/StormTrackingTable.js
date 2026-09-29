import React from "react";
import { Crosshair } from "lucide-react";
import { severityColor } from "../lib/colors";

export default function StormTrackingTable({ t, tracks, onSelectCell }) {
  return (
    <section data-testid="storm-tracking-table" className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-center gap-2 mb-3">
        <Crosshair className="w-4 h-4 text-fuchsia-400" />
        <h3 className="font-display text-sm font-bold uppercase tracking-wide text-slate-200">{t("stormcells")}</h3>
        <span className="text-[10px] font-mono text-slate-500">TITAN/SCIT · SIMULATED</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] font-mono">
          <thead>
            <tr className="text-slate-500 border-b border-slate-800 text-left">
              <th className="py-1.5 pr-2">Cell</th>
              <th className="py-1.5 pr-2">{t("maxDbz")}</th>
              <th className="py-1.5 pr-2">VIL</th>
              <th className="py-1.5 pr-2">{t("speed")}</th>
              <th className="py-1.5 pr-2">{t("bearing")}</th>
              <th className="py-1.5 pr-2">{t("trend")}</th>
              <th className="py-1.5">S/M</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((tk) => (
              <tr
                key={tk.cell_id}
                data-testid={`storm-row-${tk.cell_id}`}
                onClick={() => onSelectCell(tk.cell_id)}
                className="border-b border-slate-800/60 hover:bg-slate-900/60 cursor-pointer"
              >
                <td className="py-1.5 pr-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: severityColor(tk.severity) }} />
                  <span className="text-slate-200">{tk.cell_id}</span>
                </td>
                <td className="py-1.5 pr-2 text-slate-300">{tk.max_dbz}</td>
                <td className="py-1.5 pr-2 text-slate-300">{tk.vil}</td>
                <td className="py-1.5 pr-2 text-slate-300">{tk.speed_kmh}</td>
                <td className="py-1.5 pr-2 text-slate-300">{tk.bearing}°</td>
                <td className="py-1.5 pr-2 text-slate-400">{tk.trend}</td>
                <td className="py-1.5 text-slate-400">{Math.round(tk.split_prob * 100)}/{Math.round(tk.merge_prob * 100)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="text-[9px] text-slate-600 mt-2">Row → open vertical cross-section diagnostic</div>
    </section>
  );
}
