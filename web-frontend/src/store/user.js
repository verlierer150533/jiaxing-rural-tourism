import { defineStore } from 'pinia'

import { getProfile, login as loginApi } from '@/api/auth'
import { clearToken, getAdmin, getToken, setAdmin, setToken } from '@/utils/token'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    admin: getAdmin()
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    displayName: (state) => {
      if (!state.admin) return '未登录'
      return state.admin.real_name || state.admin.username
    }
  },
  actions: {
    async login(payload) {
      const data = await loginApi(payload)
      this.token = data.access_token
      this.admin = data.admin
      setToken(data.access_token)
      setAdmin(data.admin)
      return data
    },
    async loadProfile() {
      const admin = await getProfile()
      this.admin = admin
      setAdmin(admin)
      return admin
    },
    logout() {
      this.token = ''
      this.admin = null
      clearToken()
    }
  }
})
