"""
VayuDrishti Nowcast — deterministic SIMULATED nowcast engine.

IMPORTANT (truth-in-data): Every field produced here is SIMULATED / REPLAY DEMO
data. It is NOT derived from IMD DWR, INSAT/MOSDAC, IITM/ENTLN lightning, or any
NWP source, and must NEVER be presented as operational Indian guidance. The
c4dl-multi model referenced in the spec is Swiss research infrastructure and is
NOT deployed here; this engine is an optical-flow / persistence style baseline
over synthetic storm cells for demonstration and UI/contract validation only.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import numpy as np

MODEL_VERSION = "vayudrishti-baseline-sim-0.3.0 (optical-flow+persistence, SIMULATED)"
LEAD_TIMES = [0, 15, 30, 45, 60, 90, 120, 150, 180]
IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Pilot domains (India-first). Only domains with a configured synthetic radar
# are exposed; we never claim nationwide coverage.
# ---------------------------------------------------------------------------
DOMAINS: Dict[str, Dict[str, Any]] = {
    "mumbai": {
        "id": "mumbai",
        "name": "Mumbai (MMR)",
        "name_hi": "मुंबई (एमएमआर)",
        "center": [19.0760, 72.8777],
        "bbox": [18.30, 71.95, 19.85, 73.35],  # [minLat, minLon, maxLat, maxLon]
        "radar": "IMD DWR Mumbai (Colaba) — S-band",
        "radar_site": [18.9067, 72.8147],
        "districts": ["Mumbai City", "Mumbai Suburban", "Thane", "Raigad", "Palghar"],
        "zoom": 8,
    },
    "delhi": {
        "id": "delhi",
        "name": "Delhi NCR",
        "name_hi": "दिल्ली एनसीआर",
        "center": [28.6139, 77.2090],
        "bbox": [27.80, 76.40, 29.30, 77.95],
        "radar": "IMD DWR Delhi (Palam / Ayanagar) — S-band",
        "radar_site": [28.5665, 77.1031],
        "districts": ["New Delhi", "Gurugram", "Faridabad", "Ghaziabad", "Gautam Buddh Nagar", "Sonipat"],
        "zoom": 8,
    },
    "kolkata": {
        "id": "kolkata",
        "name": "Kolkata",
        "name_hi": "कोलकाता",
        "center": [22.5726, 88.3639],
        "bbox": [21.75, 87.55, 23.35, 89.15],
        "radar": "IMD DWR Kolkata — S-band",
        "radar_site": [22.6500, 88.4500],
        "districts": ["Kolkata", "Howrah", "North 24 Parganas", "South 24 Parganas", "Hooghly", "Nadia"],
        "zoom": 8,
    },
    "bhubaneswar": {
        "id": "bhubaneswar",
        "name": "Bhubaneswar / Paradip",
        "name_hi": "भुवनेश्वर / पारादीप",
        "center": [20.2961, 85.8245],
        "bbox": [19.50, 85.00, 20.95, 86.95],
        "radar": "IMD DWR Paradip / Gopalpur — S-band",
        "radar_site": [20.3160, 86.6100],
        "districts": ["Khordha", "Cuttack", "Puri", "Jagatsinghpur", "Kendrapara"],
        "zoom": 8,
    },
    "guwahati": {
        "id": "guwahati",
        "name": "Guwahati",
        "name_hi": "गुवाहाटी",
        "center": [26.1445, 91.7362],
        "bbox": [25.45, 90.95, 26.85, 92.55],
        "radar": "IMD DWR Guwahati — S-band",
        "radar_site": [26.1030, 91.5850],
        "districts": ["Kamrup Metropolitan", "Kamrup", "Nalbari", "Barpeta", "Darrang"],
        "zoom": 8,
    },
    "chennai": {
        "id": "chennai",
        "name": "Chennai",
        "name_hi": "चेन्नई",
        "center": [13.0827, 80.2707],
        "bbox": [12.35, 79.55, 13.80, 80.95],
        "radar": "IMD DWR Chennai — S-band",
        "radar_site": [13.0800, 80.2800],
        "districts": ["Chennai", "Chengalpattu", "Kancheepuram", "Tiruvallur", "Ranipet"],
        "zoom": 8,
    },
    "hyderabad": {
        "id": "hyderabad",
        "name": "Hyderabad",
        "name_hi": "हैदराबाद",
        "center": [17.3850, 78.4867],
        "bbox": [16.65, 77.70, 18.10, 79.25],
        "radar": "IMD DWR Hyderabad (Shamshabad) — S-band",
        "radar_site": [17.2400, 78.4300],
        "districts": ["Hyderabad", "Rangareddy", "Medchal-Malkajgiri", "Sangareddy", "Vikarabad"],
        "zoom": 8,
    },
    "bengaluru": {
        "id": "bengaluru",
        "name": "Bengaluru",
        "name_hi": "बेंगलुरु",
        "center": [12.9716, 77.5946],
        "bbox": [12.25, 76.85, 13.70, 78.30],
        "radar": "IMD DWR Bengaluru — S-band",
        "radar_site": [13.2000, 77.7100],
        "districts": ["Bengaluru Urban", "Bengaluru Rural", "Ramanagara", "Kolar", "Tumakuru"],
        "zoom": 8,
    },
    "kochi": {
        "id": "kochi",
        "name": "Kochi",
        "name_hi": "कोच्चि",
        "center": [9.9312, 76.2673],
        "bbox": [9.20, 75.55, 10.65, 76.95],
        "radar": "IMD DWR Kochi — S-band",
        "radar_site": [10.1500, 76.4000],
        "districts": ["Ernakulam", "Thrissur", "Alappuzha", "Kottayam", "Idukki"],
        "zoom": 8,
    },
}


def _rng(domain: str, salt: str = "") -> np.random.Generator:
    """Deterministic RNG seeded by domain (+optional salt) -> reproducible replay."""
    h = hashlib.sha256(f"{domain}:{salt}".encode()).hexdigest()
    return np.random.default_rng(int(h[:16], 16))


def now_times() -> Dict[str, str]:
    utc = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "issue_utc": utc.isoformat(),
        "issue_ist": utc.astimezone(IST).isoformat(),
    }


# ---------------------------------------------------------------------------
# Storm-cell scenario per domain (stable per domain for replay).
# ---------------------------------------------------------------------------
def _cells(domain: str) -> List[Dict[str, Any]]:
    d = DOMAINS[domain]
    rng = _rng(domain, "cells")
    cy, cx = d["center"]
    ncells = 3
    cells = []
    for i in range(ncells):
        # place cells near center, upstream (SW) so they advect NE across the city
        lat0 = cy + rng.uniform(-0.55, 0.15) - 0.15
        lon0 = cx + rng.uniform(-0.55, 0.15) - 0.15
        max_dbz = float(rng.uniform(46, 62))
        sigma = float(rng.uniform(0.10, 0.20))  # degrees
        # motion in deg/min (typical convective advection ~ 30-55 km/h toward NE/E)
        speed_kmh = float(rng.uniform(28, 55))
        bearing = float(rng.uniform(30, 85))  # coming FROM SW, going toward NE
        # convert speed+bearing(toward) to deg/min
        v_kmmin = speed_kmh / 60.0
        dlat = (v_kmmin * math.cos(math.radians(bearing))) / 111.0
        dlon = (v_kmmin * math.sin(math.radians(bearing))) / (111.0 * math.cos(math.radians(cy)))
        cells.append({
            "cell_id": f"{domain[:3].upper()}-C{i+1:02d}",
            "lat0": lat0, "lon0": lon0,
            "max_dbz": max_dbz, "sigma": sigma,
            "dlat": dlat, "dlon": dlon,
            "speed_kmh": round(speed_kmh, 1), "bearing": round(bearing, 0),
            "growth": float(rng.uniform(-0.04, 0.06)),  # dBZ intensification per min
            "split_prob": float(rng.uniform(0.02, 0.35)),
            "merge_prob": float(rng.uniform(0.02, 0.30)),
            "vil": float(rng.uniform(8, 42)),
        })
    return cells


def _cell_center_at(cell: Dict[str, Any], t: int) -> List[float]:
    return [cell["lat0"] + cell["dlat"] * t, cell["lon0"] + cell["dlon"] * t]


def _cell_dbz_at(cell: Dict[str, Any], t: int) -> float:
    return max(0.0, min(70.0, cell["max_dbz"] + cell["growth"] * t))


# ---------------------------------------------------------------------------
# Reflectivity grid -> filtered cells for map rendering
# ---------------------------------------------------------------------------
def reflectivity_frame(domain: str, t: int) -> List[Dict[str, Any]]:
    d = DOMAINS[domain]
    minlat, minlon, maxlat, maxlon = d["bbox"]
    n = 34
    lats = np.linspace(minlat, maxlat, n)
    lons = np.linspace(minlon, maxlon, n)
    cells = _cells(domain)
    rng = _rng(domain, f"noise{t}")
    noise = rng.normal(0, 2.0, size=(n, n))
    out = []
    dlat_step = (maxlat - minlat) / (n - 1)
    dlon_step = (maxlon - minlon) / (n - 1)
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            val = 0.0
            for c in cells:
                clat, clon = _cell_center_at(c, t)
                dbz = _cell_dbz_at(c, t)
                dist2 = (la - clat) ** 2 + (lo - clon) ** 2
                val = max(val, dbz * math.exp(-dist2 / (2 * c["sigma"] ** 2)))
            val += noise[i, j]
            if val >= 15:
                out.append({
                    "lat": round(float(la), 4),
                    "lon": round(float(lo), 4),
                    "dbz": round(float(min(val, 70)), 1),
                    "dlat": round(dlat_step, 4),
                    "dlon": round(dlon_step, 4),
                })
    return out


def lightning_frame(domain: str, t: int) -> List[Dict[str, Any]]:
    cells = _cells(domain)
    rng = _rng(domain, f"lightning{t}")
    strikes = []
    for c in cells:
        dbz = _cell_dbz_at(c, t)
        if dbz < 42:
            continue
        clat, clon = _cell_center_at(c, t)
        count = int((dbz - 40) * rng.uniform(1.0, 2.2))
        for _ in range(count):
            strikes.append({
                "lat": round(float(clat + rng.normal(0, c["sigma"] * 0.8)), 4),
                "lon": round(float(clon + rng.normal(0, c["sigma"] * 0.8)), 4),
                "age_min": int(rng.integers(0, 15)),
                "type": "CG" if rng.random() > 0.35 else "IC",
                "kA": round(float(rng.uniform(5, 45)), 1),
            })
    return strikes


def motion_vectors(domain: str, t: int) -> List[Dict[str, Any]]:
    cells = _cells(domain)
    vecs = []
    for c in cells:
        clat, clon = _cell_center_at(c, t)
        # arrow endpoint 30 min ahead
        vecs.append({
            "lat": round(clat, 4), "lon": round(clon, 4),
            "lat2": round(clat + c["dlat"] * 30, 4),
            "lon2": round(clon + c["dlon"] * 30, 4),
            "speed_kmh": c["speed_kmh"], "bearing": c["bearing"],
        })
    return vecs


# ---------------------------------------------------------------------------
# INSAT-3D IR cloud-top brightness temperature (distinct satellite channel).
# Cold cloud tops (deep convection / anvils) spread wider than the radar core.
# ---------------------------------------------------------------------------
def satellite_ir_frame(domain: str, t: int) -> List[Dict[str, Any]]:
    d = DOMAINS[domain]
    minlat, minlon, maxlat, maxlon = d["bbox"]
    n = 30
    lats = np.linspace(minlat, maxlat, n)
    lons = np.linspace(minlon, maxlon, n)
    cells = _cells(domain)
    rng = _rng(domain, f"ir{t}")
    noise = rng.normal(0, 1.3, size=(n, n))
    dlat_step = (maxlat - minlat) / (n - 1)
    dlon_step = (maxlon - minlon) / (n - 1)
    out = []
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            cooling = 0.0
            for c in cells:
                clat, clon = _cell_center_at(c, t)
                dbz = _cell_dbz_at(c, t)
                anvil = c["sigma"] * 2.4  # broader than radar core
                depth = max(0.0, (dbz - 26)) * 2.5  # K of cloud-top cooling
                dist2 = (la - clat) ** 2 + (lo - clon) ** 2
                cooling = max(cooling, depth * math.exp(-dist2 / (2 * anvil ** 2)))
            bt = 292.0 - cooling + noise[i, j]  # K
            bt = max(198.0, min(300.0, bt))
            if bt <= 268:  # only render meaningful cloud
                out.append({
                    "lat": round(float(la), 4), "lon": round(float(lo), 4),
                    "bt": round(float(bt), 1),
                    "dlat": round(dlat_step, 4), "dlon": round(dlon_step, 4),
                })
    return out


# ---------------------------------------------------------------------------
# NWP CAPE (instability) field + 0-6 km shear / steering vectors.
# ---------------------------------------------------------------------------
def nwp_frame(domain: str, t: int) -> Dict[str, Any]:
    d = DOMAINS[domain]
    minlat, minlon, maxlat, maxlon = d["bbox"]
    n = 16
    lats = np.linspace(minlat, maxlat, n)
    lons = np.linspace(minlon, maxlon, n)
    cells = _cells(domain)
    rng = _rng(domain, f"nwp{t}")
    dlat_step = (maxlat - minlat) / (n - 1)
    dlon_step = (maxlon - minlon) / (n - 1)
    cape_cells = []
    cape_grid = np.zeros((n, n))
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            # background instability gradient (more unstable to the south)
            base = 850 + 1300 * ((maxlat - la) / (maxlat - minlat)) + 350 * math.sin((lo - minlon) * 3.0)
            enh = 0.0
            for c in cells:
                # instability pools ahead (downstream) of each storm
                alat = c["lat0"] + c["dlat"] * (t + 30)
                alon = c["lon0"] + c["dlon"] * (t + 30)
                dist2 = (la - alat) ** 2 + (lo - alon) ** 2
                enh = max(enh, 1500 * math.exp(-dist2 / (2 * (c["sigma"] * 2.5) ** 2)))
            cape = max(0.0, min(4200.0, base + enh + rng.normal(0, 110)))
            cape_grid[i, j] = cape
            if cape >= 500:
                cape_cells.append({
                    "lat": round(float(la), 4), "lon": round(float(lo), 4),
                    "cape": int(cape),
                    "dlat": round(dlat_step, 4), "dlon": round(dlon_step, 4),
                })
    steer_dlat = float(np.mean([c["dlat"] for c in cells]))
    steer_dlon = float(np.mean([c["dlon"] for c in cells]))
    mag = math.hypot(steer_dlat, steer_dlon) or 1.0
    vectors = []
    for i in range(1, n, 4):
        for j in range(1, n, 4):
            la = float(lats[i]); lo = float(lons[j])
            shear = round(9 + (cape_grid[i, j] / 4200.0) * 20 + rng.uniform(-2, 2), 1)
            scale = 0.14
            vectors.append({
                "lat": round(la, 4), "lon": round(lo, 4),
                "lat2": round(la + (steer_dlat / mag) * scale, 4),
                "lon2": round(lo + (steer_dlon / mag) * scale, 4),
                "shear_ms": shear,
            })
    return {
        "cape": cape_cells,
        "shear_vectors": vectors,
        "cape_max": int(cape_grid.max()),
        "units": {"cape": "J/kg", "shear": "m/s (0-6 km)"},
        "data_state": "simulated",
    }


# ---------------------------------------------------------------------------
# Probabilistic risk zones (thresholded, cleaned probability field) as GeoJSON
# ---------------------------------------------------------------------------
def _severity_for(prob: float) -> str:
    if prob >= 0.75:
        return "red"
    if prob >= 0.55:
        return "orange"
    if prob >= 0.35:
        return "yellow"
    return "green"


_SEVERITY_LABEL = {
    "green": ("No Warning", "कोई चेतावनी नहीं"),
    "yellow": ("Watch — Be Updated", "निगरानी — सूचित रहें"),
    "orange": ("Alert — Be Prepared", "सतर्क — तैयार रहें"),
    "red": ("Warning — Take Action", "चेतावनी — कार्रवाई करें"),
}


def _circle_polygon(clat: float, clon: float, r_deg: float, k: int = 28) -> List[List[float]]:
    ring = []
    for a in range(k + 1):
        ang = 2 * math.pi * a / k
        ring.append([round(clon + r_deg * math.cos(ang) / max(math.cos(math.radians(clat)), 0.1), 4),
                     round(clat + r_deg * math.sin(ang), 4)])
    return ring


def risk_zones(domain: str, t: int) -> Dict[str, Any]:
    cells = _cells(domain)
    times = now_times()
    features = []
    for c in cells:
        dbz = _cell_dbz_at(c, t)
        prob = max(0.0, min(0.97, (dbz - 20) / 50.0 + 0.05))
        if prob < 0.35:
            continue
        clat, clon = _cell_center_at(c, t)
        sev = _severity_for(prob)
        r = c["sigma"] * (1.6 if sev == "red" else 1.9 if sev == "orange" else 2.3)
        confidence = round(max(0.35, 0.9 - t / 300.0), 2)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [_circle_polygon(clat, clon, r)]},
            "properties": {
                "cell_id": c["cell_id"],
                "lead_time_min": t,
                "probability": round(prob, 2),
                "severity": sev,
                "severity_label": _SEVERITY_LABEL[sev][0],
                "severity_label_hi": _SEVERITY_LABEL[sev][1],
                "hazard": "Thunderstorm with lightning" + (", gusty winds & hail" if sev == "red" else ""),
                "confidence": confidence,
                "model_version": MODEL_VERSION,
                "input_freshness_min": 5 + t // 15,
                "data_state": "simulated",
                "provenance": "SIMULATED synthetic storm cells (no live IMD/INSAT input)",
                "issued_ist": times["issue_ist"],
            },
        })
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# Storm-cell tracking (TITAN/SCIT style)
# ---------------------------------------------------------------------------
def storm_tracks(domain: str) -> List[Dict[str, Any]]:
    cells = _cells(domain)
    tracks = []
    for c in cells:
        past = [_cell_center_at(c, tt) for tt in range(-45, 1, 15)]
        future = [_cell_center_at(c, tt) for tt in LEAD_TIMES]
        centroid = _cell_center_at(c, 0)
        tracks.append({
            "cell_id": c["cell_id"],
            "centroid": [round(centroid[0], 4), round(centroid[1], 4)],
            "max_dbz": round(_cell_dbz_at(c, 0), 1),
            "vil": round(c["vil"], 1),
            "speed_kmh": c["speed_kmh"],
            "bearing": c["bearing"],
            "trend": "intensifying" if c["growth"] > 0.01 else ("weakening" if c["growth"] < -0.01 else "steady"),
            "split_prob": round(c["split_prob"], 2),
            "merge_prob": round(c["merge_prob"], 2),
            "severity": _severity_for(max(0.0, min(0.97, (_cell_dbz_at(c, 0) - 20) / 50.0 + 0.05))),
            "past_track": [[round(p[0], 4), round(p[1], 4)] for p in past],
            "forecast_track": [[round(p[0], 4), round(p[1], 4)] for p in future],
            "data_state": "simulated",
        })
    return tracks


# ---------------------------------------------------------------------------
# Vertical cross-section diagnostic (altitude vs radial distance)
# ---------------------------------------------------------------------------
def cross_section(domain: str, cell_id: str) -> Dict[str, Any]:
    cells = {c["cell_id"]: c for c in _cells(domain)}
    c = cells.get(cell_id) or list(cells.values())[0]
    n_alt, n_rad = 24, 40  # 0-16 km, 0-80 km
    alts = np.linspace(0, 16, n_alt)
    rads = np.linspace(0, 80, n_rad)
    max_dbz = _cell_dbz_at(c, 0)
    core_r = 40  # km
    grid = []
    for ai, alt in enumerate(alts):
        row = []
        for ri, rad in enumerate(rads):
            # convective core near mid-troposphere, decaying with height & offset
            v_alt = math.exp(-((alt - 4.0) ** 2) / (2 * 5.5 ** 2))
            v_rad = math.exp(-((rad - core_r) ** 2) / (2 * 14 ** 2))
            dbz = max_dbz * v_alt * v_rad
            row.append(round(float(dbz), 1))
        grid.append(row)
    return {
        "cell_id": c["cell_id"],
        "altitudes_km": [round(float(a), 1) for a in alts],
        "radial_km": [round(float(r), 1) for r in rads],
        "reflectivity": grid,
        "freezing_level_km": 4.5,
        "echo_top_km": round(float(9 + max_dbz / 12), 1),
        "data_state": "simulated",
        "note": "Diagnostic cross-section — SIMULATED, not a measured RHI scan.",
    }


# ---------------------------------------------------------------------------
# Verification / calibration (SIMULATED synthetic scores)
# ---------------------------------------------------------------------------
def verification(domain: str) -> Dict[str, Any]:
    rng = _rng(domain, "verif")
    per_lead = []
    for t in LEAD_TIMES[1:]:
        decay = t / 180.0
        pod = round(0.90 - 0.30 * decay + rng.uniform(-0.02, 0.02), 3)
        far = round(0.12 + 0.28 * decay + rng.uniform(-0.02, 0.02), 3)
        csi = round(pod * (1 - far) * (0.9 + rng.uniform(-0.03, 0.03)), 3)
        ets = round(csi - 0.07 - 0.03 * decay, 3)
        hss = round(2 * ets / (1 + ets) if (1 + ets) else 0, 3)
        brier = round(0.05 + 0.10 * decay + rng.uniform(-0.01, 0.01), 3)
        model = {
            "lead_time_min": t, "pod": pod, "far": far, "csi": csi,
            "ets": ets, "hss": hss, "brier": brier,
            "track_error_km": round(3 + 14 * decay + rng.uniform(-1, 1), 1),
            "latency_s": round(1.2 + rng.uniform(0, 1.5), 2),
        }
        # baselines
        persistence = {"lead_time_min": t, "csi": round(csi * (0.72 - 0.15 * decay), 3)}
        optflow = {"lead_time_min": t, "csi": round(csi * (0.88 - 0.06 * decay), 3)}
        per_lead.append({"model": model, "persistence": persistence, "optical_flow": optflow})

    # reliability curve
    bins = np.linspace(0.05, 0.95, 10)
    reliability = [{"forecast_prob": round(float(b), 2),
                    "observed_freq": round(float(min(1.0, max(0.0, b + rng.uniform(-0.06, 0.05)))), 3),
                    "n": int(rng.integers(30, 400))} for b in bins]
    # ROC / PR
    roc = [{"fpr": round(float(x), 2), "tpr": round(float(min(1, x ** 0.45 + rng.uniform(-0.02, 0.02))), 3)}
           for x in np.linspace(0, 1, 11)]
    pr = [{"recall": round(float(x), 2), "precision": round(float(min(1, 0.95 - 0.5 * x + rng.uniform(-0.03, 0.03))), 3)}
          for x in np.linspace(0, 1, 11)]
    return {
        "domain": domain,
        "per_lead": per_lead,
        "reliability_curve": reliability,
        "roc_curve": roc,
        "pr_curve": pr,
        "roc_auc": 0.86,
        "pr_auc": 0.71,
        "data_state": "simulated",
        "partition": "chronological blocked train/val/test (event-level, no adjacent-frame leakage)",
        "note": "SIMULATED verification scores for UI/contract demo. Not validated on authorized Indian events.",
    }
