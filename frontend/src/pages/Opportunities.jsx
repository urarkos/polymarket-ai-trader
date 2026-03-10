import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { ConfidenceBadge, StatusBadge, OutcomeBadge } from '../components/Badge'
import { Tooltip } from '../components/Card'
import { ChevronDown, ChevronRight, RefreshCw, Square } from 'lucide-react'

const STATUS_FILTERS = ['all', 'pending', 'executed', 'failed', 'skipped']
const STATUS_LABELS = {
  all: 'Все',
  pending: 'Ожидание',
  executed: 'Исполнено',
  failed: 'Ошибка',
  skipped: 'Пропущено',
}

export default function Opportunities() {
  const [opps, setOpps] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(null)
  const [stopping, setStopping] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const pollRef = useRef(null)

  async function load() {
    setLoading(true)
    try {
      const data = await api.getOpportunities(filter === 'all' ? '' : filter)
      setOpps(data.opportunities || [])
    } finally {
      setLoading(false)
    }
  }

  function startPolling() {
    if (pollRef.current) return
    pollRef.current = setInterval(async () => {
      try {
        const state = await api.getScanStatus()
        setScanProgress({ processed: state.processed, total: state.total })
        if (!state.running) {
          stopPolling()
          setScanning(false)
          setStopping(false)
          setScanProgress(null)
          await load()
        }
      } catch {
        stopPolling()
        setScanning(false)
        setStopping(false)
        setScanProgress(null)
      }
    }, 1500)
  }

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  async function scan() {
    setScanning(true)
    setScanProgress(null)
    try {
      await api.triggerScan()
      startPolling()
    } catch (e) {
      setScanning(false)
      alert(`Не удалось запустить сканирование: ${e.message}`)
    }
  }

  async function stopScan() {
    setStopping(true)
    try {
      await api.stopScan()
    } catch (e) {
      setStopping(false)
      alert(`Не удалось остановить: ${e.message}`)
    }
  }

  useEffect(() => {
    // Sync with any scan already running on mount
    api.getScanStatus().then((state) => {
      if (state.running) {
        setScanning(true)
        setScanProgress({ processed: state.processed, total: state.total })
        startPolling()
      }
    }).catch(() => {})
    return () => stopPolling()
  }, [])

  async function placeBet(id) {
    try {
      await api.placeBet(id)
      await load()
    } catch (e) {
      alert(`Ошибка: ${e.message}`)
    }
  }

  useEffect(() => { load() }, [filter])

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-white">Сигналы</h1>
        <div className="flex items-center gap-3">
          {/* Filter */}
          <div className="flex bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  filter === s
                    ? 'bg-green-500 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
          {scanning ? (
            <div className="flex items-center gap-2">
              {scanProgress && scanProgress.total > 0 && (
                <span className="text-xs text-gray-400">
                  {scanProgress.processed}/{scanProgress.total}
                </span>
              )}
              <button
                onClick={stopScan}
                disabled={stopping}
                className="flex items-center gap-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg"
              >
                <Square className="w-4 h-4" />
                {stopping ? 'Остановка...' : 'Стоп'}
              </button>
            </div>
          ) : (
            <button
              onClick={scan}
              className="flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              <RefreshCw className="w-4 h-4" />
              Сканировать
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Загрузка...</div>
      ) : opps.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-gray-500">
            <p>Сигналы не найдены.</p>
            <p className="text-xs mt-2">Запустите сканирование.</p>
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
                      <OutcomeBadge outcome={opp.outcome} />
                      <ConfidenceBadge level={opp.confidence} />
                      <StatusBadge status={opp.status} />
                      <Tooltip text="Разница между оценкой AI и ценой рынка — потенциальная прибыльность">
                        <span className="text-xs text-gray-400 cursor-help">
                          Перевес <span className="text-green-400 font-semibold">{(opp.edge * 100).toFixed(1)}%</span>
                        </span>
                      </Tooltip>
                      <Tooltip text="Рекомендуемый размер ставки по критерию Келли с учётом банкролла и уверенности AI">
                        <span className="text-xs text-gray-400 cursor-help">
                          Ставка Kelly <span className="text-white font-semibold">${opp.kelly_bet_usdc}</span>
                        </span>
                      </Tooltip>
                    </div>
                  </div>
                  <Tooltip text="Текущая цена рынка / консенсус-оценка AI">
                    <ProbabilityBar
                      market={opp.current_price}
                      consensus={opp.consensus_probability}
                      outcome={opp.outcome}
                    />
                  </Tooltip>
                </div>
              </button>

              {/* Expanded detail */}
              {expanded === opp.id && (
                <div className="border-t border-gray-800 p-4 space-y-4">
                  {/* Probabilities */}
                  <div className="grid grid-cols-3 gap-4">
                    <ProbBox label="Цена рынка" value={opp.current_price} color="text-gray-300" />
                    <ProbBox label="Claude" value={opp.claude_probability} color="text-blue-400" />
                    <ProbBox label="Gemini" value={opp.gemini_probability} color="text-purple-400" />
                  </div>

                  {/* Reasoning */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-blue-400 mb-2">Анализ Claude</p>
                      <p className="text-xs text-gray-300 leading-relaxed">{opp.claude_reasoning || 'Аргументация отсутствует'}</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-purple-400 mb-2">Анализ Gemini</p>
                      <p className="text-xs text-gray-300 leading-relaxed">{opp.gemini_reasoning || 'Аргументация отсутствует'}</p>
                    </div>
                  </div>

                  {/* Action */}
                  {opp.status === 'pending' && (
                    <div className="flex justify-end">
                      <button
                        onClick={() => placeBet(opp.id)}
                        className="bg-green-500 hover:bg-green-600 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
                      >
                        Поставить ${opp.kelly_bet_usdc}
                      </button>
                    </div>
                  )}

                  <p className="text-xs text-gray-600">
                    Найдено: {new Date(opp.created_at).toLocaleString('ru-RU')} ·
                    Истекает: {opp.expires_at ? new Date(opp.expires_at).toLocaleString('ru-RU') : '—'}
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
      <p className="text-xs text-gray-500">Рынок / AI</p>
      <p className="text-sm font-bold text-white">
        {marketPct}% / <span className="text-green-400">{consensusPct ?? '—'}%</span>
      </p>
    </div>
  )
}
