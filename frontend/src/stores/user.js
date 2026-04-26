import { defineStore } from 'pinia'
import { usersAPI } from '../api'

export const useUserStore = defineStore('user', {
  state: () => ({
    users: [],
    currentUser: null,
    stats: null,
    loading: false,
    error: null
  }),

  actions: {
    async fetchUsers() {
      this.loading = true
      try {
        const response = await usersAPI.getUsers()
        this.users = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async fetchUser(userId) {
      try {
        const response = await usersAPI.getUser(userId)
        this.currentUser = response.data
      } catch (error) {
        this.error = error.message
      }
    },

    async updateUser(userId, userData) {
      try {
        const response = await usersAPI.updateUser(userId, userData)
        const index = this.users.findIndex(u => u.id === userId)
        if (index !== -1) {
          this.users[index] = response.data
        }
        return { success: true }
      } catch (error) {
        return {
          success: false,
          message: error.response?.data?.detail || 'Update failed'
        }
      }
    },

    async deleteUser(userId) {
      try {
        await usersAPI.deleteUser(userId)
        this.users = this.users.filter(u => u.id !== userId)
        return { success: true }
      } catch (error) {
        return {
          success: false,
          message: error.response?.data?.detail || 'Delete failed'
        }
      }
    },

    async fetchStats() {
      try {
        const response = await usersAPI.getStats()
        this.stats = response.data
      } catch (error) {
        this.error = error.message
      }
    }
  }
})
