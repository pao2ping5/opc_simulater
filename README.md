# OPC 通用模拟器

> 读取 Excel 点表自动建模, 12 种值生成策略模拟工业设备数据, Web 控制台行内编辑节点元数据, REST API 供外部消费.

## 用途

无真实 OPC 设备时驱动整个综合采矿监控系统: 替代采煤机/支架/皮带/泵站等设备的 OPC UA 数据源, 让前端、采集程序、告警、分析等模块都能基于合理的模拟数据开发与演示.

> **注意**: 本模拟器的 `opcua.py` 是 in-process mock shim, **不监听 `opc.tcp://` 协议**, 不接受真实 OPC UA 客户端连接. 真正的对外接口是 REST API (`http://localhost:18480/api/*`).

## 特性

- **Excel 点表自动建模** — 读 `node_id`/`data_type`/`range_lo/hi`/`unit`/`gen_strategy`/`gen_params` 等列, dot 分层构建地址空间 (`Shearer.left_motor.current` → `Shearer/LeftMotor/Current` 三级 folder)
- **12 种值生成策略** — 均匀/正态/正弦/随机游走/斜坡/计数器/恒定/布尔翻转 + 电流/温度/压力/转速 4 种设备专用
- **Web 控制台 (React 19 + Vite + TanStack Virtual)** — 1674 节点虚拟滚动, 行内编辑元数据, 模式切换, 批量操作
- **REST API** — 节点查询/值轮询/模式切换/元数据更新/模型上传导出
- **可选 Bearer token 鉴权** — `OPC_API_TOKEN` 环境变量启用
- **断网友好** — 默认绑 `127.0.0.1`, CORS 白名单, 请求大小上限
- **80 个 pytest 测试** — 策略数学/Excel 解析/JSON 往返/HTTP 处理器全覆盖

## 快速开始

### 后端

```bash
cd opc_simulator
pip install -r requirements.txt   # opcua, openpyxl

# 默认读 ../opc_list_test.xlsx
python web_server.py
```

启动后:
- Web 控制台: http://127.0.0.1:18480
- REST API: http://127.0.0.1:18480/api/nodes
- 健康检查: http://127.0.0.1:18480/api/health

### 前端 (开发模式)

```bash
cd opc_simulator/frontend
npm install
npm run dev      # Vite dev server, HMR, 自动代理 /api 到 :18480
npm run build    # 产出 frontend/dist/, 由 web_server.py 静态托管
```

### CLI 模式 (无 Web 控制台)

```bash
python server.py [--xlsx path/to/model.xlsx]
# 仅启动 OPC 模拟循环, 同时生成客户端点表 opc_sim_list.xlsx
```

## Excel 点表格式

首行表头, 支持中英文别名. 必填列: `node_id`, `data_type`. 其余可选:

| 列 | 别名 | 说明 |
|----|------|------|
| `node_id` | — | dot 分层路径, 如 `Shearer.left_motor.current` |
| `data_type` | — | `float` / `int` / `bool` / `string` |
| `range_lo` / `range_hi` | `rangelo` / `rangehi` / `低限` / `高限` / `min` / `max` | 量程范围 |
| `unit` | `单位` | 工程单位 (`A` / `MPa` / `rpm`...) |
| `gen_strategy` | `strategy` / `策略` | 见下表, 留空按 data_type 自动选择 |
| `gen_params` | `params` / `策略参数` | JSON 字符串, 如 `{"center_ratio":0.6}` |
| `description` | `描述` / `备注` | 自由文本 |
| `instance_count` | `实例数` / `数量` | >1 时按 `_000`/`_001`... 展开 |
| `display_name` | `显示名` / `别名` | OPC UA DisplayName 覆盖 |
| `group_depth` | `分组深度` | node_id 前几段作为分组, 默认 1 |

### 内置策略

| 名称 | 说明 | 典型用途 |
|------|------|----------|
| `random_uniform` | 均匀随机 | 通用 float/int |
| `random_normal` | 正态分布 | 传感器噪声 |
| `sinusoidal` | 正弦波 | 周期信号 |
| `random_walk` | 布朗运动 | 缓变过程 |
| `ramp` | 线性斜坡 | 累积量 |
| `counter` | 计数器 | 计件 |
| `constant` | 恒定值 | 设定值 (用 `gen_params.value`) |
| `binary_toggle` | 随机 0/1 | 布尔信号 |
| `random_current` | 电机电流仿真 | 60% 中心 + 抖动 |
| `random_temp` | 温度仿真 | 40% 中心 + 小抖动 |
| `random_pressure` | 压力仿真 | 50% 中心 + 微抖动 |
| `random_speed` | 转速仿真 | 70% 中心 + 微抖动 |

