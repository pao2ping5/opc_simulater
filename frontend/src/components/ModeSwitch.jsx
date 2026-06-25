import { memo } from 'react'

const SIZES = {
  lg: { track: 'w-14 h-8', knob: 'w-7 h-7', on: '2px', off: '30px' },
  md: { track: 'w-12 h-6', knob: 'w-5 h-5', on: '2px', off: '22px' },
}

export const ModeSwitch = memo(function ModeSwitch({ isRandom, onToggle, size = 'md' }) {
  const s = SIZES[size] || SIZES.md

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isRandom}
      aria-label={isRandom ? '随机模式，点击切换为手动' : '手动模式，点击切换为随机'}
      onClick={onToggle}
      className={`relative ${s.track} rounded-full transition-colors cursor-pointer shrink-0`}
      style={{ background: isRandom ? 'var(--cyan-dim)' : 'var(--orange-dim)' }}>
      <div
        className={`absolute top-0.5 ${s.knob} rounded-full transition-all shadow-md`}
        style={{
          left: isRandom ? s.on : s.off,
          background: isRandom ? 'var(--cyan)' : 'var(--orange)',
        }}
      />
    </button>
  )
})
