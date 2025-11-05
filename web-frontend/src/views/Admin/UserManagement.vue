<template>
  <div class="user-management">
    <div class="header">
      <h1>用户管理</h1>
      <div class="header-actions">
        <button @click="showAddUser = true" class="add-button">添加用户</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="users-table">
      <table>
        <thead>
          <tr>
            <th>用户名</th>
            <th>状态</th>
            <th>启用</th>
            <th>游戏</th>
            <th>Campaign</th>
            <th>进度</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.Id">
            <td>
              <span class="username-link" @click="showUserDetail(user.Id)">
                {{ user.Login }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', user.status.status.toLowerCase()]">
                {{ user.status.status }}
              </span>
            </td>
            <td>
              <input
                type="checkbox"
                :checked="user.Enabled"
                @change="toggleUser(user.Id, $event)"
              />
            </td>
            <td>
              <span class="game-name">{{ user.status.campaign?.game || '-' }}</span>
            </td>
            <td>{{ user.status.campaign?.campaign || '-' }}</td>
            <td>
              <div v-if="user.status.progress" class="progress">
                {{ user.status.progress.current }}/{{ user.status.progress.required }} 分钟
              </div>
              <span v-else>-</span>
            </td>
            <td>
              <button @click="deleteUser(user.Id)" class="delete-button">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 添加用户对话框 -->
    <div v-if="showAddUser" class="modal">
      <div class="modal-content">
        <h2>添加Twitch用户</h2>

        <div v-if="addUserState === 'initial'" class="step">
          <p class="info">通过调用C# bot的 --add-account 命令添加用户</p>
          <button @click="() => { console.log('[UserManagement] 点击了启动添加用户按钮'); initiateAddUser(); }" :disabled="loading" class="primary-button">
            {{ loading ? '启动中...' : '启动添加用户流程' }}
          </button>
        </div>

        <div v-else-if="addUserState === 'auth_required'" class="step">
          <p class="success">✅ C# Bot已启动，请完成Twitch授权：</p>
          <div class="auth-box">
            <p><strong>访问链接：</strong></p>
            <a :href="verificationUri" target="_blank" class="auth-link">{{ verificationUri }}</a>
            <p><strong>输入代码：</strong></p>
            <p class="code">{{ userCode }}</p>
          </div>
          <p class="instruction">完成授权后，bot会自动添加用户到系统</p>
          <input
            v-model="checkUsername"
            placeholder="输入Twitch用户名检查是否已添加"
            class="input-field"
          />
          <button @click="checkUserAdded" :disabled="checking" class="primary-button">
            {{ checking ? '检查中...' : '检查用户是否已添加' }}
          </button>
          <p v-if="checkMessage" :class="['message', checkSuccess ? 'success' : 'error']">
            {{ checkMessage }}
          </p>
        </div>

        <div v-else-if="addUserState === 'error'" class="step">
          <p class="error">❌ {{ errorMessage }}</p>
          <p v-if="botOutput" class="bot-output">Bot输出：<br>{{ botOutput }}</p>
          <button @click="resetAddUser" class="primary-button">重试</button>
        </div>

        <button @click="closeModal" class="close-button">关闭</button>
      </div>
    </div>

    <!-- 用户详情对话框 -->
    <div v-if="showDetail" class="modal">
      <div class="modal-content detail-modal">
        <h2>用户详细信息</h2>

        <div v-if="loadingDetail" class="loading">加载中...</div>

        <div v-else-if="userDetail" class="detail-content">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">用户名:</span>
                <span class="detail-value">{{ userDetail.user.Login }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">用户ID:</span>
                <span class="detail-value">{{ userDetail.user.Id }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">状态:</span>
                <span :class="['status-badge', userDetail.status.toLowerCase()]">
                  {{ userDetail.status }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">启用:</span>
                <span class="detail-value">{{ userDetail.user.Enabled ? '是' : '否' }}</span>
              </div>
            </div>
          </div>

          <!-- Campaign信息 -->
          <div class="detail-section" v-if="userDetail.campaign">
            <h3>Campaign信息</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">游戏:</span>
                <span class="detail-value game-name">{{ userDetail.campaign.game }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Campaign:</span>
                <span class="detail-value">{{ userDetail.campaign.campaign }}</span>
              </div>
            </div>
          </div>

          <!-- 观看信息 -->
          <div class="detail-section" v-if="userDetail.broadcaster || userDetail.progress">
            <h3>观看信息</h3>
            <div class="detail-grid">
              <div class="detail-item" v-if="userDetail.broadcaster">
                <span class="detail-label">正在观看:</span>
                <span class="detail-value broadcaster-name">{{ userDetail.broadcaster }}</span>
              </div>
              <div class="detail-item full-width" v-if="userDetail.progress">
                <span class="detail-label">进度:</span>
                <div class="progress-detail">
                  <div class="progress-bar-small">
                    <div
                      class="progress-fill-small"
                      :style="{ width: userDetail.progress.percentage + '%' }"
                    ></div>
                  </div>
                  <span class="progress-text">
                    {{ userDetail.progress.current }} / {{ userDetail.progress.required }} 分钟
                    ({{ Math.round(userDetail.progress.percentage) }}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 优先游戏 -->
          <div class="detail-section" v-if="userDetail.user.FavouriteGames && userDetail.user.FavouriteGames.length > 0">
            <h3>优先游戏</h3>
            <div class="favourite-games">
              <span class="game-tag-small" v-for="game in userDetail.user.FavouriteGames" :key="game">
                {{ game }}
              </span>
            </div>
          </div>

          <!-- 最近日志 -->
          <div class="detail-section" v-if="userDetail.recent_logs && userDetail.recent_logs.length > 0">
            <h3>最近日志 (最新20条)</h3>
            <div class="logs-container">
              <div class="log-line" v-for="(log, index) in userDetail.recent_logs" :key="index">
                {{ log }}
              </div>
            </div>
          </div>

          <!-- 最后更新时间 -->
          <div class="detail-section" v-if="userDetail.last_update">
            <div class="detail-item">
              <span class="detail-label">最后更新:</span>
              <span class="detail-value">{{ formatTime(userDetail.last_update) }}</span>
            </div>
          </div>
        </div>

        <button @click="closeDetailModal" class="close-button">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '../../api/client'

const users = ref<any[]>([])
const loading = ref(false)
const showAddUser = ref(false)
const addUserState = ref<'initial' | 'auth_required' | 'error'>('initial')
const userCode = ref('')
const verificationUri = ref('')
const checkUsername = ref('')
const checking = ref(false)
const checkMessage = ref('')
const checkSuccess = ref(false)
const errorMessage = ref('')
const botOutput = ref('')
const showDetail = ref(false)
const loadingDetail = ref(false)
const userDetail = ref<any>(null)

const loadUsers = async () => {
  console.log('[UserManagement] 加载用户列表...')
  loading.value = true
  try {
    const response = await apiClient.get('/admin/users')
    console.log('[UserManagement] 用户列表加载成功，数量:', response.data.users.length)
    users.value = response.data.users
  } catch (error) {
    console.error('[UserManagement] 加载用户失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleUser = async (userId: string, event: Event) => {
  const enabled = (event.target as HTMLInputElement).checked
  try {
    await apiClient.patch(`/admin/users/${userId}/enable`, { enabled })
    await loadUsers()
  } catch (error) {
    console.error('更新用户状态失败:', error)
  }
}

const deleteUser = async (userId: string) => {
  if (!confirm('确定要删除该用户吗？')) return
  try {
    await apiClient.delete(`/admin/users/${userId}`)
    await loadUsers()
  } catch (error) {
    console.error('删除用户失败:', error)
  }
}

const initiateAddUser = async () => {
  console.log('[UserManagement] ========== 开始添加用户流程 ==========')
  loading.value = true

  try {
    console.log('[UserManagement] 步骤1: 调用添加用户API')
    console.log('[UserManagement] API地址: /admin/users/add/initiate')

    const response = await apiClient.post('/admin/users/add/initiate')

    console.log('[UserManagement] 步骤2: API调用成功')
    console.log('[UserManagement] 响应状态码:', response.status)
    console.log('[UserManagement] 响应数据:', JSON.stringify(response.data, null, 2))
    console.log('[UserManagement] 响应数据.status:', response.data.status)
    console.log('[UserManagement] 响应数据.user_code:', response.data.user_code)
    console.log('[UserManagement] 响应数据.verification_uri:', response.data.verification_uri)
    console.log('[UserManagement] 响应数据.message:', response.data.message)
    console.log('[UserManagement] 响应数据.bot_output:', response.data.bot_output)

    if (response.data.status === 'success') {
      // 成功提取到授权信息
      console.log('[UserManagement] 步骤3: 成功提取授权信息')
      console.log('[UserManagement] 设置状态为: auth_required')
      console.log('[UserManagement] 用户代码:', response.data.user_code)
      console.log('[UserManagement] 授权链接:', response.data.verification_uri)

      addUserState.value = 'auth_required'
      userCode.value = response.data.user_code
      verificationUri.value = response.data.verification_uri

      console.log('[UserManagement] 状态更新完成')
      console.log('[UserManagement] addUserState.value:', addUserState.value)
      console.log('[UserManagement] userCode.value:', userCode.value)
      console.log('[UserManagement] verificationUri.value:', verificationUri.value)
    } else {
      // 没有提取到授权信息，显示bot输出
      console.log('[UserManagement] 步骤3: 未能提取授权信息')
      console.log('[UserManagement] 响应状态:', response.data.status)
      console.log('[UserManagement] 错误消息:', response.data.message)
      console.log('[UserManagement] Bot输出:', response.data.bot_output)
      console.log('[UserManagement] 设置状态为: error')

      addUserState.value = 'error'
      errorMessage.value = response.data.message
      botOutput.value = response.data.bot_output || ''

      console.log('[UserManagement] 错误状态设置完成')
    }
  } catch (error: any) {
    console.error('[UserManagement] ========== API调用异常 ==========')
    console.error('[UserManagement] 错误对象:', error)
    console.error('[UserManagement] 错误消息:', error.message)
    console.error('[UserManagement] 响应数据:', error.response?.data)
    console.error('[UserManagement] 响应状态码:', error.response?.status)
    console.error('[UserManagement] 完整错误:', JSON.stringify(error, null, 2))

    addUserState.value = 'error'
    errorMessage.value = error.response?.data?.detail || '启动失败'

    console.error('[UserManagement] 错误状态设置完成')
  } finally {
    loading.value = false
    console.log('[UserManagement] ========== 添加用户流程结束 ==========')
    console.log('[UserManagement] 最终状态: addUserState.value =', addUserState.value)
    console.log('[UserManagement] loading =', loading.value)
  }
}

const checkUserAdded = async () => {
  console.log('[UserManagement] ========== 开始检查用户 ==========')
  console.log('[UserManagement] 输入的用户名:', checkUsername.value)

  if (!checkUsername.value.trim()) {
    console.log('[UserManagement] 用户名为空，终止检查')
    checkMessage.value = '请输入用户名'
    checkSuccess.value = false
    return
  }

  checking.value = true
  checkMessage.value = ''

  try {
    console.log('[UserManagement] 调用检查用户API')
    console.log('[UserManagement] API地址:', `/admin/users/check/${checkUsername.value}`)

    const response = await apiClient.get(`/admin/users/check/${checkUsername.value}`)

    console.log('[UserManagement] API响应:', JSON.stringify(response.data, null, 2))
    console.log('[UserManagement] 用户是否已添加:', response.data.added)

    if (response.data.added) {
      console.log('[UserManagement] ✅ 用户已成功添加')
      checkMessage.value = `✅ 用户 ${checkUsername.value} 已成功添加！`
      checkSuccess.value = true
      // 刷新用户列表并关闭对话框
      console.log('[UserManagement] 2秒后刷新用户列表并关闭对话框')
      setTimeout(async () => {
        console.log('[UserManagement] 刷新用户列表...')
        await loadUsers()
        console.log('[UserManagement] 关闭对话框...')
        closeModal()
      }, 2000)
    } else {
      console.log('[UserManagement] ⚠️ 用户尚未添加')
      checkMessage.value = '用户尚未添加，请确认已完成Twitch授权'
      checkSuccess.value = false
    }
  } catch (error: any) {
    console.error('[UserManagement] ========== 检查用户失败 ==========')
    console.error('[UserManagement] 错误:', error)
    console.error('[UserManagement] 响应数据:', error.response?.data)
    checkMessage.value = error.response?.data?.detail || '检查失败'
    checkSuccess.value = false
  } finally {
    checking.value = false
    console.log('[UserManagement] ========== 检查用户流程结束 ==========')
    console.log('[UserManagement] 检查结果:', checkSuccess.value)
  }
}

const resetAddUser = () => {
  console.log('[UserManagement] 重置添加用户状态')
  addUserState.value = 'initial'
  errorMessage.value = ''
  botOutput.value = ''
}

const closeModal = () => {
  console.log('[UserManagement] 关闭添加用户对话框')
  showAddUser.value = false
  addUserState.value = 'initial'
  userCode.value = ''
  verificationUri.value = ''
  checkUsername.value = ''
  checkMessage.value = ''
  checkSuccess.value = false
  errorMessage.value = ''
  botOutput.value = ''
  console.log('[UserManagement] 对话框状态已重置')
}

const showUserDetail = async (userId: string) => {
  console.log('[UserManagement] ========== 查看用户详情 ==========')
  console.log('[UserManagement] 用户ID:', userId)

  showDetail.value = true
  loadingDetail.value = true
  userDetail.value = null

  try {
    const response = await apiClient.get(`/admin/users/${userId}/detail`)
    console.log('[UserManagement] 用户详情:', response.data)
    userDetail.value = response.data
  } catch (error: any) {
    console.error('[UserManagement] 加载用户详情失败:', error)
    alert(`加载用户详情失败: ${error.response?.data?.detail || '未知错误'}`)
    showDetail.value = false
  } finally {
    loadingDetail.value = false
  }
}

const closeDetailModal = () => {
  console.log('[UserManagement] 关闭用户详情对话框')
  showDetail.value = false
  userDetail.value = null
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

onMounted(() => {
  console.log('[UserManagement] ========== 用户管理页面已挂载 ==========')
  loadUsers()
  // 定期刷新状态
  console.log('[UserManagement] 设置定时器：每30秒刷新一次用户列表')
  setInterval(() => {
    loadUsers()
  }, 30000)
})
</script>

<style scoped>
.user-management {
  color: #efeff1;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.add-button {
  padding: 0.75rem 1.5rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.add-button:hover {
  background: #772ce8;
}

.users-table {
  background: #1f1f23;
  border-radius: 8px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #3a3a3d;
}

th {
  background: #18181b;
  font-weight: 600;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
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

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: #1f1f23;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
}

.code {
  font-size: 1.5rem;
  font-weight: 600;
  color: #9147ff;
  text-align: center;
  margin: 1rem 0;
}

.link {
  color: #9147ff;
  text-decoration: none;
  word-break: break-all;
}

.primary-button {
  padding: 0.75rem 1.5rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin: 0.5rem;
}

.close-button {
  padding: 0.75rem 1.5rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

.info {
  color: #adadb8;
  margin-bottom: 1rem;
}

.success {
  color: #28a745;
  font-weight: 600;
  margin-bottom: 1rem;
}

.error {
  color: #dc3545;
  font-weight: 600;
}

.auth-box {
  background: #18181b;
  padding: 1.5rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.auth-link {
  display: block;
  color: #9147ff;
  word-break: break-all;
  margin: 0.5rem 0 1rem 0;
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}

.instruction {
  color: #adadb8;
  font-size: 0.9rem;
  margin: 1rem 0;
}

.input-field {
  width: 100%;
  padding: 0.75rem;
  background: #18181b;
  border: 1px solid #3a3a3d;
  border-radius: 4px;
  color: #efeff1;
  margin: 1rem 0;
}

.message {
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
}

.message.success {
  background: rgba(40, 167, 69, 0.1);
  border: 1px solid #28a745;
}

.message.error {
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid #dc3545;
}

.bot-output {
  background: #18181b;
  padding: 1rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  margin: 1rem 0;
  color: #adadb8;
}

.delete-button {
  padding: 0.5rem 1rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.delete-button:hover {
  background: #c82333;
}

.game-name {
  color: #9147ff;
  font-weight: 500;
}

.username-link {
  color: #9147ff;
  cursor: pointer;
  text-decoration: underline;
  transition: color 0.2s;
}

.username-link:hover {
  color: #772ce8;
}

.detail-modal {
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-section {
  background: #18181b;
  padding: 1.5rem;
  border-radius: 8px;
}

.detail-section h3 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: #9147ff;
  border-bottom: 2px solid #3a3a3d;
  padding-bottom: 0.5rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 0.85rem;
  color: #adadb8;
}

.detail-value {
  font-size: 1rem;
  color: #efeff1;
  font-weight: 500;
}

.broadcaster-name {
  color: #9147ff;
  font-weight: 600;
  font-size: 1.1rem;
}

.progress-detail {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-bar-small {
  width: 100%;
  height: 25px;
  background: #0e0e10;
  border-radius: 12px;
  overflow: hidden;
}

.progress-fill-small {
  height: 100%;
  background: linear-gradient(90deg, #9147ff 0%, #772ce8 100%);
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 0.9rem;
  color: #adadb8;
}

.favourite-games {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.game-tag-small {
  background: #9147ff;
  padding: 0.5rem 1rem;
  border-radius: 15px;
  font-size: 0.85rem;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  background: #0e0e10;
  padding: 1rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
}

.log-line {
  padding: 0.25rem 0;
  color: #adadb8;
  line-height: 1.5;
  border-bottom: 1px solid #1f1f23;
}

.log-line:last-child {
  border-bottom: none;
}
</style>

