import { useState } from 'react'
import { search } from '../api'

// ── Constants ──────────────────────────────────────────────────────────────
const CATEGORIES = [
  { value: '',      label: 'All Categories' },
  { value: 'cs.LG', label: 'cs.LG · Machine Learning' },
  { value: 'cs.CL', label: 'cs.CL · NLP' },
  { value: 'cs.CV', label: 'cs.CV · Computer Vision' },
  { value: 'cs.AI', label: 'cs.AI · Artificial Intelligence' },
  { value: 'cs.IR', label: 'cs.IR · Information Retrieval' },
]

const CAT_COLORS = {
  'cs.LG': { bg: '#dbeafe', text: '#1e40af' },
  'cs.CL': { bg: '#ede9fe', text: '#5b21b6' },
  'cs.CV': { bg: '#d1fae5', text: '#065f46' },
  'cs.AI': { bg: '#fef3c7', text: '#92400e' },
  'cs.IR': { bg: '#fee2e2', text: '#991b1b' },
}

const CAT_SHORT = {
  'cs.LG': 'ML', 'cs.CL': 'NLP', 'cs.CV': 'Vision',
  'cs.AI': 'AI', 'cs.IR': 'IR',
}

// ── Styles ─────────────────────────────────────────────────────────────────
const S = {
  // Hero
  hero: {
    background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)',
    padding: '48px 24px 36px',
    textAlign: 'center',
  },
  heroTitle: {
    fontSize: 36, fontWeight: 800, color: '#f8fafc',
    letterSpacing: '-0.5px', marginBottom: 6,
  },
  heroSub: {
    fontSize: 14, color: '#94a3b8', marginBottom: 28,
    letterSpacing: '0.02em',
  },
  searchRow: {
    display: 'flex', gap: 10, maxWidth: 700,
    margin: '0 auto', alignItems: 'center',
  },
  searchInput: {
    flex: 1, padding: '14px 20px', fontSize: 16,
    border: 'none', borderRadius: 10, outline: 'none',
    background: '#fff', color: '#0f172a',
    boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
    fontFamily: 'inherit',
  },
  searchBtn: {
    padding: '14px 28px', background: '#2563eb', color: '#fff',
    border: 'none', borderRadius: 10, cursor: 'pointer',
    fontSize: 15, fontWeight: 700, whiteSpace: 'nowrap',
    boxShadow: '0 4px 12px rgba(37,99,235,0.4)',
    transition: 'background 0.15s',
  },

  // Controls below hero
  controls: {
    background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
    padding: '14px 24px',
    display: 'flex', gap: 32, alignItems: 'center',
    flexWrap: 'wrap', justifyContent: 'center',
  },
  controlLabel: {
    display: 'flex', alignItems: 'center', gap: 10,
    fontSize: 13, color: '#475569', fontWeight: 500,
  },
  alphaValue: {
    fontWeight: 700, color: '#2563eb',
    minWidth: 28, display: 'inline-block', textAlign: 'center',
  },
  alphaHint: { fontSize: 11, color: '#94a3b8' },
  topkInput: {
    width: 64, padding: '5px 8px', border: '1px solid #cbd5e1',
    borderRadius: 6, fontSize: 13, textAlign: 'center',
    fontFamily: 'inherit',
  },

  // Category pills
  pillRow: {
    display: 'flex', gap: 8, padding: '14px 24px',
    overflowX: 'auto', background: '#fff',
    borderBottom: '1px solid #f1f5f9',
    justifyContent: 'center', flexWrap: 'wrap',
  },
  pill: (active) => ({
    padding: '6px 16px', borderRadius: 20, fontSize: 13,
    fontWeight: 500, cursor: 'pointer', border: 'none',
    transition: 'all 0.15s', whiteSpace: 'nowrap',
    background: active ? '#2563eb' : '#f1f5f9',
    color: active ? '#fff' : '#475569',
  }),

  // Body
  body: { maxWidth: 860, margin: '0 auto', padding: '20px 16px 60px' },
  meta: {
    fontSize: 13, color: '#64748b', marginBottom: 16,
    display: 'flex', alignItems: 'center', gap: 12,
  },
  metaDot: { color: '#cbd5e1' },
  error: {
    background: '#fef2f2', border: '1px solid #fecaca',
    borderRadius: 8, padding: '12px 16px',
    color: '#dc2626', fontSize: 14, marginBottom: 16,
  },

  // Result card
  card: {
    background: '#fff', border: '1px solid #e2e8f0',
    borderRadius: 12, padding: '20px 22px', marginBottom: 14,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
    transition: 'box-shadow 0.15s',
  },
  cardTop: {
    display: 'flex', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 6,
  },
  catBadge: (cat) => ({
    display: 'inline-block', padding: '2px 10px', borderRadius: 20,
    fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
    background: CAT_COLORS[cat]?.bg ?? '#f1f5f9',
    color: CAT_COLORS[cat]?.text ?? '#475569',
  }),
  docId: { fontSize: 11, color: '#cbd5e1', fontFamily: 'monospace' },
  titleLink: {
    display: 'block', fontSize: 17, fontWeight: 700,
    color: '#1d4ed8', marginBottom: 8, lineHeight: 1.4,
    textDecoration: 'none', cursor: 'pointer',
  },
  snippet: {
    fontSize: 13, color: '#4b5563', lineHeight: 1.7,
    marginBottom: 14,
  },

  // Scores
  scores: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 },
  scoreBlock: {},
  scoreHeader: {
    display: 'flex', justifyContent: 'space-between',
    marginBottom: 4,
  },
  scoreLabel: { fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' },
  scoreVal: { fontSize: 11, fontWeight: 700, color: '#374151' },
  track: { height: 5, background: '#f1f5f9', borderRadius: 3, overflow: 'hidden' },
  fill: (pct, color) => ({
    height: '100%', width: `${pct}%`,
    background: color, borderRadius: 3,
    transition: 'width 0.4s ease',
  }),

  // Empty
  empty: {
    textAlign: 'center', padding: '60px 20px',
    color: '#94a3b8', fontSize: 15,
  },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  emptyHint: { fontSize: 13, color: '#cbd5e1', marginTop: 6 },
}

