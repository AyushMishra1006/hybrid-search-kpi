import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import KPIPage from './pages/KPIPage'
import EvalPage from './pages/EvalPage'
import DebugPage from './pages/DebugPage'

const NAV_STYLE = {
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  padding: '0 24px',
  height: 52,
  background: '#1e293b',
  borderBottom: '1px solid #334155',
}

const LINK_STYLE = {
  padding: '6px 14px',
  borderRadius: 6,
  fontSize: 14,
  fontWeight: 500,
  color: '#94a3b8',
  transition: 'all 0.15s',
}

const ACTIVE_STYLE = {
  ...LINK_STYLE,
  background: '#2563eb',
  color: '#fff',
}

const BRAND = {
  marginRight: 'auto',
  fontWeight: 700,
  fontSize: 15,
  color: '#f1f5f9',
  letterSpacing: '-0.3px',
}

export default function App() {
  return (
    <BrowserRouter>
      <nav style={NAV_STYLE}>
        <span style={BRAND}>Hybrid Search KPI</span>
        {[['/', 'Search'], ['/kpi', 'KPI'], ['/eval', 'Eval'], ['/debug', 'Debug']].map(([to, label]) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => isActive ? ACTIVE_STYLE : LINK_STYLE}
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/kpi" element={<KPIPage />} />
        <Route path="/eval" element={<EvalPage />} />
        <Route path="/debug" element={<DebugPage />} />
      </Routes>
    </BrowserRouter>
  )
}
