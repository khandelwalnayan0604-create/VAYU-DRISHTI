export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export async function getJSON(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export async function postJSON(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export function capUrl(alertId, domain) {
  return `${API}/alerts/${alertId}/cap.xml?domain=${domain}`;
}
