import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userType = ref<'admin' | 'user' | null>(null)
  const userInfo = ref<any>(null)

  axios.defaults.headers.common['Authorization'] = token.value ? `Bearer ${token.value}` : ''

  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post(`${API_BASE}/auth/admin/login`, {
        username,
        password
      })
      
      token.value = response.data.access_token
      userType.value = 'admin'
      localStorage.setItem('token', token.value)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      
      // 获取用户信息
      const userResponse = await axios.get(`${API_BASE}/auth/me`)
      userInfo.value = userResponse.data
      
      return true
    } catch (error: any) {
      console.error('登录失败:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await axios.post(`${API_BASE}/auth/logout`)
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      token.value = null
      userType.value = null
      userInfo.value = null
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    }
  }

  const checkAuth = async () => {
    if (!token.value) return false
    
    try {
      const response = await axios.get(`${API_BASE}/auth/me`)
      userInfo.value = response.data
      userType.value = response.data.type
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  return {
    token,
    userType,
    userInfo,
    login,
    logout,
    checkAuth
  }
})

