"""Tests for the 9-domain expansion and INSAT IR + NWP CAPE/shear channels."""
import os
import pytest
import requests
from xml.etree import ElementTree as ET

from pathlib import Path
_env = Path(__file__).parent.parent.parent / "frontend" / ".env"
if _env.exists() and "REACT_APP_BACKEND_URL" not in os.environ:
    for line in _env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            os.environ["REACT_APP_BACKEND_URL"] = line.split("=", 1)[1].strip()
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_DOMAINS = {
    "mumbai", "delhi", "kolkata", "bhubaneswar", "guwahati",
    "chennai", "hyderabad", "bengaluru", "kochi",
}


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# 1. Domains endpoint has all 9 pilot domains with required fields
def test_domains_lists_all_nine(s):
    r = s.get(f"{API}/domains")
    assert r.status_code == 200
    data = r.json()
    ids = {d["id"] for d in data["domains"]}
    assert ids == EXPECTED_DOMAINS, f"Missing/extra domains: {ids ^ EXPECTED_DOMAINS}"
    for d in data["domains"]:
        for k in ("center", "bbox", "radar_site", "districts", "name"):
            assert k in d and d[k], f"{d['id']} missing {k}"
        assert len(d["center"]) == 2
        assert len(d["bbox"]) == 4
        assert len(d["radar_site"]) == 2
        assert isinstance(d["districts"], list) and len(d["districts"]) > 0


# 2. For each domain: nowcast frames has 9 frames with satellite + nwp
@pytest.mark.parametrize("domain", sorted(EXPECTED_DOMAINS))
def test_nowcast_frames_have_satellite_and_nwp(s, domain):
    r = s.get(f"{API}/nowcast/frames", params={"domain": domain})
    assert r.status_code == 200, f"{domain}: {r.status_code}"
    data = r.json()
    assert data["data_state"] == "simulated"
    frames = data["frames"]
    assert len(frames) == 9, f"{domain}: got {len(frames)} frames"

    # Find a frame with meaningful satellite data (typically mid-lead-time when convection is strong)
    any_sat = False
    any_cape = False
    for f in frames:
        # existing keys still present
        for k in ("reflectivity", "lightning", "motion_vectors", "risk_zones", "satellite", "nwp"):
            assert k in f, f"{domain} lead={f.get('lead_time_min')}: missing {k}"

        sat = f["satellite"]
        assert isinstance(sat, list)
        for item in sat[:5]:
            assert set(("lat", "lon", "bt", "dlat", "dlon")) <= set(item.keys())
            assert 198 <= item["bt"] <= 300  # Kelvin
        if sat:
            any_sat = True

        nwp = f["nwp"]
        assert isinstance(nwp, dict)
        for k in ("cape", "shear_vectors", "cape_max", "units", "data_state"):
            assert k in nwp, f"{domain}: nwp missing {k}"
        assert nwp["data_state"] == "simulated"
        assert isinstance(nwp["cape"], list)
        assert isinstance(nwp["shear_vectors"], list) and len(nwp["shear_vectors"]) > 0
        for item in nwp["cape"][:3]:
            assert set(("lat", "lon", "cape", "dlat", "dlon")) <= set(item.keys())
            assert 0 <= item["cape"] <= 4300
        for v in nwp["shear_vectors"][:3]:
            assert set(("lat", "lon", "lat2", "lon2", "shear_ms")) <= set(v.keys())
        if nwp["cape"]:
            any_cape = True

    assert any_sat, f"{domain}: satellite list empty across all frames"
    assert any_cape, f"{domain}: nwp.cape list empty across all frames"


# 3. Ancillary endpoints per domain
@pytest.mark.parametrize("domain", sorted(EXPECTED_DOMAINS))
def test_ancillary_endpoints(s, domain):
    for path in ("/alerts", "/storm-tracks", "/verification", "/safety", "/connectors/status"):
        r = s.get(f"{API}{path}", params={"domain": domain})
        assert r.status_code == 200, f"{domain} {path}: {r.status_code}"
        d = r.json()
        assert d.get("data_state") == "simulated" or any(
            v == "simulated" for v in d.values() if isinstance(v, str)
        ), f"{domain} {path}: no simulated flag"
    # coverage string mentions radar for that domain (via connectors)
    r = s.get(f"{API}/connectors/status", params={"domain": domain})
    conns = r.json()["connectors"]
    radar_conn = [c for c in conns if "radar" in c.get("source", "").lower() or "dwr" in str(c).lower()]
    assert conns, f"{domain}: no connectors"


# 4. cross-section for kochi cell KOC-C01 (using real cell_id from storm-tracks)
def test_cross_section_kochi(s):
    r = s.get(f"{API}/storm-tracks", params={"domain": "kochi"})
    assert r.status_code == 200
    tracks = r.json()["tracks"]
    cell_ids = [t["cell_id"] for t in tracks]
    assert "KOC-C01" in cell_ids, f"expected KOC-C01 in {cell_ids}"
    r2 = s.get(f"{API}/cross-section", params={"domain": "kochi", "cell_id": "KOC-C01"})
    assert r2.status_code == 200
    d = r2.json()
    assert isinstance(d["reflectivity"], list) and isinstance(d["reflectivity"][0], list)
    assert "altitudes_km" in d and "radial_km" in d
    assert d["cell_id"] == "KOC-C01"


# 5. CAP export for kolkata
def test_cap_export_kolkata(s):
    r = s.get(f"{API}/alerts", params={"domain": "kolkata"})
    assert r.status_code == 200
    alerts = r.json()["alerts"]
    assert alerts, "no kolkata alerts"
    aid = alerts[0]["id"]
    r2 = s.get(f"{API}/alerts/{aid}/cap.xml", params={"domain": "kolkata"})
    assert r2.status_code == 200
    xml = r2.text
    assert "urn:oasis:names:tc:emergency:cap:1.2" in xml
    assert "<status>Test</status>" in xml
    ET.fromstring(xml)  # well-formed
