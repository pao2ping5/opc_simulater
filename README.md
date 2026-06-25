# OPC Simulator

煤矿综合监控系统 OPC UA 数据模拟器 — 用于开发和测试阶段替代真实 PLC 设备，提供完整的模拟数据流和可视化 Web 控制台。

## 功能特性

- **OPC UA 服务器** — 模拟 10 类采矿设备（采煤机、电液控、三机、皮带、泵站、供电、移变、开关、故障、设备启停）的全部点位数据
- **智能模拟算法** — 根据点位名称关键词（电流、温度、压力、转速、瓦斯浓度等）自动生成符合工程特征的波动数据
- **双模式切换** — 支持 `随机`（自动模拟）和 `手动`（指定固定值）两种工作模式，可对单个节点或全局批量切换
- **Web 控制台** — 内置 React 前端，桌面端虚拟化表格布局、移动端卡片布局，支持设备分类筛选和搜索
- **REST API** — 提供 HTTP 接口供外部系统查询节点状态和下发控制指令
- **Excel 点表驱动** — 从标准 Excel 点表自动读取点位信息，无需修改代码即可适配不同项目

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+（仅前端开发需要）

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务（带 Web 控制台）

```bash
python web_server.py
```

启动后访问：
- **Web 控制台**: http://localhost:18480
- **OPC UA 服务器**: `opc.tcp://localhost:14840/freeopcua/server/`

### 3. 仅启动 OPC 服务器（无 Web 界面）

```bash
python server.py
```

### 4. 前端开发模式

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务器会自动将 `/api` 请求代理到后端 `http://localhost:18480`。

## 项目结构

```
opc_simulater/
├── server.py              # 纯 OPC UA 模拟服务器
├── web_server.py          # OPC UA + HTTP Web 控制台（主入口）
├── test_client.py         # OPC UA 测试客户端
├── requirements.txt       # Python 依赖
├── opc_list_test.xlsx     # 设备点位表（10 类设备，1600+ 点位）
└── frontend/              # React 前端
    ├── src/
    │   ├── App.jsx        # 主布局（响应式：桌面表格 / 移动卡片）
    │   ├── api/           # HTTP API 客户端
    │   ├── hooks/         # 数据管理 hooks
    │   └── components/    # UI 组件
    ├── package.json
    └── vite.config.js
```

## 架构说明

```
┌─────────────────────────────────────────────┐
│              web_server.py                   │
│                                             │
│  opc_list_test.xlsx ──▶ MiningOPCSimulator  │
│                         ├── modes{}         │
│                         ├── manual_vals{}   │
│                         └── current_vals{}  │
│                              │              │
│                         ┌────┴────┐         │
│                         ▼         ▼         │
│                      OPC UA    HTTP API     │
│                      :14840    :18480       │
└─────────────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
         OPC 客户端            React 前端 (SPA)
        (Django 等)           手机 / PC 浏览器
```

### 模拟值生成逻辑

`generate_value()` 根据点位名称中的关键词自动选择模拟策略：

| 关键词 | 模拟行为 |
|--------|----------|
| 通讯 | 固定为 1（正常） |
| 运行/状态 | 周期性开关（75% 运行） |
| 电流 | 基值 ± 随机波动 + 正弦曲线 |
| 温度 | 45°C 附近波动，含缓慢漂移 |
| 压力 | 20 附近波动 |
| 瓦斯 | 0.05~0.20 低浓度范围 |
| 闭锁/急停 | 固定为 0（正常） |
| 其他 | 根据名称特征生成合理范围的随机值 |

### REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/nodes` | GET | 获取所有节点信息（分组、模式、当前值） |
| `/api/values` | GET | 获取所有节点的当前值 |
| `/api/set_mode` | POST | 切换单个节点模式 `{ "unique_key": "shearer/0", "mode": "manual" }` |
| `/api/set_value` | POST | 设置节点手动值 `{ "unique_key": "shearer/0", "value": 42.5 }` |
| `/api/set_all_mode` | POST | 批量切换所有节点模式 `{ "mode": "random" }` |

## 点表格式

项目使用 Excel 点表（`opc_list_test.xlsx`）定义设备点位，格式如下：

| 设备启停 | (地址) | 采煤机 | (地址) | 电液控 | (地址) | ... |
|----------|--------|--------|--------|--------|--------|-----|
| 1#采煤机通讯状态 | ns=... | 左滚筒电流 | ns=... | 1#支架压力 | ns=... | ... |
| 1#采煤机运行状态 | ns=... | 右滚筒电流 | ns=... | 1#支架高度 | ns=... | ... |

共 10 类设备，每类包含名称列和 OPC 地址列，点位数量约 1600+。

## 技术栈

**后端：**
- Python 3
- [opcua](https://github.com/FreeOpcUa/opcua-asyncio) — OPC UA 服务器/客户端
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel 读写
- http.server — 内置 HTTP 服务器

**前端：**
- React 19
- Vite 8
- Tailwind CSS 4
- [@tanstack/react-virtual](https://tanstack.com/virtual) — 虚拟化列表（支持 1600+ 节点流畅滚动）

## 许可证

MIT License
