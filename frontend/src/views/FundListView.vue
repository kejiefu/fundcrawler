<template>
  <div>
    <header class="top-bar">
      <h1>{{ pageTitle }}</h1>
      <div class="user-info">
        <span>Welcome, {{ user?.full_name || user?.username }}</span>
      </div>
    </header>

    <div class="content">
      <div class="card">
        <div class="card-header">
          <h2>{{ pageTitle }}</h2>
          <button @click="refreshData" class="btn-primary">Refresh</button>
        </div>

        <div v-if="loading" class="loading">Loading...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <table v-else class="funds-table">
          <thead>
            <tr>
              <th>基金代码</th>
              <th>基金名称</th>
              <th>基金类型</th>
              <th>单位净值</th>
              <th>累计净值</th>
              <th>日涨跌幅</th>
              <th>更新时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fund in funds" :key="fund.code">
              <td>{{ fund.code }}</td>
              <td>{{ fund.name }}</td>
              <td>
                <span :class="['type-badge', getFundTypeClass(fund.type)]">
                  {{ fund.type }}
                </span>
              </td>
              <td>{{ fund.nav }}</td>
              <td>{{ fund.acc_nav }}</td>
              <td>
                <span :class="[getChangeClass(fund.change)]">
                  {{ fund.change >= 0 ? '+' : '' }}{{ fund.change }}%
                </span>
              </td>
              <td>{{ formatDate(fund.update_time) }}</td>
            </tr>
            <tr v-if="funds.length === 0">
              <td colspan="7" class="no-data">No data available</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

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

const getFundTypeClass = (type) => {
  return type === 'Stock' ? 'type-stock' : 'type-bond'
}

const getChangeClass = (change) => {
  return change >= 0 ? 'change-positive' : 'change-negative'
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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

.content {
  padding: 32px;
}

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.btn-primary {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: #5568d3;
}

.loading,
.error,
.no-data {
  padding: 40px;
  text-align: center;
  color: #666;
}

.error {
  color: #e74c3c;
}

.funds-table {
  width: 100%;
  border-collapse: collapse;
}

.funds-table th,
.funds-table td {
  padding: 14px 20px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.funds-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.funds-table td {
  color: #333;
  font-size: 14px;
}

.funds-table tr:hover {
  background: #f8f9fa;
}

.type-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.type-stock {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.type-badge.type-bond {
  background: rgba(72, 199, 142, 0.15);
  color: #48c78e;
}

.change-positive {
  color: #e74c3c;
  font-weight: 500;
}

.change-negative {
  color: #48c78e;
  font-weight: 500;
}
</style>
