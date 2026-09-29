import React from "react";
import { X } from "lucide-react";
import { dbzColor } from "../lib/colors";

export default function VerticalCrossSection({ t, data, onClose }) {
  if (!data) return null;
  const { reflectivity, altitudes_km, radial_km, freezing_level_km, echo_top_km } = data;
  const nAlt = altitudes_km.length;
  const nRad = radial_km.length;
  return (
    <div className="fixed inset-0 z-[1400] grid place-items-center p-4 bg-black/70 backdrop-blur-sm" data-testid="cross-section-modal">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-700 bg-slate-950 p-4 shadow-2xl">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-display text-base font-bold uppercase tracking-wide text-slate-100">
              {t("crossSection")} · {data.cell_id}
            </h3>
            <p className="text-[10px] font-mono text-amber-400">{t("diagnostic")}</p>
          </div>
          <button data-testid="cross-section-close" onClick={onClose}
            className="grid place-items-center w-8 h-8 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-100">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex gap-2">
          <div className="flex flex-col justify-between py-1 text-[9px] font-mono text-slate-500" style={{ height: 240 }}>
            {[...altitudes_km].reverse().filter((_, i) => i % 4 === 0).map((a) => <span key={a}>{a}km</span>)}
          </div>
          <div className="flex-1">
            <div className="relative rounded-lg overflow-hidden border border-slate-800" style={{ height: 240 }}>
              <div className="grid h-full w-full" style={{ gridTemplateColumns: `repeat(${nRad}, 1fr)`, gridTemplateRows: `repeat(${nAlt}, 1fr)` }}>
                {[...reflectivity].reverse().map((row, ri) =>
                  row.map((v, ci) => (
                    <div key={`${ri}-${ci}`} style={{ background: v >= 15 ? dbzColor(v) : "transparent", opacity: v >= 15 ? 0.85 : 1 }} />
                  ))
                )}
              </div>
              {/* freezing level line */}
              <div className="absolute left-0 right-0 border-t border-dashed border-cyan-300/70"
                style={{ bottom: `${(freezing_level_km / altitudes_km[nAlt - 1]) * 100}%` }}>
                <span className="absolute right-1 -top-3 text-[9px] font-mono text-cyan-300">0°C {freezing_level_km}km</span>
              </div>
            </div>
            <div className="flex justify-between mt-1 text-[9px] font-mono text-slate-500">
              <span>0 km</span><span>Radial distance →</span><span>{radial_km[nRad - 1]} km</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-3 text-[11px] font-mono text-slate-400">
          <span>Echo top: <span className="text-slate-200">{echo_top_km} km</span></span>
          <span>Freezing level: <span className="text-slate-200">{freezing_level_km} km</span></span>
          <span className="ml-auto text-amber-400">{data.data_state.toUpperCase()}</span>
        </div>
      </div>
    </div>
  );
}
