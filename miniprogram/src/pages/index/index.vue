<template>
  <view class="page">
    <!-- 顶部横幅 -->
    <view class="banner">
      <view class="banner-title">海宁乡村农文旅</view>
      <view class="banner-sub">海宁 · 果园采摘 × 古镇人文 × 田园观光</view>
      <view class="banner-stats">
        <view class="stat">
          <text class="stat-num">{{ total }}</text>
          <text class="stat-label">在册资源</text>
        </view>
        <view class="stat">
          <text class="stat-num">{{ towns.length }}</text>
          <text class="stat-label">覆盖镇街</text>
        </view>
        <view class="stat">
          <text class="stat-num">{{ categories.length }}</text>
          <text class="stat-label">资源类别</text>
        </view>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="quick">
      <view class="quick-item" @tap="goMap">
        <view class="quick-icon">🗺️</view>
        <view class="quick-text">地图导览</view>
      </view>
      <view class="quick-item" @tap="goList('')">
        <view class="quick-icon">🧺</view>
        <view class="quick-text">资源浏览</view>
      </view>
      <view class="quick-item" @tap="goList('果园')">
        <view class="quick-icon">🍇</view>
        <view class="quick-text">果园采摘</view>
      </view>
      <view class="quick-item" @tap="goList('古镇')">
        <view class="quick-icon">🏯</view>
        <view class="quick-text">古镇古村</view>
      </view>
    </view>

    <!-- 热门资源 -->
    <view class="section">
      <view class="section-head">
        <text class="section-title">热门推荐</text>
        <text class="section-more" @tap="goList('')">全部 ›</text>
      </view>

      <view v-if="loading" class="muted">加载中…</view>
      <view v-else-if="!hotList.length" class="muted">暂无资源，请先在后台添加</view>

      <view v-for="item in hotList" :key="item.id" class="res-card" @tap="goDetail(item.id)">
        <view class="res-thumb" :class="categoryClass(item.category)">{{ item.category.slice(0, 1) }}</view>
        <view class="res-body">
          <view class="res-name">{{ item.name }}</view>
          <view class="res-meta">{{ item.town }} · {{ item.category }}</view>
          <view class="res-summary">{{ item.summary }}</view>
          <view class="res-foot">
            <text class="res-hot">🔥 {{ item.view_count }} 次浏览</text>
            <text class="res-link">查看详情 ›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 采摘月历 -->
    <view class="section">
      <view class="section-head">
        <text class="section-title">黄湾水果采摘月历</text>
        <text class="section-tip">13000 余亩果园 · 四季有果</text>
      </view>
      <view class="calendar">
        <view v-for="item in fruitCalendar" :key="item.month" class="cal-cell">
          <text class="cal-month">{{ item.month }}月</text>
          <text class="cal-fruit">{{ item.fruit }}</text>
        </view>
      </view>
      <view class="muted cal-note">数据来源：海宁市文化和广电旅游体育局 · 黄湾镇水果采摘季</view>
    </view>

    <view class="footer">数据由 Web 管理后台统一维护 · 小程序端仅展示与导流</view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { categoryClass } from '../../utils/category'

import { fetchAttractions, fetchMeta } from '../../api/attraction'

const loading = ref(true)
const hotList = ref([])
const categories = ref([])
const towns = ref([])
const total = ref(0)

const fruitCalendar = [
  { month: 1, fruit: '葡萄柚' },
  { month: 2, fruit: '沃柑' },
  { month: 3, fruit: '黄美人' },
  { month: 4, fruit: '樱桃' },
  { month: 5, fruit: '枇杷' },
  { month: 6, fruit: '杨梅' },
  { month: 7, fruit: '桃子' },
  { month: 8, fruit: '火龙果' },
  { month: 9, fruit: '葡萄' },
  { month: 10, fruit: '橘子' },
  { month: 11, fruit: '橘子' },
  { month: 12, fruit: '红美人' }
]

function goMap() {
  uni.switchTab({ url: '/pages/map/map' })
}

function goList(category) {
  const query = category ? `?category=${encodeURIComponent(category)}` : ''
  uni.navigateTo({ url: `/pages/list/list${query}` })
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/detail/detail?id=${id}` })
}

onMounted(async () => {
  try {
    const [page, meta] = await Promise.all([
      fetchAttractions({ page: 1, page_size: 6, sort: '-view_count' }),
      fetchMeta()
    ])
    hotList.value = page.list || []
    total.value = page.total || 0
    categories.value = meta.categories || []
    towns.value = meta.towns || []
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page {
  padding: 24rpx 24rpx 40rpx;
}

.banner {
  background: linear-gradient(135deg, #21463a 0%, #2f7d4f 60%, #5aa87c 100%);
  border-radius: 24rpx;
  padding: 32rpx 28rpx;
  color: #ffffff;
}

.banner-title {
  font-size: 40rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.banner-sub {
  font-size: 24rpx;
  opacity: 0.85;
  margin-top: 8rpx;
}

.banner-stats {
  display: flex;
  margin-top: 26rpx;
}

.stat {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 38rpx;
  font-weight: 700;
}

.stat-label {
  font-size: 22rpx;
  opacity: 0.8;
  margin-top: 4rpx;
}

.quick {
  display: flex;
  background: #ffffff;
  border-radius: 20rpx;
  margin-top: -20rpx;
  padding: 24rpx 0;
  box-shadow: 0 8rpx 24rpx rgba(33, 70, 58, 0.08);
  position: relative;
  z-index: 2;
}

.quick-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.quick-icon {
  font-size: 40rpx;
}

.quick-text {
  font-size: 24rpx;
  margin-top: 8rpx;
  color: #34493d;
}

.section {
  margin-top: 34rpx;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #21463a;
}

.section-more {
  font-size: 24rpx;
  color: #2f7d4f;
}

.section-tip {
  font-size: 22rpx;
  color: #8a9a90;
}

.res-card {
  display: flex;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 6rpx 18rpx rgba(33, 70, 58, 0.06);
}

.res-thumb {
  width: 104rpx;
  height: 104rpx;
  border-radius: 16rpx;
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cat-town {
  background: linear-gradient(135deg, #c9772a, #e0a25e);
}

.cat-orchard {
  background: linear-gradient(135deg, #2f7d4f, #5aa87c);
}

.cat-village {
  background: linear-gradient(135deg, #3a6ea5, #6a9bd1);
}

.cat-scenic {
  background: linear-gradient(135deg, #8a5cc4, #ad86dc);
}

.res-body {
  flex: 1;
  margin-left: 20rpx;
  min-width: 0;
}

.res-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #21463a;
}

.res-meta {
  font-size: 22rpx;
  color: #2f7d4f;
  margin-top: 4rpx;
}

.res-summary {
  font-size: 24rpx;
  color: #6c7d72;
  margin-top: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.res-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 10rpx;
  font-size: 22rpx;
}

.res-hot {
  color: #b7791f;
}

.res-link {
  color: #2f7d4f;
}

.calendar {
  display: flex;
  flex-wrap: wrap;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 16rpx 8rpx;
}

.cal-cell {
  width: 16.66%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10rpx 0;
}

.cal-month {
  font-size: 22rpx;
  color: #8a9a90;
}

.cal-fruit {
  font-size: 24rpx;
  color: #2f7d4f;
  font-weight: 600;
  margin-top: 4rpx;
}

.cal-note {
  margin-top: 12rpx;
}

.footer {
  margin-top: 40rpx;
  text-align: center;
  font-size: 22rpx;
  color: #9aa9a0;
}
</style>
