"""
Source connectors — each returns a health/status record and is independently
disable-able. In this demo build every connector runs in SIMULATED / REPLAY
mode: it does NOT contact IMD, MOSDAC/INSAT, IITM/ENTLN or any NWP endpoint.
Switching to authorized live connectors is an env-driven operation documented
in the README; credentials are never exposed to the browser.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from nowcast import DOMAINS

IST = timezone(timedelta(hours=5, minutes=30))

# A connector is "enabled" unless disabled via env: VD_DISABLE_<KEY>=1
_CONNECTOR_DEFS = [
    {
        "key": "dwr",
        "name": "IMD Doppler Weather Radar (DWR)",
        "product": "S-band reflectivity + radial velocity",
        "channels": ["reflectivity_dbz", "radial_velocity", "quality_flags"],
        "coverage_note": "Per-domain radar site (see domain).",
        "nominal_latency_s": 300,
        "cadence_min": 10,
        "license": "IMD authorization required for operational feed",
    },
    {
        "key": "insat",
        "name": "INSAT-3D / MOSDAC Satellite",
        "product": "IR/WV brightness temperature + cloud-top cooling rate",
        "channels": ["ir_bt", "wv_bt", "cooling_rate"],
        "coverage_note": "Full-disk; sampled to domain.",
        "nominal_latency_s": 1800,
        "cadence_min": 30,
        "license": "MOSDAC/ISRO terms of use",
    },
    {
        "key": "lightning",
        "name": "IITM / ENTLN Lightning Network",
        "product": "CG/IC strike geolocation, polarity, peak current",
        "channels": ["strike_lat_lon", "type", "peak_current_kA", "age_min"],
        "coverage_note": "Network-dependent detection efficiency.",
        "nominal_latency_s": 60,
        "cadence_min": 1,
        "license": "IITM/authorized provider agreement",
    },
    {
        "key": "nwp",
        "name": "NWP (GFS / ERA5 / NCMRWF)",
        "product": "CAPE, CIN, PW, 0-6km shear, steering wind",
        "channels": ["cape", "cin", "pw", "shear_0_6km", "steering_wind"],
        "coverage_note": "Model grid regridded to domain.",
        "nominal_latency_s": 5400,
        "cadence_min": 360,
        "license": "GFS public / ERA5 CDS / IMD-authorized",
    },
]

_MODE = os.environ.get("VD_DATA_MODE", "simulated")  # simulated | replay | live


def _disabled(key: str) -> bool:
    return os.environ.get(f"VD_DISABLE_{key.upper()}", "0") == "1"


def connector_status(domain: str) -> List[Dict[str, Any]]:
    if domain not in DOMAINS:
        return []
    d = DOMAINS[domain]
    now = datetime.now(timezone.utc)
    out = []
    # deterministic-ish but time-based freshness
    for i, c in enumerate(_CONNECTOR_DEFS):
        enabled = not _disabled(c["key"])
        # synthetic source/retrieval timestamps
        src_age = c["cadence_min"] + (i * 2)
        source_time = now - timedelta(minutes=src_age)
        retrieval_time = now - timedelta(seconds=max(5, c["nominal_latency_s"] // 60))
        latency_s = round((retrieval_time - source_time).total_seconds(), 0)
        stale = latency_s > c["nominal_latency_s"] * 3
        quality_flags = []
        if c["key"] == "dwr":
            quality_flags = ["clutter_filtered", "beam_blockage_corrected"]
        elif c["key"] == "insat":
            quality_flags = ["parallax_uncorrected"]
        elif c["key"] == "lightning":
            quality_flags = ["network_de_variable"]
        elif c["key"] == "nwp":
            quality_flags = ["coarse_grid_regridded"]

        if not enabled:
            status = "disabled"
        elif stale:
            status = "stale"
        else:
            status = "ok"

        out.append({
            "key": c["key"],
            "name": c["name"],
            "product": c["product"],
            "channels": c["channels"],
            "coverage": d["radar"] if c["key"] == "dwr" else c["coverage_note"],
            "domain": domain,
            "enabled": enabled,
            "mode": _MODE,
            "data_state": "simulated" if _MODE == "simulated" else _MODE,
            "status": status,
            "source_time": source_time.replace(microsecond=0).isoformat(),
            "retrieval_time": retrieval_time.replace(microsecond=0).isoformat(),
            "source_time_utc": source_time.replace(microsecond=0).isoformat(),
            "source_time_ist": source_time.astimezone(IST).replace(microsecond=0).isoformat(),
            "retrieval_time_utc": retrieval_time.replace(microsecond=0).isoformat(),
            "latency_s": latency_s,
            "nominal_latency_s": c["nominal_latency_s"],
            "cadence_min": c["cadence_min"],
            "quality_flags": quality_flags,
            "license": c["license"],
            "error": None if enabled else "Connector disabled via configuration.",
        })
    return out
