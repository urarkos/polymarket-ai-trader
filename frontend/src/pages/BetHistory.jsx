import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, StatCard } from '../components/Card'
import { StatusBadge } from '../components/Badge'
import { ExternalLink } from 'lucide-react'

export default function BetHistory() {
  const [bets, setBets] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const [b, s] = await Promise.all([api.getBets(), api.getStats()])
      setBets(b.bets || [])
      setStats(s)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-white">История ставок</h1>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Всего ставок"
            value={stats.total_bets}
            sub={`${stats.won} выиграно / ${stats.lost} проиграно`}
            tooltip="Общее количество размещённых ставок"
          />
          <StatCard
            label="P&L"
            value={`$${stats.total_pnl_usdc >= 0 ? '+' : ''}${stats.total_pnl_usdc}`}
            color={stats.total_pnl_usdc >= 0 ? 'text-green-400' : 'text-red-400'}
            tooltip="Суммарная прибыль или убыток в USDC по всем завершённым ставкам"
          />
          <StatCard
            label="Винрейт"
            value={`${stats.win_rate}%`}
            color="text-blue-400"
            tooltip="Доля выигранных ставок от всех завершённых (выиграно + проиграно)"
          />
          <StatCard
            label="ROI"
            value={`${stats.roi_pct}%`}
            color={stats.roi_pct >= 0 ? 'text-green-400' : 'text-red-400'}
            tooltip="Доходность на вложенный капитал: P&L ÷ суммарно поставлено × 100%"
          />
        </div>
      )}

      {/* Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wide">
                <th className="text-left p-4">Рынок</th>
                <th className="text-left p-4">Исход</th>
                <th className="text-right p-4">Сумма</th>
                <th className="text-right p-4">Цена входа</th>
                <th className="text-right p-4">P&L</th>
                <th className="text-left p-4">Статус</th>
                <th className="text-right p-4">Дата</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} className="text-center py-12 text-gray-500">Загрузка...</td></tr>
              ) : bets.length === 0 ? (
                <tr><td colSpan={8} className="text-center py-12 text-gray-500">Ставок пока нет</td></tr>
              ) : bets.map((bet) => (
                <tr key={bet.id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                  <td className="p-4 max-w-xs">
                    <p className="text-white truncate">{bet.question}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{bet.market_id?.slice(0, 12)}...</p>
                  </td>
                  <td className="p-4">
                    <span className={`font-semibold ${bet.outcome === 'YES' ? 'text-green-400' : 'text-red-400'}`}>
                      {bet.outcome === 'YES' ? 'ДА' : 'НЕТ'}
                    </span>
                  </td>
                  <td className="p-4 text-right text-white">${bet.amount_usdc}</td>
                  <td className="p-4 text-right text-gray-400">{(bet.price_at_bet * 100).toFixed(1)}¢</td>
                  <td className="p-4 text-right">
                    {bet.pnl_usdc != null ? (
                      <span className={bet.pnl_usdc >= 0 ? 'text-green-400' : 'text-red-400'}>
                        ${bet.pnl_usdc >= 0 ? '+' : ''}{bet.pnl_usdc.toFixed(2)}
                      </span>
                    ) : <span className="text-gray-600">—</span>}
                  </td>
                  <td className="p-4"><StatusBadge status={bet.status} /></td>
                  <td className="p-4 text-right text-xs text-gray-500">
                    {new Date(bet.placed_at).toLocaleDateString('ru-RU')}
                  </td>
                  <td className="p-4">
                    {bet.tx_hash && (
                      <a
                        href={`https://polygonscan.com/tx/${bet.tx_hash}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-gray-500 hover:text-white"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
