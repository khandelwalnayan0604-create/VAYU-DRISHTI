# VayuDrishti Nowcast — SIH 2026 / SIH26072

**AIML-based nowcasting of thunderstorm & lightning** using atmospheric observations
(radar, satellite, lightning, NWP). India-first UI (Indian map extents, IST, IMD
warning terminology, INSAT/DWR product framing, district boundaries).

> ⚠️ **TRUTH-IN-DATA — READ THIS FIRST.** This build runs on **SIMULATED / REPLAY
> DEMO** data. It is **NOT** derived from IMD DWR, INSAT/MOSDAC, IITM/ENTLN
> lightning, or any NWP source, and must **NOT** be treated as operational Indian
> guidance. The `MeteoSwiss/c4dl-multi` model is **Swiss research infrastructure**,
> used here only as an adapter/baseline concept and **NOT deployed for India**.
> Every view and every API response is explicitly labelled
> `simulated` / `test` / `historical` / `delayed` / `live`.

---

## Stack (as deployed here)

The original problem statement specifies a Postgres/PostGIS + Celery/Redis + Docker
Compose monorepo. This deployment adapts that architecture **faithfully in spirit**
to the managed platform stack while preserving the non-negotiable ethos
(honest data-state labelling, typed source connectors with health records,
0–180 min @ 15-min forecasting, verification, CAP 1.2 Test export):

| Concern | Spec | This build |
|---|---|---|
| API | FastAPI | FastAPI (`/app/backend`) |
| Geospatial store | PostGIS | MongoDB (alert audit); GeoJSON computed in-engine |
| Jobs | Celery/Redis | Deterministic on-request simulator (replayable via seed) |
| Frontend | React + TS + Vite + Leaflet | React + CRACO + **vanilla Leaflet** |
| Model | c4dl-multi (retrained) | Optical-flow/persistence baseline over synthetic cells (SIMULATED) |

## Run

Backend, frontend and MongoDB are supervisor-managed and already running.
- Frontend: `REACT_APP_BACKEND_URL` (see `frontend/.env`)
- API docs: `${REACT_APP_BACKEND_URL}/docs`
- Backend tests: `cd /app && pytest backend/tests/backend_test.py -v`

## Data-availability table (honest — MIXED state)

| Source | Connector | State in this build | Authorized-live path |
|---|---|---|---|
| **NWP (NOAA GFS 0.25°)** | `nwp` | **REAL — `live`/`delayed`** (CAPE + 0-6 km bulk shear + steering wind), fetched from Open-Meteo's free GFS endpoint, per-lead across the timeline. Falls back to synthetic and relabels `simulated` if unreachable. | Already live; no key needed. Public-domain NOAA data via Open-Meteo (CC-BY 4.0). |
| IMD Doppler Weather Radar (S-band) | `dwr` | **SIMULATED** feed + authorized connector `disabled — awaiting authorized credentials` | Set `VD_DWR_CREDENTIALS` (IMD data-supply agreement) |
| INSAT-3D / MOSDAC (IR/WV) | `insat` | **SIMULATED** feed + authorized connector `disabled — awaiting authorized credentials` | Set `VD_INSAT_CREDENTIALS` (MOSDAC login) |
| Lightning (IITM / ILDN) | `lightning` | **SIMULATED** feed + authorized connector `disabled — awaiting authorized credentials` | Set `VD_LIGHTNING_CREDENTIALS` (IITM/ILDN agreement) |

The global banner reflects the live mix, e.g. *"NWP: LIVE NOAA GFS · radar / satellite / lightning: SIMULATED"*.

## How to enable each authorized source (Phase 2)

Enabling a pending source is a **configuration step, not a rebuild** — set the
credential env var (server-side only, never exposed to the browser) and restart:

| Source | Env var | Provider access route | License / attribution |
|---|---|---|---|
| IMD DWR radar | `VD_DWR_CREDENTIALS` | IMD data-supply agreement / MoES; RCTLS DWR product access | © India Meteorological Department |
| INSAT-3D | `VD_INSAT_CREDENTIALS` | MOSDAC portal login (mosdac.gov.in) → INSAT-3D product order/API | © ISRO / MOSDAC |
| Lightning | `VD_LIGHTNING_CREDENTIALS` | IITM Pune / India Lightning Detection Network (ILDN) agreement | © IITM Pune / ILDN |
| NWP (GFS) | *(none — already live)* | Open-Meteo GFS endpoint (free) | NOAA GFS public domain; Open-Meteo CC-BY 4.0 |

Each connector remains independently disable-able via `VD_DISABLE_<KEY>=1`.

## Switching to authorized live connectors (documented, not enabled)

Live data and `Actual` CAP dispatch are gated behind environment switches that are
**intentionally off** in this demo. Credentials are **never** exposed to the browser.

```bash
VD_DATA_MODE=live            # simulated | replay | live
VD_DISABLE_DWR=0             # per-connector kill switch
VD_CAP_STATUS=Actual         # requires ops authorization below
VD_OPS_AUTHORIZED=1          # controlled operational-authorization switch
```
Without `VD_CAP_STATUS=Actual` **and** `VD_OPS_AUTHORIZED=1`, all CAP messages are
emitted with `<status>Test</status>` and nothing is dispatched (no SMS/push/3rd-party).

## System / data architecture

`connectors.py` (typed source health) → `nowcast.py` (canonical grid → reflectivity,
lightning, motion, storm tracks, thresholded probability → GeoJSON risk zones,
cross-section, verification) → `server.py` (versioned `/api` REST) → React/Leaflet
operator & public dashboards. See `docs/` for data contracts and validation protocol.

## Validation results (SIMULATED)

Verification is computed for demo/contract purposes only (`/api/verification`): per-lead
POD/FAR/CSI/ETS/HSS/Brier, reliability curve, ROC/PR-AUC, track error, latency, with
persistence and optical-flow baselines at every lead time. Partitions are described as
chronological, event-level blocked splits to prevent adjacent-frame leakage. **These
numbers are synthetic and are NOT validated on authorized Indian events.**

## Known limitations

- No real observations; storm cells are synthetic Gaussian advecting fields.
- No trained Indian model; c4dl-multi is not deployed.
- MongoDB used instead of PostGIS; geometry is GeoJSON, not spatial-indexed.
- 3–6 h NWP-dominated outlook is out of scope for this MVP (0–180 min only).

## Plan for operational validation with IMD / domain experts

1. Sign data agreements (IMD DWR, MOSDAC/INSAT, IITM/ENTLN lightning, NCMRWF NWP).
2. Build authorized-historical event archive; replay through the same pipeline.
3. Train/fine-tune an Indian fusion model; blocked event-level splits.
4. Independent-event verification vs persistence & optical-flow at every lead time.
5. Expert review of thresholds/alert policy before any `Actual` CAP switch is enabled.

## Attribution

See `THIRD_PARTY_NOTICES.md`. Reference repositories were studied for interface and
workflow ideas; capabilities here are independently implemented for this spec. Basemap:
Esri Dark Gray Canvas. No source's live-data claims, weights, thresholds, or sample
feeds were copied.
