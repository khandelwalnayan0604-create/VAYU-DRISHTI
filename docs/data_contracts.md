# Data Contracts & Validation Protocol — VayuDrishti Nowcast

All payloads carry a `data_state` ∈ {`simulated`,`test`,`historical`,`delayed`,`live`}.
In this build everything is `simulated`.

## REST API (prefix `/api`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service meta + disclaimer |
| GET | `/health?domain=` | Overall status + per-connector health |
| GET | `/domains` | Pilot domains (Mumbai, Delhi NCR): center, bbox, radar_site, districts |
| GET | `/connectors/status?domain=` | Typed source health records |
| GET | `/nowcast/frames?domain=` | 9 frames (0–180 min @15): reflectivity, lightning, motion_vectors, risk_zones GeoJSON |
| GET | `/storm-tracks?domain=` | TITAN/SCIT-style cell tracks (id, centroid, dBZ, VIL, speed, bearing, split/merge, past+forecast track) |
| GET | `/cross-section?domain=&cell_id=` | Diagnostic altitude×radial reflectivity grid |
| GET | `/verification?domain=` | Per-lead POD/FAR/CSI/ETS/HSS/Brier + reliability/ROC/PR + baselines |
| GET | `/alerts?domain=` | De-duplicated alerts (worst per cell), CAP status=Test |
| GET | `/alerts/{id}/cap.xml?domain=` | CAP 1.2 XML (`<status>Test</status>`) |
| POST | `/alerts/{id}/ack` | Acknowledge → audit record in MongoDB |
| GET | `/alerts/audit?domain=` | Ack/audit history |
| GET | `/safety?domain=` | Public severity, onset, EN/HI advice + safety rules |

## Connector health record fields
`key, name, product, channels, coverage, domain, enabled, mode, data_state, status
(ok|stale|disabled), source_time(+_utc/_ist), retrieval_time(+_utc), latency_s,
nominal_latency_s, cadence_min, quality_flags[], license, error`.

## Risk-zone GeoJSON Feature properties
`cell_id, lead_time_min, probability, severity (green|yellow|orange|red),
severity_label(+_hi), hazard, confidence, model_version, input_freshness_min,
data_state, provenance, issued_ist`.

## Canonical grid (AnalysisCube concept)
Per-domain local lat/lon grid over `bbox`; UTC valid/issue times with IST display.
Channels represented: radar reflectivity, lightning (count/age/type/kA), motion,
NWP framing (documented), quality/provenance masks. Missing channels are explicitly
masked/omitted — never silent zero-filled.

## Validation protocol (for future authorized-data phase)
- Chronological, **event-level blocked** train/val/test — adjacent frames from one
  event cannot leak across splits.
- Compare model vs **persistence** and **optical-flow** at every lead time.
- Metrics by lead time & region: POD, FAR, CSI, ETS, HSS, Brier, reliability curve,
  PR-AUC, ROC-AUC, track position error, latency.
- Reproducible event replay: deterministic seed per domain (`nowcast._rng`).
- Contract tests (`backend/tests/backend_test.py`): CRS/time labels, missing/stale
  source, empty lightning feed, CAP XML structure, GeoJSON validity, disclosure labels.
