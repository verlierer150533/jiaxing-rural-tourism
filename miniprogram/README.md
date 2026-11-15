# 小程序端（Uni-app）

《基于 WebGIS 与多端协同的海宁乡村农文旅服务平台》移动端，编译目标为微信小程序，同时可编译 H5 便于浏览器预览。

## 一、功能对应关系

| 模块 | 小程序端表现 | 对应后台 |
|---|---|---|
| 资源展示 | 首页热门推荐、资源列表分类浏览 | 资源管理 |
| 空间导览 | 地图页加载海宁市农文旅点位、分类筛选、点击 marker 弹卡片、一键导航 | 经纬度维护 |
| 详情与导流 | 详情页展示简介/坐标，外链按钮点击后复制链接（无站内支付） | 外链字段 |
| 行为埋点 | 进入详情自动上报 `view`，点击外链上报 `click_external` | 实时大屏 |
| 游客标识 | 本地生成设备会话号 `session_id`，用于后台 UV 去重 | 大屏 UV 指标 |

## 二、运行方式

### 1. 微信开发者工具（主目标）

```bash
cd miniprogram
npm install
npm run dev:mp-weixin      # 或 npm run build:mp-weixin
```

用微信开发者工具导入 `miniprogram/dist/dev/mp-weixin`（构建产物为 `dist/build/mp-weixin`），
在「详情 → 本地设置」中勾选 **不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书**，
否则 `http://127.0.0.1:5000` 的请求会被拦截。

> `src/manifest.json` 中的 `mp-weixin.appid` 当前为测试号 `touristappid`，正式预览请替换为自己的 AppID。

### 2. H5 预览（快速看界面）

```bash
npm run dev:h5
```

浏览器访问 Vite 输出的地址即可。注意：H5 下 `<map>` 组件需要配置腾讯地图 key（`manifest.json → h5.sdkConfigs.maps.qqmap.key`），
未配置时地图页为空白，其余页面不受影响。

## 三、后端地址

统一在 `src/config.js` 中修改：

```js
export const BASE_URL = 'http://127.0.0.1:5000/api'
```

真机调试时需把 `127.0.0.1` 换成局域网 IP（如 `http://192.168.1.10:5000/api`），并确保后端以 `0.0.0.0` 监听（当前 `app.py` 已如此）。

## 四、埋点约定

| 行为 | action | target_type | 触发时机 |
|---|---|---|---|
| 进入详情页 | `view` | `attraction` | `onLoad` 成功拿到详情后 |
| 点击外链 | `click_external` | `attraction` | 复制外链之前 |

埋点请求失败**静默忽略**（`utils/track.js`），不会打断游客浏览。

## 五、已知限制

1. 微信小程序不允许直接打开第三方商城链接，故外链采用「复制 + 提示」方案；若后续配置了业务域名，可改为 `web-view` 页面承载。
2. 地图坐标为公开地图初值，与微信地图（GCJ-02）存在数十至数百米偏移，正式上线前应统一坐标系并做一次人工校准。
3. 当前无登录体系，游客免注册；设备会话号仅用于 UV 统计，不采集个人身份信息。
