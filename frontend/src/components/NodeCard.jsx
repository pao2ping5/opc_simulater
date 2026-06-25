import { memo } from 'react'
import { ModeBadge } from './ModeBadge'
import { ModeSwitch } from './ModeSwitch'
import { ValueField } from './ValueField'

export const NodeCard = memo(function NodeCard({ node, uniqueKey, onSetMode, onSetValue }) {
  const isRandom = node.mode === 'random'

  return (
    <div
      className="rounded-xl overflow-hidden border"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      <div className="flex">
        <div className="w-1 shrink-0" style={{ background: isRandom ? 'var(--cyan)' : 'var(--orange)' }} />
        <div className="flex-1 p-3 min-w-0">
          <div className="text-sm mb-3 truncate font-medium" title={node.name} style={{ color: 'var(--text)' }}>
            {node.name}
          </div>

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 shrink-0">
              <ModeBadge isRandom={isRandom} />
              <ModeSwitch
                size="lg"
                isRandom={isRandom}
                onToggle={() => onSetMode(uniqueKey, isRandom ? 'manual' : 'random')}
              />
            </div>
            <div className="min-w-0 flex-1">
              <ValueField
                node={node}
                uniqueKey={uniqueKey}
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
