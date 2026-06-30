import { useState, memo } from 'react'
import { ConfirmDialog } from './ConfirmDialog'

export const Header = memo(function Header({ stats, onSetAllMode }) {
  const [pendingMode, setPendingMode] = useState(null)

  const handleConfirm = async () => {
    if (!pendingMode) return
    const mode = pendingMode
    // Optimistically close the dialog so the user gets immediate feedback.
    // If the API call fails, onSetAllMode (which calls useNodes.handleSetAllMode)
    // will surface the error via the top-level ErrorBar.
    setPendingMode(null)
    try {
      await onSetAllMode(mode)
    } catch {
      // Error already surfaced via useNodes error state; nothing to do here.
    }
  }

  const modeLabel = pendingMode === 'random' ? '随机' : '手动'

  return (
    <>
      <header
        className="sticky top-0 z-50 border-b"
        style={{
          background: 'rgba(17, 24, 34, 0.92)',
          backdropFilter: 'blur(12px)',
          borderColor: 'var(--border)',
        }}>
        <div className="max-w-[1400px] mx-auto px-3 sm:px-6 py-3 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'var(--surface2)', border: '1px solid var(--border-light)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div className="min-w-0">
              <h1 className="text-sm font-semibold tracking-wide truncate" style={{ color: 'var(--text)' }}>
                OPC 模拟器
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 shrink-0">
            <div
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg"
              style={{ background: 'var(--surface2)', border: '1px solid var(--border)' }}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--cyan)' }} />
              <span className="text-xs font-medium whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>
                运行中 · {stats.total} 节点
              </span>
            </div>

            <div className="flex gap-1 sm:gap-1.5">
              <button
                onClick={() => setPendingMode('random')}
                className="px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer whitespace-nowrap"
                style={{
                  background: 'transparent',
                  color: 'var(--cyan)',
                  border: '1px solid rgba(0,212,170,0.35)',
                }}>
                全部随机
              </button>
              <button
                onClick={() => setPendingMode('manual')}
                className="px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer whitespace-nowrap"
                style={{
                  background: 'transparent',
                  color: 'var(--orange)',
                  border: '1px solid rgba(245,158,11,0.35)',
                }}>
                全部手动
              </button>
            </div>
          </div>
        </div>
      </header>

      <ConfirmDialog
        open={pendingMode !== null}
        title="确认批量操作"
        message={`将把全部 ${stats.total} 个节点切换为${modeLabel}模式，此操作不可撤销，是否继续？`}
        confirmLabel={`切换为${modeLabel}`}
        variant={pendingMode === 'manual' ? 'manual' : 'default'}
        onConfirm={handleConfirm}
        onCancel={() => setPendingMode(null)}
      />
    </>
  )
})
