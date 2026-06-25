import { useState, memo, useMemo } from 'react'

export const ValueField = memo(function ValueField({
  node,
  uniqueKey,
  onSetValue,
  layout = 'row',
}) {
  const [manualValue, setManualValue] = useState(node.manual?.toString() || '0')
  const [confirmed, setConfirmed] = useState(false)
  const isRandom = node.mode === 'random'

  const displayValue = useMemo(() => {
    if (typeof node.value === 'number') {
      return Number.isInteger(node.value) ? node.value.toString() : node.value.toFixed(2)
    }
    return node.value
  }, [node.value])

  const handleConfirm = async () => {
    const v = parseFloat(manualValue)
    if (isNaN(v)) return
    await onSetValue(uniqueKey, v)
    setConfirmed(true)
    setTimeout(() => setConfirmed(false), 1500)
  }

  if (isRandom) {
    return (
      <div className={layout === 'row' ? 'text-right' : 'flex flex-col items-end'}>
        <span className="font-mono text-base sm:text-sm font-bold" style={{ color: 'var(--text)' }}>
          {displayValue}
        </span>
      </div>
    )
  }

  return (
    <div className={`flex gap-1.5 items-center ${layout === 'row' ? 'justify-end' : 'justify-end w-full'}`}>
      <div className="flex flex-col items-end">
        <input
          type="number"
          step="any"
          value={manualValue}
          onChange={e => setManualValue(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleConfirm()}
          className="w-[88px] sm:w-[90px] px-2 py-2 sm:py-1.5 rounded-lg font-mono text-sm text-right outline-none"
          style={{
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            color: 'var(--orange)',
          }}
        />
      </div>
      <button
        onClick={handleConfirm}
        className="px-3 py-2 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-all self-end min-h-[44px] sm:min-h-0"
        style={{
          background: confirmed ? 'var(--cyan)' : 'var(--orange)',
          color: '#000',
        }}>
        {confirmed ? '✓' : '确认'}
      </button>
    </div>
  )
})
