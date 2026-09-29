import React, { useEffect, useRef } from "react";
import L from "leaflet";
import { dbzColor, severityColor, irColor, capeColor } from "../lib/colors";

// Vanilla-Leaflet map (robust across React versions). Redraws overlay layers
// whenever the active forecast frame, layer toggles, or tracks change.
export default function RadarNowcastMap({
  center, zoom, bbox, radarSite, frame, tracks, layers, onSelectCell,
}) {
  const elRef = useRef(null);
  const mapRef = useRef(null);
  const groupsRef = useRef({});

  // init once
  useEffect(() => {
    if (mapRef.current || !elRef.current) return;
    const map = L.map(elRef.current, {
      center, zoom, zoomControl: true, attributionControl: true,
      preferCanvas: true,
    });
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      { attribution: "Esri Dark Gray Canvas · SIMULATED demo overlays", maxZoom: 16 }
    ).addTo(map);
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 16, opacity: 0.9 }
    ).addTo(map);

    groupsRef.current = {
      satellite: L.layerGroup().addTo(map),
      nwp: L.layerGroup().addTo(map),
      radar: L.layerGroup().addTo(map),
      riskzones: L.layerGroup().addTo(map),
      tracks: L.layerGroup().addTo(map),
      vectors: L.layerGroup().addTo(map),
      lightning: L.layerGroup().addTo(map),
      site: L.layerGroup().addTo(map),
    };
    mapRef.current = map;
    setTimeout(() => map.invalidateSize(), 200);
    return () => { map.remove(); mapRef.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // recenter on domain change
  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.setView(center, zoom);
      setTimeout(() => mapRef.current.invalidateSize(), 150);
    }
  }, [center, zoom]);

  // radar site marker
  useEffect(() => {
    const g = groupsRef.current.site;
    if (!g) return;
    g.clearLayers();
    if (radarSite) {
      L.circleMarker(radarSite, { radius: 6, color: "#06B6D4", weight: 2, fillColor: "#0B1220", fillOpacity: 1 })
        .bindTooltip("IMD DWR site (SIMULATED)", { direction: "top" })
        .addTo(g);
      L.circle(radarSite, { radius: 100000, color: "#06B6D4", weight: 1, opacity: 0.25, fill: false, dashArray: "4 6" }).addTo(g);
    }
  }, [radarSite]);

  // redraw dynamic overlays
  useEffect(() => {
    const g = groupsRef.current;
    const map = mapRef.current;
    if (!g.radar || !map || !frame) return;

    // toggle helper
    const setVis = (key, on) => {
      if (!g[key]) return;
      if (on && !map.hasLayer(g[key])) g[key].addTo(map);
      if (!on && map.hasLayer(g[key])) map.removeLayer(g[key]);
    };

    // RADAR reflectivity
    g.radar.clearLayers();
    (frame.reflectivity || []).forEach((c) => {
      const b = [[c.lat - c.dlat / 2, c.lon - c.dlon / 2], [c.lat + c.dlat / 2, c.lon + c.dlon / 2]];
      L.rectangle(b, { stroke: false, fillColor: dbzColor(c.dbz), fillOpacity: 0.55 }).addTo(g.radar);
    });

    // SATELLITE — INSAT-3D IR cloud-top brightness temperature (distinct channel)
    g.satellite.clearLayers();
    (frame.satellite || []).forEach((c) => {
      const b = [[c.lat - c.dlat / 2, c.lon - c.dlon / 2], [c.lat + c.dlat / 2, c.lon + c.dlon / 2]];
      L.rectangle(b, { stroke: false, fillColor: irColor(c.bt), fillOpacity: 0.42 }).addTo(g.satellite);
    });

    // NWP — CAPE instability field + 0-6 km shear/steering vectors
    g.nwp.clearLayers();
    const nwp = frame.nwp || {};
    (nwp.cape || []).forEach((c) => {
      const b = [[c.lat - c.dlat / 2, c.lon - c.dlon / 2], [c.lat + c.dlat / 2, c.lon + c.dlon / 2]];
      L.rectangle(b, { stroke: false, fillColor: capeColor(c.cape), fillOpacity: 0.3 })
        .bindTooltip(`CAPE ${c.cape} J/kg`, { direction: "top", sticky: true })
        .addTo(g.nwp);
    });
    (nwp.shear_vectors || []).forEach((v) => {
      L.polyline([[v.lat, v.lon], [v.lat2, v.lon2]], { color: "#A3E635", weight: 1.5, opacity: 0.85 })
        .bindTooltip(`0–6 km shear ${v.shear_ms} m/s`, { direction: "top" }).addTo(g.nwp);
      L.circleMarker([v.lat, v.lon], { radius: 2, color: "#A3E635", weight: 1, fillColor: "#A3E635", fillOpacity: 1 }).addTo(g.nwp);
    });

    // RISK ZONES
    g.riskzones.clearLayers();
    ((frame.risk_zones && frame.risk_zones.features) || []).forEach((f) => {
      const p = f.properties;
      const latlngs = f.geometry.coordinates[0].map((c) => [c[1], c[0]]);
      const col = severityColor(p.severity);
      L.polygon(latlngs, { color: col, weight: 2, fillColor: col, fillOpacity: 0.12, dashArray: "6 4" })
        .bindPopup(
          `<b>${p.severity_label}</b><br/>Cell ${p.cell_id}<br/>Lead +${p.lead_time_min} min<br/>Prob ${(p.probability * 100).toFixed(0)}% · Conf ${(p.confidence * 100).toFixed(0)}%<br/><i>${p.data_state.toUpperCase()}</i>`
        )
        .addTo(g.riskzones);
    });

    // STORM TRACKS
    g.tracks.clearLayers();
    (tracks || []).forEach((tk) => {
      const col = severityColor(tk.severity);
      if (tk.past_track && tk.past_track.length)
        L.polyline(tk.past_track, { color: "#94A3B8", weight: 2, opacity: 0.7, dashArray: "3 5" }).addTo(g.tracks);
      if (tk.forecast_track && tk.forecast_track.length)
        L.polyline(tk.forecast_track, { color: col, weight: 2.5, opacity: 0.9 }).addTo(g.tracks);
      L.circleMarker(tk.centroid, { radius: 7, color: col, weight: 2, fillColor: "#0B1220", fillOpacity: 1 })
        .bindTooltip(`${tk.cell_id} · ${tk.max_dbz} dBZ · ${tk.speed_kmh} km/h`, { direction: "top" })
        .on("click", () => onSelectCell && onSelectCell(tk.cell_id))
        .addTo(g.tracks);
    });

    // MOTION VECTORS
    g.vectors.clearLayers();
    (frame.motion_vectors || []).forEach((v) => {
      L.polyline([[v.lat, v.lon], [v.lat2, v.lon2]], { color: "#38BDF8", weight: 2, opacity: 0.9 }).addTo(g.vectors);
      L.circleMarker([v.lat2, v.lon2], { radius: 3, color: "#38BDF8", weight: 2, fillColor: "#38BDF8", fillOpacity: 1 }).addTo(g.vectors);
    });

    // LIGHTNING
    g.lightning.clearLayers();
    (frame.lightning || []).forEach((s) => {
      const fresh = s.age_min <= 5;
      L.circleMarker([s.lat, s.lon], {
        radius: fresh ? 3.5 : 2.5,
        color: fresh ? "#FDE047" : "#F59E0B",
        weight: 1, fillColor: fresh ? "#FEF08A" : "#F59E0B",
        fillOpacity: fresh ? 0.95 : 0.5,
      }).addTo(g.lightning);
    });

    setVis("radar", layers.radar);
    setVis("satellite", layers.satellite);
    setVis("nwp", layers.nwp);
    setVis("riskzones", layers.riskzones);
    setVis("tracks", layers.tracks);
    setVis("vectors", layers.vectors);
    setVis("lightning", layers.lightning);
  }, [frame, tracks, layers, onSelectCell]);

  return <div ref={elRef} data-testid="radar-nowcast-map" className="absolute inset-0 h-full w-full" />;
}
