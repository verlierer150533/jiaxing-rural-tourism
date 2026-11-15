<template>
  <view class="page">
    <view class="profile">
      <view class="avatar">游</view>
      <view class="profile-body">
        <view class="profile-name">游客模式</view>
        <view class="profile-sub">免注册浏览 · 行为匿名统计</view>
      </view>
    </view>

    <view class="card section">
      <view class="row">
        <text class="row-label">设备会话号</text>
        <text class="row-value mono">{{ sessionId }}</text>
      </view>
      <view class="row">
        <text class="row-label">作用</text>
        <text class="row-value">用于后台 UV 去重，不含个人身份信息</text>
      </view>
      <button class="btn ghost" size="mini" @tap="onResetSession">重新生成会话号</button>
    </view>

    <view class="card section">
      <view class="card-head">
        <text class="card-title">我的收藏</text>
        <text v-if="favorites.length" class="muted">{{ favorites.length }} 个</text>
      </view>

      <view v-if="!favorites.length" class="muted empty">还没有收藏，去详情页点个爱心吧</view>

      <view v-for="item in favorites" :key="'fav-' + item.id" class="fav-item">
        <view class="fav-thumb" :class="categoryClass(item.category)" @tap="goDetail(item.id)">
          <image v-if="item.images && item.images.length" class="fav-img" :src="item.images[0]" mode="aspectFill" />
          <text v-else class="fav-char">{{ item.category.slice(0, 1) }}</text>
        </view>
        <view class="fav-body" @tap="goDetail(item.id)">
          <view class="hi-name">{{ item.name }}</view>
          <view class="hi-meta">{{ item.town }} · {{ item.category }}</view>
        </view>
        <text class="fav-cancel" @tap.stop="onUnfavorite(item)">取消</text>
      </view>
    </view>

    <view class="card section">
      <view class="card-head">
        <text class="card-title">最近浏览</text>
        <text v-if="history.length" class="clear" @tap="onClear">清空</text>
      </view>

      <view v-if="!history.length" class="muted empty">还没有浏览记录</view>

      <view v-for="item in history" :key="item.id + '-' + item.at" class="history-item" @tap="goDetail(item.id)">
        <view class="hi-name">{{ item.name }}</view>
        <view class="hi-meta">{{ item.town }} · {{ item.category }}</view>
      </view>
    </view>

    <view class="card section">
      <view class="card-title">关于本平台</view>
      <view class="paragraph">
        海宁乡村农文旅服务平台由 Web 管理后台与微信小程序两端协同：
        后台负责资源维护与数据大屏监控，小程序端负责游客展示与空间导览。
        平台不涉及在线支付，商品与农产品信息仅作展示与跳转导流。
      </view>
    </view>

    <view class="footer">数据来源：海宁市农文旅资源 · 实时统计由后端 WebSocket 推送</view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { categoryClass } from '../../utils/category'
import { fetchFavorites, toggleFavorite } from '../../api/favorite'
import { getSessionId, resetSessionId } from '../../utils/session'
import { clearLocalHistory, getLocalHistory } from '../../utils/track'

const sessionId = ref('')
const history = ref([])
const favorites = ref([])

async function loadFavorites() {
  try {
    const data = await fetchFavorites(getSessionId())
    favorites.value = data.list || []
  } catch (error) {
    favorites.value = []
  }
}

async function onUnfavorite(item) {
  try {
    await toggleFavorite(getSessionId(), item.id)
    favorites.value = favorites.value.filter((row) => row.id !== item.id)
    uni.showToast({ title: '已取消收藏', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error.message || '操作失败', icon: 'none' })
  }
}

function refresh() {
  sessionId.value = getSessionId()
  history.value = getLocalHistory()
}

function onResetSession() {
  sessionId.value = resetSessionId()
  uni.showToast({ title: '已重新生成', icon: 'none' })
}

function onClear() {
  clearLocalHistory()
  history.value = []
  uni.showToast({ title: '已清空', icon: 'none' })
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/detail/detail?id=${id}` })
}

onMounted(() => {
  refresh()
  loadFavorites()
})

// 每次回到「我的」都刷新收藏，保证从详情页收藏后能立刻看到
onShow(() => {
  loadFavorites()
})
</script>

<style scoped>
.page {
  padding: 24rpx 24rpx 40rpx;
}

.profile {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #21463a, #2f7d4f);
  border-radius: 24rpx;
  padding: 30rpx 26rpx;
  color: #ffffff;
}

.avatar {
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  font-weight: 700;
}

.profile-body {
  margin-left: 22rpx;
}

.profile-name {
  font-size: 32rpx;
  font-weight: 700;
}

.profile-sub {
  font-size: 22rpx;
  opacity: 0.85;
  margin-top: 6rpx;
}

.section {
  margin-top: 20rpx;
}

.row {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f5f2;
  font-size: 24rpx;
}

.row-label {
  color: #8a9a90;
}

.row-value {
  color: #34493d;
  text-align: right;
  max-width: 420rpx;
}

.mono {
  font-family: Consolas, Monaco, monospace;
}

.btn.ghost {
  margin-top: 18rpx;
  background: #eef5f0;
  color: #2f7d4f;
  border-radius: 999rpx;
  font-size: 24rpx;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear {
  font-size: 24rpx;
  color: #b7791f;
}

.history-item {
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f5f2;
}

.hi-name {
  font-size: 26rpx;
  color: #21463a;
  font-weight: 600;
}

.hi-meta {
  font-size: 22rpx;
  color: #8a9a90;
  margin-top: 4rpx;
}

.empty {
  padding: 20rpx 0;
}

.paragraph {
  font-size: 24rpx;
  color: #566a5d;
  line-height: 1.75;
  margin-top: 10rpx;
}

.footer {
  margin-top: 34rpx;
  text-align: center;
  font-size: 22rpx;
  color: #9aa9a0;
}

.fav-item {
  display: flex;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f5f2;
}

.fav-thumb {
  width: 84rpx;
  height: 84rpx;
  border-radius: 14rpx;
  overflow: hidden;
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

.fav-img {
  width: 84rpx;
  height: 84rpx;
  display: block;
}

.fav-char {
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 700;
}

.fav-body {
  flex: 1;
  margin-left: 18rpx;
  min-width: 0;
}

.fav-cancel {
  font-size: 22rpx;
  color: #b7791f;
  padding: 8rpx 4rpx 8rpx 16rpx;
}
</style>
