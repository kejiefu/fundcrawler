<template>
  <div>
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
.top-bar {
  background: white;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.top-bar h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
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
  grid-template-columns: repeat(4, 1fr);
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
}

.stat-icon {
  font-size: 40px;
}

.stat-icon.blue {
  color: #667eea;
}

.stat-icon.green {
  color: #48c78e;
}

.stat-icon.purple {
  color: #764ba2;
}

.stat-icon.orange {
  color: #f093fb;
}

.stat-info h3 {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-info p {
  color: #888;
  font-size: 14px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-dot {
  width: 8px;
  height: 8px;
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
  color: #888;
  font-size: 12px;
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

.loading,
.no-data {
  padding: 40px;
  text-align: center;
  color: #666;
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
