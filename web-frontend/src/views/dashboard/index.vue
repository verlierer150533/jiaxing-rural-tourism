<template>
  <div>
    <div class="toolbar">
      <div class="title-block">
        <h3 class="page-title">运营概览</h3>
        <p class="page-subtitle">探索潮乡农文旅，赋能数字新乡村</p>
      </div>
      <div>
        <el-tag type="info" effect="plain" size="small">
          数据截至 {{ updatedAt || '—' }}
        </el-tag>
        <el-button size="small" :loading="loading" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="6">
        <div class="kpi-card" style="background: linear-gradient(135deg, #2f7d4f, #4aa06a)">
          <div class="label">今日浏览量 PV</div>
          <div class="value">{{ overview.today.pv }}</div>
          <div class="hint">累计 {{ overview.total.pv }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="kpi-card" style="background: linear-gradient(135deg, #2b6cb0, #4a90d9)">
          <div class="label">今日访客数 UV</div>
          <div class="value">{{ overview.today.uv }}</div>
          <div class="hint">累计 {{ overview.total.uv }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="kpi-card" style="background: linear-gradient(135deg, #b7791f, #d69e2e)">
          <div class="label">今日外链点击</div>
          <div class="value">{{ overview.today.click_external }}</div>
          <div class="hint">纯导流，无支付</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="kpi-card" style="background: linear-gradient(135deg, #5b4b8a, #8a76c4)">
          <div class="label">外链点击转化率</div>
          <div class="value">{{ (overview.today.conversion_rate * 100).toFixed(2) }}%</div>
          <div class="hint">上架资源 {{ overview.total.attraction_count }} 个</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never">
          <template #header><span class="card-title">今日分时浏览量</span></template>
          <ChartPanel :option="hourlyOption" height="268px" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header><span class="card-title">资源类别分布</span></template>
          <ChartPanel :option="categoryOption" height="268px" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header><span class="card-title">海宁市农文旅资源分布</span></template>
          <GisMap :markers="markers" height="360px" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header><span class="card-title">热度排行 Top 8</span></template>
          <ChartPanel :option="rankOption" height="360px" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchMapMarkers } from '@/api/attraction'
import { fetchOverview } from '@/api/stats'
import ChartPanel from '@/components/ChartPanel.vue'
import GisMap from '@/components/GisMap.vue'

const loading = ref(false)
const updatedAt = ref('')
const markers = ref([])

const overview = reactive({
  today: { pv: 0, uv: 0, click_external: 0, conversion_rate: 0 },
  total: { pv: 0, uv: 0, attraction_count: 0, log_count: 0 },
  category_dist: [],
  town_dist: [],
  top_attractions: [],
  hourly: [],
  latest: []
})

const hourlyOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 44, right: 18, top: 24, bottom: 32 },
  xAxis: {
    type: 'category',
    data: overview.hourly.map((item) => `${item.hour}:00`),
    axisLabel: { interval: 3, fontSize: 11 },
    axisLine: { lineStyle: { color: '#c9d8cf' } }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#eef4f0' } },
    axisLabel: { fontSize: 11 }
  },
  series: [
    {
      type: 'line',
      smooth: true,
      symbolSize: 5,
      data: overview.hourly.map((item) => item.pv),
      itemStyle: { color: '#2f7d4f' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(47,125,79,0.35)' },
            { offset: 1, color: 'rgba(47,125,79,0.02)' }
          ]
        }
      }
    }
  ]
}))

const categoryOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 11 } },
  series: [
    {
      type: 'pie',
      radius: ['42%', '66%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c}' },
      data: overview.category_dist
    }
  ]
}))

const rankOption = computed(() => {
  const list = [...overview.top_attractions].reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 112, right: 30, top: 12, bottom: 24 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#eef4f0' } },
      axisLabel: { fontSize: 11, color: '#5b6b62' }
    },
    yAxis: {
      type: 'category',
      data: list.map((item) => item.name),
      // 原来的默认灰色（#6E7079）在浅色卡片上偏淡，这里改为深墨绿并略微加粗
      axisLabel: { fontSize: 12, color: '#2c3e35', fontWeight: 500 },
      axisLine: { lineStyle: { color: '#c9d8cf' } }
    },
    series: [
      {
        type: 'bar',
        barWidth: 12,
        data: list.map((item) => item.view_count),
        itemStyle: { color: '#3f9c65', borderRadius: [0, 6, 6, 0] }
      }
    ]
  }
})

async function loadAll() {
  loading.value = true
  try {
    const [data, mapData] = await Promise.all([fetchOverview(), fetchMapMarkers()])
    Object.assign(overview, data)
    markers.value = mapData || []
    updatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar .page-title {
  margin: 0;
}

.toolbar > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kpi-row {
  margin-bottom: 16px;
}

.chart-row {
  margin-bottom: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
}
</style>
