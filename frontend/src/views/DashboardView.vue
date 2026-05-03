<template>
  <div class="dashboard">
    <el-page-header @back="goBack" content="Dashboard">
      <template #extra>
        <span class="user-info">Welcome, {{ user?.full_name || user?.username }}</span>
      </template>
    </el-page-header>

    <div class="dashboard-content">
      <div class="stats-grid">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon blue">
            <el-icon><User /></el-icon>
          </div>
          <el-statistic title="Total Users" :value="stats?.total_users || 0" />
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon green">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <el-statistic title="Active Users" :value="stats?.active_users || 0" />
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon purple">
            <el-icon><UserFilled /></el-icon>
          </div>
          <el-statistic title="Administrators" :value="stats?.admin_users || 0" />
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon orange">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <el-statistic title="System Uptime" :value="stats?.uptime || '99.9%'" />
        </el-card>
      </div>

      <div class="dashboard-grid">
        <el-card title="Recent Activity" shadow="hover">
          <template #header>
            <span class="card-title">Recent Activity</span>
          </template>
          <el-timeline v-if="!loading && activities.length > 0">
            <el-timeline-item
              v-for="(activity, index) in activities"
              :key="index"
              :timestamp="formatTime(activity.timestamp)"
            >
              {{ activity.description }}
            </el-timeline-item>
          </el-timeline>
          <div v-else class="empty-state">
            <el-empty v-if="!loading" description="No recent activity" />
            <el-skeleton v-else />
          </div>
        </el-card>

        <el-card title="System Status" shadow="hover">
          <template #header>
            <span class="card-title">System Status</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="Status">
              <el-tag :type="stats?.system_status === 'operational' ? 'success' : 'warning'">
                {{ stats?.system_status || 'operational' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Last Updated">
              {{ formatTime(stats?.last_updated) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { dashboardAPI } from '../api'
import { User, CircleCheck, UserFilled, TrendCharts } from '@element-plus/icons-vue'

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

const goBack = () => {
  router.back()
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
  padding: 24px;
}

.user-info {
  color: #666;
  font-size: 14px;
}

.dashboard-content {
  margin-top: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.blue {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.stat-icon.green {
  background: rgba(72, 199, 142, 0.15);
  color: #48c78e;
}

.stat-icon.purple {
  background: rgba(118, 75, 162, 0.15);
  color: #764ba2;
}

.stat-icon.orange {
  background: rgba(240, 147, 251, 0.15);
  color: #f093fb;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.empty-state {
  padding: 20px;
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>