# 基于 WebGIS 的海宁乡村农文旅服务平台设计与实现

面向海宁市乡村农文旅资源的「WebGIS 展示 + 多端协同 + 实时数据」服务平台。以一套 Flask 后端同时支撑 **Web 管理端**、**实时数据大屏** 与 **微信小程序游客端**，实现资源点位的地理可视化、内容运营、游客浏览行为采集与实时统计。

> 本科毕业设计作品 · 浙江越秀外国语学院 网络媒体学院 数字媒体技术

## 功能概览

| 端 | 主要功能 |
| --- | --- |
| Web 管理端 | 登录鉴权、运营概览、资源点位增删改查与上下架、多条件查询、实时数据大屏入口 |
| 实时数据大屏 | PV/UV 实时滚动、近 7 日趋势、热度排行、分类占比、镇街分布、GIS 点位地图，SocketIO 推送 + 断线退避重连 + 轮询兜底 |
| 微信小程序 | 首页推荐、地图导览（海宁边界 + 点位气泡）、资源列表筛选、详情介绍、收藏、外链导流与跳转埋点 |
| 后端服务 | 18 个 REST 接口、WebSocket 实时通道、JWT 鉴权、Redis 缓存与消息通道、日志埋点 |

## 技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | Python 3.12 · Flask 2.3 · Flask-SQLAlchemy · Flask-JWT-Extended · Flask-SocketIO（eventlet） |
| 数据 | MySQL 8.0（`jiaxing_rural`）· Redis 5.0（缓存 + Pub/Sub 消息通道） |
| Web 前端 | Vue 3 · Vite 5 · Element Plus · ECharts 5 · Leaflet 1.9 · socket.io-client |
| 小程序 | Uni-app 3（Vue 3 语法）编译至 `mp-weixin`，同时可编译 H5 |

## 目录结构

```
jiaxing-rural-tourism/
├─ web-backend/              # Flask 后端
│  ├─ app.py                 # 应用工厂、蓝图注册、SocketIO 启动（:5000）
│  ├─ config.py              # 全局配置（全部支持环境变量覆盖）
│  ├─ models.py              # admin / attraction / system_log / favorite
│  ├─ init_db.py             # 建库建表 + 种子数据（--demo 生成演示日志）
│  ├─ api/                   # auth / attraction / log / stats / favorite
│  ├─ ws/events.py           # namespace="/ws"，事件 new_data
│  ├─ utils/                 # 统一响应、鉴权装饰器、Redis 缓存
│  └─ tests/                 # ws_probe.py / bench.py / simulate_visitor.py
├─ web-frontend/             # Vue3 管理端 + 大屏（:5173）
│  ├─ src/views/             # login / dashboard / attraction / screen
│  ├─ src/components/        # GisMap.vue（Leaflet）、ChartPanel.vue
│  └─ public/gis/            # 海宁边界 GeoJSON（本地文件，断网可用）
├─ miniprogram/              # Uni-app 小程序 5 页
├─ docs/                     # 需求、设计、测试、说明书、开发日志、图件
├─ 说明文档/                  # 交付说明、开发 README、项目目标与约束
├─ data/gis/                 # 边界数据源
├─ tools/redis/              # Redis 5.0 便携版（一键启动用）
├─ 启动后端服务.bat           # 拉 Redis + 起 Flask
└─ 启动网页端.bat             # 起 Vite 并自动打开浏览器
```

## 快速开始

### 1. 环境

- Python 3.10+、Node.js 18+、MySQL 8.0（服务已启动，默认 `root` / 空密码 / `127.0.0.1:3306`）
- Redis 可选用：`tools/redis/redis-server.exe` 已随仓库提供，缺省时后端自动降级（功能不受影响，仅少了缓存）

### 2. 初始化数据库

```bash
cd web-backend
pip install -r requirements.txt
python init_db.py --demo          # 建库建表 + 12 个海宁点位 + 近 7 天演示日志
```

### 3. 启动

双击项目根目录的 `启动后端服务.bat`，再双击 `启动网页端.bat`，浏览器会自动打开 <http://127.0.0.1:5173>。

