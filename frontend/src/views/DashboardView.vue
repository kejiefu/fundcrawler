<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item active">
          <span class="nav-icon">📊</span>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/users" class="nav-item">
          <span class="nav-icon">👥</span>
          <span>Users</span>
        </router-link>
        <router-link to="/profile" class="nav-item">
          <span class="nav-icon">👤</span>
          <span>Profile</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <button @click="handleLogout" class="logout-button">
          <span class="nav-icon">🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <h1>Dashboard</h1>
        <div class="user-info">
          <span>Welcome, {{ user?.full_name || user?.username }}</span>
        </div>
      </header>

      <div class="dashboard-content">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon blue">👥</div>
            <div class="stat-info">
              <h3>{{ stats?.total_users || 0 }}</h3>
              <p>Total Users</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon green">✅</div>
            <div class="stat-info">
              <h3>{{ stats?.active_users || 0 }}</h3>
              <p>Active Users</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon purple">⚡</div>
            <div class="stat-info">
              <h3>{{ stats?.admin_users || 0 }}</h3>
              <p>Administrators</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon orange">⚙️</div>
            <div class="stat-info">
              <h3>{{ stats?.uptime || '99.9%' }}</h3>
              <p>System Uptime</p>
            </div>
          </div>
        </div>

        <div class="dashboard-grid">
          <div class="card activity-card">
            <h2>Recent Activity</h2>
            <div class="activity-list">
              <div v-if="loading" class="loading">Loading...</div>
              <div v-else-if="activities.length === 0" class="no-data">No recent activity</div>
              <div v-else v-for="(activity, index) in activities" :key="index" class="activity-item">
                <div class="activity-dot"></div>
                <div class="activity-content">
                  <p>{{ activity.description }}</p>
                  <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card system-card">
            <h2>System Status</h2>
            <div class="system-info">
              <div class="system-item">
                <span>Status</span>
                <span class="status-badge success">{{ stats?.system_status || 'operational' }}</span>
              </div>
              <div class="system-item">
                <span>Last Updated</span>
                <span>{{ formatTime(stats?.last_updated) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { dashboardAPI } from '../api'

const router = useRouter()
const authStore = useAuthStore()

const user = authStore.user
const stats = ref(null)
const activities = ref([])
const loading = ref(true)

const fetchDashboardData = async () => {
  try {
    const [statsRes, activityRes] = await Promise.all([
      dashboardAPI.getStats(),
      dashboardAPI.getActivity()
    ])
    stats.value = statsRes.data
    activities.value = activityRes.data.activities
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  authStore.fetchCurrentUser()
  fetchDashboardData()
})
</script>

<style scoped>
.dashboard {
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

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.router-link-active,
.nav-item.active {
  background: rgba(102, 126, 234, 0.3);
  color: white;
}

.nav-icon {
  font-size: 20px;
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

.top-bar {
  background: white;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.top-bar h1 {
  font-size: 24px;
  color: #1a1a2e;
}

.user-info {
  color: #666;
  font-size: 14px;
}

.dashboard-content {
  padding: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.blue { background: rgba(102, 126, 234, 0.15); }
.stat-icon.green { background: rgba(72, 199, 142, 0.15); }
.stat-icon.purple { background: rgba(118, 75, 162, 0.15); }
.stat-icon.orange { background: rgba(255, 165, 2, 0.15); }

.stat-info h3 {
  font-size: 32px;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.stat-info p {
  color: #666;
  font-size: 14px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card h2 {
  font-size: 18px;
  color: #1a1a2e;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  gap: 12px;
}

.activity-dot {
  width: 10px;
  height: 10px;
  background: #667eea;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.activity-content p {
  color: #333;
  font-size: 14px;
  margin-bottom: 4px;
}

.activity-time {
  color: #999;
  font-size: 12px;
}

.loading,
.no-data {
  text-align: center;
  color: #999;
  padding: 40px;
}

.system-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.system-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.system-item:last-child {
  border-bottom: none;
}

.system-item span:first-child {
  color: #666;
  font-size: 14px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.success {
  background: rgba(72, 199, 142, 0.15);
  color: #48c78e;
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
