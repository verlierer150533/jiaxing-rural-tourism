<template>
  <view v-if="detail" class="page">
    <view class="hero-wrap">
      <!-- 有图：轮播；无图：回退为类别渐变背景 -->
      <swiper
        v-if="images.length"
        class="hero-swiper"
        :indicator-dots="true"
        indicator-color="rgba(255,255,255,0.45)"
        indicator-active-color="#ffffff"
        :autoplay="true"
        :interval="3500"
        :duration="500"
        :circular="true"
      >
        <swiper-item v-for="(img, idx) in images" :key="idx">
          <image class="hero-img" :src="img" mode="aspectFill" />
        </swiper-item>
      </swiper>
      <view v-else class="hero" :class="categoryClass(detail.category)"></view>

      <view class="hero-mask"></view>

      <view class="hero-text">
        <view class="hero-cat">{{ detail.category }}</view>
        <view class="hero-name">{{ detail.name }}</view>
        <view class="hero-town">{{ detail.town }}</view>
      </view>

      <view class="fav-btn" :class="{ active: favorited }" @tap="onFavorite">
        <text class="fav-icon">{{ favorited ? '♥' : '♡' }}</text>
        <text class="fav-text">{{ favorited ? '已收藏' : '收藏' }}</text>
      </view>
    </view>

    <view class="stat-row">
      <view class="stat">
        <text class="num">{{ detail.view_count }}</text>
        <text class="label">累计浏览</text>
      </view>
      <view class="stat">
        <text class="num">{{ detail.longitude.toFixed(4) }}</text>
        <text class="label">经度</text>
      </view>
      <view class="stat">
        <text class="num">{{ detail.latitude.toFixed(4) }}</text>
        <text class="label">纬度</text>
      </view>
    </view>

    <view class="card section">
      <view class="card-title">简介</view>
      <view class="paragraph">{{ detail.summary || '暂无简介' }}</view>
    </view>

    <view class="card section">
      <view class="card-title">详细介绍</view>
      <view class="paragraph">{{ detail.description || '暂无详细介绍' }}</view>
    </view>

    <view class="card section">
      <view class="card-title">位置与导览</view>
      <view class="paragraph">{{ detail.address || '暂无地址' }}</view>
      <view class="map-tip" @tap="navigateTo">
        <text class="map-icon">🧭</text>
        <text>打开微信地图导航到这里</text>
      </view>
    </view>

    <view v-if="detail.purchase_url" class="card section">
      <view class="card-title">相关商品 / 外部购买</view>
      <view class="paragraph">
        本平台不提供在线支付。点击后复制「海宁 {{ detail.name }}」的淘宝搜索链接，
        打开淘宝 App 即可查看相关商品。
      </view>
      <button class="btn-outline" size="mini" @tap="onExternal">前往淘宝购买（复制链接）</button>
    </view>

    <view class="footer">浏览足迹已实时上报，可在 Web 后台大屏查看</view>
  </view>

  <view v-else class="loading muted">加载中…</view>
</template>

<script setup>
import { ref } from 'vue'
import { categoryClass } from '../../utils/category'
import { onLoad } from '@dcloudio/uni-app'

import { fetchAttraction } from '../../api/attraction'
import { checkFavorite, toggleFavorite } from '../../api/favorite'
import { saveLocalHistory, track } from '../../utils/track'
import { getSessionId } from '../../utils/session'

const detail = ref(null)
const attractionId = ref(0)
const images = ref([])
const favorited = ref(false)
const favoriteCount = ref(0)
const favLoading = ref(false)

