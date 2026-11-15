# 海宁乡村农文旅服务平台

> **本文件位于 `jiaxing-rural-tourism\说明文档\` 子目录。**
> 文中所有相对路径（如 `cd web-backend`）都以**项目根目录**（即本文件的上一级 `jiaxing-rural-tourism\`）为基准执行。
> 日常启动建议直接双击根目录下的 `启动后端服务.bat` 与 `启动网页端.bat`。

> 本科毕业设计作品 · 浙江越秀外国语学院 网络传播学院 数字媒体技术
> \*\*基于WebGIS的海宁乡村农文旅服务平台设计与实现\*\*
> 学生：许焱飞（2333700）　指导教师：于宁宁

## 一、作品定位

以海宁市为空间范围，做「Web 管理后台 + 微信小程序」双端协同的乡村农文旅信息平台：
后台负责资源维护与数据大屏监控，小程序负责游客浏览与地图导览，两端共用同一套后端与数据库。
**全平台不做在线支付**，农产品/商品仅展示并提供外链导流。

## 二、技术栈

|层|技术|
|-|-|
|后端|Flask 2.3 + SQLAlchemy + Flask-JWT-Extended + Flask-SocketIO（eventlet）|
|数据|MySQL 8.0（业务库） + Redis 5（缓存 + SocketIO 消息通道）|
|Web 端|Vue3 + Vite + Element Plus + ECharts + Leaflet|
|小程序端|Uni-app（Vue3）+ 微信原生 `<map>` 组件|

## 三、目录

```
jiaxing-rural-tourism/
├─ web-backend/      Flask 后端（API + WebSocket + 初始化脚本 + 测试探针）
├─ web-frontend/     Vue3 管理后台 + 实时数据大屏
├─ miniprogram/      Uni-app 小程序（可编译 H5）
├─ data/gis/         海宁市 / 嘉兴市 GeoJSON 底图
└─ .gitignore
```

## 四、启动步骤（本地开发）

> \*\*最快的方式\*\*：双击项目根目录下的两个批处理文件即可 ——
> `启动后端服务.bat`（自动拉起 Redis + Flask），再双击 `启动网页端.bat`（自动开浏览器）。
> 下面是不用 bat 时的等价手工步骤。

### 1\. 数据库

MySQL 8.0 需已启动，账号 `root` / 空密码（可在 `web-backend/config.py` 用环境变量改）。

```powershell
cd web-backend
python init\_db.py --demo --reset-logs   # 建库建表 + 管理员 + 12 个点位 + 近 7 天演示日志
```

> 不带 `--demo` 只做结构与基础数据；`--reset-logs` 会先清空 `system\_log`。

### 2\. Redis（可选但推荐）

```powershell
tools\\redis\\redis-server.exe --port 6379 --bind 127.0.0.1 --save 3600 1
```

未启动 Redis 时后端仍可正常工作，只是失去地图点位缓存与跨进程广播能力（`/api/ping` 中 `redis` 为 `false`）。

### 3\. 后端

```powershell
cd web-backend
python app.py
# http://127.0.0.1:5000/api/ping
```

### 4\. Web 管理端

```powershell
cd web-frontend
npm install
npm run dev
# http://127.0.0.1:5173  账号 admin / admin123
```

大屏为独立全屏页：`http://127.0.0.1:5173/screen`

> 若 `npm run build` 报 `esbuild ... Access is denied`，把 `TEMP` 指到项目内目录再构建：
> `$env:TEMP='./.tmp'; $env:TMP='./.tmp'; npm run build`

### 5\. 小程序端

```powershell
cd miniprogram
npm install
npm run dev:mp-weixin
```

微信开发者工具导入 `miniprogram/dist/dev/mp-weixin`，勾选「不校验合法域名」。
真机调试时把 `src/config.js` 的 `127.0.0.1` 换成局域网 IP。

## 五、核心链路

```
小程序浏览详情 ──POST /api/log──► system\_log 落库
                                  ├─ attraction.view\_count +1（原子自增）
                                  ├─ 今日 PV/UV/外链点击 实时统计
                                  └─ SocketIO 经 Redis Pub/Sub 广播 new\_data
                                              ▼
                          Web 大屏（/ws 订阅）ECharts + KPI 实时跳动
```

## 六、主要接口

|方法|路径|鉴权|说明|
|-|-|-|-|
|GET|`/api/ping`|-|健康检查（含 Redis / WebSocket 状态）|
|POST|`/api/auth/login`|-|管理员登录，返回 JWT|
|GET|`/api/attractions`|-|上架资源列表（关键词/类别/镇街/分页）|
|GET|`/api/attractions/<id>`|-|资源详情|
|GET|`/api/attractions/map`|-|地图点位（Redis 缓存 60s）|
|GET|`/api/attractions/meta`|-|类别与镇街聚合（缓存 120s）|
|GET|`/api/attractions/admin`|JWT|后台列表（含下架）|
|POST/PUT/DELETE|`/api/attractions...`|JWT|资源增删改、上下架|
|POST|`/api/log`|-|浏览足迹上报（触发实时广播）|
|GET|`/api/logs`|JWT|足迹查询|
|GET|`/api/stats/overview`|JWT|大屏首屏统计|

WebSocket：命名空间 `/ws`，事件 `new\_data`。

## 七、验证脚本

```powershell
cd web-backend
python tests\\ws\_probe.py                       # 直连后端验证实时推送
$env:PROBE\_BASE='http://127.0.0.1:5173'; python tests\\ws\_probe.py   # 经 Vite 代理验证
```

## 八、已知限制

1. 资源坐标取自公开地图初值，与微信地图（GCJ-02）存在偏移，正式发布前需统一坐标系并人工校准。
2. 微信小程序不允许直接打开第三方商城链接，外链以「复制 + 提示」方式导流。
3. 本机无 Docker，部署章节以本地进程方式演示；容器化脚本待补充。

