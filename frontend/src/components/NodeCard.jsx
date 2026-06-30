import { memo } from 'react'
import { ModeBadge } from './ModeBadge'
import { ModeSwitch } from './ModeSwitch'
import { ValueField } from './ValueField'
import { NodeMetaField } from './NodeMetaField'
import { nodeLabel } from '../utils/nodeLabel'

export const NodeCard = memo(function NodeCard({
  node,
  nodeId,
  value,
  strategies,
  onSetMode,
  onSetValue,
  onUpdateMeta,
}) {
  const isRandom = node.mode === 'random'
  const label = nodeLabel(node)

  return (
    <div
      className="rounded-xl overflow-hidden border"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      <div className="flex">
        <div className="w-1 shrink-0" style={{ background: isRandom ? 'var(--cyan)' : 'var(--orange)' }} />
        <div className="flex-1 p-3 min-w-0">
          {/* Title */}
          <div className="text-sm mb-2 truncate font-medium" title={label} style={{ color: 'var(--text)' }}>
            {label}
          </div>

          {/* Compact meta editor */}
          {onUpdateMeta && (
            <NodeMetaField node={node} strategies={strategies} onUpdateMeta={onUpdateMeta} compact />
          )}

          {/* Mode + Value */}
          <div className="flex items-center justify-between gap-3 mt-2">
            <div className="flex items-center gap-2 shrink-0">
              <ModeBadge isRandom={isRandom} />
              <ModeSwitch
                size="lg"
                isRandom={isRandom}
                onToggle={() => onSetMode(nodeId, isRandom ? 'manual' : 'random')}
              />
            </div>
            <div className="min-w-0 flex-1">
              <ValueField
                node={node}
                nodeId={nodeId}
                value={value}
                onSetValue={onSetValue}
                layout="row"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
})
