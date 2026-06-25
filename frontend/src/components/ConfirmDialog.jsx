import { memo, useEffect } from 'react'

export const ConfirmDialog = memo(function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = '确认',
  onConfirm,
  onCancel,
  variant = 'default',
}) {
  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onCancel])

  if (!open) return null

  const confirmStyle = variant === 'danger'
    ? { background: 'var(--danger)', color: '#fff' }
    : variant === 'manual'
      ? { background: 'var(--orange)', color: '#000' }
      : { background: 'var(--cyan)', color: '#000' }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title">
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.6)' }} />
      <div
        className="relative w-full max-w-sm rounded-xl border p-5 shadow-2xl"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        onClick={e => e.stopPropagation()}>
        <h2 id="confirm-dialog-title" className="text-base font-semibold mb-2" style={{ color: 'var(--text)' }}>
          {title}
        </h2>
        <p className="text-sm mb-5 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          {message}
        </p>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors"
            style={{ background: 'var(--surface2)', color: 'var(--text)', border: '1px solid var(--border)' }}>
            取消
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-opacity hover:opacity-90"
            style={confirmStyle}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
})
