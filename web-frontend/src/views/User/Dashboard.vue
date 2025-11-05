<template>
  <div class="user-dashboard">
    <h1>我的仪表盘</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else-if="dashboardData">
      <div class="status-card">
        <h2>当前状态</h2>
        <div class="status-info">
          <span :class="['status-badge', dashboardData.status.toLowerCase()]">
            {{ dashboardData.status }}
          </span>
          <p v-if="dashboardData.last_update">
            最后更新: {{ formatTime(dashboardData.last_update) }}
          </p>
          <p class="enabled-status">
            Bot状态: {{ dashboardData.enabled ? '已启用' : '已禁用' }}
          </p>
        </div>
      </div>

      <div v-if="dashboardData.campaign" class="campaign-card">
        <h2>当前Campaign</h2>
        <p><strong>游戏:</strong> {{ dashboardData.campaign.game }}</p>
        <p><strong>Campaign:</strong> {{ dashboardData.campaign.campaign }}</p>
      </div>

      <div v-if="dashboardData.broadcaster" class="broadcaster-card">
        <h2>正在观看</h2>
        <p class="broadcaster-name">{{ dashboardData.broadcaster }}</p>
      </div>

      <div v-if="dashboardData.progress" class="progress-card">
        <h2>观看进度</h2>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: dashboardData.progress.percentage + '%' }"
          ></div>
        </div>
        <p>{{ dashboardData.progress.current }} / {{ dashboardData.progress.required }} 分钟
          ({{ Math.round(dashboardData.progress.percentage) }}%)</p>
      </div>

      <div v-if="dashboardData.favourite_games && dashboardData.favourite_games.length > 0" class="games-card">
        <h2>我的优先游戏</h2>
        <div class="games-list">
          <span v-for="game in dashboardData.favourite_games" :key="game" class="game-tag">
            {{ game }}
          </span>
        </div>
      </div>
    </template>

    <div v-else-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { apiClient } from '../../api/client'

const loading = ref(true)
const error = ref('')
const dashboardData = ref<any>(null)
let refreshInterval: number | null = null

const loadDashboard = async () => {
  try {
    const response = await apiClient.get('/user/dashboard')
    dashboardData.value = response.data
    console.log('[Dashboard] 接收到的数据:', response.data)
    console.log('[Dashboard] campaign:', response.data.campaign)
    console.log('[Dashboard] broadcaster:', response.data.broadcaster)
    console.log('[Dashboard] progress:', response.data.progress)
    error.value = ''
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载仪表盘失败'
    console.error('加载仪表盘失败:', err)
  } finally {
    loading.value = false
  }
}

const formatTime = (isoString: string) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadDashboard()
  // 每30秒刷新一次
  refreshInterval = window.setInterval(loadDashboard, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.user-dashboard {
  color: #efeff1;
}

h1 {
  margin-bottom: 2rem;
  font-size: 2rem;
}

h2 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #adadb8;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
  font-size: 1.1rem;
}

.error {
  color: #ff3333;
}

.status-card, .campaign-card, .broadcaster-card, .progress-card, .games-card {
  background: #1f1f23;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.status-info p {
  margin: 0.5rem 0;
  color: #adadb8;
}

.enabled-status {
  font-weight: 600;
  color: #9147ff;
}

.status-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.status-badge.idle {
  background: #6c757d;
}

.status-badge.seeking {
  background: #ffc107;
  color: #000;
}

.status-badge.watching {
  background: #28a745;
}

.status-badge.error {
  background: #dc3545;
}

.status-badge.unknown {
  background: #3a3a3d;
}

.broadcaster-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #9147ff;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background: #3a3a3d;
  border-radius: 15px;
  overflow: hidden;
  margin: 1rem 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #9147ff 0%, #772ce8 100%);
  transition: width 0.5s ease;
}

.games-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.game-tag {
  background: #9147ff;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
}
</style>

