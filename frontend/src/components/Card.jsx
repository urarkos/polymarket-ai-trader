import { clsx } from 'clsx'
import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'

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
  const [visible, setVisible] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0 })
  const ref = useRef(null)

  function show() {
    if (!ref.current) return
    const r = ref.current.getBoundingClientRect()
    setPos({ top: r.top + window.scrollY - 8, left: r.left + r.width / 2 })
    setVisible(true)
  }

  return (
    <span ref={ref} className="inline-flex" onMouseEnter={show} onMouseLeave={() => setVisible(false)}>
      {children}
      {visible && createPortal(
        <span
          style={{ top: pos.top, left: pos.left, transform: 'translate(-50%, -100%)' }}
          className="fixed z-[9999] px-2.5 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 pointer-events-none shadow-lg whitespace-nowrap normal-case tracking-normal font-normal"
        >
          {text}
          <span className="absolute left-1/2 -translate-x-1/2 top-full border-4 border-transparent border-t-gray-700" />
        </span>,
        document.body
      )}
    </span>
  )
}
