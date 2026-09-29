# Third-Party Notices — VayuDrishti Nowcast

This project was informed by the following reference repositories named in the SIH26072
brief. They were studied for **interface, workflow, and validation-plan ideas only**.
All capabilities in this build are **independently implemented** against the problem
specification. No code, model weights, live-data claims, warning thresholds, accuracy
figures, or sample/simulated datasets were copied from any of them. Before any code
reuse in a production system, re-check each repository's current license and retain the
notices/attribution it requires.

| Repository | Link | Referenced for (concept only) |
|---|---|---|
| MeteoSwiss/c4dl-multi | https://github.com/MeteoSwiss/c4dl-multi | Fusion-model interface / verification concept. **Swiss weights NOT deployed.** |
| STORMTRACE | https://github.com/targaryenv2/STORMTRACE | Temporal alignment, mosaicking, tracking, uncertainty concepts |
| SIH-Nowcasting | https://github.com/Avenger2007/SIH-Nowcasting- | Connector design, provenance, CAPE/CIN display concepts |
| VajraNow | https://github.com/harshacsit/vajranow | Observe→fuse→predict→explain→alert workflow, optical-flow baseline |
| Thunderguard.AI | https://github.com/HimanshuRaj88/Thunderguard.AI | GeoJSON risk zones, operator/public views |
| Risora Thunderstorm Nowcasting | https://github.com/yamankashyap2912/risora-thunderstorm-nowcasting | FastAPI+React/Leaflet map/timeline, CAP, cross-section |
| NEXUS-NOWCAST | https://github.com/ganes-git/NEXUS-NOWCAST | Ingestion/CAP/GeoJSON utility concepts |
| ThunderWatch AI | https://github.com/nachiket-mr360/ThunderWatch_AI | RF baseline concept |
| thunderstorm-nowcasting | https://github.com/rutvik06-lux/thunderstorm-nowcasting | Limitations & independent-event validation approach |
| vidyutNet | https://github.com/AkashVK04/vidyutNet | Stakeholder dashboards, regional-language alerts |

## Runtime / library attributions
- Leaflet (BSD-2-Clause), React, FastAPI, Recharts, lucide-react, Tailwind CSS.
- Basemap tiles: Esri "World Dark Gray Canvas" (© Esri and its data providers).
- CAP 1.2: OASIS Common Alerting Protocol v1.2 schema structure.
- Lightning-safety wording paraphrases public NDMA / IMD guidance (30-30 rule).
