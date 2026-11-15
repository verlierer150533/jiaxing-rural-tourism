<template>
  <el-container class="layout">
    <el-aside width="216px" class="aside">
      <div class="brand">
        <!-- 手绘风 Logo：屋脊 + 潮水，呼应“古镇 + 钱塘潮” -->
        <svg class="brand-logo" viewBox="0 0 40 40" aria-hidden="true">
          <defs>
            <linearGradient id="jrtLogoGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#4ec9b0" />
              <stop offset="1" stop-color="#e2c275" />
            </linearGradient>
          </defs>
          <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="url(#jrtLogoGrad)" opacity="0.16" />
          <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="none" stroke="url(#jrtLogoGrad)"
            stroke-width="1.2" opacity="0.65" />
          <path d="M20 8.5 L32 17.5 H8 Z" fill="url(#jrtLogoGrad)" />
          <rect x="12.5" y="17.4" width="15" height="1.6" rx="0.8" fill="#e2c275" opacity="0.75" />
          <path d="M8.5 23.5 q5.2 -4 10.5 0 t10.5 0" fill="none" stroke="#4ec9b0" stroke-width="1.8"
            stroke-linecap="round" />
          <path d="M8.5 29 q5.2 -4 10.5 0 t10.5 0" fill="none" stroke="#e2c275" stroke-width="1.8"
            stroke-linecap="round" opacity="0.75" />
        </svg>
        <div class="brand-text">
          <div class="brand-title">海宁乡村农文旅</div>
          <div class="brand-sub">信息展示与服务平台</div>
        </div>
      </div>

      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>运营概览</span>
        </el-menu-item>
        <el-menu-item index="/attraction">
          <el-icon><Location /></el-icon>
          <span>资源管理</span>
        </el-menu-item>
        <el-menu-item index="/screen">
          <el-icon><Monitor /></el-icon>
          <span>实时数据大屏</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header" height="56px">
        <div class="header-left">{{ currentTitle }}</div>
        <div class="header-right">
          <el-tag type="success" effect="plain" size="small">Web 管理端</el-tag>
          <el-dropdown @command="onCommand">
            <span class="user">
              {{ userStore.displayName }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">账号信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '管理后台')

async function onCommand(command) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    userStore.logout()
    router.replace({ name: 'login' })
    return
  }
  if (command === 'profile') {
    ElMessage.info(
      `账号：${userStore.admin?.username || '-'}　角色：${userStore.admin?.role || '-'}`
    )
  }
}
</script>

<style scoped>
.layout {
  height: 100%;
}

.aside {
  background: linear-gradient(180deg, #1d4436 0%, #123026 100%);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.04);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 18px 14px;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-logo {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.28));
}

.brand-text {
  min-width: 0;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  white-space: nowrap;
}

.brand-sub {
  font-size: 11px;
  opacity: 0.68;
  margin-top: 3px;
  letter-spacing: 0.5px;
}

.menu {
  border-right: none;
  flex: 1;
  background: transparent;
  padding-top: 8px;
}

.menu :deep(.el-menu-item) {
  color: #cfded6;
  height: 44px;
  line-height: 44px;
  margin: 4px 10px;
  border-radius: 8px;
  font-size: 14px;
}

.menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(78, 201, 176, 0.22), rgba(201, 162, 39, 0.14));
  color: #ffffff;
  box-shadow: inset 3px 0 0 #e2c275;
}

.header {
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(47, 125, 79, 0.12);
}

.header-left {
  font-size: 15px;
  font-weight: 600;
  position: relative;
  padding-left: 12px;
}

.header-left::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--jrt-green), var(--jrt-gold));
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--jrt-green);
}

.main {
  padding: 18px 20px;
  background: transparent;
  overflow: auto;
}
</style>
