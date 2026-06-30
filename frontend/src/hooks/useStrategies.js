import { useState, useEffect } from 'react'
import * as api from '../api'

/**
 * Fetch the list of available value-generation strategies from the backend
 * once on mount.  Used to populate the strategy dropdown in NodeMetaField
 * so the frontend never hardcodes strategy names that may drift from
 * ``common._BUILTIN_STRATEGIES``.
 *
 * Returns ``{ strategies, loading, error }`` where ``strategies`` is a list
 * of ``{ name, description }``.  Falls back to an empty list on error so
 * the dropdown renders with just the "auto" option.
 */
export function useStrategies() {
  const [strategies, setStrategies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await api.fetchStrategies()
        if (!cancelled) {
          setStrategies(Array.isArray(data) ? data : [])
          setError(null)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message)
          // Keep empty list — the dropdown still shows "auto".
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  return { strategies, loading, error }
}
