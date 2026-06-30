import { memo, useRef, useCallback } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { NodeRow } from './NodeRow'

const ROW_HEIGHT = 48

// Available viewport height for the scrolling list.
// Header (~56px sticky) + ErrorBar (~36px when shown) + Stats card (~84px)
// + TabBar (~44px) + SearchBar (~52px) + page padding (24px) ≈ 296px.
// Subtract another ~64px for breathing room.  These are approximations;
// the overscan and minHeight keep things sane if the estimate is off.
const TABLE_VIEWPORT_OFFSET = 360
const TABLE_MIN_HEIGHT = 400

export const NodeTable = memo(function NodeTable({ flatNodes, values, strategies, onSetMode, onSetValue, onUpdateMeta }) {
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
        key={item.nodeId}
        index={virtualRow.index + 1}
        node={item.node}
        nodeId={item.nodeId}
        value={values ? values[item.nodeId] : undefined}
        strategies={strategies}
        onSetMode={onSetMode}
        onSetValue={onSetValue}
        onUpdateMeta={onUpdateMeta}
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
  }, [flatNodes, values, strategies, onSetMode, onSetValue, onUpdateMeta])

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      <div
        className="flex items-center py-3 px-3 text-xs font-semibold uppercase tracking-wider border-b"
        style={{ background: 'var(--surface2)', color: 'var(--text-muted)', borderColor: 'var(--border)' }}>
        <div className="w-1 shrink-0" />
        <div className="hidden xl:block w-12 shrink-0">序号</div>
        <div className="flex-1 min-w-[100px]">节点名称</div>
        <div className="hidden xl:flex items-center gap-1.5 px-1 shrink-0">
          <span style={{ width: '64px' }}>类型</span>
          <span style={{ width: '120px' }}>量程</span>
          <span style={{ width: '44px' }}>单位</span>
          <span style={{ width: '110px' }}>策略</span>
        </div>
        <div className="w-[110px] shrink-0">模式</div>
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
          style={{ height: `calc(100vh - ${TABLE_VIEWPORT_OFFSET}px)`, overflow: 'auto', minHeight: `${TABLE_MIN_HEIGHT}px` }}>
          <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
            {virtualizer.getVirtualItems().map(renderRow)}
          </div>
        </div>
      )}
    </div>
  )
})
