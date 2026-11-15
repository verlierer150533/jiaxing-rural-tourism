<template>
  <view class="page">
    <view class="tabs">
      <view
        v-for="item in tabs"
        :key="item.value"
        class="tab"
        :class="{ active: category === item.value }"
        @tap="onTab(item.value)"
      >
        {{ item.label }}
      </view>
    </view>

    <view class="search">
      <input v-model="keyword" class="search-input" placeholder="搜索名称 / 镇街" confirm-type="search"
        @confirm="reload" />
      <text class="search-btn" @tap="reload">搜索</text>
    </view>

    <view v-if="loading" class="muted empty">加载中…</view>
    <view v-else-if="!list.length" class="muted empty">没有符合条件的资源</view>

    <view v-for="item in list" :key="item.id" class="item" @tap="goDetail(item.id)">
      <view class="thumb" :class="categoryClass(item.category)">{{ item.category.slice(0, 1) }}</view>
      <view class="body">
        <view class="name">{{ item.name }}</view>
        <view class="meta">{{ item.town }} · {{ item.category }}</view>
        <view class="summary">{{ item.summary }}</view>
      </view>
      <view class="arrow">›</view>
    </view>

    <view v-if="hasMore && !loading" class="load-more" @tap="loadMore">加载更多</view>
    <view v-else-if="list.length" class="muted end">已经到底啦</view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { categoryClass } from '../../utils/category'
import { onLoad } from '@dcloudio/uni-app'

import { fetchAttractions } from '../../api/attraction'

const tabs = [
  { label: '全部', value: '' },
  { label: '果园', value: '果园' },
  { label: '古镇', value: '古镇' },
  { label: '村落', value: '村落' },
  { label: '景区', value: '景区' }
]

const list = ref([])
const category = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)

const hasMore = ref(false)

async function load(reset = false) {
  loading.value = true
  try {
    const data = await fetchAttractions({
      page: page.value,
      page_size: pageSize,
      category: category.value || undefined,
      keyword: keyword.value || undefined
    })
    const rows = data.list || []
    list.value = reset ? rows : list.value.concat(rows)
    total.value = data.total || 0
    hasMore.value = list.value.length < total.value
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load(true)
}

function loadMore() {
  page.value += 1
  load(false)
}

function onTab(value) {
  category.value = value
  reload()
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/detail/detail?id=${id}` })
}

onLoad((query) => {
  if (query && query.category) {
    category.value = query.category
  }
})

onMounted(() => {
  load(true)
})
</script>

<style scoped>
.page {
  padding: 20rpx 24rpx 40rpx;
}

.tabs {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.tab {
  padding: 10rpx 26rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #34493d;
  font-size: 24rpx;
}

.tab.active {
  background: #2f7d4f;
  color: #ffffff;
}

.search {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 999rpx;
  padding: 12rpx 22rpx;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  font-size: 26rpx;
}

.search-btn {
  color: #2f7d4f;
  font-size: 26rpx;
  margin-left: 12rpx;
}

.item {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 14rpx;
}

.thumb {
  width: 92rpx;
  height: 92rpx;
  border-radius: 16rpx;
  color: #ffffff;
  font-size: 36rpx;
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

.body {
  flex: 1;
  margin-left: 18rpx;
  min-width: 0;
}

.name {
  font-size: 28rpx;
  font-weight: 600;
  color: #21463a;
}

.meta {
  font-size: 22rpx;
  color: #2f7d4f;
  margin-top: 4rpx;
}

.summary {
  font-size: 22rpx;
  color: #6c7d72;
  margin-top: 6rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  color: #b9c7bf;
  font-size: 34rpx;
  margin-left: 8rpx;
}

.empty,
.end {
  text-align: center;
  padding: 30rpx 0;
}

.load-more {
  text-align: center;
  color: #2f7d4f;
  font-size: 26rpx;
  padding: 20rpx 0;
}
</style>
