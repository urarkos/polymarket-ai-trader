import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import {
  Shield, AlertTriangle, Save, Key, Eye, EyeOff,
  CheckCircle, XCircle, Loader, FlaskConical
} from 'lucide-react'

export default function SettingsPage() {
  const [settings, setSettings] = useState(null)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const [keys, setKeys] = useState({})
  const [keyForm, setKeyForm] = useState({
    anthropic_api_key: '',
    gemini_api_key: '',
    polymarket_private_key: '',
  })
  const [showKeys, setShowKeys] = useState({})
  const [savingKeys, setSavingKeys] = useState(false)
  const [savedKeys, setSavedKeys] = useState(false)
  // { key_name: { status: 'idle'|'testing'|'ok'|'error', detail: '' } }
  const [testResults, setTestResults] = useState({})

  useEffect(() => {
    api.getSettings().then((s) => { setSettings(s); setForm(s) })
    api.getKeys().then(setKeys)
  }, [])

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function save() {
    setSaving(true)
    try {
      await api.updateSettings(form)
      setSettings(form)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      alert('Ошибка сохранения: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  async function saveKeys() {
    const payload = {}
    for (const [k, v] of Object.entries(keyForm)) {
      if (v.trim()) payload[k] = v.trim()
    }
    if (Object.keys(payload).length === 0) return

    setSavingKeys(true)
    try {
      await api.updateKeys(payload)
      const fresh = await api.getKeys()
      setKeys(fresh)
      setKeyForm({ anthropic_api_key: '', gemini_api_key: '', polymarket_private_key: '' })
      setSavedKeys(true)
      setTimeout(() => setSavedKeys(false), 2500)
    } catch (e) {
      alert('Ошибка сохранения ключей: ' + e.message)
    } finally {
      setSavingKeys(false)
    }
  }

  async function testKey(name) {
    setTestResults(r => ({ ...r, [name]: { status: 'testing', detail: '' } }))
    try {
      const res = await api.testKey(name)
      setTestResults(r => ({
        ...r,
        [name]: { status: res.ok ? 'ok' : 'error', detail: res.ok ? res.detail : res.error },
      }))
    } catch (e) {
      setTestResults(r => ({ ...r, [name]: { status: 'error', detail: e.message } }))
    }
  }

  if (!settings) return <div className="p-6 text-gray-500">Загрузка настроек...</div>

  const KEY_FIELDS = [
    { name: 'anthropic_api_key', label: 'Anthropic API Key (Claude)', placeholder: 'sk-ant-...' },
    { name: 'gemini_api_key', label: 'Gemini API Key', placeholder: 'AIza...' },
    { name: 'polymarket_private_key', label: 'Polymarket — приватный ключ', placeholder: '0x...' },
  ]

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-white">Настройки</h1>

      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex gap-3">
        <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-yellow-200">
          <p className="font-semibold">Предупреждение о рисках</p>
          <p className="mt-1 text-yellow-300/80">
            Автоматические ставки несут финансовые риски. Начинайте с малых сумм
            и тестируйте без реальных средств, прежде чем включать авто-ставку.
          </p>
        </div>
      </div>

      {/* API Keys */}
      <Card className="space-y-5">
        <div className="flex items-center gap-2">
          <Key className="w-5 h-5 text-blue-400" />
          <h2 className="font-semibold text-white">API Ключи</h2>
        </div>
        <p className="text-xs text-gray-500 -mt-2">
          Ключи хранятся в базе данных. Оставьте поле пустым, чтобы сохранить текущее значение.
        </p>

        {KEY_FIELDS.map(({ name, label, placeholder }) => (
          <KeyField
            key={name}
            label={label}
            placeholder={placeholder}
            current={keys[name]}
            value={keyForm[name]}
            show={showKeys[name]}
            testResult={testResults[name]}
            onToggleShow={() => setShowKeys(s => ({ ...s, [name]: !s[name] }))}
            onChange={(v) => setKeyForm(f => ({ ...f, [name]: v }))}
            onTest={() => testKey(name)}
          />
        ))}

        <div className="flex items-center justify-between pt-1">
          <div className="text-xs">
            {savedKeys && (
              <span className="flex items-center gap-1 text-green-400">
                <CheckCircle className="w-3.5 h-3.5" /> Ключи сохранены
              </span>
            )}
          </div>
          <button
            onClick={saveKeys}
            disabled={savingKeys || !Object.values(keyForm).some(v => v.trim())}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
          >
            <Save className="w-4 h-4" />
            {savingKeys ? 'Сохранение...' : 'Сохранить ключи'}
          </button>
        </div>
      </Card>

      {/* Auto-bet toggle */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Shield className={"w-5 h-5 " + (form.auto_bet_enabled ? 'text-green-400' : 'text-gray-500')} />
              <h2 className="font-semibold text-white">Авто-ставка</h2>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              При включении бот автоматически размещает ставки без вашего подтверждения.
            </p>
          </div>
          <button
            onClick={() => set('auto_bet_enabled', !form.auto_bet_enabled)}
            className={"relative w-12 h-6 rounded-full transition-colors " + (form.auto_bet_enabled ? 'bg-green-500' : 'bg-gray-700')}
          >
            <span className={"absolute top-1 w-4 h-4 bg-white rounded-full transition-all " + (form.auto_bet_enabled ? 'left-7' : 'left-1')} />
          </button>
        </div>
      </Card>

      {/* Trading parameters */}
      <Card className="space-y-5">
        <h2 className="font-semibold text-white">Параметры торговли</h2>
        <NumberField label="Банкролл (USDC)" help="Общий капитал, используемый для расчёта ставок по критерию Келли"
          value={form.bankroll_usdc} onChange={(v) => set('bankroll_usdc', v)} min={10} max={100000} step={10} />
        <NumberField label="Макс. ставка за сделку (USDC)" help="Жёсткий лимит на одну ставку вне зависимости от расчёта Келли"
          value={form.max_bet_usdc} onChange={(v) => set('max_bet_usdc', v)} min={1} max={10000} step={1} />
        <NumberField label="Минимальный перевес (%)" help="Рынки с меньшим перевесом AI пропускаются. Повышайте, чтобы торговать только на высоких перевесах"
          value={form.min_edge * 100} onChange={(v) => set('min_edge', v / 100)} min={1} max={50} step={0.5} suffix="%" />
        <NumberField label="Доля Келли (%)" help="Какую долю от полного размера Келли использовать. 25% — стандартный консервативный подход"
          value={form.kelly_fraction * 100} onChange={(v) => set('kelly_fraction', v / 100)} min={5} max={100} step={5} suffix="%" />
        <NumberField label="Интервал сканирования (мин)" help="Как часто автоматически сканировать рынки в поисках сигналов"
          value={form.scan_interval_minutes} onChange={(v) => set('scan_interval_minutes', v)} min={5} max={1440} step={5} suffix="мин" />
        <NumberField label="Рынков за сканирование" help="Сколько топ-рынков (по объёму 24ч) анализировать за один скан. Больше — шире охват, но медленнее и дороже"
          value={form.scan_markets_limit} onChange={(v) => set('scan_markets_limit', v)} min={10} max={500} step={10} suffix="рынков" />
      </Card>

      <div className="flex justify-end">
        <button onClick={save} disabled={saving}
          className="flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-lg transition-colors">
          <Save className="w-4 h-4" />
          {saving ? 'Сохранение...' : saved ? 'Сохранено!' : 'Сохранить'}
        </button>
      </div>
    </div>
  )
}

function KeyField({ label, placeholder, current, value, show, testResult, onToggleShow, onChange, onTest }) {
  const tr = testResult || { status: 'idle' }
  const canTest = !!current  // can test if a key is stored

  return (
    <div>
      <label className="block text-sm font-medium text-gray-300">{label}</label>
      {current && (
        <p className="text-xs text-gray-500 mt-0.5 font-mono">Текущий: {current}</p>
      )}
      <div className="flex items-center gap-2 mt-1.5">
        <div className="relative flex-1">
          <input
            type={show ? 'text' : 'password'}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={current ? 'Введите новое значение для замены...' : placeholder}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 pr-10 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500"
          />
          <button type="button" onClick={onToggleShow}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
            {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        <button
          type="button"
          onClick={onTest}
          disabled={!canTest || tr.status === 'testing'}
          title={canTest ? 'Проверить ключ' : 'Сначала сохраните ключ'}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 disabled:opacity-40 transition-colors flex-shrink-0"
        >
          {tr.status === 'testing'
            ? <Loader className="w-4 h-4 animate-spin" />
            : <FlaskConical className="w-4 h-4" />}
          Тест
        </button>
      </div>
      {tr.status === 'ok' && (
        <p className="flex items-center gap-1 text-xs text-green-400 mt-1">
          <CheckCircle className="w-3.5 h-3.5" /> {tr.detail}
        </p>
      )}
      {tr.status === 'error' && (
        <p className="flex items-center gap-1 text-xs text-red-400 mt-1">
          <XCircle className="w-3.5 h-3.5" /> {tr.detail}
        </p>
      )}
    </div>
  )
}

function NumberField({ label, help, value, onChange, min, max, step, suffix }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300">{label}</label>
      {help && <p className="text-xs text-gray-500 mt-0.5">{help}</p>}
      <div className="flex items-center gap-2 mt-2">
        <input type="number" value={value} min={min} max={max} step={step}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-36 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
        {suffix && <span className="text-gray-500 text-sm">{suffix}</span>}
      </div>
    </div>
  )
}
