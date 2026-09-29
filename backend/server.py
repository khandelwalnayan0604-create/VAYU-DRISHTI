from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

import nowcast as ng
import connectors as conn
from cap import build_cap_xml, cap_status

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="VayuDrishti Nowcast API", version="0.3.0")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vayudrishti")

DISCLAIMER = (
    "SIMULATED / REPLAY DEMO data. Not derived from IMD DWR, INSAT/MOSDAC, "
    "IITM/ENTLN lightning or NWP. Not operational guidance. c4dl-multi (Swiss) "
    "is a research baseline only and is NOT deployed for India."
)


def _domain_or_404(domain: str):
    if domain not in ng.DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    return ng.DOMAINS[domain]


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------
@api_router.get("/")
async def root():
    return {
        "service": "VayuDrishti Nowcast",
        "challenge": "SIH 2026 / SIH26072",
        "version": "0.3.0",
        "data_state": "simulated",
        "disclaimer": DISCLAIMER,
    }


@api_router.get("/health")
async def health(domain: Optional[str] = None):
    domains = [domain] if domain else list(ng.DOMAINS.keys())
    src = {}
    for d in domains:
        if d in ng.DOMAINS:
            statuses = conn.connector_status(d)
            src[d] = {
                "ok": sum(1 for s in statuses if s["status"] == "ok"),
                "total": len(statuses),
                "connectors": statuses,
            }
    return {
        "status": "up",
        "data_state": "simulated",
        "mode": os.environ.get("VD_DATA_MODE", "simulated"),
        "cap_status_default": cap_status(),
        "model_version": ng.MODEL_VERSION,
        "times": ng.now_times(),
        "sources": src,
        "disclaimer": DISCLAIMER,
    }


@api_router.get("/domains")
async def domains():
    return {
        "data_state": "simulated",
        "domains": [
            {
                "id": d["id"], "name": d["name"], "name_hi": d["name_hi"],
                "center": d["center"], "bbox": d["bbox"], "zoom": d["zoom"],
                "radar": d["radar"], "radar_site": d["radar_site"], "districts": d["districts"],
            } for d in ng.DOMAINS.values()
        ],
    }


@api_router.get("/connectors/status")
async def connectors_status(domain: str = Query(...)):
    _domain_or_404(domain)
    return {"domain": domain, "data_state": "simulated", "connectors": conn.connector_status(domain)}


# --------------------------------------------------------------------------
# Nowcast frames (0-180 min @ 15-min)
# --------------------------------------------------------------------------
@api_router.get("/nowcast/frames")
async def nowcast_frames(domain: str = Query(...)):
    d = _domain_or_404(domain)
    times = ng.now_times()
    frames = []
    for t in ng.LEAD_TIMES:
        frames.append({
            "lead_time_min": t,
            "valid_utc": times["issue_utc"],
            "valid_ist": times["issue_ist"],
            "reflectivity": ng.reflectivity_frame(domain, t),
            "satellite": ng.satellite_ir_frame(domain, t),
            "nwp": ng.nwp_frame(domain, t),
            "lightning": ng.lightning_frame(domain, t),
            "motion_vectors": ng.motion_vectors(domain, t),
            "risk_zones": ng.risk_zones(domain, t),
        })
    return {
        "domain": domain,
        "domain_name": d["name"],
        "center": d["center"],
        "bbox": d["bbox"],
        "zoom": d["zoom"],
        "lead_times": ng.LEAD_TIMES,
        "model_version": ng.MODEL_VERSION,
        "data_state": "simulated",
        "issue_times": times,
        "disclaimer": DISCLAIMER,
        "frames": frames,
    }


@api_router.get("/storm-tracks")
async def storm_tracks(domain: str = Query(...)):
    _domain_or_404(domain)
    return {"domain": domain, "data_state": "simulated", "model_version": ng.MODEL_VERSION,
            "tracks": ng.storm_tracks(domain)}


@api_router.get("/cross-section")
async def cross_section(domain: str = Query(...), cell_id: str = Query(...)):
    _domain_or_404(domain)
    return ng.cross_section(domain, cell_id)


@api_router.get("/verification")
async def verification(domain: str = Query(...)):
    _domain_or_404(domain)
    return ng.verification(domain)


# --------------------------------------------------------------------------
# Alerts (derived from risk zones) + CAP export + acknowledge/audit
# --------------------------------------------------------------------------
_SAFETY = {
    "green": {
        "en": "No thunderstorm expected now. Stay aware of updates.",
        "hi": "अभी कोई आंधी-तूफान अपेक्षित नहीं। अपडेट पर नज़र रखें।",
    },
    "yellow": {
        "en": "Thunderstorms possible. Keep an eye on the sky and plan to move indoors.",
        "hi": "आंधी संभव है। आसमान पर नज़र रखें और घर के अंदर जाने की योजना बनाएं।",
    },
    "orange": {
        "en": "Thunderstorm likely soon. Move indoors, unplug appliances, avoid open fields and tall trees.",
        "hi": "जल्द आंधी की संभावना। घर के अंदर जाएँ, उपकरण बंद करें, खुले मैदान और ऊँचे पेड़ों से बचें।",
    },
    "red": {
        "en": "Take action now. Seek sturdy shelter immediately. Follow the 30-30 rule. Stay away from water and metal.",
        "hi": "अभी कार्रवाई करें। तुरंत मज़बूत आश्रय लें। 30-30 नियम अपनाएँ। पानी और धातु से दूर रहें।",
    },
}
_SEV_RANK = {"green": 0, "yellow": 1, "orange": 2, "red": 3}


