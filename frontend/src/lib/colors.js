// dBZ reflectivity scale (matches design_guidelines)
export function dbzColor(dbz) {
  if (dbz < 15) return "transparent";
  if (dbz < 25) return "#38BDF8";
  if (dbz < 35) return "#22C55E";
  if (dbz < 45) return "#EAB308";
  if (dbz < 55) return "#F97316";
  if (dbz < 65) return "#EF4444";
  return "#A855F7";
}

export const DBZ_SCALE = [
  { label: "15–25 Light", color: "#38BDF8" },
  { label: "25–35 Moderate", color: "#22C55E" },
  { label: "35–45 Heavy", color: "#EAB308" },
  { label: "45–55 T'storm", color: "#F97316" },
  { label: "55–65 Severe", color: "#EF4444" },
  { label: ">65 Extreme", color: "#A855F7" },
];

export const SEVERITY = {
  green: { color: "#22C55E", label: "No Warning" },
  yellow: { color: "#EAB308", label: "Watch" },
  orange: { color: "#F97316", label: "Alert" },
  red: { color: "#EF4444", label: "Warning" },
};

export function severityColor(sev) {
  return (SEVERITY[sev] || SEVERITY.green).color;
}

// Data-state badge tokens
export const STATE_BADGE = {
  simulated: "bg-amber-500/20 text-amber-300 border-amber-500/50",
  test: "bg-indigo-500/20 text-indigo-300 border-indigo-500/50",
  live: "bg-emerald-500/20 text-emerald-300 border-emerald-500/50",
  delayed: "bg-rose-500/20 text-rose-300 border-rose-500/50",
  historical: "bg-sky-500/20 text-sky-300 border-sky-500/50",
};
