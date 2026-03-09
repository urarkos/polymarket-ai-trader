import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { ConfidenceBadge, StatusBadge } from '../components/Badge'
import { ChevronDown, ChevronRight, RefreshCw, Filter } from 'lucide-react'

const STATUS_FILTERS = ['all', 'pending', 'executed', 'failed', 'skipped']

export default function Opportunities() {
  const [opps, setOpps] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [expanded, setExpanded] = useState(null)

  async function load() {
    setLoading(true)
    try {
      const data = await api.getOpportunities(filter === 'all' ? '' : filter)
      setOpps(data.opportunities || [])
    } finally {
      setLoading(false)
    }
  }

  async function scan() {
    setScanning(true)
    try {
      await api.triggerScan()
      await load()
    } finally {
      setScanning(false)
    }
  }

  async function placeBet(id) {
    try {
      await api.placeBet(id)
      await load()
    } catch (e) {
      alert(`Failed: ${e.message}`)
    }
  }

  useEffect(() => { load() }, [filter])

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-white">Opportunities</h1>
        <div className="flex items-center gap-3">
          {/* Filter */}
          <div className="flex bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                  filter === s
                    ? 'bg-green-500 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
          <button
            onClick={scan}
            disabled={scanning}
            className="flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scanning...' : 'Scan'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading...</div>
      ) : opps.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-500">
            <p>No opportunities found.</p>
            <p className="text-xs mt-2">Try running a scan.</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {opps.map((opp) => (
            <Card key={opp.id} className="p-0 overflow-hidden">
              {/* Summary row */}
              <button
                onClick={() => setExpanded(expanded === opp.id ? null : opp.id)}
                className="w-full text-left p-4 hover:bg-gray-800/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-gray-500">
                    {expanded === opp.id ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-medium">{opp.question}</p>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                        opp.outcome === 'YES'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>{opp.outcome}</span>
                      <ConfidenceBadge level={opp.confidence} />
                      <StatusBadge status={opp.status} />
                      <span className="text-xs text-gray-400">
                        Edge <span className="text-green-400 font-semibold">{(opp.edge * 100).toFixed(1)}%</span>
                      </span>
                      <span className="text-xs text-gray-400">
                        Kelly <span className="text-white font-semibold">${opp.kelly_bet_usdc}</span>
                      </span>
                    </div>
                  </div>
                  <ProbabilityBar
                    market={opp.current_price}
                    consensus={opp.consensus_probability}
                    outcome={opp.outcome}
                  />
                </div>
              </button>

              {/* Expanded detail */}
              {expanded === opp.id && (
                <div className="border-t border-gray-800 p-4 space-y-4">
                  {/* Probabilities */}
                  <div className="grid grid-cols-3 gap-4">
                    <ProbBox label="Market Price" value={opp.current_price} color="text-gray-300" />
                    <ProbBox label="Claude" value={opp.claude_probability} color="text-blue-400" />
                    <ProbBox label="Gemini" value={opp.gemini_probability} color="text-purple-400" />
                  </div>

                  {/* Reasoning */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-blue-400 mb-2">Claude Analysis</p>
                      <p className="text-xs text-gray-300 leading-relaxed">{opp.claude_reasoning || 'No reasoning provided'}</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-purple-400 mb-2">Gemini Analysis</p>
                      <p className="text-xs text-gray-300 leading-relaxed">{opp.gemini_reasoning || 'No reasoning provided'}</p>
                    </div>
                  </div>

                  {/* Action */}
                  {opp.status === 'pending' && (
                    <div className="flex justify-end">
                      <button
                        onClick={() => placeBet(opp.id)}
                        className="bg-green-500 hover:bg-green-600 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
                      >
                        Place Bet ${opp.kelly_bet_usdc}
                      </button>
                    </div>
                  )}

                  <p className="text-xs text-gray-600">
                    Found: {new Date(opp.created_at).toLocaleString()} ·
                    Expires: {opp.expires_at ? new Date(opp.expires_at).toLocaleString() : '—'}
                  </p>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function ProbBox({ label, value, color }) {
  return (
    <div className="text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-xl font-bold mt-1 ${color}`}>
        {value != null ? `${(value * 100).toFixed(0)}%` : '—'}
      </p>
    </div>
  )
}

function ProbabilityBar({ market, consensus, outcome }) {
  const marketPct = (market * 100).toFixed(0)
  const consensusPct = consensus != null ? (consensus * 100).toFixed(0) : null

  return (
    <div className="flex-shrink-0 text-right">
      <p className="text-xs text-gray-500">Market / AI</p>
      <p className="text-sm font-bold text-white">
        {marketPct}% / <span className="text-green-400">{consensusPct ?? '—'}%</span>
      </p>
    </div>
  )
}
