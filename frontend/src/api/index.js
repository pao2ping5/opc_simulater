const BASE_URL = '/api'

// ── Internal helpers ──────────────────────────────────────────────

class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.status = status
    this.body = body
  }
}

async function _jsonOrThrow(res) {
  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch (e) {
      // Non-JSON response (e.g. plain text error page)
    }
  }
  if (!res.ok) {
    const msg = (data && (data.error || data.message)) || `HTTP ${res.status}`
    throw new ApiError(msg, res.status, data)
  }
  return data ?? {}
}

// ── Node data ──────────────────────────────────────────────────────

export async function fetchNodes() {
  const res = await fetch(`${BASE_URL}/nodes`)
  return _jsonOrThrow(res)
}

export async function fetchValues() {
  const res = await fetch(`${BASE_URL}/values`)
  return _jsonOrThrow(res)
}

// ── Mode / Value control ───────────────────────────────────────────

export async function setMode(nodeId, mode) {
  const res = await fetch(`${BASE_URL}/set_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ unique_key: nodeId, mode }),
  })
  return _jsonOrThrow(res)
}

export async function setValue(nodeId, value) {
  const res = await fetch(`${BASE_URL}/set_value`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ unique_key: nodeId, value }),
  })
  return _jsonOrThrow(res)
}

export async function setAllMode(mode) {
  const res = await fetch(`${BASE_URL}/set_all_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
  return _jsonOrThrow(res)
}

// ── Metadata editing ───────────────────────────────────────────────

export async function updateNodeMeta(nodeId, updates) {
  const res = await fetch(`${BASE_URL}/nodes/${encodeURIComponent(nodeId)}/meta`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  })
  return _jsonOrThrow(res)
}

export async function batchUpdateNodes(updates) {
  const res = await fetch(`${BASE_URL}/nodes/batch`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  })
  return _jsonOrThrow(res)
}

// ── Strategies ─────────────────────────────────────────────────────

export async function fetchStrategies() {
  const res = await fetch(`${BASE_URL}/strategies`)
  return _jsonOrThrow(res)
}

// ── Model management ───────────────────────────────────────────────

export async function uploadModel(filePath) {
  const res = await fetch(`${BASE_URL}/model/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath }),
  })
  return _jsonOrThrow(res)
}

export { ApiError }
