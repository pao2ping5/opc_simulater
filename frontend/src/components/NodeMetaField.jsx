import { useState, useCallback, memo, useEffect } from 'react'

const DATA_TYPES = ['float', 'int', 'bool', 'string']

/**
 * Inline-editable metadata fields for a single OPC node.
 * Shows: data_type dropdown, range lo-hi inputs, unit input, strategy dropdown.
 *
 * ``strategies`` is a list of ``{ name, description }`` pulled from
 * ``/api/strategies`` at the App level.  When empty (e.g. backend unreachable),
 * the dropdown still renders with just the "auto" option.
 */
export const NodeMetaField = memo(function NodeMetaField({
  node,
  strategies = [],
  onUpdateMeta,
  compact = false,
}) {
  const [lo, setLo] = useState(String(node.range_lo ?? 0))
  const [hi, setHi] = useState(String(node.range_hi ?? 100))
  const [unit, setUnit] = useState(node.unit ?? '')

  // Sync local inputs when upstream node metadata changes (e.g. another
  // browser edited the same node, or a model reload happened).  Without
  // this, the inputs would show stale values forever.
  useEffect(() => {
    setLo(String(node.range_lo ?? 0))
  }, [node.range_lo])
  useEffect(() => {
    setHi(String(node.range_hi ?? 100))
  }, [node.range_hi])
  useEffect(() => {
    setUnit(node.unit ?? '')
  }, [node.unit])

  const handleTypeChange = useCallback(
    (e) => onUpdateMeta(node.node_id, { data_type: e.target.value }),
    [node.node_id, onUpdateMeta],
  )

  const handleStrategyChange = useCallback(
    (e) => onUpdateMeta(node.node_id, { gen_strategy: e.target.value }),
    [node.node_id, onUpdateMeta],
  )

  const handleRangeBlur = useCallback(() => {
    const nlo = parseFloat(lo)
    const nhi = parseFloat(hi)
    if (isNaN(nlo) || isNaN(nhi)) return
    onUpdateMeta(node.node_id, {
      range_lo: Math.min(nlo, nhi),
      range_hi: Math.max(nlo, nhi),
    })
    setLo(String(Math.min(nlo, nhi)))
    setHi(String(Math.max(nlo, nhi)))
  }, [node.node_id, lo, hi, onUpdateMeta])

  const handleUnitBlur = useCallback(() => {
    onUpdateMeta(node.node_id, { unit })
  }, [node.node_id, unit, onUpdateMeta])

  const inputCls =
    'bg-[var(--bg)] border border-[var(--border)] rounded px-1.5 py-1 text-xs font-mono outline-none focus:border-[var(--cyan)] text-right w-full'

  const selectCls =
    'bg-[var(--bg)] border border-[var(--border)] rounded px-1 py-1 text-xs outline-none focus:border-[var(--cyan)]'

  if (compact) {
    // Mobile card layout: 2 rows
    return (
      <div className="space-y-1.5 mt-2">
        {/* Row 1: type + range + unit */}
        <div className="flex items-center gap-1 text-xs">
          <select
            value={node.data_type || 'float'}
            onChange={handleTypeChange}
            className={selectCls}
            style={{ color: 'var(--text)' }}>
            {DATA_TYPES.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            type="number"
            step="any"
            value={lo}
            onChange={e => setLo(e.target.value)}
            onBlur={handleRangeBlur}
            onKeyDown={e => e.key === 'Enter' && handleRangeBlur()}
            className={inputCls}
            style={{ width: '56px' }}
            title="量程下限"
          />
          <span style={{ color: 'var(--text-muted)' }}>~</span>
          <input
            type="number"
            step="any"
            value={hi}
            onChange={e => setHi(e.target.value)}
            onBlur={handleRangeBlur}
            onKeyDown={e => e.key === 'Enter' && handleRangeBlur()}
            className={inputCls}
            style={{ width: '56px' }}
            title="量程上限"
          />
          <input
            type="text"
            value={unit}
            onChange={e => setUnit(e.target.value)}
            onBlur={handleUnitBlur}
            onKeyDown={e => e.key === 'Enter' && handleUnitBlur()}
            className={inputCls.replace('text-right', 'text-left')}
            style={{ width: '36px' }}
            placeholder="单位"
            title="单位"
          />
        </div>
        {/* Row 2: strategy dropdown */}
        <select
          value={node.gen_strategy || ''}
          onChange={handleStrategyChange}
          className={selectCls + ' w-full'}
          style={{ color: 'var(--text)' }}
          title="值生成策略">
          <option value="">自动选择</option>
          {strategies.map(s => (
            <option key={s.name} value={s.name}>{s.description || s.name}</option>
          ))}
        </select>
      </div>
    )
  }

  // Table row layout: inline columns
  return (
    <>
      {/* type */}
      <select
        value={node.data_type || 'float'}
        onChange={handleTypeChange}
        className={selectCls}
        style={{ color: 'var(--text)', width: '64px' }}>
        {DATA_TYPES.map(t => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      {/* range */}
      <div className="flex items-center gap-0.5" style={{ width: '120px' }}>
        <input
          type="number"
          step="any"
          value={lo}
          onChange={e => setLo(e.target.value)}
          onBlur={handleRangeBlur}
          onKeyDown={e => e.key === 'Enter' && handleRangeBlur()}
          className={inputCls}
          style={{ width: '48px' }}
          title="量程下限"
        />
        <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>~</span>
        <input
          type="number"
          step="any"
          value={hi}
          onChange={e => setHi(e.target.value)}
          onBlur={handleRangeBlur}
          onKeyDown={e => e.key === 'Enter' && handleRangeBlur()}
          className={inputCls}
          style={{ width: '48px' }}
          title="量程上限"
        />
      </div>

      {/* unit */}
      <input
        type="text"
        value={unit}
        onChange={e => setUnit(e.target.value)}
        onBlur={handleUnitBlur}
        onKeyDown={e => e.key === 'Enter' && handleUnitBlur()}
        className={inputCls.replace('text-right', 'text-left')}
        style={{ width: '44px' }}
        placeholder="单位"
        title="单位"
      />

      {/* strategy */}
      <select
        value={node.gen_strategy || ''}
        onChange={handleStrategyChange}
        className={selectCls}
        style={{ color: 'var(--text)', width: '110px' }}
        title="值生成策略">
        <option value="">自动</option>
        {strategies.map(s => (
          <option key={s.name} value={s.name}>{s.description || s.name}</option>
        ))}
      </select>
    </>
  )
})
