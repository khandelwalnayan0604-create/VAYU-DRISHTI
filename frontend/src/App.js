import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import "@/App.css";
import { getJSON, postJSON } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { severityColor } from "@/lib/colors";
import { DataStateBadge } from "@/components/DataStateBadge";
import VayuDrishtiHeader from "@/components/VayuDrishtiHeader";
import RadarNowcastMap from "@/components/RadarNowcastMap";
import ForecastTimelineBar from "@/components/ForecastTimelineBar";
import LayerControl from "@/components/LayerControl";
import AlertPanel from "@/components/AlertPanel";
import OperatorSourceHealth from "@/components/OperatorSourceHealth";
import StormTrackingTable from "@/components/StormTrackingTable";
import VerificationMetricsPanel from "@/components/VerificationMetricsPanel";
import VerticalCrossSection from "@/components/VerticalCrossSection";
import PublicSafetyAlertView from "@/components/PublicSafetyAlertView";
import { AlertTriangle } from "lucide-react";

const HERO = "https://images.unsplash.com/photo-1605727216801-e27ce1d0cc28?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600";

function istNow() {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit",
  }).format(new Date());
}

export default function App() {
  const [lang, setLang] = useState("en");
  const [role, setRole] = useState("operator");
  const [domain, setDomain] = useState("mumbai");
  const [domains, setDomains] = useState([]);
  const [nowcast, setNowcast] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [connectors, setConnectors] = useState([]);
  const [verification, setVerification] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [safety, setSafety] = useState(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [crossSection, setCrossSection] = useState(null);
  const [opTab, setOpTab] = useState("sources");
  const [clock, setClock] = useState(istNow());
  const [layers, setLayers] = useState({
    radar: true, satellite: false, nwp: false, lightning: true, vectors: true, tracks: true, riskzones: true,
  });

  const t = useT(lang);
  const playRef = useRef(null);

  useEffect(() => {
    const id = setInterval(() => setClock(istNow()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => { getJSON("/domains").then((d) => setDomains(d.domains)).catch(() => {}); }, []);

  const loadDomain = useCallback(async (dom) => {
    try {
      const [nc, tr, cs, vf, al, sf] = await Promise.all([
        getJSON(`/nowcast/frames?domain=${dom}`),
        getJSON(`/storm-tracks?domain=${dom}`),
        getJSON(`/connectors/status?domain=${dom}`),
        getJSON(`/verification?domain=${dom}`),
        getJSON(`/alerts?domain=${dom}`),
        getJSON(`/safety?domain=${dom}`),
      ]);
      setNowcast(nc); setTracks(tr.tracks); setConnectors(cs.connectors);
      setVerification(vf); setAlerts(al.alerts); setSafety(sf);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { loadDomain(domain); setIdx(0); }, [domain, loadDomain]);

  // play loop
  useEffect(() => {
    if (playing && nowcast) {
      playRef.current = setInterval(() => {
        setIdx((i) => (i + 1) % nowcast.lead_times.length);
      }, 900);
    } else if (playRef.current) {
      clearInterval(playRef.current);
    }
    return () => playRef.current && clearInterval(playRef.current);
  }, [playing, nowcast]);

  const frame = nowcast ? nowcast.frames[idx] : null;
  const leadTimes = nowcast ? nowcast.lead_times : [0];
  const activeTracks = layers.tracks ? tracks : [];

  const openCrossSection = useCallback(async (cellId) => {
    try {
      const cs = await getJSON(`/cross-section?domain=${domain}&cell_id=${cellId}`);
      setCrossSection(cs);
    } catch (e) { console.error(e); }
  }, [domain]);

  const focusAlert = (a) => {
    const i = leadTimes.indexOf(a.lead_time_min);
    if (i >= 0) { setIdx(i); setPlaying(false); }
    setLayers((l) => ({ ...l, riskzones: true }));
  };

  const ackAlert = async (a) => {
    try {
      await postJSON(`/alerts/${a.id}/ack`, { domain, operator: "operator-demo", note: "acknowledged from console" });
      const al = await getJSON(`/alerts?domain=${domain}`);
      setAlerts(al.alerts);
    } catch (e) { console.error(e); }
  };

  const domainName = useMemo(() => {
    const d = domains.find((x) => x.id === domain);
    return d ? (lang === "hi" ? d.name_hi : d.name) : domain;
  }, [domains, domain, lang]);

  const worstSeverity = alerts[0]?.severity || "green";

  return (
    <div className="App">
      <VayuDrishtiHeader
        t={t} lang={lang} setLang={setLang} role={role} setRole={setRole}
        domain={domain} setDomain={setDomain} domains={domains} istClock={clock}
      />

      {/* Global disclosure ribbon */}
      <div className="flex items-center gap-2 px-3 sm:px-5 py-1.5 bg-amber-500/10 border-b border-amber-500/25 text-[11px] text-amber-200/90">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span className="truncate">
          {nowcast?.disclaimer || "SIMULATED / REPLAY DEMO — not operational IMD guidance. c4dl-multi (Swiss) is a research baseline only."}
        </span>
      </div>

      {role === "public" ? (
        <main className="min-h-[calc(100vh-6.5rem)] bg-[#050811]">
          <PublicSafetyAlertView t={t} lang={lang} domain={domain} domainName={domainName} safety={safety} heroUrl={HERO} />
        </main>
      ) : (
        <main className="flex flex-col lg:flex-row h-[calc(100vh-6.5rem)] overflow-hidden bg-[#050811]">
          {/* Map viewport */}
          <div className="relative flex-1 h-[55vh] lg:h-full bg-[#070B14]">
            {nowcast && (
              <RadarNowcastMap
                center={nowcast.center} zoom={nowcast.zoom} bbox={nowcast.bbox}
                radarSite={domains.find((d) => d.id === domain)?.radar_site}
                frame={frame} tracks={activeTracks} layers={layers} onSelectCell={openCrossSection}
              />
            )}
            <LayerControl t={t} layers={layers} toggle={(k) => setLayers((l) => ({ ...l, [k]: !l[k] }))} />

            {/* model version chip */}
            <div className="absolute top-3 right-3 z-[1000] bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-lg px-2.5 py-1.5 max-w-[240px]">
              <div className="flex items-center gap-1.5">
                <DataStateBadge state="simulated" />
              </div>
              <div className="text-[9px] font-mono text-slate-400 mt-1 leading-tight">{nowcast?.model_version}</div>
            </div>

            {nowcast && (
              <ForecastTimelineBar
                t={t} leadTimes={leadTimes} idx={idx} setIdx={setIdx}
                playing={playing} setPlaying={setPlaying} worstSeverity={worstSeverity}
              />
            )}
          </div>

          {/* Operator sidebar */}
          <aside className="w-full lg:w-[480px] xl:w-[540px] h-full overflow-y-auto border-l border-slate-800/80 bg-slate-950/70 p-3 sm:p-4 space-y-4">
            <AlertPanel t={t} lang={lang} domain={domain} alerts={alerts} onFocusAlert={focusAlert} onAck={ackAlert} />

            <div className="flex rounded-lg border border-slate-800 overflow-hidden text-xs font-semibold uppercase tracking-wide">
              {[["sources", t("sources")], ["cells", t("stormcells")], ["verify", t("verification")]].map(([k, label]) => (
                <button key={k} data-testid={`op-tab-${k}`} onClick={() => setOpTab(k)}
                  className={`flex-1 py-2 transition-colors ${opTab === k ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-900/50 text-slate-400 hover:text-slate-200"}`}>
                  {label}
                </button>
              ))}
            </div>

            {opTab === "sources" && <OperatorSourceHealth t={t} connectors={connectors} />}
            {opTab === "cells" && <StormTrackingTable t={t} tracks={tracks} onSelectCell={openCrossSection} />}
            {opTab === "verify" && <VerificationMetricsPanel t={t} verification={verification} />}
          </aside>
        </main>
      )}

      {crossSection && <VerticalCrossSection t={t} data={crossSection} onClose={() => setCrossSection(null)} />}
    </div>
  );
}
