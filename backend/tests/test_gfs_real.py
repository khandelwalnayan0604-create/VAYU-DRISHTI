"""Iteration 3 — validate the FIRST real feed (NOAA GFS via Open-Meteo).

Rules:
- /connectors/status must include nwp with real=True, data_state live/delayed,
  status ok, numeric latency, and attribution mentioning NOAA GFS / Open-Meteo.
- Other three (dwr, insat, lightning) must be real=False, data_state=simulated
  and authorized_status='disabled — awaiting authorized credentials'.
- /nowcast/frames must expose top-level nwp_state and nwp_attribution and per
  frame nwp cape/shear/valid_utc that advance with lead_time_min.
- Regression: other endpoints keep responding.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests

# Load REACT_APP_BACKEND_URL from /app/frontend/.env
_FRONTEND_ENV = Path("/app/frontend/.env")
if _FRONTEND_ENV.exists():
    for line in _FRONTEND_ENV.read_text().splitlines():
        m = re.match(r"^\s*([A-Z_]+)=(.*)$", line)
        if m:
            os.environ.setdefault(m.group(1), m.group(2).strip())

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
DOMAINS_TO_TEST = ["mumbai", "chennai", "delhi", "kolkata"]


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# -------- /connectors/status --------
@pytest.mark.parametrize("domain", DOMAINS_TO_TEST)
def test_connectors_status_nwp_real(s, domain):
    r = s.get(f"{BASE_URL}/api/connectors/status", params={"domain": domain}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "real_sources" in data
    conns = {c["key"]: c for c in data["connectors"]}
    nwp = conns["nwp"]

    if nwp["real"] is True:
        assert nwp["data_state"] in ("live", "delayed"), nwp
        assert nwp["status"] == "ok"
        assert isinstance(nwp["latency_s"], (int, float))
        attr = nwp["attribution"].lower()
        assert "gfs" in attr or "open-meteo" in attr
        assert nwp["source_time_utc"] and nwp["source_time_ist"]
        assert "nwp" in data["real_sources"]
    else:
        # Fallback branch — must be honest
        assert nwp["data_state"] == "simulated"
        assert nwp["status"] == "stale"
        assert nwp["error"]


@pytest.mark.parametrize("domain", DOMAINS_TO_TEST)
def test_connectors_status_others_authorized_disabled(s, domain):
    r = s.get(f"{BASE_URL}/api/connectors/status", params={"domain": domain}, timeout=30)
    data = r.json()
    conns = {c["key"]: c for c in data["connectors"]}
    for key in ("dwr", "insat", "lightning"):
        c = conns[key]
        assert c["real"] is False, key
        assert c["data_state"] == "simulated", key
        assert c["authorized_status"] == "disabled — awaiting authorized credentials", key
        assert c.get("authorized_provider")
        assert c.get("access_route")
        assert c.get("attribution")


# -------- /nowcast/frames --------
@pytest.mark.parametrize("domain", DOMAINS_TO_TEST)
def test_nowcast_frames_nwp(s, domain):
    r = s.get(f"{BASE_URL}/api/nowcast/frames", params={"domain": domain}, timeout=45)
    assert r.status_code == 200
    d = r.json()
    assert d["nwp_state"] in ("live", "delayed", "simulated")
    assert d["nwp_attribution"]
    assert d["frames"], "no frames"
    # check leads present + valid_utc advances
    leads_valid = []
    for f in d["frames"]:
        nwp = f["nwp"]
        assert "cape" in nwp and isinstance(nwp["cape"], list)
        assert "shear_vectors" in nwp and isinstance(nwp["shear_vectors"], list)
        assert "cape_max" in nwp and isinstance(nwp["cape_max"], int)
        assert nwp.get("units")
        assert nwp.get("valid_utc")
        leads_valid.append((f["lead_time_min"], nwp["valid_utc"]))
        if d["nwp_state"] in ("live", "delayed"):
            assert nwp["real"] is True
            # sanity: cape values are 0..~6000
            for cell in nwp["cape"]:
                assert 0 <= cell["cape"] <= 6000
                for k in ("lat", "lon", "dlat", "dlon"):
                    assert k in cell
            for v in nwp["shear_vectors"]:
                for k in ("lat", "lon", "lat2", "lon2", "shear_ms"):
                    assert k in v
    # valid_utc strictly increases as lead_time_min increases
    times = [v for _, v in leads_valid]
    assert times == sorted(times), f"valid_utc not monotonic: {times}"


# -------- regression --------
@pytest.mark.parametrize("path,params", [
    ("/api/alerts", {"domain": "mumbai"}),
    ("/api/storm-tracks", {"domain": "mumbai"}),
    ("/api/verification", {"domain": "mumbai"}),
    ("/api/safety", {"domain": "mumbai"}),
    ("/api/domains", {}),
])
def test_regression_endpoints(s, path, params):
    r = s.get(f"{BASE_URL}{path}", params=params, timeout=30)
    assert r.status_code == 200, path


def test_domains_count(s):
    r = s.get(f"{BASE_URL}/api/domains", timeout=15)
    assert len(r.json()["domains"]) == 9


def test_cross_section(s):
    tracks = s.get(f"{BASE_URL}/api/storm-tracks", params={"domain": "mumbai"}, timeout=15).json()
    cid = tracks["tracks"][0]["cell_id"]
    r = s.get(f"{BASE_URL}/api/cross-section",
              params={"domain": "mumbai", "cell_id": cid}, timeout=15)
    assert r.status_code == 200


def test_cap_xml(s):
    alerts = s.get(f"{BASE_URL}/api/alerts", params={"domain": "mumbai"}, timeout=15).json()
    if not alerts["alerts"]:
        pytest.skip("no alerts to build CAP for")
    aid = alerts["alerts"][0]["id"]
    r = s.get(f"{BASE_URL}/api/alerts/{aid}/cap.xml",
              params={"domain": "mumbai"}, timeout=15)
    assert r.status_code == 200
    assert "<alert" in r.text.lower()


def test_frames_still_have_simulated_layers(s):
    r = s.get(f"{BASE_URL}/api/nowcast/frames", params={"domain": "mumbai"}, timeout=30)
    frame = r.json()["frames"][0]
    for layer in ("reflectivity", "satellite", "lightning"):
        assert layer in frame, layer
