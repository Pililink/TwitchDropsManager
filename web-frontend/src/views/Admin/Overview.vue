<template>
  <div class="admin-overview">
    <h1>系统概览</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="stats-container">
      <!-- 用户统计 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon users-icon">👥</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon enabled-icon">✅</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.enabled_users }}</div>
            <div class="stat-label">启用用户</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon disabled-icon">⏸️</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.disabled_users }}</div>
            <div class="stat-label">禁用用户</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon campaigns-icon">🎮</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.active_campaigns_count }}</div>
            <div class="stat-label">活跃Campaign</div>
          </div>
        </div>
      </div>

      <!-- 状态统计 -->
      <div class="status-section">
        <h2>用户状态分布</h2>
        <div class="status-grid">
          <div class="status-item" v-for="(count, status) in stats.status_counts" :key="status">
            <span :class="['status-badge', status.toLowerCase()]">{{ status }}</span>
            <span class="status-count">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- 总进度 -->
      <div class="progress-section">
        <h2>总观看进度</h2>
        <div class="progress-info">
          <div class="progress-stats">
            <span class="progress-current">{{ stats.total_progress }}</span>
            <span class="progress-separator">/</span>
            <span class="progress-required">{{ stats.total_required }}</span>
            <span class="progress-unit">分钟</span>
          </div>
          <div class="progress-percentage">{{ Math.round(stats.progress_percentage) }}%</div>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar-fill" :style="{ width: stats.progress_percentage + '%' }"></div>
        </div>
      </div>

      <!-- 活跃游戏 -->
      <div class="games-section" v-if="stats.active_games && stats.active_games.length > 0">
        <h2>当前挂宝游戏</h2>
        <div class="games-grid">
          <div class="game-tag" v-for="game in stats.active_games" :key="game">
            {{ game }}
          </div>
        </div>
      </div>

      <!-- 活跃Campaign -->
      <div class="campaigns-section" v-if="stats.active_campaigns && stats.active_campaigns.length > 0">
        <h2>活跃Campaigns</h2>
        <div class="campaigns-list">
          <div class="campaign-item" v-for="campaign in stats.active_campaigns" :key="campaign">
            📌 {{ campaign }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '../../api/client'

const loading = ref(true)
const stats = ref<any>({
  total_users: 0,
  enabled_users: 0,
  disabled_users: 0,
  status_counts: {},
  total_progress: 0,
  total_required: 0,
  progress_percentage: 0,
  active_campaigns_count: 0,
  active_games_count: 0,
  active_campaigns: [],
  active_games: []
})

const loadStats = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/admin/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计信息失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  // 每30秒刷新一次
  setInterval(loadStats, 30000)
})
</script>

<style scoped>
.admin-overview {
  color: #efeff1;
}

h1 {
  margin-bottom: 2rem;
  font-size: 2rem;
}

h2 {
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: #adadb8;
}

.loading {
  text-align: center;
  padding: 3rem;
  font-size: 1.1rem;
}

.stats-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: linear-gradient(135deg, #1f1f23 0%, #2a2a2e 100%);
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid #3a3a3d;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(145, 71, 255, 0.2);
}

.stat-icon {
  font-size: 2.5rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(145, 71, 255, 0.1);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #9147ff;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.9rem;
  color: #adadb8;
}

.status-section,
.progress-section,
.games-section,
.campaigns-section {
  background: #1f1f23;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #3a3a3d;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #18181b;
  border-radius: 8px;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
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

.status-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #9147ff;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.progress-stats {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 1.2rem;
}

.progress-current {
  font-size: 1.8rem;
  font-weight: 700;
  color: #9147ff;
}

.progress-separator {
  color: #adadb8;
}

.progress-required {
  font-size: 1.5rem;
  color: #adadb8;
}

.progress-unit {
  font-size: 1rem;
  color: #6c757d;
}

.progress-percentage {
  font-size: 2rem;
  font-weight: 700;
  color: #28a745;
}

.progress-bar-container {
  width: 100%;
  height: 40px;
  background: #18181b;
  border-radius: 20px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #9147ff 0%, #772ce8 100%);
  transition: width 0.5s ease;
  border-radius: 20px;
}

.games-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.game-tag {
  background: linear-gradient(135deg, #9147ff 0%, #772ce8 100%);
  padding: 0.75rem 1.5rem;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(145, 71, 255, 0.3);
}

.campaigns-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.campaign-item {
  background: #18181b;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #9147ff;
  font-size: 1rem;
}
</style>
