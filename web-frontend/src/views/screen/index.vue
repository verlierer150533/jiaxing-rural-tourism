<template>
  <div class="screen">
    <header class="screen-header">
      <div class="header-side">
        <el-button link class="back" @click="router.push('/dashboard')">← 返回后台</el-button>
      </div>
      <div class="header-title">
        <h1>海宁乡村农文旅服务平台 · 实时数据大屏</h1>
        <p>数据来源：小程序端浏览足迹 · WebSocket 实时推送</p>
      </div>
      <div class="header-side right">
        <span class="clock">{{ clock }}</span>
        <span class="ws-status" :class="wsConnected ? 'on' : 'off'">
          <i></i>{{ wsConnected ? 'WebSocket 已连接' : '连接中断，重连中' }}
        </span>
      </div>
    </header>

    <section class="kpi-row">
      <div v-for="item in kpiList" :key="item.key" class="kpi" :class="{ pulse: pulseKey === item.key }">
        <div class="kpi-label">{{ item.label }}</div>
        <div class="kpi-value">{{ item.value }}</div>
        <div class="kpi-hint">{{ item.hint }}</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel span-2">
        <div class="panel-title">今日分时浏览量（PV）</div>
        <ChartPanel :option="hourlyOption" height="240px" />
      </div>

      <div class="panel">
        <div class="panel-title">资源类别分布</div>
        <ChartPanel :option="categoryOption" height="240px" />
      </div>

      <div class="panel span-2">
        <div class="panel-title">海宁市农文旅资源空间分布</div>
        <GisMap :markers="markers" height="300px" dark />
      </div>

      <div class="panel">
        <div class="panel-title">
          实时足迹
          <span class="live-dot"></span>
        </div>
        <ul class="feed">
          <li v-for="item in feed" :key="item.uid" class="feed-item">
            <span class="feed-time">{{ item.time }}</span>
            <span class="feed-action" :class="item.action">{{ actionText(item.action) }}</span>
            <span class="feed-name">{{ item.name || '未知资源' }}</span>
            <span class="feed-source">{{ item.source === 'miniprogram' ? '小程序' : 'Web' }}</span>
          </li>
          <li v-if="!feed.length" class="feed-empty">等待小程序端产生浏览行为…</li>
        </ul>
      </div>

      <div class="panel span-2">
        <div class="panel-title">资源热度排行</div>
        <ChartPanel :option="rankOption" height="240px" />
      </div>

      <div class="panel">
        <div class="panel-title">镇街资源分布</div>
        <ChartPanel :option="townOption" height="240px" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { io } from 'socket.io-client'

import { fetchMapMarkers } from '@/api/attraction'
import { fetchOverview } from '@/api/stats'
import ChartPanel from '@/components/ChartPanel.vue'
import GisMap from '@/components/GisMap.vue'

const router = useRouter()

const clock = ref('')
const wsConnected = ref(false)
const pulseKey = ref('')
const markers = ref([])
const feed = ref([])
let clockTimer = null
let socket = null
let pollTimer = null
let feedSeq = 0

const overview = reactive({
  today: { pv: 0, uv: 0, click_external: 0, conversion_rate: 0 },
  total: { pv: 0, uv: 0, attraction_count: 0, log_count: 0 },
  category_dist: [],
  town_dist: [],
  top_attractions: [],
  hourly: []
})

const kpiList = computed(() => [
  {
    key: 'pv',
    label: '今日浏览量 PV',
    value: overview.today.pv,
    hint: `累计 ${overview.total.pv}`
  },
  {
    key: 'uv',
    label: '今日访客 UV',
    value: overview.today.uv,
    hint: `累计 ${overview.total.uv}`
  },
  {
    key: 'click',
    label: '外链点击',
    value: overview.today.click_external,
    hint: '零支付纯导流'
  },
  {
    key: 'rate',
    label: '点击转化率',
    value: `${(overview.today.conversion_rate * 100).toFixed(2)}%`,
    hint: `上架资源 ${overview.total.attraction_count}`
  }
])

// 国风文旅配色：暗夜蓝底 + 暖金 / 青瓷，替换掉原来的荧光绿
const C = {
  gold: '#e2c275',
  goldDeep: '#b98a3c',
  teal: '#4ec9b0',
  blue: '#7fa8c9',
  clay: '#c98f6b',
  violet: '#a48fd0',
  text: '#cfe0f2',
  textMuted: '#9fb3c8',
  axis: 'rgba(212, 175, 55, 0.28)',
  split: 'rgba(159, 179, 200, 0.10)',
  panel: '#0b1a2c'
}

const axisStyle = {
  axisLine: { lineStyle: { color: C.axis } },
  axisLabel: { color: C.textMuted, fontSize: 11 },
  splitLine: { lineStyle: { color: C.split } }
}

const darkTooltip = {
  backgroundColor: 'rgba(10, 22, 38, 0.94)',
  borderColor: 'rgba(212, 175, 55, 0.35)',
  borderWidth: 1,
  textStyle: { color: '#e6eef8', fontSize: 12 }
}

