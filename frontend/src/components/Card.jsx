import { clsx } from 'clsx'

export function Card({ children, className }) {
  return (
    <div className={clsx('bg-gray-900 border border-gray-800 rounded-xl p-5', className)}>
      {children}
    </div>
  )
}

export function StatCard({ label, value, sub, color = 'text-white' }) {
  return (
    <Card>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </Card>
  )
}
