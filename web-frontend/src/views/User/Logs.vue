<template>
  <div class="user-logs">
    <h1>我的日志</h1>

    <div v-if="loading && logs.length === 0" class="loading">加载中...</div>

    <div v-else class="logs-container">
      <div v-for="(log, index) in logs" :key="index" class="log-entry">
        <span class="log-level" :class="log.level.toLowerCase()">[{{ log.level }}]</span>
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>

      <div v-if="logs.length === 0" class="no-logs">暂无日志</div>
    </div>

    <div class="pagination">
      <button @click="prevPage" :disabled="page === 1">上一页</button>
      <span>第 {{ page }} 页，共 {{ totalPages }} 页 (总计 {{ total }} 条)</span>
      <button @click="nextPage" :disabled="page >= totalPages">下一页</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { apiClient } from '../../api/client'

const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(100)
const total = ref(0)
const loading = ref(false)
const error = ref('')
let refreshInterval: number | null = null

const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

const loadLogs = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get('/user/logs', {
      params: {
        page: page.value,
        page_size: pageSize.value
      }
    })
    logs.value = response.data.logs
    total.value = response.data.total
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载日志失败'
    console.error('加载日志失败:', err)
  } finally {
    loading.value = false
  }
}

const formatTime = (isoString: string) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    loadLogs()
  }
}

const nextPage = () => {
  if (page.value < totalPages.value) {
    page.value++
    loadLogs()
  }
}

onMounted(() => {
  loadLogs()
  // 每60秒刷新一次
  refreshInterval = window.setInterval(loadLogs, 60000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.user-logs {
  color: #efeff1;
}

h1 {
  margin-bottom: 2rem;
  font-size: 2rem;
}

.loading, .no-logs {
  text-align: center;
  padding: 3rem;
  color: #adadb8;
}

.error {
  color: #ff3333;
  text-align: center;
  padding: 1rem;
  background: rgba(255, 51, 51, 0.1);
  border-radius: 4px;
  margin-top: 1rem;
}

.logs-container {
  background: #1f1f23;
  padding: 1rem;
  border-radius: 8px;
  max-height: 600px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.log-entry {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  border-bottom: 1px solid #3a3a3d;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85rem;
  line-height: 1.6;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-level {
  font-weight: 600;
  min-width: 50px;
  flex-shrink: 0;
}

.log-level.inf {
  color: #28a745;
}

.log-level.wrn {
  color: #ffc107;
}

.log-level.err {
  color: #dc3545;
}

.log-time {
  color: #6c757d;
  min-width: 180px;
  flex-shrink: 0;
}

.log-message {
  color: #efeff1;
  flex: 1;
  word-break: break-word;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
}

.pagination button {
  padding: 0.5rem 1rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  background: #772ce8;
}

.pagination button:disabled {
  background: #3a3a3d;
  cursor: not-allowed;
  opacity: 0.5;
}

.pagination span {
  color: #adadb8;
}
</style>
