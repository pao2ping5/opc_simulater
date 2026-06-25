import { memo } from 'react'

export const SearchBar = memo(function SearchBar({ value, onChange, resultCount, totalCount }) {
  const hasSearch = value.length > 0

  return (
    <div className="mb-4">
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--text-muted)"
          strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder="搜索节点名称..."
          className="w-full pl-10 pr-10 py-2.5 rounded-xl text-sm outline-none transition-colors"
          style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            color: 'var(--text)',
          }}
        />
        {hasSearch && (
          <button
            type="button"
            onClick={() => onChange('')}
            className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg cursor-pointer transition-colors"
            style={{ color: 'var(--text-muted)' }}
            aria-label="清除搜索">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      {totalCount !== undefined && (
        <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
          {hasSearch
            ? `找到 ${resultCount} 条节点`
            : `共 ${resultCount ?? totalCount} 条节点`}
        </div>
      )}
    </div>
  )
})
