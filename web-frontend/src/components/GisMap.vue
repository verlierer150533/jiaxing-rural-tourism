<template>
  <div ref="container" class="gis-map" :style="{ height }"></div>
</template>

<script setup>
import L from 'leaflet'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  markers: { type: Array, default: () => [] },
  height: { type: String, default: '420px' },
  // 是否显示地图外的装饰背景（大屏用）
  dark: { type: Boolean, default: false }
})

const emit = defineEmits(['select'])

const container = ref(null)
let map = null
let markerLayer = null
let boundaryLayer = null

const CATEGORY_COLOR = {
  古镇: '#c9772a',
  果园: '#2f7d4f',
  村落: '#3a6ea5',
  景区: '#8a5cc4'
}

function markerIcon(category) {
  const color = CATEGORY_COLOR[category] || '#2f7d4f'
  return L.divIcon({
    className: 'jrt-marker',
    html: `<span style="background:${color}"></span><em>${category || ''}</em>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  })
}

async function loadBoundary() {
  try {
    const response = await fetch('/gis/haining.json')
    if (!response.ok) return
    const geojson = await response.json()
    boundaryLayer = L.geoJSON(geojson, {
      style: {
        color: '#2f7d4f',
        weight: 2,
        fillColor: '#3f9c65',
        fillOpacity: props.dark ? 0.16 : 0.1
      }
    }).addTo(map)
    map.fitBounds(boundaryLayer.getBounds(), { padding: [16, 16] })
  } catch (error) {
    console.warn('海宁市边界加载失败', error)
  }
}

function renderMarkers() {
  if (!map) return
  if (markerLayer) {
    markerLayer.clearLayers()
  } else {
    markerLayer = L.layerGroup().addTo(map)
  }

  props.markers.forEach((item) => {
    if (item.longitude == null || item.latitude == null) return
    const marker = L.marker([item.latitude, item.longitude], {
      icon: markerIcon(item.category),
      title: item.name
    })
    marker.bindPopup(
      `<div class="popup-title">${item.name}</div>
       <div class="popup-sub">${item.category || ''} · ${item.town || ''}</div>
       <div class="popup-desc">${item.summary || ''}</div>`,
      { maxWidth: 260 }
    )
    marker.on('click', () => emit('select', item))
    marker.addTo(markerLayer)
  })
}

onMounted(async () => {
  map = L.map(container.value, {
    zoomControl: true,
    attributionControl: false,
    center: [30.47, 120.68],
    zoom: 10,
    minZoom: 8,
    maxZoom: 16
  })
  // 不依赖在线瓦片，直接以 GeoJSON 边界为底图，离线演示也能正常显示
  map.getContainer().style.background = props.dark ? '#0b1f18' : '#eaf2ec'
  await loadBoundary()
  renderMarkers()
})

watch(() => props.markers, renderMarkers, { deep: true })

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.gis-map {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
}

:deep(.jrt-marker) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.jrt-marker span) {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.35);
  display: block;
}

:deep(.jrt-marker em) {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  font-style: normal;
  font-size: 11px;
  color: #24422f;
  background: rgba(255, 255, 255, 0.86);
  padding: 0 4px;
  border-radius: 3px;
  white-space: nowrap;
}

:deep(.leaflet-popup-content) {
  margin: 10px 12px;
  font-size: 12px;
  line-height: 1.6;
}

:deep(.popup-title) {
  font-weight: 700;
  font-size: 13px;
}

:deep(.popup-sub) {
  color: #2f7d4f;
}

:deep(.popup-desc) {
  color: #4a5a50;
  margin-top: 4px;
}
</style>
