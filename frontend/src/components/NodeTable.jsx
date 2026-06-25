import { memo, useRef, useCallback } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { NodeRow } from './NodeRow'

const ROW_HEIGHT = 48

export const NodeTable = memo(function NodeTable({ flatNodes, onSetMode, onSetValue }) {
  const parentRef = useRef(null)

  const virtualizer = useVirtualizer({
    count: flatNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 10,
  })

  const renderRow = useCallback((virtualRow) => {
    const item = flatNodes[virtualRow.index]
    if (!item) return null
    return (
      <NodeRow
        key={item.uniqueKey}
        index={virtualRow.index + 1}
        node={item.node}
        uniqueKey={item.uniqueKey}
        onSetMode={onSetMode}
        onSetValue={onSetValue}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: `${virtualRow.size}px`,
          transform: `translateY(${virtualRow.start}px)`,
        }}
      />
    )
  }, [flatNodes, onSetMode, onSetValue])

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      <div
        className="flex items-center py-3 px-3 text-xs font-semibold uppercase tracking-wider border-b"
        style={{ background: 'var(--surface2)', color: 'var(--text-muted)', borderColor: 'var(--border)' }}>
        <div className="w-1 shrink-0" />
        <div className="hidden sm:block w-12 shrink-0">序号</div>
        <div className="flex-1 min-w-[120px]">节点名称</div>
        <div className="w-[120px] shrink-0">模式</div>
        <div className="w-[180px] shrink-0 text-right pr-3">当前值</div>
      </div>

      {flatNodes.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <span className="mt-3 text-sm" style={{ color: 'var(--text-muted)' }}>没有匹配的节点</span>
        </div>
      ) : (
        <div
          ref={parentRef}
          style={{ height: 'calc(100vh - 360px)', overflow: 'auto', minHeight: '400px' }}>
          <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
            {virtualizer.getVirtualItems().map(renderRow)}
          </div>
        </div>
      )}
    </div>
  )
})
