import { memo } from 'react'

export const Stats = memo(function Stats({ stats }) {
  const randomPercent = stats.total > 0 ? Math.round(stats.random / stats.total * 100) : 0
  const manualPercent = stats.total > 0 ? Math.round(stats.manual / stats.total * 100) : 0

  return (
    <>
      {/* 移动端：单条摘要卡 */}
      <div
        className="sm:hidden rounded-xl p-3 border mb-4"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div>
            <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>总节点</div>
            <div className="text-2xl font-bold font-mono" style={{ color: 'var(--text)' }}>{stats.total}</div>
          </div>
          <div>
            <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>随机</div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold font-mono" style={{ color: 'var(--cyan)' }}>{stats.random}</span>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{randomPercent}%</span>
            </div>
          </div>
          <div>
            <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>手动</div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold font-mono" style={{ color: 'var(--orange)' }}>{stats.manual}</span>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{manualPercent}%</span>
            </div>
          </div>
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs w-8 shrink-0" style={{ color: 'var(--cyan)' }}>随机</span>
            <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
              <div className="h-full rounded-full" style={{ width: `${randomPercent}%`, background: 'var(--cyan)' }} />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs w-8 shrink-0" style={{ color: 'var(--orange)' }}>手动</span>
            <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
              <div className="h-full rounded-full" style={{ width: `${manualPercent}%`, background: 'var(--orange)' }} />
            </div>
          </div>
        </div>
      </div>

      {/* 桌面端：三卡布局 */}
      <div className="hidden sm:grid grid-cols-3 gap-3 mb-4">
        <StatCard label="总节点" value={stats.total} color="var(--text)" />
        <StatCard
          label="随机模式"
          value={stats.random}
          percent={randomPercent}
          color="var(--cyan)"
          iconColor="var(--cyan)"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
              <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          }
        />
        <StatCard
          label="手动模式"
          value={stats.manual}
          percent={manualPercent}
          color="var(--orange)"
          iconColor="var(--orange)"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--orange)" strokeWidth="2">
              <path d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" />
            </svg>
          }
        />
      </div>
    </>
  )
})

const StatCard = memo(function StatCard({ label, value, percent, color, icon }) {
  return (
    <div
      className="rounded-xl p-4 border"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</span>
        {icon || (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
        )}
      </div>
      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold font-mono" style={{ color }}>{value}</span>
        {percent !== undefined && (
          <span className="text-sm mb-1" style={{ color: 'var(--text-muted)' }}>{percent}%</span>
        )}
      </div>
      {percent !== undefined && (
        <div className="mt-3 h-1 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
          <div className="h-full rounded-full transition-all" style={{ width: `${percent}%`, background: color }} />
        </div>
      )}
    </div>
  )
})
