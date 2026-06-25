import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import * as api from '../api'

export function useNodes() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const timerRef = useRef(null)
  const valuesRef = useRef({})

  const loadNodes = useCallback(async () => {
    const data = await api.fetchNodes()
    setGroups(data)
    setLoading(false)
  }, [])

  const refreshValues = useCallback(async () => {
    const vals = await api.fetchValues()
    valuesRef.current = vals

    setGroups(prev => {
      let changed = false
      const next = prev.map(g => {
        let groupChanged = false
        const nodes = g.nodes.map(n => {
          const newVal = vals[n.name]
          if (newVal !== undefined && newVal !== n.value) {
            groupChanged = true
            return { ...n, value: newVal }
          }
          return n
        })
        if (groupChanged) {
          changed = true
          return { ...g, nodes }
        }
        return g
      })
      return changed ? next : prev
    })
  }, [])

  const handleSetMode = useCallback(async (uniqueKey, mode) => {
    await api.setMode(uniqueKey, mode)
    setGroups(prev => prev.map(g => ({
      ...g,
      nodes: g.nodes.map((n, i) => {
        const key = `${g.key}/${i}`
        return key === uniqueKey ? { ...n, mode } : n
      })
    })))
  }, [])

  const handleSetValue = useCallback(async (uniqueKey, value) => {
    await api.setValue(uniqueKey, value)
    setGroups(prev => prev.map(g => ({
      ...g,
      nodes: g.nodes.map((n, i) => {
        const key = `${g.key}/${i}`
        return key === uniqueKey ? { ...n, manual: value, mode: 'manual' } : n
      })
    })))
  }, [])

  const handleSetAllMode = useCallback(async (mode) => {
    await api.setAllMode(mode)
    setGroups(prev => prev.map(g => ({
      ...g,
      nodes: g.nodes.map(n => ({ ...n, mode }))
    })))
  }, [])

  useEffect(() => {
    loadNodes()
    timerRef.current = setInterval(refreshValues, 2000)
    return () => clearInterval(timerRef.current)
  }, [loadNodes, refreshValues])

  const stats = useMemo(() => ({
    total: groups.reduce((sum, g) => sum + g.nodes.length, 0),
    random: groups.reduce((sum, g) => sum + g.nodes.filter(n => n.mode === 'random').length, 0),
    manual: groups.reduce((sum, g) => sum + g.nodes.filter(n => n.mode === 'manual').length, 0)
  }), [groups])

  return {
    groups,
    stats,
    loading,
    setMode: handleSetMode,
    setValue: handleSetValue,
    setAllMode: handleSetAllMode
  }
}
