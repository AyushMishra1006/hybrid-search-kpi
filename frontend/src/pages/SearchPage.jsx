import { useState } from 'react'
import { search } from '../api'

const S = {
  page: { maxWidth: 820, margin: '0 auto', padding: '2rem 1rem' },
  heading: { fontSize: 24, fontWeight: 700, marginBottom: 20, color: '#0f172a' },
  form: { marginBottom: 20 },
  inputRow: { display: 'flex', gap: 8, marginBottom: 12 },
  input: {
    flex: 1, padding: '10px 14px', fontSize: 15,
    border: '1px solid #cbd5e1', borderRadius: 8,
    outline: 'none', background: '#fff',
  },
  btn: {
    padding: '10px 22px', background: '#2563eb', color: '#fff',
    border: 'none', borderRadius: 8, cursor: 'pointer',
    fontSize: 15, fontWeight: 600,
  },
  controls: { display: 'flex', gap: 28, alignItems: 'center', flexWrap: 'wrap' },
  label: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#475569' },
  badge: { fontWeight: 700, color: '#1e40af', minWidth: 28 },
  topkInput: {
    width: 60, padding: '4px 8px', border: '1px solid #cbd5e1',
    borderRadius: 6, fontSize: 13, textAlign: 'center',
  },
  meta: { fontSize: 13, color: '#64748b', marginBottom: 16 },
  error: { color: '#dc2626', marginBottom: 16, fontSize: 14 },
  card: {
    background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 10, padding: '16px 18px', marginBottom: 12,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  docId: { fontSize: 11, color: '#94a3b8', marginBottom: 2 },
  title: { fontWeight: 600, fontSize: 15, marginBottom: 6, color: '#0f172a' },
  snippet: { fontSize: 13, color: '#475569', lineHeight: 1.6, marginBottom: 12 },
  scores: { display: 'flex', gap: 10 },
  scoreWrap: { flex: 1 },
  scoreLabel: { fontSize: 11, color: '#64748b', marginBottom: 3 },
  scoreTrack: { height: 6, background: '#f1f5f9', borderRadius: 3, overflow: 'hidden' },
  emptyState: {
    textAlign: 'center', padding: '4rem 2rem', color: '#94a3b8', fontSize: 15,
  },
}

const SCORE_COLORS = { bm25: '#3b82f6', vector: '#10b981', hybrid: '#8b5cf6' }

function ScoreBar({ label, value, color }) {
  const pct = Math.min(Math.max(value * 100, 0), 100).toFixed(0)
  return (
    <div style={S.scoreWrap}>
      <div style={S.scoreLabel}>{label} {pct}%</div>
      <div style={S.scoreTrack}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.3s' }} />
      </div>
    </div>
  )
}

export default function SearchPage() {
  const [query, setQuery]     = useState('')
  const [alpha, setAlpha]     = useState(0.5)
  const [topK, setTopK]       = useState(10)
  const [results, setResults] = useState(null)
  const [meta, setMeta]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await search(query.trim(), topK, alpha, {})
      setResults(data.results)
      setMeta({ latency_ms: data.latency_ms, result_count: data.result_count })
    } catch (err) {
      setError(err.message)
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={S.page}>
      <h1 style={S.heading}>Search</h1>

      <form style={S.form} onSubmit={handleSubmit}>
        <div style={S.inputRow}>
          <input
            style={S.input}
            type="text"
            placeholder="Search Wikipedia articles..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <button style={S.btn} type="submit" disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        <div style={S.controls}>
          <label style={S.label}>
            Alpha (BM25 weight)&nbsp;<span style={S.badge}>{alpha.toFixed(1)}</span>
            <input
              type="range" min="0" max="1" step="0.1" value={alpha}
              onChange={e => setAlpha(parseFloat(e.target.value))}
            />
            <span style={{ fontSize: 11, color: '#94a3b8' }}>0=semantic&nbsp;&nbsp;1=keyword</span>
          </label>
          <label style={S.label}>
            Top-K
            <input
              style={S.topkInput}
              type="number" min="1" max="50" value={topK}
              onChange={e => setTopK(Math.min(50, Math.max(1, parseInt(e.target.value) || 10)))}
            />
          </label>
        </div>
      </form>

      {error && <div style={S.error}>Error: {error}</div>}
      {meta && (
        <div style={S.meta}>
          {meta.result_count} result{meta.result_count !== 1 ? 's' : ''} &middot; {meta.latency_ms.toFixed(1)} ms
        </div>
      )}

      {results && results.length === 0 && (
        <div style={S.emptyState}>No results found. Try a different query or lower alpha.</div>
      )}

      {results && results.map(r => (
        <div key={r.doc_id} style={S.card}>
          <div style={S.docId}>{r.doc_id}</div>
          <div style={S.title}>{r.title}</div>
          <div style={S.snippet} dangerouslySetInnerHTML={{ __html: r.snippet }} />
          <div style={S.scores}>
            <ScoreBar label="BM25"   value={r.bm25_score}   color={SCORE_COLORS.bm25} />
            <ScoreBar label="Vector" value={r.vector_score} color={SCORE_COLORS.vector} />
            <ScoreBar label="Hybrid" value={r.hybrid_score} color={SCORE_COLORS.hybrid} />
          </div>
        </div>
      ))}

      {!results && !loading && (
        <div style={S.emptyState}>Enter a query above to search 400 Wikipedia articles.</div>
      )}
    </div>
  )
}
