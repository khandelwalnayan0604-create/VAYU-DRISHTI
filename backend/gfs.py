"""
Live NOAA GFS connector (Phase 1 — the ONE real feed).

Fetches genuine NOAA GFS forecast fields (CAPE + pressure-level winds → 0-6 km
bulk shear) for each Indian pilot domain via Open-Meteo's free, key-free GFS
distribution endpoint (https://open-meteo.com/, model=gfs, NOAA GFS 0.25°).

Truth-in-data:
- On a successful fetch the NWP source is REAL and labelled `live` (fresh) or
  `delayed` (older valid time). Source time, retrieval time and latency are real.
- On any failure/timeout the caller falls back to the SIMULATED synthetic NWP
  field and RELABELS that source `simulated` — never a silent swap.

Attribution: "NOAA GFS (public domain) via Open-Meteo (CC-BY 4.0)".
"""
from __future__ import annotations

import math
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import requests

import nowcast as ng

IST = timezone(timedelta(hours=5, minutes=30))
ATTRIBUTION = "NOAA GFS (public domain) via Open-Meteo (CC-BY 4.0)"
_ENDPOINT = "https://api.open-meteo.com/v1/gfs"
_GRID_N = 6            # 6x6 = 36 points per domain
_TTL_S = 900          # cache a domain's raw pull for 15 min
_TIMEOUT_S = 12

_CACHE: Dict[str, Any] = {}          # domain -> {"ts": epoch, "raw": {...}}
_LOCKS: Dict[str, threading.Lock] = {}


def _lock(domain: str) -> threading.Lock:
    if domain not in _LOCKS:
        _LOCKS[domain] = threading.Lock()
    return _LOCKS[domain]


def _grid(domain: str):
    d = ng.DOMAINS[domain]
    minlat, minlon, maxlat, maxlon = d["bbox"]
    dlat = (maxlat - minlat) / _GRID_N
    dlon = (maxlon - minlon) / _GRID_N
    pts = []
    for i in range(_GRID_N):
        for j in range(_GRID_N):
            lat = minlat + (i + 0.5) * dlat
            lon = minlon + (j + 0.5) * dlon
            pts.append((round(lat, 4), round(lon, 4)))
    return pts, round(dlat, 4), round(dlon, 4)


def _fetch_raw(domain: str) -> Optional[Dict[str, Any]]:
    """Network pull (blocking). Cached per-domain with TTL + lock."""
    now = time.time()
    cached = _CACHE.get(domain)
    if cached and now - cached["ts"] < _TTL_S:
        return cached["raw"]
    with _lock(domain):
        cached = _CACHE.get(domain)
        if cached and time.time() - cached["ts"] < _TTL_S:
            return cached["raw"]
        pts, dlat, dlon = _grid(domain)
        lats = ",".join(str(p[0]) for p in pts)
        lons = ",".join(str(p[1]) for p in pts)
        params = {
            "latitude": lats,
            "longitude": lons,
            "hourly": "cape,wind_speed_1000hPa,wind_speed_500hPa,wind_direction_1000hPa,wind_direction_500hPa",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "forecast_days": 2,
        }
        for attempt in range(3):
            try:
                r = requests.get(_ENDPOINT, params=params, timeout=_TIMEOUT_S)
                r.raise_for_status()
                data = r.json()
                locs = data if isinstance(data, list) else [data]
                raw = {"points": pts, "dlat": dlat, "dlon": dlon, "locs": locs,
                       "retrieval_utc": datetime.now(timezone.utc).replace(microsecond=0)}
                _CACHE[domain] = {"ts": time.time(), "raw": raw}
                return raw
            except Exception:
                time.sleep(0.8 * (attempt + 1))
        return None


def warm_cache(domain: str) -> bool:
    """Prime a domain's GFS cache (used at startup so first user call is real)."""
    return _fetch_raw(domain) is not None


def _uv(speed: float, direction: float):
    """Meteorological dir (FROM) -> (u,v) pointing toward wind motion."""
    if speed is None or direction is None:
        return 0.0, 0.0
    r = math.radians(direction)
    u = -speed * math.sin(r)
    v = -speed * math.cos(r)
    return u, v


def _nearest_idx(times: List[str], target: datetime) -> int:
    best_i, best_d = 0, None
    for i, ts in enumerate(times):
        try:
            dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
        except Exception:
            continue
        diff = abs((dt - target).total_seconds())
        if best_d is None or diff < best_d:
            best_d, best_i = diff, i
    return best_i


