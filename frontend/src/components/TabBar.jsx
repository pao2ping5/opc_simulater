import { memo } from 'react'

export const TabBar = memo(function TabBar({ groups, activeTab, onSwitch }) {
  return (
    <div className="tab-scroll-fade mb-4">
      <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-hide pr-6">
        <Tab label="全部" active={activeTab === 'all'} onClick={() => onSwitch('all')} />
        {groups.map(g => (
          <Tab
            key={g.key}
            label={g.label}
            count={g.nodes.length}
            active={activeTab === g.key}
            onClick={() => onSwitch(g.key)}
          />
        ))}
      </div>
    </div>
  )
})

const Tab = memo(function Tab({ label, count, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer"
      style={{
        background: active ? 'var(--surface3)' : 'transparent',
        color: active ? 'var(--nav-active)' : 'var(--text-secondary)',
        border: active ? '1px solid var(--border-light)' : '1px solid transparent',
      }}>
      {label}
      {count !== undefined && (
        <span
          className="px-1.5 py-0.5 rounded text-xs font-mono"
          style={{
            background: active ? 'var(--surface4)' : 'var(--surface2)',
            color: active ? 'var(--text-primary)' : 'var(--text-muted)',
          }}>
          {count}
        </span>
      )}
    </button>
  )
})
