import { memo } from 'react'
import { ModeBadge } from './ModeBadge'
import { ModeSwitch } from './ModeSwitch'
import { ValueField } from './ValueField'

export const NodeRow = memo(function NodeRow({ index, node, uniqueKey, onSetMode, onSetValue, style }) {
  const isRandom = node.mode === 'random'

  return (
    <div
      style={style}
      className="flex items-center border-b transition-colors hover:bg-[var(--surface2)] group"
      data-unique-key={uniqueKey}>
      <div className="w-1 self-stretch shrink-0" style={{ background: isRandom ? 'var(--cyan)' : 'var(--orange)' }} />

      <div
        className="hidden sm:block w-12 px-3 py-2.5 text-xs font-mono shrink-0"
        style={{ color: 'var(--text-muted)' }}>
        {String(index).padStart(3, '0')}
      </div>

      <div className="flex-1 min-w-[120px] px-3 py-2.5 text-sm truncate" style={{ color: 'var(--text)' }}>
        {node.name}
      </div>

      <div className="w-[120px] px-3 py-2.5 shrink-0 flex items-center gap-2">
        <ModeBadge isRandom={isRandom} />
        <ModeSwitch
          isRandom={isRandom}
          onToggle={() => onSetMode(uniqueKey, isRandom ? 'manual' : 'random')}
        />
      </div>

      <div className="w-[180px] px-3 py-2.5 shrink-0">
        <ValueField
          node={node}
          uniqueKey={uniqueKey}
          onSetValue={onSetValue}
          layout="row"
        />
      </div>
    </div>
  )
})
