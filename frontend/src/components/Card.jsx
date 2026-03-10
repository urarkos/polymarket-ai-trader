import { clsx } from 'clsx'

export function Card({ children, className }) {
  return (
    <div className={clsx('bg-gray-900 border border-gray-800 rounded-xl p-5', className)}>
      {children}
    </div>
  )
}

export function StatCard({ label, value, sub, color = 'text-white', tooltip }) {
  return (
    <Card>
      <p className="text-xs text-gray-500 uppercase tracking-wide">
        {tooltip ? (
          <Tooltip text={tooltip}><span className="cursor-help border-b border-dashed border-gray-600">{label}</span></Tooltip>
        ) : label}
      </p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </Card>
  )
}

export function Tooltip({ children, text }) {
  return (
    <span className="relative group inline-flex">
      {children}
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap shadow-lg normal-case tracking-normal font-normal">
        {text}
      </span>
    </span>
  )
}
