import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import * as api from '../api'

/**
 * Hook for managing OPC simulator node state.
 *
 * Separates ``groups`` (structural data — rarely changes) from ``values``
 * (per-tick live values — changes every 2s).  Previous versions mutated
 * ``groups[].nodes[].value`` on each poll, which produced new node object
 * references every 2s and defeated React.memo on every row.  Now ``values``
 * is a flat ``{ [node_id]: value }`` map that updates independently; rows
 * look up their value via ``nodeId``.
 *
 * Polling pauses when the document is hidden and resumes on visibility
 * change with an immediate refresh.
 */
export function useNodes() {
  const [groups, setGroups] = useState([])
  const [values, setValues] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const loadNodes = useCallback(async () => {
    try {
      setError(null)
      const data = await api.fetchNodes()
      // Initial values: pull from the embedded `value` field so the first
      // render isn't all zeros before /api/values fires.
      const initialVals = {}
      for (const g of data) {
        for (const n of g.nodes) {
          initialVals[n.node_id] = n.value
        }
      }
      setGroups(data)
      setValues(initialVals)
    } catch (e) {
      setError(`加载节点失败: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }, [])

  // Poll values every 2s.  Only the flat `values` map is replaced —
  // `groups` (and all node object references inside it) stay stable, so
  // memoized rows don't re-render unless their own value changed.
  const refreshValues = useCallback(async () => {
    if (document.hidden) return
    let vals
    try {
      vals = await api.fetchValues()
    } catch (e) {
      setError(`刷新值失败: ${e.message}`)
      return
    }
    setError(null)
    setValues(vals)
  }, [])

  // ── Mutations ──────────────────────────────────────────────────────
  //
  // All mutations update `groups` for structural fields (mode, manual,
  // meta) so the UI reflects the change immediately.  Value field is left
  // to be overwritten by the next /api/values poll.  On failure, roll back
  // to the previous groups state.

  const handleSetMode = useCallback(async (nodeId, mode) => {
    const prev = groups
    setGroups(g =>
      g.map(grp => ({
        ...grp,
        nodes: grp.nodes.map(n =>
          n.node_id === nodeId ? { ...n, mode } : n,
        ),
      })),
    )
    try {
      await api.setMode(nodeId, mode)
    } catch (e) {
      setGroups(prev)
      setError(`切换模式失败: ${e.message}`)
    }
  }, [groups])

  const handleSetValue = useCallback(async (nodeId, value) => {
    const prev = groups
    setGroups(g =>
      g.map(grp => ({
        ...grp,
        nodes: grp.nodes.map(n =>
          n.node_id === nodeId
            ? { ...n, manual: value, mode: 'manual' }
            : n,
        ),
      })),
    )
    // Optimistically update the values map too so the UI shows the new
    // manual value immediately instead of waiting for the next poll.
    setValues(v => ({ ...v, [nodeId]: value }))
    try {
      await api.setValue(nodeId, value)
    } catch (e) {
      setGroups(prev)
      setError(`设值失败: ${e.message}`)
    }
  }, [groups])

  const handleSetAllMode = useCallback(async (mode) => {
    const prev = groups
    setGroups(g =>
      g.map(grp => ({
        ...grp,
        nodes: grp.nodes.map(n => ({ ...n, mode })),
      })),
    )
    try {
      await api.setAllMode(mode)
    } catch (e) {
      setGroups(prev)
      setError(`批量切换失败: ${e.message}`)
    }
  }, [groups])

  const handleUpdateMeta = useCallback(async (nodeId, updates) => {
    const prev = groups
    setGroups(g =>
      g.map(grp => ({
        ...grp,
        nodes: grp.nodes.map(n =>
          n.node_id === nodeId ? { ...n, ...updates } : n,
        ),
      })),
    )
    try {
      await api.updateNodeMeta(nodeId, updates)
    } catch (e) {
      setGroups(prev)
      setError(`更新元数据失败: ${e.message}`)
    }
  }, [groups])

  useEffect(() => {
    loadNodes()
    timerRef.current = setInterval(refreshValues, 2000)
    const onVisibility = () => {
      if (!document.hidden) refreshValues()
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      clearInterval(timerRef.current)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [loadNodes, refreshValues])

  const stats = useMemo(
    () => ({
      total: groups.reduce((sum, g) => sum + g.nodes.length, 0),
      random: groups.reduce(
        (sum, g) => sum + g.nodes.filter(n => n.mode === 'random').length,
        0,
      ),
      manual: groups.reduce(
        (sum, g) => sum + g.nodes.filter(n => n.mode === 'manual').length,
        0,
      ),
    }),
    [groups],
  )

  const clearError = useCallback(() => setError(null), [])

  return {
    groups,
    values,
    stats,
    loading,
    error,
    clearError,
    setMode: handleSetMode,
    setValue: handleSetValue,
    setAllMode: handleSetAllMode,
    updateMeta: handleUpdateMeta,
  }
}
