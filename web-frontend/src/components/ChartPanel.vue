<template>
  <div ref="container" class="chart-panel" :style="{ height }"></div>
</template>

<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '280px' }
})

const container = ref(null)
let chart = null

function resize() {
  if (chart) chart.resize()
}

onMounted(() => {
  chart = echarts.init(container.value)
  chart.setOption(props.option)
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  (option) => {
    if (chart) chart.setOption(option, true)
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.chart-panel {
  width: 100%;
}
</style>