async function load() {
  try {
    const data = await fetchAttraction(attractionId.value)
    detail.value = data
    images.value = Array.isArray(data.images) ? data.images : []
    // 埋点：浏览详情（驱动 Web 大屏实时跳动）
    track('view', 'attraction', data.id, `查看详情 ${data.name}`)
    saveLocalHistory(data)
    loadFavoriteState(data.id)
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

async function loadFavoriteState(id) {
  try {
    const data = await checkFavorite(getSessionId(), id)
    favorited.value = !!data.favorited
    favoriteCount.value = data.favorite_count || 0
  } catch (error) {
    /* 收藏状态拿不到不影响浏览 */
  }
}

async function onFavorite() {
  if (favLoading.value) return
  favLoading.value = true
  try {
    const data = await toggleFavorite(getSessionId(), detail.value.id)
    favorited.value = !!data.favorited
    favoriteCount.value = data.favorite_count || 0
    uni.showToast({
      title: favorited.value ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
  } catch (error) {
    uni.showToast({ title: error.message || '操作失败', icon: 'none' })
  } finally {
    favLoading.value = false
  }
}

function navigateTo() {
  uni.openLocation({
    latitude: Number(detail.value.latitude),
    longitude: Number(detail.value.longitude),
    name: detail.value.name,
    address: detail.value.address || '',
    scale: 16
  })
}

function onExternal() {
  const url = detail.value.purchase_url || detail.value.external_url
  if (!url) {
    uni.showToast({ title: '暂无购买链接', icon: 'none' })
    return
  }
  // 埋点：外链点击（用于后台计算导流转化率）
  track('click_external', 'attraction', detail.value.id, `淘宝搜索 ${detail.value.name}`)

  uni.setClipboardData({
    data: url,
    success: () => {
      uni.showModal({
        title: '淘宝搜索链接已复制',
        content: '请打开淘宝 App 查看「海宁 ' + detail.value.name + '」的相关商品。',
        showCancel: false
      })
    }
  })
}

onLoad((query) => {
  attractionId.value = Number((query && query.id) || 0)
  if (!attractionId.value) {
    uni.showToast({ title: '缺少资源编号', icon: 'none' })
    return
  }
  load()
})
</script>

<style scoped>
.page {
  padding: 24rpx 24rpx 40rpx;
}

.hero-wrap {
  position: relative;
  height: 420rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background: #21463a;
}

.hero-swiper {
  width: 100%;
  height: 420rpx;
}

.hero-img {
  width: 100%;
  height: 420rpx;
  display: block;
}

.hero-mask {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 220rpx;
  background: linear-gradient(180deg, rgba(10, 30, 20, 0) 0%, rgba(10, 30, 20, 0.72) 100%);
  pointer-events: none;
}

.hero-text {
  position: absolute;
  left: 28rpx;
  right: 28rpx;
  bottom: 24rpx;
  color: #ffffff;
}

.fav-btn {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.28);
  color: #ffffff;
  font-size: 24rpx;
}

.fav-btn.active {
  background: rgba(214, 68, 92, 0.92);
}

.fav-icon {
  font-size: 30rpx;
  line-height: 1;
}

.fav-text {
  font-size: 22rpx;
}

.hero {
  border-radius: 24rpx;
  padding: 36rpx 28rpx;
  color: #ffffff;
  height: 420rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

/* 无图点位：用「潮水纹 + 底部蒙版 + 类别主题色」三层渐变做海宁风占位背景
   （全部为 CSS 渐变，不依赖网络图片，断网也不会白屏） */
.cat-town {
  background:
    radial-gradient(120% 80% at 82% 8%, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0) 62%),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.09) 0 10rpx, rgba(255, 255, 255, 0) 10rpx 36rpx),
    linear-gradient(180deg, rgba(6, 20, 16, 0) 38%, rgba(6, 20, 16, 0.76) 100%),
    linear-gradient(135deg, #7a4b23, #c9a24f);
}

.cat-orchard {
  background:
    radial-gradient(120% 80% at 82% 8%, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0) 62%),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0 10rpx, rgba(255, 255, 255, 0) 10rpx 36rpx),
    linear-gradient(180deg, rgba(6, 20, 16, 0) 38%, rgba(6, 20, 16, 0.74) 100%),
    linear-gradient(135deg, #1f6a45, #6fb98a);
}

.cat-village {
  background:
    radial-gradient(120% 80% at 82% 8%, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0) 62%),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.09) 0 10rpx, rgba(255, 255, 255, 0) 10rpx 36rpx),
    linear-gradient(180deg, rgba(6, 20, 16, 0) 38%, rgba(6, 20, 16, 0.74) 100%),
    linear-gradient(135deg, #204a63, #5d93ad);
}

.cat-scenic {
  background:
    radial-gradient(120% 80% at 82% 8%, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0) 62%),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0 10rpx, rgba(255, 255, 255, 0) 10rpx 36rpx),
    linear-gradient(180deg, rgba(6, 20, 16, 0) 38%, rgba(6, 20, 16, 0.74) 100%),
    linear-gradient(135deg, #3d3a63, #7f7bb0);
}

.hero-cat {
  display: inline-block;
  font-size: 22rpx;
  background: rgba(255, 255, 255, 0.22);
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
}

.hero-name {
  font-size: 44rpx;
  font-weight: 700;
  margin-top: 16rpx;
}

.hero-town {
  font-size: 24rpx;
  opacity: 0.88;
  margin-top: 10rpx;
}

.stat-row {
  display: flex;
  margin-top: 20rpx;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 22rpx 0;
}

.stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.num {
  font-size: 30rpx;
  font-weight: 700;
  color: #21463a;
}

.label {
  font-size: 22rpx;
  color: #8a9a90;
  margin-top: 6rpx;
}

.section {
  margin-top: 20rpx;
}

.card-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #21463a;
  margin-bottom: 12rpx;
}

.paragraph {
  font-size: 26rpx;
  color: #566a5d;
  line-height: 1.75;
}

.map-tip {
  margin-top: 18rpx;
  background: #eef5f0;
  border-radius: 14rpx;
  padding: 18rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  color: #2f7d4f;
  font-size: 26rpx;
}

.map-icon {
  font-size: 30rpx;
}

.btn-outline {
  margin-top: 18rpx;
  border: 1rpx solid #2f7d4f;
  color: #2f7d4f;
  background: transparent;
  border-radius: 999rpx;
  font-size: 26rpx;
}

.footer {
  margin-top: 30rpx;
  text-align: center;
  font-size: 22rpx;
  color: #9aa9a0;
}

.loading {
  padding: 80rpx;
  text-align: center;
}
</style>
