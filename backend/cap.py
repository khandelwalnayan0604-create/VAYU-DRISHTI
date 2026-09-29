"""
CAP 1.2 (Common Alerting Protocol) export.

Safety guard: alerts are emitted with <status>Test</status> by default. Emitting
an <status>Actual</status> CAP message (or dispatching SMS/push/3rd-party) requires
an explicit operational-authorization switch (VD_CAP_STATUS=Actual + VD_OPS_AUTHORIZED=1)
that is intentionally NOT enabled in this demo. This build never dispatches.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

IST = timezone(timedelta(hours=5, minutes=30))

_SEV_TO_CAP = {
    "green": ("Minor", "Likely", "Advisory"),
    "yellow": ("Moderate", "Possible", "Watch"),
    "orange": ("Severe", "Likely", "Prepare"),
    "red": ("Extreme", "Observed", "Take Action"),
}


def cap_status() -> str:
    if os.environ.get("VD_CAP_STATUS") == "Actual" and os.environ.get("VD_OPS_AUTHORIZED") == "1":
        return "Actual"
    return "Test"


def build_cap_xml(alert: dict, domain_name: str, polygon_coords: list) -> str:
    sev, cert, resp = _SEV_TO_CAP.get(alert["severity"], ("Unknown", "Unknown", "Monitor"))
    now = datetime.now(timezone.utc)
    sent = now.astimezone(IST).replace(microsecond=0).isoformat()
    expires = (now + timedelta(minutes=alert.get("lead_time_min", 60) + 60)).astimezone(IST).replace(microsecond=0).isoformat()
    status = cap_status()
    # polygon: CAP wants "lat,lon lat,lon ..." (note lat,lon order)
    poly = " ".join(f"{round(c[1],4)},{round(c[0],4)}" for c in polygon_coords)
    aid = escape(alert["id"])
    headline = escape(f"[{status}] {alert['severity'].upper()} Thunderstorm/Lightning — {domain_name} (T+{alert.get('lead_time_min',0)} min)")
    desc = escape(alert.get("description", ""))
    instruction = escape(alert.get("instruction", ""))
    area = escape(f"{domain_name} pilot domain")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>{aid}</identifier>
  <sender>vayudrishti-nowcast-demo@example.in</sender>
  <sent>{sent}</sent>
  <status>{status}</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <note>SIMULATED demonstration message. Not an official IMD warning.</note>
  <info>
    <language>en-IN</language>
    <category>Met</category>
    <event>Thunderstorm and Lightning Nowcast</event>
    <responseType>{resp}</responseType>
    <urgency>Expected</urgency>
    <severity>{sev}</severity>
    <certainty>{cert}</certainty>
    <senderName>VayuDrishti Nowcast (SIMULATED)</senderName>
    <headline>{headline}</headline>
    <description>{desc}</description>
    <instruction>{instruction}</instruction>
    <parameter>
      <valueName>model_version</valueName>
      <value>{escape(alert.get('model_version',''))}</value>
    </parameter>
    <parameter>
      <valueName>data_state</valueName>
      <value>simulated</value>
    </parameter>
    <parameter>
      <valueName>probability</valueName>
      <value>{alert.get('probability','')}</value>
    </parameter>
    <area>
      <areaDesc>{area}</areaDesc>
      <polygon>{poly}</polygon>
    </area>
  </info>
</alert>"""
