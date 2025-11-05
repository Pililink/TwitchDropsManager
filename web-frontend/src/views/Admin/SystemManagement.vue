<template>
  <div class="system-management">
    <h1>系统管理</h1>

    <!-- Bot管理区域 -->
    <div class="section bot-management">
      <h2>🤖 Bot管理</h2>
      <div class="bot-controls">
        <div class="bot-info">
          <div class="info-item">
            <span class="label">下次重启时间：</span>
            <span class="value">{{ nextRestartTime || '未设置' }}</span>
          </div>
        </div>
        <button @click="handleRestart" class="restart-button" :disabled="restarting">
          {{ restarting ? '重启中...' : '⚡ 立即重启Bot' }}
        </button>
      </div>
    </div>

    <!-- 管理员管理区域 -->
    <div class="section admin-management">
      <div class="section-header">
        <h2>👤 管理员管理</h2>
        <button @click="showAddAdminModal = true" class="add-button">➕ 添加管理员</button>
      </div>

      <div v-if="loading" class="loading">加载中...</div>

      <div v-else class="admins-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="admin in admins" :key="admin.id">
              <td>{{ admin.id }}</td>
              <td>{{ admin.username }}</td>
              <td>
                <span :class="['status-badge', admin.is_active ? 'active' : 'inactive']">
                  {{ admin.is_active ? '启用' : '禁用' }}
                </span>
              </td>
              <td>{{ formatDate(admin.created_at) }}</td>
              <td class="actions">
                <button
                  v-if="admin.id !== currentAdminId"
                  @click="toggleAdminStatus(admin)"
                  class="action-button"
                  :class="admin.is_active ? 'disable' : 'enable'"
                >
                  {{ admin.is_active ? '禁用' : '启用' }}
                </button>
                <button
                  v-if="admin.id !== currentAdminId"
                  @click="deleteAdmin(admin)"
                  class="action-button delete"
                >
                  删除
                </button>
                <span v-else class="current-admin-tag">当前账户</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 密码管理区域 -->
    <div class="section password-management">
      <h2>🔒 修改密码</h2>
      <form @submit.prevent="handleChangePassword" class="password-form">
        <div class="form-group">
          <label>旧密码：</label>
          <input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入旧密码"
            required
          />
        </div>
        <div class="form-group">
          <label>新密码：</label>
          <input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            required
          />
        </div>
        <div class="form-group">
          <label>确认新密码：</label>
          <input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            required
          />
        </div>
        <button type="submit" class="submit-button" :disabled="changingPassword">
          {{ changingPassword ? '修改中...' : '修改密码' }}
        </button>
      </form>
    </div>

    <!-- 添加管理员弹窗 -->
    <div v-if="showAddAdminModal" class="modal-overlay" @click="showAddAdminModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>添加管理员</h3>
          <button @click="showAddAdminModal = false" class="close-button">✕</button>
        </div>
        <form @submit.prevent="handleAddAdmin" class="modal-form">
          <div class="form-group">
            <label>用户名：</label>
            <input
              v-model="newAdmin.username"
              type="text"
              placeholder="请输入用户名"
              required
            />
          </div>
          <div class="form-group">
            <label>密码：</label>
            <input
              v-model="newAdmin.password"
              type="password"
              placeholder="请输入密码"
              required
            />
          </div>
          <div class="form-group">
            <label>确认密码：</label>
            <input
              v-model="newAdmin.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              required
            />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddAdminModal = false" class="cancel-button">
              取消
            </button>
            <button type="submit" class="submit-button" :disabled="adding">
              {{ adding ? '添加中...' : '添加' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const currentAdminId = ref<number | null>(null)

const loading = ref(true)
const admins = ref<any[]>([])
const nextRestartTime = ref<string>('')
const restarting = ref(false)
const changingPassword = ref(false)

const showAddAdminModal = ref(false)
const adding = ref(false)
const newAdmin = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loadAdmins = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/admin/admins')
    admins.value = response.data.admins
    currentAdminId.value = authStore.userInfo?.id || null
  } catch (error) {
    console.error('加载管理员列表失败:', error)
    alert('加载管理员列表失败')
  } finally {
    loading.value = false
  }
}

const loadNextRestartTime = async () => {
  try {
    const response = await apiClient.get('/admin/bot/next-restart')
    nextRestartTime.value = response.data.formatted_time
  } catch (error) {
    console.error('加载重启时间失败:', error)
  }
}

const handleRestart = async () => {
  if (!confirm('确定要重启Bot吗？这将中断所有正在进行的挂宝任务。')) {
    return
  }

  restarting.value = true
  try {
    const response = await apiClient.post('/admin/bot/restart')
    alert(response.data.message || '重启命令已发送')
    await loadNextRestartTime()
  } catch (error) {
    console.error('重启失败:', error)
    alert('重启失败，请查看控制台')
  } finally {
    restarting.value = false
  }
}