- 管理端账号：`admin` / `admin123`
- 健康检查：<http://127.0.0.1:5000/api/ping>（返回 `database`、`redis`、`async_mode` 等状态）

> `POST /api/auth/login` 与 `ws://127.0.0.1:5000/ws` 不能用浏览器直接打开，报错属正常。

### 4. 小程序

```bash
cd miniprogram
npm install
npm run build:mp-weixin           # 产物在 dist/build/mp-weixin
```

用微信开发者工具导入 `miniprogram/dist/build/mp-weixin` 即可预览；本地调试时在 `src/config.js` 中把接口地址指向 `http://127.0.0.1:5000`。

## 接口一览（18 个）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | 管理员登录，返回 JWT |
| GET | `/api/auth/profile` | 当前管理员信息 |
| PUT | `/api/auth/password` | 修改密码 |
| GET | `/api/attractions` | 前台资源列表（分页、关键词、类别、镇街） |
| GET | `/api/attractions/admin` | 后台资源列表 |
| GET | `/api/attractions/map` | 地图点位（Redis 缓存 60s） |
| GET | `/api/attractions/meta` | 类别 / 镇街字典（缓存 120s） |
| GET | `/api/attractions/<id>` | 资源详情（浏览量原子自增） |
| POST | `/api/attractions` | 新增资源 |
| PUT | `/api/attractions/<id>` | 编辑资源 |
| DELETE | `/api/attractions/<id>` | 删除资源 |
| PUT | `/api/attractions/<id>/status` | 上架 / 下架 |
| POST | `/api/log` | 埋点上报（PV/UV、行为类型） |
| GET | `/api/logs` | 访问日志分页查询 |
| GET | `/api/stats/overview` | 大屏统计指标 |
| POST | `/api/favorite` | 收藏 / 取消收藏（设备会话维度） |
| GET | `/api/favorite` | 我的收藏列表 |
| GET | `/api/favorite/check` | 是否已收藏 |

实时通道：Socket.IO `namespace="/ws"`，`connect` 时返回当前统计快照，数据变化时广播 `new_data`。

## 测试与性能

- 功能测试：34 条用例通过，覆盖鉴权、资源 CRUD、埋点、统计、收藏、实时推送与异常分支（详见 `docs/04_系统测试报告.md`）。
- 压测（每场景 200 请求 / 10 并发）：资源列表 154.3 RPS（平均 60.5 ms，P95 77.9 ms）；地图接口在 Redis 缓存下 513.7 RPS（18.0 ms，P95 32.3 ms），吞吐约 3.3 倍、延迟下降约 70%；埋点写入 62.4 RPS（158.2 ms），错误数均为 0。

## 文档

| 文件 | 内容 |
| --- | --- |
| `docs/01_需求分析与竞品分析.md` | 调研结论、竞品矩阵、功能需求 |
| `docs/02_多端功能对照表.md` | 16 项功能 × 4 端映射与一致性机制 |
| `docs/03_系统功能结构图与核心业务流程.md` | 功能结构树、6 张流程图、数据流 |
| `docs/04_系统测试报告.md` | 34 条用例、缺陷记录 |
| `docs/05_作品说明书.md` | 作品说明书全文 |
| `docs/06_开发日志与踩坑记录.md` | 各阶段开发记录与问题复盘 |
| `docs/figures/` | 功能结构图、时序图、流程图 |
| `说明文档/作品说明文档.md` | 交付说明、启动方式、FAQ |

## 设计要点

- **多端一致**：一套后端、统一响应结构（`{code, message, data}`）与同一套资源模型，Web 与小程序读写同一份数据。
- **实时性**：埋点写库后经 SocketIO 广播，大屏即时刷新；Redis Pub/Sub 保证多进程下消息可达。
- **可用性兜底**：Redis 不可用时自动跳过缓存直接查库；WebSocket 断线按 1s→8s 指数退避重连，并以 15s 轮询兜底。
- **离线可演示**：海宁边界与点位数据本地化，不依赖在线瓦片服务。

## 说明

本项目为教学与毕业设计用途，资源数据为海宁市公开信息的整理示例，购买链接仅作跳转展示，平台不参与交易与资金流转。
