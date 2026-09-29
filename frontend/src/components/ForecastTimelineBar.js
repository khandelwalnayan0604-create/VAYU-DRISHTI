import React from "react";
import { Play, Pause, SkipForward, SkipBack } from "lucide-react";
import { DBZ_SCALE } from "../lib/colors";

export default function ForecastTimelineBar({ t, leadTimes, idx, setIdx, playing, setPlaying, worstSeverity }) {
  const lead = leadTimes[idx];
  return (
    <div
      data-testid="forecast-timeline"
      className="absolute bottom-3 left-3 right-3 lg:left-6 lg:right-6 z-[1000] bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-xl p-3 shadow-2xl"
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1">
          <button data-testid="timeline-step-backward" onClick={() => setIdx(Math.max(0, idx - 1))}
            className="grid place-items-center w-8 h-8 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300 hover:border-cyan-500/50 transition-colors">
            <SkipBack className="w-4 h-4" />
          </button>
          <button data-testid="timeline-play-btn" onClick={() => setPlaying(!playing)}
            className="grid place-items-center w-9 h-9 rounded-md bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 hover:bg-cyan-500/30 transition-colors">
            {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button data-testid="timeline-step-forward" onClick={() => setIdx(Math.min(leadTimes.length - 1, idx + 1))}
            className="grid place-items-center w-8 h-8 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300 hover:border-cyan-500/50 transition-colors">
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-col min-w-[86px]">
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">{t("leadTime")}</span>
          <span data-testid="timeline-lead-value" className="font-mono text-xl font-bold text-cyan-300 leading-none">
            {lead === 0 ? t("now") : `T+${lead}`}
            {lead !== 0 && <span className="text-xs text-slate-400 ml-1">{t("minutes")}</span>}
          </span>
        </div>

        <div className="flex-1">
          <input
            data-testid="timeline-slider"
            type="range" min={0} max={leadTimes.length - 1} step={1} value={idx}
            onChange={(e) => setIdx(Number(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer"
          />
          <div className="flex justify-between mt-1">
            {leadTimes.map((lt, i) => (
              <button key={lt} data-testid={`timeline-tick-${lt}`} onClick={() => setIdx(i)}
                className={`text-[9px] font-mono transition-colors ${i === idx ? "text-cyan-300 font-bold" : "text-slate-600 hover:text-slate-400"}`}>
                {lt === 0 ? "0" : lt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-slate-800/70 flex items-center gap-2 overflow-x-auto">
        <span className="text-[9px] font-mono uppercase tracking-widest text-slate-500 shrink-0">dBZ</span>
        {DBZ_SCALE.map((s) => (
          <div key={s.label} className="flex items-center gap-1 shrink-0">
            <span className="w-3 h-3 rounded-sm" style={{ background: s.color }} />
            <span className="text-[9px] text-slate-400 whitespace-nowrap">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