const handleAddAdmin = async () => {
  if (newAdmin.value.password !== newAdmin.value.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }

  adding.value = true
  try {
    await apiClient.post('/admin/admins', {
      username: newAdmin.value.username,
      password: newAdmin.value.password
    })
    alert('管理员添加成功')
    showAddAdminModal.value = false
    newAdmin.value = { username: '', password: '', confirmPassword: '' }
    await loadAdmins()
  } catch (error: any) {
    console.error('添加管理员失败:', error)
    alert(error.response?.data?.detail || '添加管理员失败')
  } finally {
    adding.value = false
  }
}

const toggleAdminStatus = async (admin: any) => {
  const action = admin.is_active ? '禁用' : '启用'
  if (!confirm(`确定要${action}管理员 ${admin.username} 吗？`)) {
    return
  }

  try {
    await apiClient.patch(`/admin/admins/${admin.id}`, {
      is_active: !admin.is_active
    })
    alert(`管理员已${action}`)
    await loadAdmins()
  } catch (error: any) {
    console.error(`${action}管理员失败:`, error)
    alert(error.response?.data?.detail || `${action}管理员失败`)
  }
}

const deleteAdmin = async (admin: any) => {
  if (!confirm(`确定要删除管理员 ${admin.username} 吗？此操作不可恢复！`)) {
    return
  }

  try {
    await apiClient.delete(`/admin/admins/${admin.id}`)
    alert('管理员已删除')
    await loadAdmins()
  } catch (error: any) {
    console.error('删除管理员失败:', error)
    alert(error.response?.data?.detail || '删除管理员失败')
  }
}

const handleChangePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    alert('两次输入的新密码不一致')
    return
  }

  if (passwordForm.value.newPassword.length < 6) {
    alert('新密码长度至少为6位')
    return
  }

  changingPassword.value = true
  try {
    await apiClient.post('/admin/change-password', {
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })
    alert('密码修改成功，请重新登录')
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }

    // 登出并跳转到登录页
    await authStore.logout()
    window.location.href = '/login'
  } catch (error: any) {
    console.error('修改密码失败:', error)
    alert(error.response?.data?.detail || '修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAdmins()
  loadNextRestartTime()

  // 每分钟刷新重启时间
  setInterval(loadNextRestartTime, 60000)
})
</script>

<style scoped>
.system-management {
  color: #efeff1;
}

h1 {
  margin-bottom: 2rem;
  font-size: 2rem;
}

.section {
  background: #1f1f23;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #3a3a3d;
  margin-bottom: 2rem;
}

h2 {
  font-size: 1.3rem;
  margin-bottom: 1.5rem;
  color: #adadb8;
}

/* Bot管理 */
.bot-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.bot-info {
  flex: 1;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
}

.info-item .label {
  color: #adadb8;
}

.info-item .value {
  color: #9147ff;
  font-weight: 600;
}

.restart-button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #9147ff 0%, #772ce8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.restart-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(145, 71, 255, 0.4);
}

.restart-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 管理员管理 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin-bottom: 0;
}

.add-button {
  padding: 0.5rem 1rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
}

.add-button:hover {
  background: #218838;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #adadb8;
}

.admins-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #18181b;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #adadb8;
  border-bottom: 2px solid #3a3a3d;
}

td {
  padding: 1rem;
  border-bottom: 1px solid #3a3a3d;
}

tbody tr:hover {
  background: #18181b;
}

.status-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #28a745;
  color: white;
}

.status-badge.inactive {
  background: #6c757d;
  color: white;
}

.actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.action-button {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s;
}

.action-button.enable {
  background: #28a745;
  color: white;
}

.action-button.enable:hover {
  background: #218838;
}

.action-button.disable {
  background: #ffc107;
  color: #000;
}

.action-button.disable:hover {
  background: #e0a800;
}

.action-button.delete {
  background: #dc3545;
  color: white;
}

.action-button.delete:hover {
  background: #c82333;
}

.current-admin-tag {
  padding: 0.4rem 0.8rem;
  background: #9147ff;
  color: white;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

/* 密码管理 */
.password-form {
  max-width: 500px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #adadb8;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  background: #18181b;
  border: 1px solid #3a3a3d;
  border-radius: 6px;
  color: #efeff1;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #9147ff;
}

.submit-button {
  padding: 0.75rem 1.5rem;
  background: #9147ff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.2s;
}

.submit-button:hover:not(:disabled) {
  background: #772ce8;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1f1f23;
  border-radius: 12px;
  border: 1px solid #3a3a3d;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #3a3a3d;
}

.modal-header h3 {
  margin: 0;
  color: #efeff1;
  font-size: 1.3rem;
}

.close-button {
  background: none;
  border: none;
  color: #adadb8;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  color: #efeff1;
}

.modal-form {
  padding: 1.5rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.cancel-button {
  padding: 0.75rem 1.5rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.2s;
}

.cancel-button:hover {
  background: #5a6268;
}
</style>
