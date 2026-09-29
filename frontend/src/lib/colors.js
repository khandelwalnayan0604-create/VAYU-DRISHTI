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

// INSAT-3D IR cloud-top brightness temperature (K). Colder = deeper convection.
export function irColor(bt) {
  if (bt > 268) return "transparent";
  if (bt > 250) return "#334155";
  if (bt > 240) return "#0EA5E9";
  if (bt > 230) return "#22C55E";
  if (bt > 220) return "#EAB308";
  if (bt > 210) return "#F97316";
  if (bt > 202) return "#EF4444";
  return "#F8FAFC";
}

export const IR_SCALE = [
  { label: "≤202 K", color: "#F8FAFC" },
  { label: "210", color: "#F97316" },
  { label: "220", color: "#EAB308" },
  { label: "230", color: "#22C55E" },
  { label: "250", color: "#0EA5E9" },
  { label: "268", color: "#334155" },
];

// NWP CAPE (J/kg) instability.
export function capeColor(cape) {
  if (cape < 500) return "transparent";
  if (cape < 1000) return "#15803D";
  if (cape < 1500) return "#65A30D";
  if (cape < 2500) return "#CA8A04";
  if (cape < 3500) return "#EA580C";
  return "#DC2626";
}

export const CAPE_SCALE = [
  { label: "500–1000", color: "#15803D" },
  { label: "1000–1500", color: "#65A30D" },
  { label: "1500–2500", color: "#CA8A04" },
  { label: "2500–3500", color: "#EA580C" },
  { label: ">3500 J/kg", color: "#DC2626" },
];

// Data-state badge tokens
export const STATE_BADGE = {
  simulated: "bg-amber-500/20 text-amber-300 border-amber-500/50",
  test: "bg-indigo-500/20 text-indigo-300 border-indigo-500/50",
  live: "bg-emerald-500/20 text-emerald-300 border-emerald-500/50",
  delayed: "bg-rose-500/20 text-rose-300 border-rose-500/50",
  historical: "bg-sky-500/20 text-sky-300 border-sky-500/50",
};
