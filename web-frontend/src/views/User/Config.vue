<template>
  <div class="user-config">
    <h1>我的配置</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else-if="config">
      <div class="config-card">
        <h2>Bot状态</h2>
        <p class="status-info">
          当前状态: <strong :class="config.Enabled ? 'enabled' : 'disabled'">
            {{ config.Enabled ? '已启用' : '已禁用' }}
          </strong>
        </p>
        <p class="note">注意：只有管理员可以启用/禁用Bot</p>
      </div>

      <div class="config-card">
        <h2>优先游戏列表</h2>
        <p class="info">设置你想优先获取Drops的游戏</p>

        <div class="games-editor">
          <div class="games-list">
            <div
              v-for="(game, index) in favouriteGames"
              :key="index"
              class="game-item"
            >
              <span>{{ game }}</span>
              <button @click="removeGame(index)" class="remove-btn">✕</button>
            </div>
          </div>

          <div class="add-game">
            <input
              v-model="newGame"
              @keyup.enter="addGame"
              type="text"
              placeholder="输入游戏名称"
              class="game-input"
            />
            <button @click="addGame" class="add-btn">添加</button>
          </div>
        </div>

        <button
          @click="saveConfig"
          :disabled="saving"
          class="save-button"
        >
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>

      <div v-if="message" :class="['message', messageType]">{{ message }}</div>
    </template>

    <div v-else-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '../../api/client'

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const config = ref<any>(null)
const favouriteGames = ref<string[]>([])
const newGame = ref('')

const loadConfig = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/user/config')
    config.value = response.data
    favouriteGames.value = [...response.data.FavouriteGames]
    error.value = ''
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载配置失败'
  } finally {
    loading.value = false
  }
}

const addGame = () => {
  const game = newGame.value.trim()
  if (game && !favouriteGames.value.includes(game)) {
    favouriteGames.value.push(game)
    newGame.value = ''
  }
}

const removeGame = (index: number) => {
  favouriteGames.value.splice(index, 1)
}

const saveConfig = async () => {
  saving.value = true
  message.value = ''

  try {
    await apiClient.put('/user/config', {
      FavouriteGames: favouriteGames.value
    })
    message.value = '配置已保存'
    messageType.value = 'success'

    // 刷新配置
    await loadConfig()
  } catch (err: any) {
    message.value = err.response?.data?.detail || '保存配置失败'
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.user-config {
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

.config-card {
  background: #1f1f23;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.status-info {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.status-info strong {
  font-weight: 600;
}

.status-info .enabled {
  color: #28a745;
}

.status-info .disabled {
  color: #dc3545;
}

.note {
  color: #adadb8;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.info {
  color: #adadb8;
  margin-bottom: 1rem;
}

.games-editor {
  margin: 1.5rem 0;
}

.games-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
  min-height: 3rem;
}

.game-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #9147ff;
  padding: 0.5rem 1rem;
  border-radius: 20px;
}

.remove-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  color: #ff3333;
}

.add-game {
  display: flex;
  gap: 0.5rem;
}

.game-input {
  flex: 1;
  padding: 0.75rem;
  background: #0e0e10;
  border: 1px solid #3a3a3d;
  border-radius: 4px;
  color: #efeff1;
  font-size: 1rem;
}

.game-input:focus {
  outline: none;
  border-color: #9147ff;
}

.add-btn {
  padding: 0.75rem 1.5rem;
  background: #3a3a3d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.add-btn:hover {
  background: #4a4a4d;
}

.save-button {
  width: 100%;
  padding: 1rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.save-button:hover:not(:disabled) {
  background: #772ce8;
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message {
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
  margin-top: 1rem;
}

.message.success {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.message.error {
  background: rgba(255, 51, 51, 0.2);
  color: #ff3333;
}
</style>
