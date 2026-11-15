<template>
  <view class="map-page">
    <map
      class="map"
      :latitude="center.latitude"
      :longitude="center.longitude"
      :scale="scale"
      :markers="markers"
      show-location
      @markertap="onMarkerTap"
      @callouttap="onMarkerTap"
    />

    <view class="filter-bar">
      <view
        v-for="item in filters"
        :key="item.value"
        class="chip"
        :class="{ active: category === item.value }"
        @tap="onFilter(item.value)"
      >
        {{ item.label }}
      </view>
    </view>

    <view class="locate" @tap="locateMe">📍</view>

    <view v-if="selected" class="detail-card">
      <view class="dc-head">
        <text class="dc-name">{{ selected.name }}</text>
        <text class="dc-close" @tap="selected = null">✕</text>
      </view>
      <view class="dc-meta">{{ selected.category }} · {{ selected.town }} · 🔥 {{ selected.view_count }}</view>
      <view class="dc-summary">{{ selected.summary }}</view>
      <view class="dc-actions">
        <button class="btn ghost" size="mini" @tap="navigateTo(selected)">导航</button>
        <button class="btn primary" size="mini" @tap="openDetail(selected.id)">查看详情</button>
      </view>
    </view>

    <view v-else class="hint">点击地图上的标记查看资源，或使用上方分类筛选</view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { fetchMapMarkers } from '../../api/attraction'

const center = ref({ latitude: 30.47, longitude: 120.68 })
const scale = ref(10)
const list = ref([])
const category = ref('')
const selected = ref(null)

const filters = [
  { label: '全部', value: '' },
  { label: '果园', value: '果园' },
  { label: '古镇', value: '古镇' },
  { label: '村落', value: '村落' },
  { label: '景区', value: '景区' }
]

const markers = computed(() =>
  list.value
    .filter((item) => !category.value || item.category === category.value)
    .map((item) => ({
      id: Number(item.id),
      latitude: Number(item.latitude),
      longitude: Number(item.longitude),
      width: 26,
      height: 26,
      callout: {
        content: item.name,
        display: 'BYCLICK',
        fontSize: 12,
        padding: 6,
        borderRadius: 6,
        bgColor: '#ffffff',
        color: '#21463a'
      }
    }))
)

function onMarkerTap(event) {
  const markerId = Number(event.detail.markerId)
  selected.value = list.value.find((item) => Number(item.id) === markerId) || null
  if (selected.value) {
    center.value = {
      latitude: Number(selected.value.latitude),
      longitude: Number(selected.value.longitude)
    }
  }
}

function onFilter(value) {
  category.value = value
  selected.value = null
}

function locateMe() {
  uni.getLocation({
    type: 'gcj02',
    success: (res) => {
      center.value = { latitude: res.latitude, longitude: res.longitude }
      scale.value = 13
      uni.showToast({ title: '已定位到当前位置', icon: 'none' })
    },
    fail: () => {
      uni.showToast({ title: '定位失败，请检查权限', icon: 'none' })
    }
  })
}

function openDetail(id) {
  uni.navigateTo({ url: `/pages/detail/detail?id=${id}` })
}

function navigateTo(item) {
  uni.openLocation({
    latitude: Number(item.latitude),
    longitude: Number(item.longitude),
    name: item.name,
    address: item.address || '',
    scale: 16
  })
}

onMounted(async () => {
  try {
    list.value = await fetchMapMarkers()
  } catch (error) {
    uni.showToast({ title: error.message || '地图数据加载失败', icon: 'none' })
  }
})
</script>

<style scoped>
.map-page {
  position: relative;
  height: 100vh;
  width: 100%;
}

.map {
  width: 100%;
  height: 100%;
}

.filter-bar {
  position: absolute;
  top: 20rpx;
  left: 20rpx;
  right: 20rpx;
  display: flex;
  gap: 12rpx;
  z-index: 5;
}

.chip {
  padding: 8rpx 22rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  color: #34493d;
  font-size: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.08);
}

.chip.active {
  background: #2f7d4f;
  color: #ffffff;
}

.locate {
  position: absolute;
  right: 24rpx;
  bottom: 320rpx;
  width: 76rpx;
  height: 76rpx;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  box-shadow: 0 6rpx 18rpx rgba(0, 0, 0, 0.14);
}

.detail-card {
  position: absolute;
  left: 20rpx;
  right: 20rpx;
  bottom: 30rpx;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 26rpx;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.14);
}

.dc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dc-name {
  font-size: 32rpx;
  font-weight: 700;
  color: #21463a;
}

.dc-close {
  color: #9aa9a0;
  font-size: 26rpx;
}

.dc-meta {
  font-size: 22rpx;
  color: #2f7d4f;
  margin-top: 8rpx;
}

.dc-summary {
  font-size: 24rpx;
  color: #6c7d72;
  margin-top: 12rpx;
  line-height: 1.6;
}

.dc-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16rpx;
  margin-top: 18rpx;
}

.btn {
  border-radius: 999rpx;
  font-size: 24rpx;
  margin: 0;
}

.btn.primary {
  background: #2f7d4f;
  color: #ffffff;
}

.btn.ghost {
  background: #eef5f0;
  color: #2f7d4f;
}

.hint {
  position: absolute;
  left: 20rpx;
  right: 20rpx;
  bottom: 30rpx;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 16rpx;
  padding: 18rpx;
  font-size: 24rpx;
  color: #6c7d72;
  text-align: center;
}
</style>
