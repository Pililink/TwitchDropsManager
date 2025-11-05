<template>
  <div class="admin-layout">
    <nav class="sidebar">
      <div class="logo">Twitch挂宝管理</div>
      <router-link to="/admin/overview" class="nav-item">📊 系统概览</router-link>
      <router-link to="/admin/users" class="nav-item">👥 用户管理</router-link>
      <router-link to="/admin/system" class="nav-item">⚙️ 系统管理</router-link>
      <button @click="handleLogout" class="logout-button">登出</button>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
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
  margin-bottom: 2rem;
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

