<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <h1>海宁乡村农文旅服务平台</h1>
        <p>Web 管理后台 · 基于 WebGIS 与多端协同</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="onSubmit">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入管理员账号" size="large" clearable>
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" size="large">
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="onSubmit">
          登录
        </el-button>
      </el-form>

      <div class="login-tip">演示账号：admin / admin123</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.replace(typeof redirect === 'string' && redirect ? redirect : '/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #21463a 0%, #2f7d4f 55%, #6aa882 100%);
}

.login-card {
  width: 400px;
  background: #fff;
  border-radius: 14px;
  padding: 34px 34px 26px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.25);
}

.login-brand h1 {
  font-size: 19px;
  margin: 0 0 6px;
  color: #21463a;
}

.login-brand p {
  font-size: 12px;
  color: #7b8b82;
  margin: 0 0 24px;
}

.login-btn {
  width: 100%;
  margin-top: 6px;
  background: #2f7d4f;
  border-color: #2f7d4f;
}

.login-tip {
  margin-top: 16px;
  font-size: 12px;
  color: #9aa9a0;
  text-align: center;
}
</style>
