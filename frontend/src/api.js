const BASE = '/api'

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

export const api = {
  health: () => req('/health'),

  // Markets
  getMarkets: (limit = 30) => req(`/markets?limit=${limit}`),

  // Opportunities
  getOpportunities: (status = '', limit = 50) =>
    req(`/opportunities?${status ? `status=${status}&` : ''}limit=${limit}`),
  triggerScan: () => req('/opportunities/scan', { method: 'POST' }),
  placeBet: (id) => req(`/opportunities/${id}/bet`, { method: 'POST' }),

  // Bets
  getBets: (limit = 100) => req(`/bets?limit=${limit}`),
  getStats: () => req('/bets/stats'),

  // Settings
  getSettings: () => req('/settings'),
  updateSettings: (data) =>
    req('/settings', { method: 'PATCH', body: JSON.stringify(data) }),

  // API Keys
  getKeys: () => req('/settings/keys'),
  updateKeys: (data) =>
    req('/settings/keys', { method: 'PATCH', body: JSON.stringify(data) }),
}