const hourlyOption = computed(() => ({
  tooltip: { trigger: 'axis', ...darkTooltip },
  grid: { left: 40, right: 16, top: 18, bottom: 26 },
  xAxis: {
    type: 'category',
    data: overview.hourly.map((item) => item.hour),
    ...axisStyle
  },
  yAxis: { type: 'value', ...axisStyle },
  series: [
    {
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: overview.hourly.map((item) => item.pv),
      // 数据点弱发光（ECharts 用 shadowBlur/shadowColor 实现，等价于 CSS 的 box-shadow）
      itemStyle: {
        color: C.gold,
        borderColor: C.panel,
        borderWidth: 2,
        shadowBlur: 12,
        shadowColor: 'rgba(226, 194, 117, 0.85)'
      },
      lineStyle: { width: 3, color: C.gold },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(226, 194, 117, 0.34)' },
            { offset: 1, color: 'rgba(226, 194, 117, 0.02)' }
          ]
        }
      }
    }
  ]
}))

const categoryOption = computed(() => ({
  tooltip: { trigger: 'item', ...darkTooltip },
  color: [C.gold, C.teal, C.blue, C.clay, C.violet],
  legend: {
    bottom: 0,
    textStyle: { color: C.textMuted, fontSize: 11 },
    itemWidth: 10,
    itemHeight: 10
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '64%'],
      center: ['50%', '42%'],
      itemStyle: {
        borderColor: C.panel,
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: 'rgba(226, 194, 117, 0.25)'
      },
      label: { color: C.text, fontSize: 11, formatter: '{b} {c}' },
      data: overview.category_dist
    }
  ]
}))

const rankOption = computed(() => {
  const list = [...overview.top_attractions].reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...darkTooltip },
    grid: { left: 96, right: 30, top: 10, bottom: 18 },
    xAxis: { type: 'value', ...axisStyle },
    yAxis: { type: 'category', data: list.map((i) => i.name), ...axisStyle },
    series: [
      {
        type: 'bar',
        barWidth: 11,
        data: list.map((i) => i.view_count),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: C.goldDeep },
              { offset: 1, color: C.gold }
            ]
          },
          borderRadius: [0, 6, 6, 0],
          shadowBlur: 10,
          shadowColor: 'rgba(226, 194, 117, 0.45)'
        }
      }
    ]
  }
})

const townOption = computed(() => ({
  tooltip: { trigger: 'axis', ...darkTooltip },
  grid: { left: 40, right: 16, top: 18, bottom: 40 },
  xAxis: {
    type: 'category',
    data: overview.town_dist.map((i) => i.name),
    ...axisStyle,
    axisLabel: { color: C.textMuted, fontSize: 10, rotate: 30 }
  },
  yAxis: { type: 'value', ...axisStyle },
  series: [
    {
      type: 'bar',
      barWidth: 14,
      data: overview.town_dist.map((i) => i.value),
      itemStyle: {
        color: C.teal,
        borderRadius: [6, 6, 0, 0],
        shadowBlur: 10,
        shadowColor: 'rgba(78, 201, 176, 0.45)'
      }
    }
  ]
}))

function actionText(action) {
  return { view: '浏览', click_external: '外链点击', search: '搜索' }[action] || action
}

function pulse(key) {
  pulseKey.value = key
  window.setTimeout(() => {
    if (pulseKey.value === key) pulseKey.value = ''
  }, 900)
}

function tickClock() {
  const now = new Date()
  clock.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

async function loadBase() {
  const [data, mapData] = await Promise.all([fetchOverview(), fetchMapMarkers()])
  Object.assign(overview, data)
  markers.value = mapData || []
}

function handleRealtime(payload) {
  if (!payload || !payload.metrics) return
  overview.today.pv = payload.metrics.pv
  overview.today.uv = payload.metrics.uv
  overview.today.click_external = payload.metrics.click_external
  overview.today.conversion_rate = payload.metrics.conversion_rate

  // 当前小时 +1
  const hour = String(new Date().getHours()).padStart(2, '0')
  const target = overview.hourly.find((item) => item.hour === hour)
  if (target && payload.event === 'view') {
    target.pv += 1
  } else if (target) {
    target.pv += 0
  }

  if (payload.event === 'click_external') {
    pulse('click')
  } else {
    pulse('pv')
  }

  const targetName = payload.target ? payload.target.name : ''
  if (payload.target && payload.event === 'view') {
    const hit = overview.top_attractions.find((item) => item.id === payload.target.id)
    if (hit) hit.view_count += 1
  }

  feed.value = [
    {
      uid: ++feedSeq,
      time: (payload.log?.created_at || '').slice(11, 19) || new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      action: payload.event,
      name: targetName,
      source: payload.log?.source || 'miniprogram'
    },
    ...feed.value
  ].slice(0, 12)
}

function connectSocket() {
  socket = io('/ws', {
    path: '/socket.io',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 8000
  })

  socket.on('connect', () => {
    wsConnected.value = true
  })
  socket.on('disconnect', () => {
    wsConnected.value = false
  })
  socket.on('connect_error', () => {
    wsConnected.value = false
  })
  socket.on('new_data', handleRealtime)
}

onMounted(async () => {
  tickClock()
  clockTimer = window.setInterval(tickClock, 1000)
  await loadBase()
  connectSocket()
  // 兜底轮询：WS 断开时每 15 秒刷新一次汇总，保证大屏不会彻底静止
  pollTimer = window.setInterval(async () => {
    if (!wsConnected.value) {
      try {
        const data = await fetchOverview()
        Object.assign(overview, data)
      } catch (error) {
        /* 忽略轮询异常 */
      }
    }
  }, 15000)
})

onBeforeUnmount(() => {
  window.clearInterval(clockTimer)
  window.clearInterval(pollTimer)
  if (socket) socket.disconnect()
})
</script>

<style scoped>
.screen {
  min-height: 100vh;
  /* 暗夜蓝底，替代原来的墨绿荧光底 */
  background: radial-gradient(circle at 50% -12%, #12233d 0%, #0a1626 55%, #060d18 100%);
  color: #dbe7f5;
  padding: 14px 18px 22px;
}

.screen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.22);
}

