# PRD — VayuDrishti Nowcast (SIH 2026 / SIH26072)

## Original problem statement
Production-minded, locally runnable full-stack system for AIML-based nowcasting of
thunderstorm & lightning using multi-radar, satellite, lightning and model data.
India-first; truthful about data state (live/delayed/historical/test/simulated);
0–180 min @ 15-min MVP; operator + public views; verification; CAP 1.2 Test; EN/HI.

## User choices (this build)
- Data: **SIMULATED / replay demo**, clearly labelled.
- Pilot domains: **Mumbai (MMR)** and **Delhi NCR**.
- Auth: **none** — simple Operator/Public role toggle.
- Intelligence: **deterministic/rule-based** (no LLM).
- Design: **dark mission-control** meteorology theme.

## Architecture (adapted to platform stack)
React (CRACO) + vanilla Leaflet frontend · FastAPI backend · MongoDB (alert audit).
Backend modules: `nowcast.py` (deterministic SIMULATED engine), `connectors.py`
(typed source-health), `cap.py` (CAP 1.2, Test-by-default), `server.py` (`/api` REST).

## Personas
- **Operator / forecaster**: provenance, source freshness, quality flags, storm-cell
  tracking, per-lead verification/calibration, cross-section diagnostic, alert ack/audit.
- **Public citizen**: single risk level, onset countdown, plain safety action (EN/HI),
  latest verified alert + CAP download.

## Core requirements (static)
Honest data-state labels everywhere; 0–180 min @15; layer-togglable map (radar,
satellite, lightning, NWP framing, forecast probability, motion vectors, storm tracks,
GeoJSON risk zones); source-health; verification (POD/FAR/CSI/ETS/HSS/Brier, reliability,
ROC/PR-AUC, baselines); CAP 1.2 Test; EN/HI; c4dl-multi treated as non-deployed baseline.

## Implemented (2026-06 / first MVP)
- Deterministic replayable simulator (Mumbai, Delhi) — reflectivity grid, lightning,
  motion, storm tracks, thresholded probability → GeoJSON risk zones, cross-section.
- 4 disable-able connectors with full health records + spec field aliases.
- REST: health, domains, connectors, nowcast/frames, storm-tracks, cross-section,
  verification, alerts, cap.xml, ack, audit, safety.
- Operator + Public dashboards, dark theme, Esri dark basemap, timeline play/scrub,
  layer toggles, alert focus/ack, EN/HI, cross-section modal.
- Docs: README (honest availability table, live-switch guide, validation plan),
  THIRD_PARTY_NOTICES, docs/data_contracts.md. Backend contract tests (12/12 pass).
- E2E tested: backend 100%, frontend 100%.

## Iteration 2 (all 9 domains + real satellite/NWP channels)
- Added Kolkata, Bhubaneswar, Guwahati, Chennai, Hyderabad, Bengaluru, Kochi.
- Distinct INSAT-3D IR cloud-top channel + NWP CAPE/shear channel + layer toggle.
- Satellite basemap switcher (Esri World Imagery / OSM / Dark). Tested 21/21.

## Iteration 3 (FIRST REAL feed — NOAA GFS, 2026-06)
- Live NOAA GFS connector (`gfs.py`) via Open-Meteo (free, no key): real CAPE +
  0-6 km bulk shear + steering wind per domain, per-lead across the 0-180 min
  timeline; 15-min cache, 3x retry, 60s negative-cache, startup warm for 9 domains.
- Honest MIXED state: NWP reads `live`/`delayed` with real timestamps + NOAA/Open-Meteo
  attribution; synthetic fallback relabels `simulated` on failure. Radar/INSAT/lightning
  stay SIMULATED and expose authorized connectors `disabled — awaiting credentials`
  (enable via `VD_<KEY>_CREDENTIALS`). Banner + layer badge + source-health reflect the mix.
- Docs refreshed (availability table + how-to-enable each authorized source). Tested 21/21.

## Backlog (prioritized)
- **P1**: Add remaining pilot domains (Kolkata, Bhubaneswar, Guwahati, Chennai,
  Hyderabad, Bengaluru, Kochi); WebSocket live event stream; INSAT IR layer as distinct
  channel (not reflectivity proxy); NWP CAPE/shear contour layer.
- **P1**: Replay-mode toggle in UI + archived-event picker.
- **P2**: 3–6 h NWP-dominated outlook shown separately (clearly non-radar).
- **P2**: District-boundary GeoJSON overlay + geofenced district risk table.
- **P2**: MC-dropout/quantile uncertainty bands; alert rate-limiting config UI.
- **P3**: Authorized live-connector adapters + Indian model training pipeline.

## Next tasks
Add more pilot domains and a district-boundary overlay; introduce a distinct
satellite IR channel and an NWP CAPE layer.
