const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function _json(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export function search(query, topK, alpha, filters = {}) {
  return fetch(`${BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK, alpha, filters }),
  }).then(_json)
}

export function postFeedback(query, docId, relevant) {
  return fetch(`${BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, doc_id: docId, relevant }),
  }).then(res => { if (!res.ok) throw new Error(res.status) })
}

export function getKPI() {
  return fetch(`${BASE}/dashboard/kpi`).then(_json)
}

export function getLogs(severity = '', since = '', until = '') {
  const p = new URLSearchParams()
  if (severity) p.set('severity', severity)
  if (since)    p.set('since', since)
  if (until)    p.set('until', until)
  return fetch(`${BASE}/dashboard/logs?${p}`).then(_json)
}

export function getExperiments() {
  return fetch(`${BASE}/dashboard/experiments`).then(_json)
}
