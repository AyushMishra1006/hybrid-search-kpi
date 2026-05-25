import { useEffect, useState, useCallback } from 'react'
import { getLogs } from '../api'

const SEVERITY_COLOR = {
  info:    { bg: '#dbeafe', text: '#1e40af' },
  warning: { bg: '#fef3c7', text: '#92400e' },
  error:   { bg: '#fee2e2', text: '#991b1b' },
}

const S = {
  page: { maxWidth: 1100, margin: '0 auto', padding: '2rem 1rem' },
  heading: { fontSize: 24, fontWeight: 700, marginBottom: 6, color: '#0f172a' },
  subheading: { fontSize: 13, color: '#64748b', marginBottom: 20 },
  controlBar: {
    display: 'flex', gap: 12, alignItems: 'flex-end',
    flexWrap: 'wrap', marginBottom: 18,
    background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 10, padding: '14px 18px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  fieldWrap: { display: 'flex', flexDirection: 'column', gap: 4 },
  fieldLabel: { fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' },
  select: {
    padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: 6,
    fontSize: 13, background: '#fff', color: '#0f172a', minWidth: 130,
  },
  dateInput: {
    padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: 6,
    fontSize: 13, background: '#fff', color: '#0f172a',
  },
  refreshBtn: {
    padding: '7px 18px', background: '#2563eb', color: '#fff',
    border: 'none', borderRadius: 6, cursor: 'pointer',
    fontSize: 13, fontWeight: 600, alignSelf: 'flex-end',
  },
  clearBtn: {
    padding: '7px 14px', background: '#f1f5f9', color: '#475569',
    border: '1px solid #e2e8f0', borderRadius: 6, cursor: 'pointer',
    fontSize: 13, fontWeight: 500, alignSelf: 'flex-end',
  },
  statRow: { display: 'flex', gap: 14, marginBottom: 18, flexWrap: 'wrap' },
  statChip: {
    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
    padding: '6px 14px', fontSize: 13, color: '#374151',
  },
  statNum: { fontWeight: 700, color: '#0f172a' },
  panel: {
    background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.05)', overflow: 'hidden',
  },
  tableWrap: { overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 12 },
  th: {
    textAlign: 'left', padding: '9px 12px',
    borderBottom: '2px solid #e2e8f0', color: '#64748b',
    fontWeight: 600, fontSize: 11, textTransform: 'uppercase',
    letterSpacing: '0.04em', whiteSpace: 'nowrap', background: '#f8fafc',
  },
  thRight: {
    textAlign: 'right', padding: '9px 12px',
    borderBottom: '2px solid #e2e8f0', color: '#64748b',
    fontWeight: 600, fontSize: 11, textTransform: 'uppercase',
    letterSpacing: '0.04em', whiteSpace: 'nowrap', background: '#f8fafc',
  },
  td: { padding: '8px 12px', borderBottom: '1px solid #f1f5f9', color: '#374151', whiteSpace: 'nowrap' },
  tdQuery: { padding: '8px 12px', borderBottom: '1px solid #f1f5f9', color: '#374151', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  tdRight: { padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', color: '#374151', fontFamily: 'monospace' },
  tdMono: { padding: '8px 12px', borderBottom: '1px solid #f1f5f9', color: '#64748b', fontFamily: 'monospace', fontSize: 11, whiteSpace: 'nowrap' },
  tdError: { padding: '8px 12px', borderBottom: '1px solid #f1f5f9', color: '#dc2626', fontSize: 11, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  badge: {
    display: 'inline-block', padding: '2px 7px', borderRadius: 4,
    fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em',
  },
  empty: { color: '#94a3b8', padding: '3rem 0', textAlign: 'center', fontSize: 13 },
  error: { padding: '2rem', color: '#dc2626' },
  loading: { padding: '2rem', color: '#64748b' },
}

function SeverityBadge({ severity }) {
  const c = SEVERITY_COLOR[severity] ?? { bg: '#f1f5f9', text: '#475569' }
  return <span style={{ ...S.badge, background: c.bg, color: c.text }}>{severity}</span>
}

function fmtTs(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString([], {
      month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  } catch {
    return ts
  }
}

export default function DebugPage() {
  const [logs, setLogs]         = useState(null)
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)
  const [severity, setSeverity] = useState('')
  const [since, setSince]       = useState('')
  const [until, setUntil]       = useState('')

  const fetchLogs = useCallback(() => {
    setLoading(true)
    setError(null)
    getLogs(severity, since ? new Date(since).toISOString() : '', until ? new Date(until).toISOString() : '')
      .then(rows => { setLogs(rows); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [severity, since, until])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  function clearFilters() {
    setSeverity('')
    setSince('')
    setUntil('')
  }

  const errCount  = logs ? logs.filter(r => r.severity === 'error').length   : 0
  const warnCount = logs ? logs.filter(r => r.severity === 'warning').length : 0
  const avgLat    = logs && logs.length > 0
    ? (logs.reduce((s, r) => s + (r.latency_ms ?? 0), 0) / logs.length).toFixed(1)
    : null

  return (
    <div style={S.page}>
      <h1 style={S.heading}>Debug Logs</h1>
      <p style={S.subheading}>Query execution log · SQLite · last 500 entries</p>

      <div style={S.controlBar}>
        <div style={S.fieldWrap}>
          <span style={S.fieldLabel}>Severity</span>
          <select style={S.select} value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="">All severities</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div style={S.fieldWrap}>
          <span style={S.fieldLabel}>Since</span>
          <input
            style={S.dateInput}
            type="datetime-local"
            value={since}
            onChange={e => setSince(e.target.value)}
          />
        </div>

        <div style={S.fieldWrap}>
          <span style={S.fieldLabel}>Until</span>
          <input
            style={S.dateInput}
            type="datetime-local"
            value={until}
            onChange={e => setUntil(e.target.value)}
          />
        </div>

        <button style={S.refreshBtn} onClick={fetchLogs} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
        <button style={S.clearBtn} onClick={clearFilters}>
          Clear filters
        </button>
      </div>

      {logs && (
        <div style={S.statRow}>
          <div style={S.statChip}>
            Total: <span style={S.statNum}>{logs.length}</span>
          </div>
          <div style={S.statChip}>
            Errors: <span style={{ ...S.statNum, color: errCount > 0 ? '#dc2626' : '#0f172a' }}>{errCount}</span>
          </div>
          <div style={S.statChip}>
            Warnings: <span style={{ ...S.statNum, color: warnCount > 0 ? '#d97706' : '#0f172a' }}>{warnCount}</span>
          </div>
          {avgLat && (
            <div style={S.statChip}>
              Avg latency: <span style={S.statNum}>{avgLat} ms</span>
            </div>
          )}
        </div>
      )}

      {error && <div style={S.error}>Failed to load logs: {error}</div>}

      <div style={S.panel}>
        <div style={S.tableWrap}>
          {!logs || loading ? (
            <div style={S.loading}>Loading logs…</div>
          ) : logs.length === 0 ? (
            <div style={S.empty}>
              No logs found.{severity ? ` No "${severity}" entries in the selected range.` : ' Run a search to see logs here.'}
            </div>
          ) : (
            <table style={S.table}>
              <thead>
                <tr>
                  <th style={S.th}>Timestamp</th>
                  <th style={S.th}>Query</th>
                  <th style={S.thRight}>Latency</th>
                  <th style={S.thRight}>Alpha</th>
                  <th style={S.thRight}>Top-K</th>
                  <th style={S.thRight}>Results</th>
                  <th style={S.th}>Severity</th>
                  <th style={S.th}>Error</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(row => (
                  <tr key={row.id}>
                    <td style={S.tdMono}>{fmtTs(row.timestamp)}</td>
                    <td style={S.tdQuery} title={row.query}>{row.query}</td>
                    <td style={S.tdRight}>{row.latency_ms != null ? `${row.latency_ms.toFixed(1)} ms` : '—'}</td>
                    <td style={S.tdRight}>{row.alpha ?? '—'}</td>
                    <td style={S.tdRight}>{row.top_k}</td>
                    <td style={S.tdRight}>{row.result_count}</td>
                    <td style={S.td}><SeverityBadge severity={row.severity} /></td>
                    <td style={S.tdError} title={row.error ?? ''}>{row.error ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