.header-side {
  flex: 0 0 210px;
}

.header-side.right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.header-title {
  flex: 1;
  text-align: center;
}

.header-title h1 {
  margin: 0;
  font-size: 21px;
  letter-spacing: 2px;
  color: #f3e6c4;
  text-shadow: 0 0 18px rgba(226, 194, 117, 0.38);
}

.header-title p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8ba3bd;
  letter-spacing: 1px;
}

.back {
  color: #e2c275;
  font-size: 13px;
}

.clock {
  font-family: Consolas, Monaco, monospace;
  font-size: 14px;
  color: #cfd9e6;
}

.ws-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.ws-status i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.ws-status.on i {
  background: #4ec9b0;
  box-shadow: 0 0 8px #4ec9b0;
}

.ws-status.off i {
  background: #e06c75;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin: 14px 0;
}

.kpi {
  position: relative;
  overflow: hidden;
  background: linear-gradient(160deg, rgba(28, 52, 82, 0.78), rgba(10, 20, 34, 0.92));
  border: 1px solid rgba(212, 175, 55, 0.22);
  border-radius: 10px;
  padding: 12px 16px;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

/* 右上角暖金光斑 */
.kpi::after {
  content: '';
  position: absolute;
  top: -34px;
  right: -26px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(226, 194, 117, 0.2), rgba(226, 194, 117, 0) 70%);
  pointer-events: none;
}

.kpi.pulse {
  box-shadow: 0 0 26px rgba(226, 194, 117, 0.55);
  transform: translateY(-2px);
}

.kpi-label {
  font-size: 12px;
  color: #8ba3bd;
}

.kpi-value {
  font-size: 30px;
  font-weight: 700;
  font-family: Consolas, Monaco, monospace;
  color: #f0d489;
  margin: 4px 0 2px;
  text-shadow: 0 0 16px rgba(226, 194, 117, 0.45);
  font-variant-numeric: tabular-nums;
}

.kpi-hint {
  font-size: 11px;
  color: #7d94ad;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.panel {
  position: relative;
  background: linear-gradient(180deg, rgba(16, 32, 52, 0.82), rgba(10, 20, 34, 0.9));
  border: 1px solid rgba(212, 175, 55, 0.16);
  border-radius: 10px;
  padding: 10px 12px 6px;
}

/* 面板顶部一条金色细线，代替通体荧光的边框 */
.panel::before {
  content: '';
  position: absolute;
  left: 12px;
  right: 12px;
  top: 0;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(226, 194, 117, 0.7), rgba(226, 194, 117, 0));
}

.panel.span-2 {
  grid-column: span 2;
}

.panel-title {
  font-size: 13px;
  color: #cfe0f2;
  letter-spacing: 1px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #e2c275;
  box-shadow: 0 0 8px rgba(226, 194, 117, 0.8);
  animation: blink 1.2s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.15; }
}

.feed {
  list-style: none;
  margin: 0;
  padding: 0;
  height: 270px;
  overflow: hidden;
}

.feed-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 6px 4px;
  border-bottom: 1px dashed rgba(212, 175, 55, 0.14);
  animation: slideIn 0.4s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.feed-time {
  font-family: Consolas, Monaco, monospace;
  color: #7d94ad;
  flex: 0 0 62px;
}

.feed-action {
  flex: 0 0 58px;
  text-align: center;
  border-radius: 4px;
  padding: 1px 0;
  font-size: 11px;
}

.feed-action.view {
  background: rgba(78, 201, 176, 0.16);
  color: #7fe0cb;
}

.feed-action.click_external {
  background: rgba(226, 194, 117, 0.18);
  color: #f0d489;
}

.feed-action.search {
  background: rgba(127, 168, 201, 0.18);
  color: #a8c6e0;
}

.feed-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #dbe7f5;
}

.feed-source {
  flex: 0 0 42px;
  text-align: right;
  color: #7d94ad;
  font-size: 11px;
}

.feed-empty {
  color: #6b8199;
  font-size: 12px;
  padding: 10px 4px;
}

@media (max-width: 1400px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .panel.span-2 {
    grid-column: span 1;
  }
}
</style>
