import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getKPI } from '../api'

const S = {
  page: { maxWidth: 1000, margin: '0 auto', padding: '2rem 1rem' },
  heading: { fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#0f172a' },
  cardRow: { display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' },
  latencyCard: {
    flex: '1 1 160px', background: '#fff',
    border: '1px solid #e2e8f0', borderRadius: 10,
    padding: '18px 22px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  cardLabel: { fontSize: 12, color: '#64748b', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 },
  cardValue: { fontSize: 30, fontWeight: 700, color: '#0f172a' },
  cardUnit: { fontSize: 14, fontWeight: 400, color: '#94a3b8', marginLeft: 4 },
  panel: {
    background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 10, padding: '18px 22px', marginBottom: 20,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  panelTitle: { fontSize: 15, fontWeight: 600, marginBottom: 16, color: '#0f172a' },
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '6px 10px', borderBottom: '1px solid #f1f5f9', color: '#64748b', fontWeight: 600, fontSize: 12 },
  td: { padding: '7px 10px', borderBottom: '1px solid #f8fafc', color: '#374151' },
  tdRight: { padding: '7px 10px', borderBottom: '1px solid #f8fafc', textAlign: 'right', color: '#64748b' },
  empty: { color: '#94a3b8', padding: '1.5rem 0', textAlign: 'center', fontSize: 13 },
  error: { padding: '2rem', color: '#dc2626' },
  loading: { padding: '2rem', color: '#64748b' },
}

function LatencyCard({ label, value }) {
  return (
    <div style={S.latencyCard}>
      <div style={S.cardLabel}>{label}</div>
      <div style={S.cardValue}>
        {value != null ? value.toFixed(1) : '—'}
        <span style={S.cardUnit}>ms</span>
      </div>
    </div>
  )
}

function QueryTable({ title, items, emptyMsg }) {
  return (
    <div style={S.panel}>
      <div style={S.panelTitle}>{title}</div>
      {items && items.length > 0 ? (
        <table style={S.table}>
          <thead>
            <tr>
              <th style={S.th}>Query</th>
              <th style={{ ...S.th, textAlign: 'right' }}>Count</th>
            </tr>
          </thead>
          <tbody>
            {items.map((q, i) => (
              <tr key={i}>
                <td style={S.td}>{q.query}</td>
                <td style={S.tdRight}>{q.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div style={S.empty}>{emptyMsg}</div>
      )}
    </div>
  )
}

function formatTick(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

export default function KPIPage() {
  const [data, setData]   = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getKPI()
      .then(setData)
      .catch(e => setError(e.message))
  }, [])

  if (error) return <div style={S.error}>Error loading KPI: {error}</div>
  if (!data)  return <div style={S.loading}>Loading…</div>

  const volume = data.request_volume ?? []

  return (
    <div style={S.page}>
      <h1 style={S.heading}>KPI Dashboard</h1>

      <div style={S.cardRow}>
        <LatencyCard label="p50 Latency" value={data.latency_p50_ms} />
        <LatencyCard label="p95 Latency" value={data.latency_p95_ms} />
      </div>

      <div style={S.panel}>
        <div style={S.panelTitle}>Request Volume</div>
        {volume.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={volume} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="timestamp" tickFormatter={formatTick} tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} allowDecimals={false} />
              <Tooltip
                formatter={(v) => [v, 'Requests']}
                labelFormatter={(l) => new Date(l).toLocaleString()}
                contentStyle={{ fontSize: 12 }}
              />
              <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={S.empty}>No request data yet — run some searches first.</div>
        )}
      </div>

      <div style={S.grid2}>
        <QueryTable
          title="Top Queries"
          items={data.top_queries}
          emptyMsg="No queries logged yet."
        />
        <QueryTable
          title="Zero-Result Queries"
          items={data.zero_result_queries}
          emptyMsg="No zero-result queries."
        />
      </div>
    </div>
  )
}
