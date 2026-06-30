import { Component } from 'react'

/**
 * Top-level error boundary — catches any uncaught render error in the
 * subtree and shows a fallback message instead of a white screen.
 *
 * Does not catch errors in event handlers, async code, or effects — those
 * are surfaced via the ``useNodes`` error state and a top-level error bar.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('Uncaught render error:', error, info)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      const message = this.state.error?.message || String(this.state.error || '未知错误')
      return (
        <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'var(--bg)' }}>
          <div
            className="max-w-md w-full rounded-xl border p-6"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h2 className="text-base font-semibold mb-2" style={{ color: 'var(--orange)' }}>
              页面渲染出错
            </h2>
            <p className="text-xs font-mono mb-4 p-3 rounded" style={{
              background: 'var(--bg)',
              color: 'var(--text-muted)',
              wordBreak: 'break-all',
            }}>
              {message}
            </p>
            <button
              onClick={this.handleReset}
              className="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer"
              style={{ background: 'var(--cyan)', color: '#000' }}>
              重试
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
