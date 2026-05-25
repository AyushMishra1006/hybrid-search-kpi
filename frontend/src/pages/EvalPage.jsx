import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend,
} from 'recharts'
import { getExperiments } from '../api'

const NORM_COLOR = { minmax: '#2563eb', zscore: '#f59e0b' }

const S = {
  page: { maxWidth: 1050, margin: '0 auto', padding: '2rem 1rem' },
  heading: { fontSize: 24, fontWeight: 700, marginBottom: 6, color: '#0f172a' },
  subheading: { fontSize: 13, color: '#64748b', marginBottom: 24 },
  panel: {
    background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 10, padding: '18px 22px', marginBottom: 20,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  panelTitle: { fontSize: 15, fontWeight: 600, marginBottom: 16, color: '#0f172a' },
  filterRow: { display: 'flex', gap: 12, alignItems: 'center', marginBottom: 18 },
  filterLabel: { fontSize: 13, color: '#475569' },
  select: {
    padding: '5px 10px', border: '1px solid #cbd5e1', borderRadius: 6,
    fontSize: 13, background: '#fff', color: '#0f172a',
  },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    textAlign: 'left', padding: '8px 10px',
    borderBottom: '2px solid #e2e8f0', color: '#64748b',
    fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.04em',
  },
  thRight: {
    textAlign: 'right', padding: '8px 10px',
    borderBottom: '2px solid #e2e8f0', color: '#64748b',
    fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.04em',
  },
  td: { padding: '9px 10px', borderBottom: '1px solid #f1f5f9', color: '#374151' },
  tdRight: { padding: '9px 10px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', color: '#374151', fontWeight: 600 },
  tdMono: { padding: '9px 10px', borderBottom: '1px solid #f1f5f9', color: '#374151', fontFamily: 'monospace', fontSize: 12 },
  badge: {
    display: 'inline-block', padding: '2px 8px', borderRadius: 4,
    fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  statCards: { display: 'flex', gap: 14, marginBottom: 20, flexWrap: 'wrap' },
  statCard: {
    flex: '1 1 160px', background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 10, padding: '14px 18px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  statLabel: { fontSize: 11, color: '#64748b', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 },
  statValue: { fontSize: 28, fontWeight: 700, color: '#0f172a' },
  empty: { color: '#94a3b8', padding: '2rem 0', textAlign: 'center', fontSize: 13 },
  error: { padding: '2rem', color: '#dc2626' },
  loading: { padding: '2rem', color: '#64748b' },
}

function NormBadge({ norm }) {
  const color = norm === 'minmax' ? '#dbeafe' : '#fef3c7'
  const text  = norm === 'minmax' ? '#1e40af' : '#92400e'
  return (
    <span style={{ ...S.badge, background: color, color: text }}>
      {norm}
    </span>
  )
}

function StatCard({ label, value }) {
  return (
    <div style={S.statCard}>
      <div style={S.statLabel}>{label}</div>
      <div style={S.statValue}>{value}</div>
    </div>
  )
}

function buildChartData(experiments) {
  return experiments.map(exp => ({
    label: `α=${exp.alpha} ${exp.normalization === 'minmax' ? 'mm' : 'zs'}`,
    alpha: parseFloat(exp.alpha),
    normalization: exp.normalization,
    'nDCG@10':   parseFloat(exp['nDCG@10']).toFixed(4),
    'Recall@10': parseFloat(exp['Recall@10']).toFixed(4),
    'MRR@10':    parseFloat(exp['MRR@10']).toFixed(4),
  }))
}

function bestExp(experiments) {
  return experiments.reduce(
    (best, e) => parseFloat(e['nDCG@10']) > parseFloat(best['nDCG@10']) ? e : best,
    experiments[0],
  )
}

export default function EvalPage() {
  const [experiments, setExperiments] = useState(null)
  const [error, setError]             = useState(null)
  const [normFilter, setNormFilter]   = useState('all')

  useEffect(() => {
    getExperiments()
      .then(setExperiments)
      .catch(e => setError(e.message))
  }, [])

  if (error)        return <div style={S.error}>Error loading experiments: {error}</div>
  if (!experiments) return <div style={S.loading}>Loading…</div>

  const filtered   = normFilter === 'all' ? experiments : experiments.filter(e => e.normalization === normFilter)
  const chartData  = buildChartData(filtered)
  const best       = experiments.length > 0 ? bestExp(experiments) : null
  const avgNDCG    = experiments.length > 0
    ? (experiments.reduce((s, e) => s + parseFloat(e['nDCG@10']), 0) / experiments.length).toFixed(4)
    : '—'

  return (
    <div style={S.page}>
      <h1 style={S.heading}>Evaluation Results</h1>
      <p style={S.subheading}>
        {experiments.length} experiments · hybrid search on 400 arXiv CS abstracts · model: BAAI/bge-small-en-v1.5
      </p>

      <div style={S.statCards}>
        <StatCard label="Experiments run" value={experiments.length} />
        <StatCard label="Best nDCG@10"    value={best ? parseFloat(best['nDCG@10']).toFixed(4) : '—'} />
        <StatCard label="Best alpha"      value={best ? `α=${best.alpha}` : '—'} />
        <StatCard label="Avg nDCG@10"     value={avgNDCG} />
      </div>

      <div style={S.panel}>
        <div style={S.panelTitle}>nDCG@10 Trend by Experiment</div>

        <div style={S.filterRow}>
          <span style={S.filterLabel}>Filter:</span>
          <select style={S.select} value={normFilter} onChange={e => setNormFilter(e.target.value)}>
            <option value="all">All normalizations</option>
            <option value="minmax">Min-Max only</option>
            <option value="zscore">Z-Score only</option>
          </select>
        </div>

        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData} margin={{ top: 4, right: 20, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis
                domain={[0.7, 1.0]}
                tickFormatter={v => v.toFixed(2)}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
              />
              <Tooltip
                formatter={(v, name) => [parseFloat(v).toFixed(4), name]}
                contentStyle={{ fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="nDCG@10"   stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="Recall@10" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} strokeDasharray="5 3" />
              <Line type="monotone" dataKey="MRR@10"    stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} strokeDasharray="2 2" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={S.empty}>No experiments match the selected filter.</div>
        )}
      </div>

      <div style={S.panel}>
        <div style={S.panelTitle}>All Experiments</div>

        {experiments.length > 0 ? (
          <table style={S.table}>
            <thead>
              <tr>
                <th style={S.th}>Timestamp</th>
                <th style={S.th}>Alpha</th>
                <th style={S.th}>Normalization</th>
                <th style={S.th}>Model</th>
                <th style={S.thRight}>nDCG@10</th>
                <th style={S.thRight}>Recall@10</th>
                <th style={S.thRight}>MRR@10</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((exp, i) => {
                const isBest = best && parseFloat(exp['nDCG@10']) === parseFloat(best['nDCG@10'])
                return (
                  <tr key={i} style={isBest ? { background: '#f0f9ff' } : {}}>
                    <td style={S.tdMono}>{exp.timestamp ? exp.timestamp.slice(0, 19).replace('T', ' ') : '—'}</td>
                    <td style={S.td}>{exp.alpha}</td>
                    <td style={S.td}><NormBadge norm={exp.normalization} /></td>
                    <td style={{ ...S.tdMono, fontSize: 11 }}>{exp.model}</td>
                    <td style={{ ...S.tdRight, color: isBest ? '#16a34a' : '#374151' }}>
                      {parseFloat(exp['nDCG@10']).toFixed(4)}
                      {isBest && <span style={{ marginLeft: 6, fontSize: 10, color: '#16a34a', fontWeight: 700 }}>★ best</span>}
                    </td>
                    <td style={S.tdRight}>{parseFloat(exp['Recall@10']).toFixed(4)}</td>
                    <td style={S.tdRight}>{parseFloat(exp['MRR@10']).toFixed(4)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        ) : (
          <div style={S.empty}>No experiments found. Run eval harness to populate.</div>
        )}
      </div>
    </div>
  )
}
