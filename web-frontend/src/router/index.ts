import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import TwitchLogin from '../views/TwitchLogin.vue'
import AdminDashboard from '../views/Admin/Dashboard.vue'
import AdminOverview from '../views/Admin/Overview.vue'
import UserManagement from '../views/Admin/UserManagement.vue'
import SystemManagement from '../views/Admin/SystemManagement.vue'
import UserLayout from '../views/User/Layout.vue'
import UserDashboard from '../views/User/Dashboard.vue'
import UserConfig from '../views/User/Config.vue'
import UserLogs from '../views/User/Logs.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/twitch-login',
    name: 'TwitchLogin',
    component: TwitchLogin,
    meta: { requiresAuth: false }
  },
  {
    path: '/admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: 'overview'
      },
      {
        path: 'overview',
        name: 'AdminOverview',
        component: AdminOverview,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'system',
        name: 'SystemManagement',
        component: SystemManagement,
        meta: { requiresAuth: true, requiresAdmin: true }
      }
    ]
  },
  {
    path: '/user',
    component: UserLayout,
    meta: { requiresAuth: true, requiresUser: true },
    children: [
      {
        path: '',
        redirect: 'dashboard'
      },
      {
        path: 'dashboard',
        name: 'UserDashboard',
        component: UserDashboard,
        meta: { requiresAuth: true, requiresUser: true }
      },
      {
        path: 'config',
        name: 'UserConfig',
        component: UserConfig,
        meta: { requiresAuth: true, requiresUser: true }
      },
      {
        path: 'logs',
        name: 'UserLogs',
        component: UserLogs,
        meta: { requiresAuth: true, requiresUser: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  const requiresUser = to.matched.some(record => record.meta.requiresUser)

  // 不需要认证的路由直接通过
  if (!requiresAuth) {
    next()
    return
  }

  // 需要认证但没有token
  if (!token) {
    if (requiresAdmin) {
      next('/login')
    } else if (requiresUser) {
      next('/twitch-login')
    } else {
      next('/login')
    }
    return
  }

  // 有token，验证用户信息
  try {
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('Auth failed')
    }

    const userInfo = await response.json()

    // 保存用户信息到store
    const { useAuthStore } = await import('../stores/auth')
    const authStore = useAuthStore()
    authStore.userInfo = userInfo
    authStore.userType = userInfo.type
    authStore.token = token

    console.log('[Router] 路由守卫更新用户信息:', userInfo)

    // 检查权限匹配
    if (requiresAdmin && userInfo.type !== 'admin') {
      next('/twitch-login')
      return
    }

    if (requiresUser && userInfo.type !== 'user') {
      next('/login')
      return
    }

    next()
  } catch (error) {
    // Token无效，清除并重定向到登录
    localStorage.removeItem('token')
    if (requiresAdmin) {
      next('/login')
    } else if (requiresUser) {
      next('/twitch-login')
    } else {
      next('/login')
    }
  }
})

export default router

