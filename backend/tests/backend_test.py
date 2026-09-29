"""VayuDrishti Nowcast backend API tests."""
import os
import re
import pytest
import requests
from xml.etree import ElementTree as ET

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://drishti-storm.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# Health
def test_health_mumbai(s):
    r = s.get(f"{API}/health", params={"domain": "mumbai"})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "up"
    assert d["data_state"] == "simulated"
    src = d["sources"]["mumbai"]
    assert src["total"] == 4
    assert len(src["connectors"]) == 4
    for c in src["connectors"]:
        assert c["status"] in ("ok", "stale", "down")


# Domains
def test_domains(s):
    r = s.get(f"{API}/domains")
    assert r.status_code == 200
    ids = {d["id"] for d in r.json()["domains"]}
    assert {"mumbai", "delhi"} <= ids
    for d in r.json()["domains"]:
        assert "center" in d and "bbox" in d and "radar_site" in d and "districts" in d


# Connectors
def test_connectors_status(s):
    r = s.get(f"{API}/connectors/status", params={"domain": "mumbai"})
    assert r.status_code == 200
    conns = r.json()["connectors"]
    assert len(conns) == 4
    # NOTE: spec asks for `source_time`/`retrieval_time`, backend returns *_utc/_ist variants
    keys = {"latency_s", "quality_flags", "mode", "data_state", "status", "license", "error"}
    for c in conns:
        assert keys <= set(c.keys())
        assert "source_time_utc" in c and "retrieval_time_utc" in c


# Nowcast frames
def test_nowcast_frames(s):
    r = s.get(f"{API}/nowcast/frames", params={"domain": "mumbai"})
    assert r.status_code == 200
    data = r.json()
    frames = data["frames"]
    assert len(frames) == 9
    leads = [f["lead_time_min"] for f in frames]
    assert leads == list(range(0, 181, 15)) or leads[0] == 0 and leads[-1] == 180
    f0 = frames[0]
    assert isinstance(f0["reflectivity"], list)
    assert isinstance(f0["lightning"], list)
    assert isinstance(f0["motion_vectors"], list)
    rz = f0["risk_zones"]
    assert rz["type"] == "FeatureCollection"
    if rz["features"]:
        p = rz["features"][0]["properties"]
        for k in ("lead_time_min", "probability", "severity", "confidence", "model_version", "data_state"):
            assert k in p


# Storm tracks
def test_storm_tracks_delhi(s):
    r = s.get(f"{API}/storm-tracks", params={"domain": "delhi"})
    assert r.status_code == 200
    tracks = r.json()["tracks"]
    assert len(tracks) > 0
    t = tracks[0]
    for k in ("cell_id", "centroid", "max_dbz", "vil", "speed_kmh", "bearing", "past_track", "forecast_track", "split_prob", "merge_prob"):
        assert k in t


# Cross section
def test_cross_section(s):
    r = s.get(f"{API}/cross-section", params={"domain": "mumbai", "cell_id": "MUM-C01"})
    assert r.status_code == 200
    d = r.json()
    assert "reflectivity" in d and isinstance(d["reflectivity"], list)
    assert isinstance(d["reflectivity"][0], list)
    for k in ("altitudes_km", "radial_km", "freezing_level_km", "echo_top_km"):
        assert k in d


# Verification
def test_verification(s):
    r = s.get(f"{API}/verification", params={"domain": "mumbai"})
    assert r.status_code == 200
    d = r.json()
    assert len(d["per_lead"]) == 8
    row = d["per_lead"][0]
    assert "model" in row and "persistence" in row and "optical_flow" in row
    assert "csi" in row["model"]
    for k in ("reliability_curve", "roc_curve", "pr_curve", "roc_auc", "pr_auc"):
        assert k in d


# Alerts list
def test_alerts(s):
    r = s.get(f"{API}/alerts", params={"domain": "mumbai"})
    assert r.status_code == 200
    d = r.json()
    assert d["worst_severity"] in ("green", "yellow", "orange", "red")
    assert d["count"] == len(d["alerts"])
    if d["alerts"]:
        rank = {"green": 0, "yellow": 1, "orange": 2, "red": 3}
        ranks = [rank[a["severity"]] for a in d["alerts"]]
        assert ranks == sorted(ranks, reverse=True)
        a = d["alerts"][0]
        for k in ("id", "severity", "probability", "confidence", "lead_time_min", "polygon", "cap_status"):
            assert k in a
        assert a["cap_status"] == "Test"


# CAP XML
def test_cap_xml(s):
    r = s.get(f"{API}/alerts", params={"domain": "mumbai"})
    aid = r.json()["alerts"][0]["id"]
    r2 = s.get(f"{API}/alerts/{aid}/cap.xml", params={"domain": "mumbai"})
    assert r2.status_code == 200
    assert "application/xml" in r2.headers.get("content-type", "")
    xml = r2.text
    assert "urn:oasis:names:tc:emergency:cap:1.2" in xml
    assert "<status>Test</status>" in xml
    assert "<polygon>" in xml
    ET.fromstring(xml)  # well-formed


# Ack + audit
def test_ack_and_audit(s):
    alerts = s.get(f"{API}/alerts", params={"domain": "mumbai"}).json()["alerts"]
    aid = alerts[0]["id"]
    r = s.post(f"{API}/alerts/{aid}/ack", json={"domain": "mumbai", "operator": "TEST_operator", "note": "TEST_note"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["audit"]["alert_id"] == aid

    r2 = s.get(f"{API}/alerts", params={"domain": "mumbai"})
    found = [a for a in r2.json()["alerts"] if a["id"] == aid][0]
    assert found["acknowledged"] is True

    r3 = s.get(f"{API}/alerts/audit", params={"domain": "mumbai"})
    assert r3.status_code == 200
    assert any(rec["alert_id"] == aid for rec in r3.json()["records"])


# Safety
def test_safety(s):
    r = s.get(f"{API}/safety", params={"domain": "mumbai"})
    assert r.status_code == 200
    d = r.json()
    for k in ("severity", "severity_label", "severity_label_hi", "minutes_to_onset", "advice", "latest_alert", "rules"):
        assert k in d
    assert "en" in d["advice"] and "hi" in d["advice"]
    assert "en" in d["rules"] and "hi" in d["rules"]


def test_unknown_domain(s):
    r = s.get(f"{API}/connectors/status", params={"domain": "xyz"})
    assert r.status_code == 404
