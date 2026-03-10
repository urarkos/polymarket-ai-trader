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

import { Tooltip } from './Card'

export function OutcomeBadge({ outcome }) {
  const tip = outcome === 'YES'
    ? 'AI рекомендует ставить на ДА — его оценка вероятности выше рыночной цены'
    : 'AI рекомендует ставить на НЕТ — его оценка вероятности ниже рыночной цены'
  return (
    <Tooltip text={tip}>
      <span className={`text-xs font-bold px-2 py-0.5 rounded cursor-help ${
        outcome === 'YES' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
      }`}>
        {outcome === 'YES' ? 'ДА' : 'НЕТ'}
      </span>
    </Tooltip>
  )
}

export function ConfidenceBadge({ level }) {
  const colorMap = { HIGH: 'green', MEDIUM: 'yellow', LOW: 'red' }
  const labelMap = { HIGH: 'Высокая', MEDIUM: 'Средняя', LOW: 'Низкая' }
  const tipMap = {
    HIGH:   'Высокая уверенность — оба AI согласны, оценки близки. Ставка рассчитывается в полном размере',
    MEDIUM: 'Средняя уверенность — AI немного расходятся. Размер ставки уменьшается на 40%',
    LOW:    'Низкая уверенность — AI сильно расходятся во мнениях. Размер ставки уменьшается на 70%',
  }
  return (
    <Tooltip text={tipMap[level] || level}>
      <Badge variant={colorMap[level] || 'default'}>{labelMap[level] || level}</Badge>
    </Tooltip>
  )
}

export function StatusBadge({ status }) {
  const colorMap = {
    pending:  'yellow',
    executed: 'green',
    failed:   'red',
    skipped:  'default',
    placed:   'blue',
    won:      'green',
    lost:     'red',
  }
  const labelMap = {
    pending:  'Ожидание',
    executed: 'Исполнено',
    failed:   'Ошибка',
    skipped:  'Пропущено',
    placed:   'Размещено',
    won:      'Выиграно',
    lost:     'Проиграно',
  }
  const tipMap = {
    pending:  'Сигнал найден, ставка ещё не размещена — можно поставить вручную',
    executed: 'Ставка успешно размещена на Polymarket',
    failed:   'Ошибка при размещении ставки',
    skipped:  'Сигнал пропущен — перевес оказался недостаточным',
    placed:   'Ставка отправлена в блокчейн, ожидает подтверждения',
    won:      'Рынок закрылся в вашу пользу — ставка выиграна',
    lost:     'Рынок закрылся не в вашу пользу — ставка проиграна',
  }
  return (
    <Tooltip text={tipMap[status] || status}>
      <Badge variant={colorMap[status] || 'default'}>{labelMap[status] || status}</Badge>
    </Tooltip>
  )
}
