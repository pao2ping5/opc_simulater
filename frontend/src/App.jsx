import { useState, useMemo } from 'react'
import { useNodes } from './hooks/useNodes'
import { useFilteredNodes, useTotalNodeCount } from './hooks/useFilteredNodes'
import { useMediaQuery } from './hooks/useMediaQuery'
import { useStrategies } from './hooks/useStrategies'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ErrorBar } from './components/ErrorBar'
import { Header } from './components/Header'
import { Stats } from './components/Stats'
import { TabBar } from './components/TabBar'
import { SearchBar } from './components/SearchBar'
import { NodeTable } from './components/NodeTable'
import { NodeCardList } from './components/NodeCardList'

function App() {
  const {
    groups,
    values,
    stats,
    loading,
    error,
    clearError,
    setMode,
    setValue,
    setAllMode,
    updateMeta,
  } = useNodes()
  const { strategies } = useStrategies()
  const [activeTab, setActiveTab] = useState('all')
  const [search, setSearch] = useState('')
  // Conditionally render desktop table vs mobile card list so only one
  // virtualizer runs at a time.  Previous versions mounted both and hid one
  // via CSS, doubling the work on every render.
  const isDesktop = useMediaQuery('(min-width: 640px)')

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
    values,
    strategies,
    onSetMode: setMode,
    onSetValue: setValue,
    onUpdateMeta: updateMeta,
  }

  return (
    <div className="min-h-screen pb-[env(safe-area-inset-bottom)]" style={{ background: 'var(--bg)' }}>
      <ErrorBar error={error} onDismiss={clearError} />
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
        {isDesktop ? <NodeTable {...listProps} /> : <NodeCardList {...listProps} />}
      </div>
    </div>
  )
}

export default function AppWithBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  )
}
