import { useMemo } from 'react'
import { nodeLabel } from '../utils/nodeLabel'

export function useFilteredNodes(groups, activeTab, search) {
  return useMemo(() => {
    const filteredGroups =
      activeTab === 'all'
        ? groups
        : groups.filter(g => g.key === activeTab)

    const result = []
    filteredGroups.forEach(g => {
      g.nodes.forEach(n => {
        const label = nodeLabel(n)
        if (search && !label.toLowerCase().includes(search)) return
        result.push({
          node: n,
          nodeId: n.node_id,
        })
      })
    })
    return result
  }, [groups, activeTab, search])
}

export function useTotalNodeCount(groups) {
  return useMemo(
    () => groups.reduce((sum, g) => sum + g.nodes.length, 0),
    [groups],
  )
}
