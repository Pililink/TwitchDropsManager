<template>
  <div class="login-container">
    <div class="login-box">
      <h1>Twitch挂宝管理平台</h1>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            placeholder="请输入用户名"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="请输入密码"
          />
        </div>
        <button type="submit" :disabled="loading" class="login-button">
          {{ loading ? '登录中...' : '管理员登录' }}
        </button>
        <div v-if="error" class="error-message">{{ error }}</div>
      </form>

      <div class="user-login-link">
        <p>普通用户？</p>
        <router-link to="/twitch-login" class="link">通过Twitch登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    await authStore.login(username.value, password.value)
    router.push('/admin/users')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
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
  max-width: 400px;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #efeff1;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  color: #adadb8;
  font-size: 0.9rem;
}

input {
  padding: 0.75rem;
  background: #0e0e10;
  border: 1px solid #3a3a3d;
  border-radius: 4px;
  color: #efeff1;
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: #9147ff;
}

.login-button {
  padding: 0.75rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.login-button:hover:not(:disabled) {
  background: #772ce8;
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #ff3333;
  text-align: center;
  font-size: 0.9rem;
}

.user-login-link {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #3a3a3d;
}

.user-login-link p {
  color: #adadb8;
  margin-bottom: 0.5rem;
}

.user-login-link .link {
  color: #9147ff;
  text-decoration: none;
  font-weight: 600;
}

.user-login-link .link:hover {
  text-decoration: underline;
}
</style>