def get_nwp_bundle(domain: str, allow_fetch: bool = True) -> Dict[str, Any]:
    """Return a real GFS NWP bundle (per lead time) or {'available': False}."""
    if domain not in ng.DOMAINS:
        return {"available": False}
    if allow_fetch:
        raw = _fetch_raw(domain)
    else:
        cached = _CACHE.get(domain)
        raw = cached["raw"] if cached and time.time() - cached["ts"] < _TTL_S else None
    if not raw or not raw.get("locs"):
        return {"available": False}

    pts, dlat, dlon, locs = raw["points"], raw["dlat"], raw["dlon"], raw["locs"]
    if len(locs) < len(pts):
        return {"available": False}

    now = datetime.now(timezone.utc)
    # freshness from the NOW-nearest step of the first valid location
    ref_times = None
    for loc in locs:
        h = loc.get("hourly") or {}
        if h.get("time"):
            ref_times = h["time"]
            break
    if not ref_times:
        return {"available": False}
    now_idx = _nearest_idx(ref_times, now)
    try:
        src_valid = datetime.fromisoformat(ref_times[now_idx]).replace(tzinfo=timezone.utc)
    except Exception:
        src_valid = now
    latency_s = abs((now - src_valid).total_seconds())
    state = "live" if latency_s <= 3600 else "delayed"

    per_lead: Dict[int, Any] = {}
    for lead in ng.LEAD_TIMES:
        target = now + timedelta(minutes=lead)
        cape_cells, shear_cells = [], []
        cape_max = 0
        for (lat, lon), loc in zip(pts, locs):
            h = loc.get("hourly") or {}
            times = h.get("time") or []
            if not times:
                continue
            idx = _nearest_idx(times, target)
            cape = (h.get("cape") or [None] * len(times))[idx]
            if cape is not None:
                cape = max(0.0, float(cape))
                cape_max = max(cape_max, int(cape))
                if cape >= 100:
                    cape_cells.append({"lat": lat, "lon": lon, "cape": int(cape),
                                       "dlat": dlat, "dlon": dlon})
        # shear vectors on a 3x3 subset
        for k, ((lat, lon), loc) in enumerate(zip(pts, locs)):
            i, j = divmod(k, _GRID_N)
            if i % 2 or j % 2:
                continue
            h = loc.get("hourly") or {}
            times = h.get("time") or []
            if not times:
                continue
            idx = _nearest_idx(times, target)
            ws1 = (h.get("wind_speed_1000hPa") or [None] * len(times))[idx]
            ws5 = (h.get("wind_speed_500hPa") or [None] * len(times))[idx]
            wd1 = (h.get("wind_direction_1000hPa") or [None] * len(times))[idx]
            wd5 = (h.get("wind_direction_500hPa") or [None] * len(times))[idx]
            if ws5 is None or ws1 is None:
                continue
            u1, v1 = _uv(ws1, wd1)
            u5, v5 = _uv(ws5, wd5)
            shear = math.hypot(u5 - u1, v5 - v1)
            mag5 = math.hypot(u5, v5) or 1.0
            scale = 0.14
            shear_cells.append({
                "lat": lat, "lon": lon,
                "lat2": round(lat + (v5 / mag5) * scale, 4),
                "lon2": round(lon + (u5 / mag5) * scale / max(math.cos(math.radians(lat)), 0.1), 4),
                "shear_ms": round(shear, 1),
            })
        per_lead[lead] = {
            "cape": cape_cells,
            "shear_vectors": shear_cells,
            "cape_max": cape_max,
            "units": {"cape": "J/kg", "shear": "m/s (0-6 km bulk)"},
            "valid_utc": (now + timedelta(minutes=lead)).replace(microsecond=0).isoformat(),
        }

    return {
        "available": True,
        "state": state,
        "attribution": ATTRIBUTION,
        "model": "NOAA GFS 0.25°",
        "source_time_utc": src_valid.replace(microsecond=0).isoformat(),
        "source_time_ist": src_valid.astimezone(IST).replace(microsecond=0).isoformat(),
        "retrieval_time_utc": raw["retrieval_utc"].isoformat(),
        "latency_s": round(latency_s, 0),
        "per_lead": per_lead,
    }