const SCORE_COLOR = { bm25: '#3b82f6', vector: '#10b981', hybrid: '#8b5cf6' }

// ── Sub-components ─────────────────────────────────────────────────────────
function ScoreBar({ label, value, color }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div style={S.scoreBlock}>
      <div style={S.scoreHeader}>
        <span style={S.scoreLabel}>{label}</span>
        <span style={S.scoreVal}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div style={S.track}>
        <div style={S.fill(pct, color)} />
      </div>
    </div>
  )
}

function ResultCard({ result }) {
  const cat = result.category ?? ''
  const arXivUrl = `https://arxiv.org/search/?searchtype=all&query=${encodeURIComponent(result.title)}`

  return (
    <div style={S.card}>
      <div style={S.cardTop}>
        <span style={S.catBadge(cat)}>
          {CAT_SHORT[cat] ?? cat ?? 'arXiv'}
        </span>
        <span style={S.docId}>{result.doc_id}</span>
      </div>

      <a
        href={arXivUrl}
        target="_blank"
        rel="noopener noreferrer"
        style={S.titleLink}
      >
        {result.title}
      </a>

      <div
        style={S.snippet}
        dangerouslySetInnerHTML={{ __html: result.snippet }}
      />

      <div style={S.scores}>
        <ScoreBar label="BM25"   value={result.bm25_score}   color={SCORE_COLOR.bm25} />
        <ScoreBar label="Vector" value={result.vector_score} color={SCORE_COLOR.vector} />
        <ScoreBar label="Hybrid" value={result.hybrid_score} color={SCORE_COLOR.hybrid} />
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────
export default function SearchPage() {
  const [query, setQuery]     = useState('')
  const [alpha, setAlpha]     = useState(0.3)
  const [topK, setTopK]       = useState(10)
  const [category, setCategory] = useState('')
  const [results, setResults] = useState(null)
  const [meta, setMeta]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  async function handleSearch(e) {
    e?.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    const filters = category ? { category } : {}
    try {
      const data = await search(query.trim(), topK, alpha, filters)
      setResults(data.results)
      setMeta({ latency_ms: data.latency_ms, result_count: data.result_count })
    } catch (err) {
      setError(err.message)
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div>
      {/* ── Hero ── */}
      <div style={S.hero}>
        <div style={S.heroTitle}>Hybrid Search</div>
        <div style={S.heroSub}>
          400 arXiv CS papers &middot; BM25 + Semantic Retrieval &middot; BGE-small-en-v1.5
        </div>
        <div style={S.searchRow}>
          <input
            style={S.searchInput}
            type="text"
            placeholder="e.g. transformer attention mechanism, federated learning privacy..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            autoFocus
          />
          <button
            style={S.searchBtn}
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </div>

      {/* ── Controls ── */}
      <div style={S.controls}>
        <label style={S.controlLabel}>
          <span>Alpha (BM25 weight)</span>
          <input
            type="range" min="0" max="1" step="0.1"
            value={alpha}
            onChange={e => setAlpha(parseFloat(e.target.value))}
            style={{ width: 120 }}
          />
          <span style={S.alphaValue}>{alpha.toFixed(1)}</span>
          <span style={S.alphaHint}>0 = semantic &nbsp; 1 = keyword</span>
        </label>

        <label style={S.controlLabel}>
          <span>Top-K</span>
          <input
            style={S.topkInput}
            type="number" min="1" max="50" value={topK}
            onChange={e => setTopK(Math.min(50, Math.max(1, parseInt(e.target.value) || 10)))}
          />
        </label>
      </div>

      {/* ── Category Pills ── */}
      <div style={S.pillRow}>
        {CATEGORIES.map(c => (
          <button
            key={c.value}
            style={S.pill(category === c.value)}
            onClick={() => setCategory(c.value)}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* ── Results ── */}
      <div style={S.body}>
        {error && <div style={S.error}>Error: {error}</div>}

        {meta && (
          <div style={S.meta}>
            <span><strong>{meta.result_count}</strong> result{meta.result_count !== 1 ? 's' : ''}</span>
            <span style={S.metaDot}>·</span>
            <span>{meta.latency_ms.toFixed(1)} ms</span>
            {category && (
              <>
                <span style={S.metaDot}>·</span>
                <span>filtered to <strong>{category}</strong></span>
              </>
            )}
          </div>
        )}

        {results && results.length === 0 && (
          <div style={S.empty}>
            <div style={S.emptyIcon}>🔍</div>
            <div>No results found.</div>
            <div style={S.emptyHint}>
              Try a different query, lower alpha, or remove the category filter.
            </div>
          </div>
        )}

        {results && results.map(r => <ResultCard key={r.doc_id} result={r} />)}

        {!results && !loading && (
          <div style={S.empty}>
            <div style={S.emptyIcon}>⚡</div>
            <div>Search 400 arXiv CS papers</div>
            <div style={S.emptyHint}>
              Hybrid BM25 + semantic search · Click any result title to open on arXiv
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
