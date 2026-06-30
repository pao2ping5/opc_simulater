import { memo } from 'react'
import { ModeBadge } from './ModeBadge'
import { ModeSwitch } from './ModeSwitch'
import { ValueField } from './ValueField'
import { NodeMetaField } from './NodeMetaField'
import { nodeLabel } from '../utils/nodeLabel'

export const NodeRow = memo(function NodeRow({
  index,
  node,
  nodeId,
  value,
  strategies,
  onSetMode,
  onSetValue,
  onUpdateMeta,
  style,
}) {
  const isRandom = node.mode === 'random'
  const label = nodeLabel(node)

  return (
    <div
      style={style}
      className="flex items-center border-b transition-colors hover:bg-[var(--surface2)] group"
      data-node-id={nodeId}>
      <div className="w-1 self-stretch shrink-0" style={{ background: isRandom ? 'var(--cyan)' : 'var(--orange)' }} />

      <div
        className="hidden xl:block w-12 px-3 py-2.5 text-xs font-mono shrink-0"
        style={{ color: 'var(--text-muted)' }}>
        {String(index).padStart(3, '0')}
      </div>

      {/* Name */}
      <div className="flex-1 min-w-[100px] px-2 py-2.5 text-sm truncate" style={{ color: 'var(--text)' }}>
        {label}
      </div>

      {/* Inline meta editor: type | range | unit | strategy */}
      {onUpdateMeta && (
        <div className="hidden xl:flex items-center gap-1.5 px-1 shrink-0">
          <NodeMetaField node={node} strategies={strategies} onUpdateMeta={onUpdateMeta} compact={false} />
        </div>
      )}

      {/* Mode */}
      <div className="w-[110px] px-2 py-2.5 shrink-0 flex items-center gap-1.5">
        <ModeBadge isRandom={isRandom} />
        <ModeSwitch
          isRandom={isRandom}
          onToggle={() => onSetMode(nodeId, isRandom ? 'manual' : 'random')}
        />
      </div>

      {/* Value */}
      <div className="w-[180px] px-3 py-2.5 shrink-0">
        <ValueField
          node={node}
          nodeId={nodeId}
          value={value}
          onSetValue={onSetValue}
          layout="row"
        />
      </div>
    </div>
  )
})
