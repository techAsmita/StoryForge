async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`/api${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  } catch {
    throw new Error('Backend not reachable. Is uvicorn running on port 8000?')
  }
  if (res.status === 204) return null
  const body = await res.json().catch(() => ({}))
  if ((res.status === 502 || res.status === 504) && !body.detail) {
    throw new Error('Backend not reachable. Is uvicorn running on port 8000 (and PostgreSQL started)?')
  }
  if (!res.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join('; ')
      : body.detail
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return body
}

const json = (method, data) => ({ method, body: JSON.stringify(data) })

export const api = {
  health: () => request('/health'),
  strategies: () => request('/strategies'),
  generate: (payload) => request('/stories/generate', json('POST', payload)),
  listStories: () => request('/stories'),
  getStory: (id) => request(`/stories/${id}`),
  updateStory: (id, patch) => request(`/stories/${id}`, json('PATCH', patch)),
  retryImages: (id) => request(`/stories/${id}/images/retry`, { method: 'POST' }),
  related: (id) => request(`/stories/${id}/related`),
  deleteStory: (id) => request(`/stories/${id}`, { method: 'DELETE' }),
  getSettings: () => request('/settings'),
  saveSettings: (data) => request('/settings', json('PUT', data)),
}
