import { useEffect, useState } from 'react'
import { api } from '../api'
import { StatCard, Card } from '../components/Card'
import { ConfidenceBadge, OutcomeBadge } from '../components/Badge'
import { RefreshCw, TrendingUp, Target } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [opportunities, setOpportunities] = useState([])
  const [health, setHealth] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [error, setError] = useState(null)

  async function load() {
    try {
      const [s, o, h] = await Promise.all([
        api.getStats(),
        api.getOpportunities('pending', 5),
        api.health(),
      ])
      setStats(s)
      setOpportunities(o.opportunities || [])
      setHealth(h)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }

  async function pollScanStatus() {
    try {
      const state = await api.getScanStatus()
      setScanning(state.running)
    } catch (_) {}
  }

  async function handleScan() {
    try {
      await api.triggerScan()
      setScanning(true)
      setError(null)
    } catch (e) {
      if (e.message.includes('409')) {
        setScanning(true)
        setError(null)
      } else {
        setError(e.message)
      }
    }
  }

  async function handleStop() {
    setStopping(true)
    try {
      await api.stopScan()
      setScanning(false)
    } catch (e) {
      // 400 means scan already finished — treat as success
      if (!e.message.includes('400')) setError(e.message)
      setScanning(false)
    } finally {
      setStopping(false)
    }
  }

  useEffect(() => {
    load()
    pollScanStatus()
    const dataInterval = setInterval(load, 30000)
    const scanInterval = setInterval(pollScanStatus, 3000)
    return () => {
      clearInterval(dataInterval)
      clearInterval(scanInterval)
    }
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Дашборд</h1>
          <p className="text-gray-500 text-sm mt-1">
            Авто-ставка:{' '}
            <span className={health?.auto_bet_enabled ? 'text-green-400' : 'text-yellow-400'}>
              {health?.auto_bet_enabled ? 'ВКЛ' : 'ВЫКЛ'}
            </span>
            {' · '}Сканирование каждые {health?.scan_interval_minutes || '—'} мин
          </p>
        </div>
        <div className="flex items-center gap-2">
          {scanning && (
            <button
              onClick={handleStop}
              disabled={stopping}
              className="flex items-center gap-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {stopping ? 'Остановка...' : 'Стоп'}
            </button>
          )}
          <button
            onClick={handleScan}
            disabled={scanning}
            className={`flex items-center gap-2 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors ${
              scanning
                ? 'bg-green-700 opacity-70 cursor-not-allowed'
                : 'bg-green-500 hover:bg-green-600'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Сканирование...' : 'Сканировать'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Всего ставок"
          value={stats?.total_bets ?? '—'}
          sub={`${stats?.won ?? 0} выиграно / ${stats?.lost ?? 0} проиграно`}
          tooltip="Общее количество размещённых ставок за всё время"
        />
        <StatCard
          label="P&L"
          value={stats ? `$${stats.total_pnl_usdc >= 0 ? '+' : ''}${stats.total_pnl_usdc}` : '—'}
          color={stats?.total_pnl_usdc >= 0 ? 'text-green-400' : 'text-red-400'}
          sub={`ROI: ${stats?.roi_pct ?? 0}%`}
          tooltip="Прибыль/убыток в USDC. ROI — доходность относительно суммарно вложенного"
        />
        <StatCard
          label="Винрейт"
          value={stats ? `${stats.win_rate}%` : '—'}
          color="text-blue-400"
          sub={`${stats?.pending ?? 0} в ожидании`}
          tooltip="Доля выигранных ставок от завершённых"
        />
        <StatCard
          label="В игре"
          value={stats ? `$${stats.total_staked_usdc}` : '—'}
          color="text-purple-400"
          tooltip="Суммарный объём USDC, поставленный за всё время"
        />
      </div>

      {/* Latest opportunities */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-green-400" />
          <h2 className="font-semibold text-white">Последние сигналы</h2>
        </div>

        {opportunities.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Target className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>Сигналов пока нет.</p>
            <p className="text-xs mt-1">Нажмите «Сканировать» для поиска выгодных ставок.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {opportunities.map((opp) => (
              <OpportunityRow key={opp.id} opp={opp} onBet={load} />
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

function OpportunityRow({ opp, onBet }) {
  const [placing, setPlacing] = useState(false)

  async function handleBet() {
    setPlacing(true)
    try {
      await api.placeBet(opp.id)
      onBet()
    } catch (e) {
      alert(`Ошибка ставки: ${e.message}`)
    } finally {
      setPlacing(false)
    }
  }

  return (
    <div className="bg-gray-800/50 rounded-lg p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white font-medium truncate">{opp.question}</p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <OutcomeBadge outcome={opp.outcome} />
            <span className="text-xs text-gray-400">
              Перевес: <span className="text-green-400 font-semibold">{(opp.edge * 100).toFixed(1)}%</span>
            </span>
            <span className="text-xs text-gray-400">
              Ставка: <span className="text-white font-semibold">${opp.kelly_bet_usdc}</span>
            </span>
            <ConfidenceBadge level={opp.confidence} />
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-400">
            <span>Claude: <span className="text-blue-400">{opp.claude_probability ? (opp.claude_probability * 100).toFixed(0) + '%' : '—'}</span></span>
            <span>Gemini: <span className="text-purple-400">{opp.gemini_probability ? (opp.gemini_probability * 100).toFixed(0) + '%' : '—'}</span></span>
          </div>
        </div>
        <button
          onClick={handleBet}
          disabled={placing}
          className="flex-shrink-0 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
        >
          {placing ? '...' : 'Ставка'}
        </button>
      </div>
    </div>
  )
}
