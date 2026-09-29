import React from "react";
import { STATE_BADGE } from "../lib/colors";

export function DataStateBadge({ state = "simulated", className = "", testid }) {
  const cls = STATE_BADGE[state] || STATE_BADGE.simulated;
  return (
    <span
      data-testid={testid || `data-state-badge-${state}`}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-mono font-bold uppercase tracking-widest ${cls} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {state}
    </span>
  );
}
