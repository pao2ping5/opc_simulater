import { memo, useRef, useCallback } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { NodeCard } from './NodeCard'

const CARD_HEIGHT = 104

export const NodeCardList = memo(function NodeCardList({ flatNodes, onSetMode, onSetValue }) {
  const parentRef = useRef(null)

  const virtualizer = useVirtualizer({
    count: flatNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => CARD_HEIGHT,
    overscan: 5,
  })

  const renderCard = useCallback((virtualRow) => {
    const item = flatNodes[virtualRow.index]
    if (!item) return null
    return (
      <div
        key={item.uniqueKey}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: `${virtualRow.size}px`,
          transform: `translateY(${virtualRow.start}px)`,
          paddingBottom: '8px',
        }}>
        <NodeCard
          node={item.node}
          uniqueKey={item.uniqueKey}
          onSetMode={onSetMode}
          onSetValue={onSetValue}
        />
      </div>
    )
  }, [flatNodes, onSetMode, onSetValue])

  if (flatNodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <span className="mt-3 text-sm" style={{ color: 'var(--text-muted)' }}>没有匹配的节点</span>
      </div>
    )
  }

  return (
    <div
      ref={parentRef}
      style={{ height: 'calc(100dvh - 340px)', overflow: 'auto', minHeight: '320px' }}
      className="pb-[env(safe-area-inset-bottom)]">
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map(renderCard)}
      </div>
    </div>
  )
})