def _build_alerts(domain: str):
    """Derive de-duplicated alerts (worst severity per cell) from risk zones."""
    d = ng.DOMAINS[domain]
    best = {}
    for t in ng.LEAD_TIMES:
        fc = ng.risk_zones(domain, t)
        for f in fc["features"]:
            p = f["properties"]
            cid = p["cell_id"]
            if cid not in best or _SEV_RANK[p["severity"]] > _SEV_RANK[best[cid]["severity"]]:
                sev = p["severity"]
                aid = f"VD-{domain}-{cid}".replace(" ", "")
                best[cid] = {
                    "id": aid,
                    "domain": domain,
                    "domain_name": d["name"],
                    "cell_id": cid,
                    "severity": sev,
                    "severity_label": p["severity_label"],
                    "severity_label_hi": p["severity_label_hi"],
                    "probability": p["probability"],
                    "confidence": p["confidence"],
                    "lead_time_min": p["lead_time_min"],
                    "hazard": p["hazard"],
                    "model_version": p["model_version"],
                    "data_state": "simulated",
                    "cap_status": cap_status(),
                    "description": f"{p['hazard']} associated with cell {cid} over {d['name']}. "
                                   f"Onset in ~{p['lead_time_min']} min. Probability {int(p['probability']*100)}%.",
                    "instruction": _SAFETY[sev]["en"],
                    "instruction_hi": _SAFETY[sev]["hi"],
                    "polygon": f["geometry"]["coordinates"][0],
                    "issued_ist": p["issued_ist"],
                }
    alerts = sorted(best.values(), key=lambda a: (-_SEV_RANK[a["severity"]], a["lead_time_min"]))
    return alerts


@api_router.get("/alerts")
async def alerts(domain: str = Query(...)):
    _domain_or_404(domain)
    items = _build_alerts(domain)
    acks = {a["alert_id"]: a async for a in db.alert_audit.find({"domain": domain}, {"_id": 0})}
    for a in items:
        a["acknowledged"] = a["id"] in acks
        a["ack_record"] = acks.get(a["id"])
    worst = items[0]["severity"] if items else "green"
    return {
        "domain": domain,
        "data_state": "simulated",
        "cap_status_default": cap_status(),
        "worst_severity": worst,
        "count": len(items),
        "alerts": items,
        "disclaimer": DISCLAIMER,
    }


@api_router.get("/alerts/{alert_id}/cap.xml")
async def alert_cap(alert_id: str, domain: str = Query(...)):
    _domain_or_404(domain)
    items = {a["id"]: a for a in _build_alerts(domain)}
    a = items.get(alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    xml = build_cap_xml(a, a["domain_name"], a["polygon"])
    return Response(content=xml, media_type="application/xml")


class AckBody(BaseModel):
    domain: str
    operator: str = "operator-demo"
    note: str = ""


@api_router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: str, body: AckBody):
    _domain_or_404(body.domain)
    items = {a["id"]: a for a in _build_alerts(body.domain)}
    if alert_id not in items:
        raise HTTPException(status_code=404, detail="Alert not found")
    rec = {
        "id": str(uuid.uuid4()),
        "alert_id": alert_id,
        "domain": body.domain,
        "severity": items[alert_id]["severity"],
        "operator": body.operator,
        "note": body.note,
        "acknowledged_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "cap_status": cap_status(),
        "data_state": "simulated",
    }
    await db.alert_audit.update_one({"alert_id": alert_id, "domain": body.domain},
                                    {"$set": rec}, upsert=True)
    return {"ok": True, "audit": rec}


@api_router.get("/alerts/audit")
async def alert_audit(domain: Optional[str] = None):
    q = {"domain": domain} if domain else {}
    records = await db.alert_audit.find(q, {"_id": 0}).sort("acknowledged_at_utc", -1).to_list(500)
    return {"data_state": "simulated", "count": len(records), "records": records}


@api_router.get("/safety")
async def safety(domain: str = Query(...)):
    _domain_or_404(domain)
    items = _build_alerts(domain)
    worst = items[0] if items else None
    sev = worst["severity"] if worst else "green"
    return {
        "domain": domain,
        "data_state": "simulated",
        "severity": sev,
        "severity_label": worst["severity_label"] if worst else "No Warning",
        "severity_label_hi": worst["severity_label_hi"] if worst else "कोई चेतावनी नहीं",
        "minutes_to_onset": worst["lead_time_min"] if worst else None,
        "advice": {"en": _SAFETY[sev]["en"], "hi": _SAFETY[sev]["hi"]},
        "latest_alert": worst,
        "rules": {
            "en": ["Follow the 30-30 rule: shelter if thunder is within 30s of lightning; wait 30 min after last thunder.",
                   "Avoid open fields, hilltops, tall isolated trees and water bodies.",
                   "Unplug electrical appliances; avoid corded phones and metal objects.",
                   "If outdoors with no shelter, crouch low with feet together; do not lie flat."],
            "hi": ["30-30 नियम अपनाएँ: बिजली के 30 सेकंड के भीतर गड़गड़ाहट हो तो आश्रय लें; अंतिम गड़गड़ाहट के 30 मिनट बाद तक रुकें।",
                   "खुले मैदान, पहाड़ी चोटियों, ऊँचे अकेले पेड़ों और जल निकायों से बचें।",
                   "बिजली के उपकरण बंद करें; तार वाले फ़ोन और धातु की वस्तुओं से बचें।",
                   "यदि बाहर आश्रय न हो, तो पैर जोड़कर नीचे बैठें; ज़मीन पर सपाट न लेटें।"],
        },
        "source": "NDMA / IMD lightning safety guidance (paraphrased, SIMULATED demo)",
    }


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
