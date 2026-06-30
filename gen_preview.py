"""Generate a self-contained preview HTML from the running API.

Pulls live data from the simulator's REST API and renders a single static
HTML snapshot.  All paths/URLs are configurable via CLI args or env vars —
no hardcoded localhost or absolute Windows paths.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_API_URL = os.environ.get("OPC_API_URL", "http://localhost:18480/api/nodes")
DEFAULT_OUT_PATH = SCRIPT_DIR / "frontend" / "dist" / "preview.html"
DEFAULT_STRATEGY_COUNT = int(os.environ.get("OPC_STRATEGY_COUNT", "12"))
DEFAULT_NODE_LIMIT = int(os.environ.get("OPC_PREVIEW_NODE_LIMIT", "20"))


def fetch_nodes(api_url: str, timeout: float = 10.0) -> list:
    with urllib.request.urlopen(api_url, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from {api_url}")
        return json.loads(resp.read().decode("utf-8"))


def build_html(groups: list, total: int, strategy_count: int, node_limit: int) -> str:
    html = (
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OPC 通用模拟器预览</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
.header { background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; }
.header h1 { font-size: 22px; font-weight: 700; }
.header p { color: #94a3b8; margin-top: 4px; font-size: 13px; }
.stats { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
.stat { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px 16px; min-width: 100px; }
.stat-val { font-size: 20px; font-weight: 700; color: #38bdf8; }
.stat-label { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; flex-wrap: wrap; }
.tab { padding: 8px 16px; border-radius: 8px; font-size: 13px; cursor: pointer; border: 1px solid #334155; background: #1e293b; color: #94a3b8; }
.tab.active { background: #38bdf8; color: #0f172a; border-color: #38bdf8; font-weight: 600; }
.tab .count { font-size: 10px; opacity: 0.7; }
.table { background: #1e293b; border: 1px solid #334155; border-radius: 12px; overflow: hidden; }
.th { display: flex; padding: 10px 16px; background: #0f172a; font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.5px; }
.th > * { flex-shrink: 0; }
.row { display: flex; padding: 8px 16px; border-bottom: 1px solid #1e293b; font-size: 13px; align-items: center; }
.row:last-child { border-bottom: none; }
.row:hover { background: #0f172a; }
.col-name { flex: 1; min-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-type { width: 64px; text-align: center; color: #94a3b8; font-size: 11px; }
.col-range { width: 140px; text-align: center; color: #94a3b8; font-size: 11px; }
.col-unit { width: 56px; text-align: center; color: #64748b; font-size: 11px; }
.col-strategy { width: 130px; text-align: center; }
.col-mode { width: 80px; text-align: center; }
.col-value { width: 140px; text-align: right; font-weight: 700; font-variant-numeric: tabular-nums; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; }
.badge-random { background: rgba(56,189,248,0.15); color: #38bdf8; }
.badge-manual { background: rgba(251,146,60,0.15); color: #fb923c; }
.badge-strategy { background: rgba(168,85,247,0.15); color: #c084fc; }
.bar { width: 2px; height: 36px; margin-right: 8px; border-radius: 1px; }
.bar-random { background: #38bdf8; }
.bar-manual { background: #fb923c; }
.node-id { font-size: 10px; color: #475569; margin-top: 2px; font-family: monospace; }
.footer { margin-top:20px; text-align:center; color:#475569; font-size:11px; }
</style>
</head>
<body>
<div class="header">
  <h1>OPC 通用模拟器</h1>
  <p>通用 OPC UA 数据源 — 上传点表 Excel，自动建模生成模拟数据</p>
  <div class="stats">
    <div class="stat"><div class="stat-val">"""
        + str(total)
        + """</div><div class="stat-label">节点总数</div></div>
    <div class="stat"><div class="stat-val">"""
        + str(len(groups))
        + """</div><div class="stat-label">设备分组</div></div>
    <div class="stat"><div class="stat-val">"""
        + str(sum(1 for g in groups for n in g["nodes"] if n["mode"] == "random"))
        + """</div><div class="stat-label">随机模式</div></div>
    <div class="stat"><div class="stat-val">"""
        + str(strategy_count)
        + """</div><div class="stat-label">值生成策略</div></div>
  </div>
</div>

<div class="tabs">
"""
    )
    for i, g in enumerate(groups):
        active = " active" if i == 0 else ""
        html += '  <div class="tab{}">{} <span class="count">({})</span></div>\n'.format(
            active, g["label"], g["count"]
        )

    html += """
</div>

<div class="table">
  <div class="th">
    <div class="bar" style="background:transparent;"></div>
    <div class="col-name">节点名称</div>
    <div class="col-type">类型</div>
    <div class="col-range">量程范围</div>
    <div class="col-unit">单位</div>
    <div class="col-strategy">策略</div>
    <div class="col-mode">模式</div>
    <div class="col-value">当前值</div>
  </div>
"""
    idx = 0
    for g in groups:
        for n in g["nodes"]:
            mode = n.get("mode", "random")
            bar_cls = "bar-random" if mode == "random" else "bar-manual"
            val = n.get("value", 0)
            badge_cls = "badge-random" if mode == "random" else "badge-manual"
            mode_text = "随机" if mode == "random" else "手动"

            if n["data_type"] == "bool":
                val_str = "ON" if val else "OFF"
            elif n["data_type"] == "int":
                val_str = str(int(val))
            else:
                val_str = f"{val:.2f}"

            strat = n.get("gen_strategy", "auto")
            unit = n.get("unit", "")
            rlo = n.get("range_lo", 0)
            rhi = n.get("range_hi", 0)
            dtype = n.get("data_type", "float")

            html += '  <div class="row">\n'
            html += f'    <div class="bar {bar_cls}"></div>\n'
            html += '    <div class="col-name">{}<div class="node-id">{}</div></div>\n'.format(
                n.get("display_name") or n.get("node_id", "?"), n.get("node_id", "")
            )
            html += f'    <div class="col-type">{dtype}</div>\n'
            html += f'    <div class="col-range">{rlo} ~ {rhi}</div>\n'
            html += f'    <div class="col-unit">{unit}</div>\n'
            html += f'    <div class="col-strategy"><span class="badge badge-strategy">{strat}</span></div>\n'
            html += f'    <div class="col-mode"><span class="badge {badge_cls}">{mode_text}</span></div>\n'
            html += f'    <div class="col-value">{val_str}</div>\n'
            html += "  </div>\n"
            idx += 1
            if idx >= node_limit:
                break
        if idx >= node_limit:
            break

    if total > node_limit:
        html += f'  <div class="row" style="justify-content:center;color:#64748b;padding:12px;">... 还有 {total - node_limit} 个节点 ...</div>\n'

    html += """</div>

<div class="footer">
  OPC 通用模拟器 &middot; 实时运行中 &middot; api/nodes · api/values · api/strategies
</div>
</body>
</html>"""
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate preview HTML from OPC simulator API")
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="API base URL (default: %(default)s, env: OPC_API_URL)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_PATH,
        help="Output HTML path (default: %(default)s)",
    )
    parser.add_argument(
        "--strategy-count",
        type=int,
        default=DEFAULT_STRATEGY_COUNT,
        help="Strategy count for stat display (env: OPC_STRATEGY_COUNT)",
    )
    parser.add_argument(
        "--node-limit",
        type=int,
        default=DEFAULT_NODE_LIMIT,
        help="Max nodes to render (env: OPC_PREVIEW_NODE_LIMIT)",
    )
    args = parser.parse_args()

    try:
        data = fetch_nodes(args.api_url)
    except Exception as e:
        print(f"Error fetching API at {args.api_url}: {e}", file=sys.stderr)
        print("Is the simulator running? Try: python web_server.py", file=sys.stderr)
        sys.exit(1)

    groups = [
        {
            "key": g["key"],
            "label": g["label"],
            "count": len(g["nodes"]),
            "nodes": g["nodes"],
        }
        for g in data
    ]
    total = sum(g["count"] for g in groups)
    html = build_html(groups, total, args.strategy_count, args.node_limit)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Generated preview: {total} nodes, {len(groups)} groups -> {args.out}")


if __name__ == "__main__":
    main()
