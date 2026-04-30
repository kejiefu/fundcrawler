<template>
  <div class="app-layout">
    <!-- 只有已认证时才显示侧边栏 -->
    <aside v-if="authStore.isAuthenticated" class="sidebar">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
      </div>
      <SidebarMenu />
      <div class="sidebar-footer">
        <button @click="handleLogout" class="logout-button">
          <span class="nav-icon">🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>

    <main :class="['main-content', { 'full-width': !authStore.isAuthenticated }]">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import SidebarMenu from './components/SidebarMenu.vue'

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

.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  display: flex;
  flex-direction: column;
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
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.logout-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.main-content {
  flex: 1;
  margin-left: 260px;
  background: #f5f5f5;
  min-height: 100vh;
}

/* 未认证时主内容区全屏显示 */
.main-content.full-width {
  margin-left: 0;
}
</style>
