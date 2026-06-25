import { useState, useMemo } from 'react'
import { useNodes } from './hooks/useNodes'
import { useFilteredNodes, useTotalNodeCount } from './hooks/useFilteredNodes'
import { Header } from './components/Header'
import { Stats } from './components/Stats'
import { TabBar } from './components/TabBar'
import { SearchBar } from './components/SearchBar'
import { NodeTable } from './components/NodeTable'
import { NodeCardList } from './components/NodeCardList'

function App() {
  const { groups, stats, loading, setMode, setValue, setAllMode } = useNodes()
  const [activeTab, setActiveTab] = useState('all')
  const [search, setSearch] = useState('')

  const searchLower = useMemo(() => search.toLowerCase(), [search])
  const flatNodes = useFilteredNodes(groups, activeTab, searchLower)
  const totalCount = useTotalNodeCount(groups)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg)' }}>
        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>加载中...</div>
      </div>
    )
  }

  const listProps = {
    flatNodes,
    onSetMode: setMode,
    onSetValue: setValue,
  }

  return (
    <div className="min-h-screen pb-[env(safe-area-inset-bottom)]" style={{ background: 'var(--bg)' }}>
      <Header stats={stats} onSetAllMode={setAllMode} />
      <div className="max-w-[1400px] mx-auto px-3 sm:px-4 lg:px-6 py-3 sm:py-4">
        <Stats stats={stats} />
        <TabBar groups={groups} activeTab={activeTab} onSwitch={setActiveTab} />
        <SearchBar
          value={search}
          onChange={setSearch}
          resultCount={flatNodes.length}
          totalCount={totalCount}
        />
        <div className="sm:hidden">
          <NodeCardList {...listProps} />
        </div>
        <div className="hidden sm:block">
          <NodeTable {...listProps} />
        </div>
      </div>
    </div>
  )
}

export default App
