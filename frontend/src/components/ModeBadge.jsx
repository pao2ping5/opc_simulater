import { memo } from 'react'

export const ModeBadge = memo(function ModeBadge({ isRandom }) {
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium shrink-0"
      style={{
        background: isRandom ? 'var(--cyan-dim)' : 'var(--orange-dim)',
        color: isRandom ? 'var(--cyan)' : 'var(--orange)',
        border: `1px solid ${isRandom ? 'rgba(0,212,170,0.25)' : 'rgba(245,158,11,0.25)'}`,
      }}>
      {isRandom ? '随机' : '手动'}
    </span>
  )
})
