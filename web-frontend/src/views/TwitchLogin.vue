<template>
  <div class="login-container">
    <div class="login-box">
      <h1>Twitch用户登录</h1>

      <div v-if="!deviceCode" class="step">
        <p class="info">通过Twitch账号登录查看你的挂宝状态</p>
        <button @click="initiateLogin" :disabled="loading" class="login-button">
          {{ loading ? '请稍候...' : '使用Twitch登录' }}
        </button>
      </div>

      <div v-else-if="!loggingIn" class="step">
        <h2>请完成Twitch授权</h2>
        <p class="instruction">1. 访问以下链接：</p>
        <a :href="verificationUri" target="_blank" class="verification-link">
          {{ verificationUri }}
        </a>
        <p class="instruction">2. 输入以下代码：</p>
        <div class="code">{{ userCode }}</div>
        <button @click="pollLogin" :disabled="polling" class="login-button">
          {{ polling ? '等待授权中...' : '我已完成授权' }}
        </button>
        <button @click="resetLogin" class="secondary-button">重新开始</button>
      </div>

      <div v-else class="step">
        <div class="loading-spinner"></div>
        <p>正在登录...</p>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="admin-link">
        <router-link to="/login">管理员登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const polling = ref(false)
const loggingIn = ref(false)
const deviceCode = ref('')
const userCode = ref('')
const verificationUri = ref('')
const error = ref('')

const initiateLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.post('/auth/user/twitch/initiate')
    deviceCode.value = response.data.device_code
    userCode.value = response.data.user_code
    verificationUri.value = response.data.verification_uri
  } catch (err: any) {
    error.value = err.response?.data?.detail || '启动登录失败'
  } finally {
    loading.value = false
  }
}

const pollLogin = async () => {
  polling.value = true
  error.value = ''

  try {
    const response = await apiClient.post('/auth/user/twitch/login', null, {
      params: { device_code: deviceCode.value }
    })

    // 登录成功，保存token
    const token = response.data.access_token
    localStorage.setItem('token', token)
    authStore.token = token

    // 设置axios默认header
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`

    // 获取用户信息
    const userResponse = await apiClient.get('/auth/me')
    authStore.userInfo = userResponse.data
    authStore.userType = userResponse.data.type

    loggingIn.value = true

    // 跳转到用户dashboard
    setTimeout(() => {
      router.push('/user/dashboard')
    }, 500)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请确认已完成授权'
  } finally {
    polling.value = false
  }
}

const resetLogin = () => {
  deviceCode.value = ''
  userCode.value = ''
  verificationUri.value = ''
  error.value = ''
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0e0e10 0%, #18181b 100%);
}

.login-box {
  background: #1f1f23;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 500px;
}

h1 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: #efeff1;
}

h2 {
  color: #efeff1;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.step {
  margin: 2rem 0;
}

.info {
  text-align: center;
  color: #adadb8;
  margin-bottom: 2rem;
}

.instruction {
  color: #adadb8;
  margin: 1rem 0 0.5rem 0;
}

.verification-link {
  display: block;
  color: #9147ff;
  text-decoration: none;
  word-break: break-all;
  padding: 0.75rem;
  background: #0e0e10;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.verification-link:hover {
  background: #18181b;
}

.code {
  font-size: 2rem;
  font-weight: 600;
  color: #9147ff;
  text-align: center;
  padding: 1.5rem;
  background: #0e0e10;
  border-radius: 8px;
  letter-spacing: 0.2em;
  margin: 1rem 0;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 1rem;
}

.login-button:hover:not(:disabled) {
  background: #772ce8;
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.secondary-button {
  width: 100%;
  padding: 0.75rem;
  background: #3a3a3d;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 0.5rem;
}

.secondary-button:hover {
  background: #4a4a4d;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #3a3a3d;
  border-top-color: #9147ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 2rem auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #ff3333;
  text-align: center;
  padding: 1rem;
  background: rgba(255, 51, 51, 0.1);
  border-radius: 4px;
  margin-top: 1rem;
}

.admin-link {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #3a3a3d;
}

.admin-link a {
  color: #adadb8;
  text-decoration: none;
  font-size: 0.9rem;
}

.admin-link a:hover {
  color: #9147ff;
}
</style>
