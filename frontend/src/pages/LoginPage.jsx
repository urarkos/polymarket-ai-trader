import { useState } from 'react'
import { Zap, Lock } from 'lucide-react'
import { auth } from '../api'

export default function LoginPage({ onLogin }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!password.trim()) return
    setLoading(true)
    setError('')
    try {
      // Test the password against a protected endpoint
      const res = await fetch('/api/settings', {
        headers: { 'X-App-Password': password },
      })
      if (res.status === 401) {
        setError('Неверный пароль')
        return
      }
      if (!res.ok) throw new Error(res.status)
      auth.setPassword(password)
      onLogin()
    } catch (e) {
      if (e.message !== 'Неверный пароль') setError('Ошибка подключения')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 bg-green-500/10 border border-green-500/30 rounded-2xl flex items-center justify-center mb-4">
            <Zap className="w-7 h-7 text-green-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">PolyAI Trader</h1>
          <p className="text-gray-500 text-sm mt-1">Введите пароль для входа</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError('') }}
              placeholder="Пароль"
              autoFocus
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 pl-10 text-white placeholder-gray-600 focus:outline-none focus:border-green-500 transition-colors"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !password.trim()}
            className="w-full bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            {loading ? 'Проверка...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  )
}
