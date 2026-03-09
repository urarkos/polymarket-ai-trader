import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, History, Settings, Zap } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Opportunities from './pages/Opportunities'
import BetHistory from './pages/BetHistory'
import SettingsPage from './pages/SettingsPage'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/opportunities', icon: TrendingUp, label: 'Opportunities' },
  { to: '/history', icon: History, label: 'Bet History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col flex-shrink-0">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Zap className="text-green-400 w-6 h-6" />
            <span className="font-bold text-white text-lg">PolyAI</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">AI-powered trading</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-green-500/10 text-green-400 font-medium'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-600">Polymarket AI Trader v1.0</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/opportunities" element={<Opportunities />} />
          <Route path="/history" element={<BetHistory />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
