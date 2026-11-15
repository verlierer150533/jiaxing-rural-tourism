import axios from 'axios'
import { ElMessage } from 'element-plus'

import router from '@/router'
import { clearToken, getToken } from '@/utils/token'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const payload = response.data
    // 统一响应体 {code, message, data}
    if (payload && typeof payload.code !== 'undefined' && payload.code !== 0) {
      ElMessage.error(payload.message || '请求失败')
      return Promise.reject(new Error(payload.message || '请求失败'))
    }
    return payload ? payload.data : null
  },
  (error) => {
    const status = error.response ? error.response.status : 0
    const body = error.response ? error.response.data : null
    const message = (body && body.message) || '网络异常，请稍后重试'

    if (status === 401) {
      clearToken()
      if (router.currentRoute.value.name !== 'login') {
        ElMessage.warning('登录已过期，请重新登录')
        router.replace({ name: 'login' })
      }
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default request
