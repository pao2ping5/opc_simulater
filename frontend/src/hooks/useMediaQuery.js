import { useState, useEffect } from 'react'

/**
 * Subscribe to a CSS media query.
 *
 * @param {string} query - A media query string, e.g. ``'(min-width: 640px)'``.
 * @returns {boolean} - Whether the query currently matches.
 */
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia(query).matches
  })

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mql = window.matchMedia(query)
    const onChange = (e) => setMatches(e.matches)
    // Initial sync in case the query result changed between mount and effect
    setMatches(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return matches
}