`data_type` 自动映射: `bool→binary_toggle`, `string→constant`, `int/float→random_uniform`.

## REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 (无需鉴权) |
| GET | `/api/nodes` | 全量节点 + 当前值 + 元数据 |
| GET | `/api/values` | 轻量值轮询 (flat `{node_id: value}`) |
| GET | `/api/strategies` | 策略列表 |
| GET | `/api/model/export` | 导出当前模型 |
| POST | `/api/set_mode` | 切单节点模式 `{unique_key, mode}` |
| POST | `/api/set_value` | 设手动值 `{unique_key, value}` |
| POST | `/api/set_all_mode` | 全部切模式 `{mode}` |
| POST | `/api/model/upload` | 上传 Excel (multipart 或 `{file_path}`) |
| PATCH | `/api/nodes/{node_id}/meta` | 更新节点元数据 |
| PATCH | `/api/nodes/batch` | 批量更新元数据 |

启用鉴权时 (除 `/api/health`) 需带 `Authorization: Bearer <OPC_API_TOKEN>` 头.

## 配置 (环境变量)

| 变量 | 默认 | 说明 |
|------|------|------|
| `OPC_POINT_TABLE` | `../opc_list_test.xlsx` | 默认点表路径 |
| `OPC_WEB_HOST` | `127.0.0.1` | Web 绑定地址, 容器部署设 `0.0.0.0` |
| `OPC_API_TOKEN` | (空) | 启用 Bearer token 鉴权 |
| `OPC_CORS_ORIGIN` | (空) | CORS 白名单, 逗号分隔, `*` 全开 (不推荐) |
| `OPC_STRATEGY_COUNT` | `12` | gen_preview.py 显示用策略数 |
| `OPC_PREVIEW_NODE_LIMIT` | `20` | gen_preview.py 渲染节点上限 |

## 测试

```bash
cd opc_simulator
python -m pytest tests/ -v
# 80 passed in ~1.4s
```

测试覆盖:
- `test_strategies.py` — 12 策略返回值在范围 + 除零边缘 + 类型强转 + resolve 默认选择
- `test_model.py` — Excel 解析/别名/缺列/范围交换 + instance 展开 + JSON 往返 + 原子写
- `test_simulator.py` — setup/tick/mode/value/snapshot/meta/batch/reload 全流程
- `test_web_server.py` — multipart 解析/路径白名单/consteq/_check_auth 各种 token 场景

## 项目结构

```
opc_simulator/
├── app_config.py        # 配置 + 环境变量 + 日志
├── helpers.py           # ThreadingHTTPServer / MIME / multipart / 路径与 token 工具
├── static.py            # SPA 静态文件服务 + 路径穿越防护
├── api_handler.py       # APIHandler (REST 端点 + 上传 + 鉴权 + CORS)
├── simulator.py         # GenericOPCSimulator (web_server 与 server 共用)
├── common.py            # 数据模型 + 策略注册表 + Excel/JSON IO
├── opcua.py             # OPC UA mock shim (in-process, 不监听 opc.tcp://)
├── web_server.py        # Web 入口 (main)
├── server.py            # CLI 入口 + 客户端点表生成
├── test_client.py       # REST 测试客户端 (替代坏掉的 OPC UA client)
├── gen_preview.py       # 静态预览 HTML 生成器
├── tests/               # 80 个 pytest 测试
└── frontend/            # React SPA
    ├── src/
    │   ├── App.jsx
    │   ├── api/index.js
    │   ├── hooks/       # useNodes / useFilteredNodes / useMediaQuery / useStrategies
    │   ├── components/  # Header / Stats / TabBar / NodeTable / NodeCard / ...
    │   └── utils/       # nodeLabel
    ├── package.json
    └── vite.config.js
```

## 浏览地址

- **Web 控制台**: http://127.0.0.1:18480
- **API 文档 (本 README)**: 见上节 REST API 表
- **设计系统**: [frontend/DESIGN.md](frontend/DESIGN.md)
