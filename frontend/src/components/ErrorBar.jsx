import { memo } from 'react'

/**
 * Top-of-page error banner for non-fatal runtime errors surfaced by
 * ``useNodes.error`` (network failures, API errors, etc.).  Dismissible
 * via the ``onDismiss`` prop.  Returns ``null`` when ``error`` is empty.
 */
export const ErrorBar = memo(function ErrorBar({ error, onDismiss }) {
  if (!error) return null
  return (
    <div
      className="flex items-center justify-between gap-3 px-3 sm:px-4 py-2 border-b text-xs"
      style={{
        background: 'rgba(245, 158, 11, 0.12)',
        borderColor: 'var(--border)',
        color: 'var(--orange)',
      }}
      role="alert">
      <div className="flex items-center gap-2 min-w-0">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="shrink-0">
          <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
        <span className="truncate font-medium">{error}</span>
      </div>
      <button
        onClick={onDismiss}
        className="shrink-0 px-2 py-1 rounded text-xs cursor-pointer"
        style={{ background: 'var(--surface2)', color: 'var(--text-secondary)' }}
        aria-label="关闭错误提示">
        ✕
      </button>
    </div>
  )
})
