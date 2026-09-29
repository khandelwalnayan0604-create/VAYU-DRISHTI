# VayuDrishti Nowcast — Real Data Integration (GFS live) + Honest Multi-Source State

Bring genuine real-world data into the app starting with free NOAA GFS weather-model fields,
while keeping every other source truthfully labelled and ready to switch on once authorized.

## Who it's for
- The project owner who wants the app to show at least one real, verifiable data feed today.
- SIH reviewers who need to see a credible path from demo to authorized Indian operational data.

## What changes and what stays
- **NWP becomes REAL:** the CAPE / shear / instability layer and the operator NWP panel are fed by
  actual NOAA GFS forecast data over each Indian domain, refreshed from the latest model cycle.
- **Everything else stays clearly SIMULATED:** radar reflectivity, INSAT satellite, lightning and the
  storm-cell forecast remain synthetic and keep their `simulated` labels. Nothing synthetic is ever
  presented as real or as operational IMD guidance.
- **Truthful mixed state:** each source shows its own real state — the NWP source reads `live` or
  `delayed` (based on how old the model cycle is), with real source time, retrieval time, latency and
  a NOAA attribution; the others continue to read `simulated`. The global disclosure banner reflects
  the mix ("NWP: live NOAA GFS; radar/satellite/lightning: simulated").

## Core features (Phase 1, built now)
- **Live GFS connector** for all nine domains: fetches the latest available CAPE/CIN/shear/wind for the
  domain's map extent, aligns it to the domain grid, and drives the NWP CAPE/shear map layer and the
  operator source-health card with real numbers, real timestamps and correct freshness/latency.
- **Honest fallback:** if GFS is temporarily unreachable or the cycle is stale, the app falls back to
  the synthetic NWP field **and relabels that source `simulated`/`delayed`** — never a silent swap.
- **"Ready but disabled" real connectors** for IMD Doppler radar, INSAT-3D (MOSDAC) and lightning
  (ILDN/IITM): implemented with proper credential/config gates and licensing/attribution notes, shown
  in the source-health panel as `disabled — awaiting authorized credentials`. They activate later via
  configuration once the owner supplies access, with no further code changes.
- **Docs refresh:** an honest data-availability table (what is real vs simulated vs pending), plus a
  short "how to enable each authorized source" section with each provider's access route, license and
  required attribution.

## User flow
1. Open the app → the **NWP CAPE/shear layer now shows real GFS values**; its badge reads `live`/`delayed`
   with a real timestamp and NOAA attribution.
2. Operator source-health panel shows: NWP = real (NOAA GFS), radar/satellite/lightning = simulated,
   and the authorized connectors = disabled/awaiting credentials.
3. Radar, satellite, lightning, storm tracks and the forecast continue to work exactly as today,
   clearly marked simulated.
4. Later, when the owner has credentials, they flip a setting to turn a pending connector real —
   its badge and data update accordingly.

## UI/UX feel
- No layout redesign. Same dark mission-control dashboard.
- The difference is trust: at least one panel/layer now carries a real `live` badge and real timestamps,
  and the disclosure text distinguishes the real source from the simulated ones.

## Implementation phases
- **Phase 1 (now):** Live NOAA GFS NWP connector across all domains, honest per-source state labels and
  fallback, "ready but disabled" authorized connectors, and the docs/availability table. Outcome: the
  app shows genuine real weather-model data today, with everything else truthfully labelled.
- **Phase 2 (later):** Turn on authorized Indian sources as the owner obtains access — INSAT-3D via a
  MOSDAC login, lightning via ILDN, and IMD Doppler radar under IMD attribution — plus scheduled refresh
  and caching so real feeds stay current without slowing the UI.
- **Phase 3 (later):** Indian model training. A documented, reproducible pipeline (quality control →
  1 km gridding → normalized dBZ sequences → U-Net/ConvLSTM → CSI/POD/FAR scoring with event-level
  blocked splits) that the owner runs externally on authorized historical data and a GPU. The app's
  model adapter is swapped to the trained Indian model only after independent-event validation; until
  then it keeps the clearly-labelled baseline/simulated forecast.

## Assumptions
- **GFS is the only real feed wired now**, chosen because it is free and needs no key; it is fetched
  from NOAA's public distribution and refreshed to the newest cycle available.
- Real GFS values are labelled `live` when the cycle is fresh and `delayed` when older; if fetching
  fails, the field falls back to synthetic and is relabelled — accuracy of the state label is mandatory.
- **No provider credentials are available yet**, so IMD radar, MOSDAC INSAT and lightning are built as
  authorized-ready connectors that stay disabled until the owner provides access; enabling them is a
  configuration step, not a rebuild.
- **Model training is not performed in this build** (no GPU, no licensed Indian radar archive here);
  it is delivered as documentation/pipeline design in Phase 3, run by the owner later. The live app
  keeps its labelled baseline output meanwhile.
- Radar, satellite, lightning and the storm-cell forecast **remain SIMULATED** and clearly labelled.
- Nothing real is ever presented as operational IMD guidance; provider attributions (e.g. "Data Source:
  NOAA GFS") are shown where required.
- Adding a real network fetch may introduce minor latency; it is bounded by requesting only the needed
  variables/region and by the synthetic fallback, so the UI stays responsive.
- The free-deployment setup from the previous plan still applies; the live GFS connector runs the same
  way on the free backend host.
