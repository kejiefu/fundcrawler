import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/UsersView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/menus',
    name: 'Menus',
    component: () => import('../views/MenuView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/funds',
    name: 'Funds',
    component: () => import('../views/FundListView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/funds/stocks',
    name: 'StockFunds',
    component: () => import('../views/FundListView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/funds/bonds',
    name: 'BondFunds',
    component: () => import('../views/FundListView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/stocks/basic',
    name: 'StockBasic',
    component: () => import('../views/StockListView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/stocks/bluechip',
    name: 'BlueChipStocks',
    component: () => import('../views/StockListView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/stocks/detail/:code',
    name: 'StockDetail',
    component: () => import('../views/StockDetailSimple.vue'),
    meta: { requiresAuth: true }
  },
  
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
