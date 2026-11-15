import { createRouter, createWebHistory } from 'vue-router'

import { getToken } from '@/utils/token'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '运营概览' }
      },
      {
        path: 'attraction',
        name: 'attraction',
        component: () => import('@/views/attraction/index.vue'),
        meta: { title: '资源管理' }
      }
    ]
  },
  {
    // 大屏为独立全屏页面，不套管理后台布局
    path: '/screen',
    name: 'screen',
    component: () => import('@/views/screen/index.vue'),
    meta: { title: '实时数据大屏' }
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (to.meta.public) {
    return true
  }
  if (!getToken()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
