import { defineStore } from 'pinia'
import { authAPI } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
    isAuthenticated: !!localStorage.getItem('token')
  }),

  actions: {
    async login(username, password) {
      try {
        const response = await authAPI.login(username, password)
        this.token = response.data.access_token
        this.isAuthenticated = true
        localStorage.setItem('token', this.token)
        await this.fetchCurrentUser()
        return { success: true }
      } catch (error) {
        return {
          success: false,
          message: error.response?.data?.detail || 'Login failed'
        }
      }
    },

    async fetchCurrentUser() {
      try {
        const response = await authAPI.getCurrentUser()
        this.user = response.data
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
    }
  }
})
