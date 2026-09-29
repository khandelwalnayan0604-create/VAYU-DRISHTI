import React from "react";
import { Radar, Satellite, Zap, MoveRight, Route, Shield, Wind } from "lucide-react";
import { STATE_BADGE } from "../lib/colors";

const LAYER_DEFS = [
  { key: "radar", icon: Radar, testid: "map-layer-toggle-radar", labelKey: "radar", color: "text-emerald-400" },
  { key: "satellite", icon: Satellite, testid: "map-layer-toggle-satellite", labelKey: "satellite", color: "text-sky-400" },
  { key: "nwp", icon: Wind, testid: "map-layer-toggle-nwp", labelKey: "nwp", color: "text-lime-400" },
  { key: "lightning", icon: Zap, testid: "map-layer-toggle-lightning", labelKey: "lightning", color: "text-amber-400" },
  { key: "vectors", icon: MoveRight, testid: "map-layer-toggle-vectors", labelKey: "vectors", color: "text-cyan-400" },
  { key: "tracks", icon: Route, testid: "map-layer-toggle-tracks", labelKey: "tracks", color: "text-fuchsia-400" },
  { key: "riskzones", icon: Shield, testid: "map-layer-toggle-riskzones", labelKey: "riskzones", color: "text-rose-400" },
];

export default function LayerControl({ t, layers, toggle, basemap, setBasemap, nwpState }) {
  const nwpBadge = nwpState === "live" || nwpState === "delayed";
  return (
    <div
      data-testid="layer-control"
      className="absolute top-3 left-3 z-[1000] bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-xl p-2 shadow-2xl w-[190px]"
    >
      <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 px-1.5 pb-1">{t("layers")}</div>
      <div className="px-1.5 pb-2">
        <select
          data-testid="basemap-select"
          value={basemap}
          onChange={(e) => setBasemap(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-[11px] rounded-md px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-cyan-500"
        >
          <option value="satellite">Satellite (Esri)</option>
          <option value="osm">Standard OSM</option>
          <option value="dark">Dark Tactical</option>
        </select>
      </div>
      <div className="space-y-0.5">
        {LAYER_DEFS.map((l) => {
          const Icon = l.icon;
          const on = layers[l.key];
          return (
            <button
              key={l.key}
              data-testid={l.testid}
              onClick={() => toggle(l.key)}
              className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs font-medium transition-colors ${on ? "bg-slate-800/80 text-slate-100" : "text-slate-500 hover:bg-slate-900/60"}`}
            >
              <Icon className={`w-3.5 h-3.5 ${on ? l.color : "text-slate-600"}`} />
              <span className="flex-1 text-left truncate">{t(l.labelKey)}</span>
              {l.key === "nwp" && nwpState && (
                <span
                  data-testid="nwp-layer-state-badge"
                  className={`text-[8px] font-mono font-bold uppercase px-1 py-0.5 rounded border mr-1 ${STATE_BADGE[nwpState] || STATE_BADGE.simulated}`}
                >
                  {nwpBadge ? nwpState : "sim"}
                </span>
              )}
              <span className={`w-7 h-3.5 rounded-full relative transition-colors ${on ? "bg-cyan-500/60" : "bg-slate-700"}`}>
                <span className={`absolute top-0.5 w-2.5 h-2.5 rounded-full bg-white transition-all ${on ? "left-4" : "left-0.5"}`} />
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
