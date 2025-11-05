<template>
  <div class="user-layout">
    <nav class="sidebar">
      <div class="logo">Twitch挂宝</div>
      <div class="user-info">
        <div class="username">{{ username }}</div>
      </div>
      <router-link to="/user/dashboard" class="nav-item">仪表盘</router-link>
      <router-link to="/user/config" class="nav-item">配置</router-link>
      <router-link to="/user/logs" class="nav-item">日志</router-link>
      <button @click="handleLogout" class="logout-button">登出</button>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = computed(() => authStore.userInfo?.username || 'User')

const handleLogout = async () => {
  await authStore.logout()
  router.push('/twitch-login')
}
</script>

<style scoped>
.user-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 250px;
  background: #1f1f23;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 600;
  color: #efeff1;
  margin-bottom: 1rem;
}

.user-info {
  padding: 1rem;
  background: #18181b;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.username {
  color: #9147ff;
  font-weight: 600;
  font-size: 0.95rem;
}

.nav-item {
  padding: 0.75rem;
  color: #adadb8;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-item:hover,
.nav-item.router-link-active {
  background: #9147ff;
  color: white;
}

.logout-button {
  margin-top: auto;
  padding: 0.75rem;
  background: #ff3333;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background: #cc0000;
}

.main-content {
  flex: 1;
  padding: 2rem;
  background: #0e0e10;
}
</style>
