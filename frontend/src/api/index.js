const BASE_URL = '/api'

export async function fetchNodes() {
  const res = await fetch(`${BASE_URL}/nodes`)
  return res.json()
}

export async function fetchValues() {
  const res = await fetch(`${BASE_URL}/values`)
  return res.json()
}

export async function setMode(uniqueKey, mode) {
  await fetch(`${BASE_URL}/set_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ unique_key: uniqueKey, mode })
  })
}

export async function setValue(uniqueKey, value) {
  await fetch(`${BASE_URL}/set_value`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ unique_key: uniqueKey, value })
  })
}

export async function setAllMode(mode) {
  await fetch(`${BASE_URL}/set_all_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  })
}
