const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

const getTokens = () => ({
  access: localStorage.getItem('bp_access'),
  refresh: localStorage.getItem('bp_refresh'),
})

export const saveTokens = (data) => {
  localStorage.setItem('bp_access', data.access_token)
  localStorage.setItem('bp_refresh', data.refresh_token)
}

export const clearTokens = () => {
  localStorage.removeItem('bp_access')
  localStorage.removeItem('bp_refresh')
}

export const isSignedIn = () => Boolean(getTokens().access)

async function refreshAccess() {
  const { refresh } = getTokens()
  if (!refresh) return false
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refresh }),
  })
  if (!res.ok) return false
  saveTokens(await res.json())
  return true
}

export async function api(path, options = {}, retry = true) {
  const { access } = getTokens()
  const headers = new Headers(options.headers || {})
  if (access) headers.set('Authorization', `Bearer ${access}`)
  if (!(options.body instanceof FormData) && options.body !== undefined) headers.set('Content-Type', 'application/json')
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (res.status === 401 && retry && await refreshAccess()) return api(path, options, false)
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.detail || 'Something went wrong')
  return body
}

export { API_BASE }
