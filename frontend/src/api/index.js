import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (userData) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me')
}

export const usersAPI = {
  getUsers: (skip = 0, limit = 100) => api.get(`/users/?skip=${skip}&limit=${limit}`),
  getUser: (userId) => api.get(`/users/${userId}`),
  updateUser: (userId, userData) => api.put(`/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
  getStats: () => api.get('/users/stats/count')
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getActivity: () => api.get('/dashboard/activity')
}

export const menusAPI = {
  getMenus: () => api.get('/menus'),
  getAllMenus: () => api.get('/menus/all'),
  getMenu: (menuId) => api.get(`/menus/${menuId}`),
  createMenu: (menuData) => api.post('/menus', menuData),
  updateMenu: (menuId, menuData) => api.put(`/menus/${menuId}`, menuData),
  deleteMenu: (menuId) => api.delete(`/menus/${menuId}`)
}

export const stocksAPI = {
  getStocks: (params) => api.get('/stocks/', { params }),
  getStock: (code) => api.get(`/stocks/${code}`),
  getBoards: () => api.get('/stocks/boards')
}

export default api
