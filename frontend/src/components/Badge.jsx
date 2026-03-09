export function Badge({ children, variant = 'default' }) {
  const variants = {
    default: 'bg-gray-800 text-gray-300',
    green:   'bg-green-500/15 text-green-400',
    red:     'bg-red-500/15 text-red-400',
    yellow:  'bg-yellow-500/15 text-yellow-400',
    blue:    'bg-blue-500/15 text-blue-400',
    purple:  'bg-purple-500/15 text-purple-400',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${variants[variant]}`}>
      {children}
    </span>
  )
}

export function ConfidenceBadge({ level }) {
  const map = { HIGH: 'green', MEDIUM: 'yellow', LOW: 'red' }
  return <Badge variant={map[level] || 'default'}>{level}</Badge>
}

export function StatusBadge({ status }) {
  const map = {
    pending:  'yellow',
    executed: 'green',
    failed:   'red',
    skipped:  'default',
    placed:   'blue',
    won:      'green',
    lost:     'red',
  }
  return <Badge variant={map[status] || 'default'}>{status}</Badge>
}
