"""
Source connectors with honest, per-source data-state.

Phase 1 reality:
- NWP is REAL (NOAA GFS via Open-Meteo) — labelled `live`/`delayed` with real
  source/retrieval times and latency, or relabelled `simulated` on fallback.
- Radar (IMD DWR), Satellite (INSAT-3D/MOSDAC) and Lightning (ILDN/IITM) feed
  the map from SIMULATED synthetic data and additionally expose an
  authorized-real connector that is `disabled — awaiting authorized credentials`.
  Enabling them later is a configuration step (env creds), not a rebuild.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from nowcast import DOMAINS
import gfs

IST = timezone(timedelta(hours=5, minutes=30))
_MODE = os.environ.get("VD_DATA_MODE", "simulated")


def _disabled(key: str) -> bool:
    return os.environ.get(f"VD_DISABLE_{key.upper()}", "0") == "1"


def _authorized_enabled(key: str) -> bool:
    """A real Indian source turns on only when its credential env var is set."""
    return bool(os.environ.get(f"VD_{key.upper()}_CREDENTIALS"))


# Authorized-ready (Phase 2) source metadata — disabled until credentials exist.
_AUTHORIZED = {
    "dwr": {
        "name": "IMD Doppler Weather Radar (DWR)",
        "product": "S-band reflectivity + radial velocity",
        "channels": ["reflectivity_dbz", "radial_velocity", "quality_flags"],
        "cadence_min": 10,
        "provider": "India Meteorological Department (IMD)",
        "access_route": "IMD data-supply agreement / MoES; RCTLS DWR product access",
        "license": "IMD authorization required (attribution: © IMD)",
        "attribution": "© India Meteorological Department",
        "quality_flags": ["clutter_filtered", "beam_blockage_corrected"],
    },
    "insat": {
        "name": "INSAT-3D / MOSDAC Satellite",
        "product": "IR/WV brightness temperature + cloud-top cooling rate",
        "channels": ["ir_bt", "wv_bt", "cooling_rate"],
        "cadence_min": 30,
        "provider": "ISRO / MOSDAC",
        "access_route": "MOSDAC portal login (mosdac.gov.in) → INSAT-3D product order/API",
        "license": "MOSDAC/ISRO terms of use (attribution: ISRO/MOSDAC)",
        "attribution": "© ISRO / MOSDAC",
        "quality_flags": ["parallax_uncorrected"],
    },
    "lightning": {
        "name": "Lightning Network (IITM / ILDN)",
        "product": "CG/IC strike geolocation, polarity, peak current",
        "channels": ["strike_lat_lon", "type", "peak_current_kA", "age_min"],
        "cadence_min": 1,
        "provider": "IITM Pune / India Lightning Detection Network",
        "access_route": "IITM/ILDN data agreement (authorized provider)",
        "license": "IITM/authorized provider agreement",
        "attribution": "© IITM Pune / ILDN",
        "quality_flags": ["network_de_variable"],
    },
}


def _sim_record(key: str, domain: str) -> Dict[str, Any]:
    """A radar/satellite/lightning source: SIMULATED feed + pending real connector."""
    d = DOMAINS[domain]
    meta = _AUTHORIZED[key]
    now = datetime.now(timezone.utc)
    src = now - timedelta(minutes=meta["cadence_min"])
    enabled = not _disabled(key)
    authorized_on = _authorized_enabled(key)
    return {
        "key": key,
        "name": meta["name"],
        "product": meta["product"],
        "channels": meta["channels"],
        "coverage": d["radar"] if key == "dwr" else f"{d['name']} domain",
        "domain": domain,
        "enabled": enabled,
        "real": False,
        "mode": "simulated",
        "data_state": "simulated" if enabled else "disabled",
        "status": "simulated" if enabled else "disabled",
        "source_time": src.replace(microsecond=0).isoformat(),
        "source_time_utc": src.replace(microsecond=0).isoformat(),
        "source_time_ist": src.astimezone(IST).replace(microsecond=0).isoformat(),
        "retrieval_time": now.replace(microsecond=0).isoformat(),
        "retrieval_time_utc": now.replace(microsecond=0).isoformat(),
        "latency_s": meta["cadence_min"] * 60,
        "nominal_latency_s": meta["cadence_min"] * 60,
        "cadence_min": meta["cadence_min"],
        "quality_flags": meta["quality_flags"],
        "license": meta["license"],
        "attribution": meta["attribution"],
        "authorized_provider": meta["provider"],
        "access_route": meta["access_route"],
        "authorized_status": ("enabled" if authorized_on
                              else "disabled — awaiting authorized credentials"),
        "error": None if enabled else "Connector disabled via configuration.",
    }


def _nwp_record(domain: str, bundle: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    d = DOMAINS[domain]
    now = datetime.now(timezone.utc)
    base = {
        "key": "nwp",
        "name": "NWP — NOAA GFS (real)",
        "product": "CAPE + 0-6 km bulk shear + steering wind",
        "channels": ["cape", "shear_0_6km", "wind_1000hPa", "wind_500hPa"],
        "coverage": f"GFS 0.25° regridded to {d['name']} (6×6)",
        "domain": domain,
        "cadence_min": 360,
        "nominal_latency_s": 5 * 3600,
        "quality_flags": ["gfs_0p25deg", "coarse_regridded"],
        "license": "NOAA GFS public domain; Open-Meteo CC-BY 4.0",
        "attribution": gfs.ATTRIBUTION,
        "authorized_provider": "NOAA / NCEP (via Open-Meteo)",
        "access_route": "Open-Meteo GFS endpoint (free, no key)",
        "authorized_status": "enabled",
        "real": True,
        "enabled": True,
    }
    if bundle and bundle.get("available"):
        base.update({
            "mode": "live",
            "data_state": bundle["state"],           # live | delayed
            "status": "ok",
            "source_time": bundle["source_time_utc"],
            "source_time_utc": bundle["source_time_utc"],
            "source_time_ist": bundle["source_time_ist"],
            "retrieval_time": bundle["retrieval_time_utc"],
            "retrieval_time_utc": bundle["retrieval_time_utc"],
            "latency_s": bundle["latency_s"],
            "model": bundle["model"],
            "error": None,
        })
    else:
        base.update({
            "mode": "simulated",
            "data_state": "simulated",
            "status": "stale",
            "real": False,
            "source_time": now.replace(microsecond=0).isoformat(),
            "source_time_utc": now.replace(microsecond=0).isoformat(),
            "source_time_ist": now.astimezone(IST).replace(microsecond=0).isoformat(),
            "retrieval_time": now.replace(microsecond=0).isoformat(),
            "retrieval_time_utc": now.replace(microsecond=0).isoformat(),
            "latency_s": 0,
            "model": "synthetic fallback",
            "error": "GFS fetch unavailable — using SIMULATED synthetic NWP fallback.",
        })
    return base


def connector_status(domain: str, nwp_bundle: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if domain not in DOMAINS:
        return []
    return [
        _nwp_record(domain, nwp_bundle),
        _sim_record("dwr", domain),
        _sim_record("insat", domain),
        _sim_record("lightning", domain),
    ]
