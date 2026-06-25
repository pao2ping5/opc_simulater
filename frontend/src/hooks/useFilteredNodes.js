import { useMemo } from 'react'

export function useFilteredNodes(groups, activeTab, search) {
  return useMemo(() => {
    const filteredGroups = activeTab === 'all' ? groups : groups.filter(g => g.key === activeTab)
    const result = []
    filteredGroups.forEach(g => {
      g.nodes.forEach((n, i) => {
        if (search && !n.name.toLowerCase().includes(search)) return
        result.push({
          node: n,
          uniqueKey: `${g.key}/${i}`,
        })
      })
    })
    return result
  }, [groups, activeTab, search])
}

export function useTotalNodeCount(groups) {
  return useMemo(
    () => groups.reduce((sum, g) => sum + g.nodes.length, 0),
    [groups]
  )
}
