<template>
  <el-container class="app-container">
    <el-aside v-if="authStore.isAuthenticated" width="260px" class="app-sidebar">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
      </div>
      <SidebarMenu />
      <div class="sidebar-footer">
        <el-button @click="handleLogout" class="logout-button" type="text">
          <el-icon><component :is="Switch" /></el-icon>
          <span>Logout</span>
        </el-button>
      </div>
    </el-aside>
    <el-main :class="['app-main', { 'full-width': !authStore.isAuthenticated }]">
      <router-view :key="$route.fullPath" />
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import SidebarMenu from './components/SidebarMenu.vue'
import { Switch } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f5f5;
}

#app {
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
}

.app-sidebar {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  position: fixed;
  height: 100vh;
}

.sidebar-header {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}

.logout-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px 16px;
  color: white !important;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2) !important;
}

.app-main {
  margin-left: 260px;
  min-height: 100vh;
  background: #f5f5f5;
}

.app-main.full-width {
  margin-left: 0;
}
</style>