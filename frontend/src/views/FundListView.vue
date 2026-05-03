<template>
  <div class="fund-list">
    <el-page-header @back="goBack" :content="pageTitle">
      <template #extra>
        <span class="user-info">Welcome, {{ user?.full_name || user?.username }}</span>
      </template>
    </el-page-header>

    <div class="content">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">{{ pageTitle }}</span>
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              Refresh
            </el-button>
          </div>
        </template>

        <el-table
          v-loading="loading"
          :data="funds"
          border
          style="width: 100%"
          :empty-text="error || 'No data available'"
        >
          <el-table-column prop="code" label="基金代码" />
          <el-table-column prop="name" label="基金名称" />
          <el-table-column prop="type" label="基金类型">
            <template #default="scope">
              <el-tag :type="scope.row.type === 'Stock' ? 'primary' : 'success'">
                {{ scope.row.type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="nav" label="单位净值" />
          <el-table-column prop="acc_nav" label="累计净值" />
          <el-table-column prop="change" label="日涨跌幅">
            <template #default="scope">
              <span :class="scope.row.change >= 0 ? 'text-red' : 'text-green'">
                {{ scope.row.change >= 0 ? '+' : '' }}{{ scope.row.change }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="update_time" label="更新时间">
            <template #default="scope">
              {{ formatDate(scope.row.update_time) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Refresh } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const user = authStore.user
const funds = ref([])
const loading = ref(false)
const error = ref('')

const pageTitle = computed(() => {
  const pathMap = {
    '/funds': 'Fund Overview',
    '/funds/stocks': 'Stock Funds',
    '/funds/bonds': 'Bond Funds'
  }
  return pathMap[route.path] || 'Funds'
})

const fundType = computed(() => {
  if (route.path === '/funds/stocks') return 'stock'
  if (route.path === '/funds/bonds') return 'bond'
  return null
})

const mockFunds = {
  stock: [
    { code: '000001', name: '华夏上证50ETF', type: 'Stock', nav: 2.8765, acc_nav: 4.1234, change: 1.23, update_time: new Date().toISOString() },
    { code: '000002', name: '易方达沪深300ETF', type: 'Stock', nav: 3.4567, acc_nav: 5.2345, change: -0.56, update_time: new Date().toISOString() },
    { code: '000003', name: '南方中证500ETF', type: 'Stock', nav: 1.2345, acc_nav: 2.3456, change: 0.87, update_time: new Date().toISOString() }
  ],
  bond: [
    { code: 'B0001', name: '国债ETF', type: 'Bond', nav: 1.0567, acc_nav: 1.2345, change: 0.12, update_time: new Date().toISOString() },
    { code: 'B0002', name: '企业债ETF', type: 'Bond', nav: 1.1234, acc_nav: 1.4567, change: -0.08, update_time: new Date().toISOString() }
  ],
  all: [
    { code: '000001', name: '华夏上证50ETF', type: 'Stock', nav: 2.8765, acc_nav: 4.1234, change: 1.23, update_time: new Date().toISOString() },
    { code: '000002', name: '易方达沪深300ETF', type: 'Stock', nav: 3.4567, acc_nav: 5.2345, change: -0.56, update_time: new Date().toISOString() },
    { code: 'B0001', name: '国债ETF', type: 'Bond', nav: 1.0567, acc_nav: 1.2345, change: 0.12, update_time: new Date().toISOString() },
    { code: 'B0002', name: '企业债ETF', type: 'Bond', nav: 1.1234, acc_nav: 1.4567, change: -0.08, update_time: new Date().toISOString() }
  ]
}

const fetchFunds = async () => {
  loading.value = true
  error.value = ''
  try {
    await new Promise(resolve => setTimeout(resolve, 500))

    if (fundType.value) {
      funds.value = mockFunds[fundType.value] || []
    } else {
      funds.value = mockFunds.all
    }
  } catch (err) {
    error.value = 'Failed to load funds'
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchFunds()
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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
  fetchFunds()
})
</script>

<style scoped>
.fund-list {
  padding: 24px;
}

.user-info {
  color: #666;
  font-size: 14px;
}

.content {
  margin-top: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.text-red {
  color: #e53935;
}

.text-green {
  color: #43a047;
}
</style>