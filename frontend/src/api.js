const API_BASE = import.meta.env.VITE_API_BASE_URL

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const isJson = response.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await response.json() : null

  if (!response.ok) {
    const message = data?.detail
      ? typeof data.detail === 'string'
        ? data.detail
        : JSON.stringify(data.detail)
      : 'Something went wrong'
    throw new Error(message)
  }

  return data
}

export function signup(username, email, password) {
  return request('/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
}

export function login(email, password) {
  return request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function generateApiKey(token) {
  return request('/auth/api-key', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function createShortLink(token, { url, alias, expiresInMinutes }) {
  const body = { url }
  if (alias) body.alias = alias
  if (expiresInMinutes) body.expires_in_minutes = Number(expiresInMinutes)

  return request('/shorten', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
}

export function deleteShortLink(token, code) {
  return request(`/${code}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function fetchStats(code) {
  return request(`/stats/${code}`)
}

export function fetchAnalytics() {
  return request('/analytics')
}

export function fetchMyLinks(token) {
  return request('/my-links', {
    headers: { Authorization: `Bearer ${token}` },
  })
}
