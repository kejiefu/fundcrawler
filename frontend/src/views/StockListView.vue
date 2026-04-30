<template>
  <div>
    <header class="top-bar">
      <h1>A 股股票信息</h1>
      <div class="user-info">
        <span>Welcome, {{ user?.full_name || user?.username }}</span>
      </div>
    </header>

    <div class="content">
      <div class="card">
        <div class="card-header">
      <h2>{{ title }}</h2>
      <div class="header-actions">
          <select v-model="selectedBoard" @change="handleBoardChange" class="board-select">
            <option value="">全部板块</option>
            <option value="bluechip">蓝筹股票(股息率&gt;3.5%)</option>
            <option v-for="board in boards" :key="board" :value="board">{{ board }}</option>
          </select>
          <input
            v-model="searchQuery"
            @input="handleSearch"
            type="text"
            placeholder="搜索股票代码或名称..."
            class="search-input"
          />
          <div class="dividend-filter">
            <span class="filter-label">股息率&gt;</span>
            <input
              v-model="dividendFilter"
              @input="handleDividendChange"
              type="number"
              step="0.1"
              min="0"
              placeholder="输入阈值"
              class="dividend-input"
            />
            <span class="filter-unit">%</span>
          </div>
          <button @click="refreshData" class="btn-primary">刷新</button>
        </div>
    </div>

        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <table v-else class="stocks-table">
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>板块</th>
              <th>最新价</th>
              <th>涨跌幅</th>
              <th>涨跌额</th>
              <th>成交量</th>
              <th>成交额</th>
              <th>市盈率</th>
              <th>市净率</th>
              <th>股息率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in stocks" :key="stock.code">
              <td>{{ stock.code }}</td>
              <td>{{ stock.name }}</td>
              <td>
                <span :class="['board-badge', getBoardClass(stock.board_label)]">
                  {{ stock.board_label || '其他' }}
                </span>
              </td>
              <td>{{ stock.latest_price !== null ? stock.latest_price.toFixed(2) : '-' }}</td>
              <td>
                <span :class="[getChangeClass(stock.change_pct)]">
                  {{ stock.change_pct !== null ? (stock.change_pct >= 0 ? '+' : '') + stock.change_pct.toFixed(2) + '%' : '-' }}
                </span>
              </td>
              <td>
                <span :class="[getChangeClass(stock.change_amount)]">
                  {{ stock.change_amount !== null ? (stock.change_amount >= 0 ? '+' : '') + stock.change_amount.toFixed(2) : '-' }}
                </span>
              </td>
              <td>{{ formatNumber(stock.volume) }}</td>
              <td>{{ formatAmount(stock.amount) }}</td>
              <td>{{ stock.pe_dynamic !== null ? stock.pe_dynamic.toFixed(2) : '-' }}</td>
              <td>{{ stock.pb !== null ? stock.pb.toFixed(2) : '-' }}</td>
              <td>{{ stock.dividend_yield !== null ? stock.dividend_yield.toFixed(2) + '%' : '-' }}</td>
            </tr>
            <tr v-if="stocks.length === 0">
              <td colspan="11" class="no-data">暂无数据，请等待数据同步...</td>
            </tr>
          </tbody>
        </table>

        <div v-if="total > 0" class="pagination">
          <span class="pagination-info">
            共 {{ total }} 条，第 {{ page }}/{{ totalPages }} 页
          </span>
          <div class="pagination-buttons">
            <button @click="prevPage" :disabled="page <= 1" class="btn-page">上一页</button>
            <button @click="nextPage" :disabled="page >= totalPages" class="btn-page">下一页</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { stocksAPI } from '../api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const user = authStore.user
const stocks = ref([])
const loading = ref(false)
const error = ref('')
const boards = ref([])
const selectedBoard = ref('')
const searchQuery = ref('')
const dividendFilter = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)

let searchTimer = null

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const title = computed(() => {
  if (selectedBoard.value === 'bluechip') {
    return '蓝筹股票(股息率>3.5%)'
  }
  return 'A 股股票列表'
})

const isBluechipRoute = computed(() => route.path === '/stocks/bluechip')

watch(isBluechipRoute, (newVal, oldVal) => {
  if (newVal) {
    selectedBoard.value = 'bluechip'
    refreshData()
  } else if (oldVal && !newVal) {
    selectedBoard.value = ''
    refreshData()
  }
})

const fetchStocks = async () => {
  loading.value = true
  error.value = ''
  try {
    const dividendMin = selectedBoard.value === 'bluechip' ? 3.5 : 
                        (dividendFilter.value ? parseFloat(dividendFilter.value) : undefined)
    const params = {
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value,
      board_label: selectedBoard.value === 'bluechip' ? undefined : selectedBoard.value || undefined,
      search: searchQuery.value || undefined,
      dividend_yield_min: dividendMin
    }
    const response = await stocksAPI.getStocks(params)
    stocks.value = response.data.items
    total.value = response.data.total
  } catch (err) {
    error.value = '加载股票数据失败'
    console.error('Failed to load stocks:', err)
  } finally {
    loading.value = false
  }
}

const fetchBoards = async () => {
  try {
    const response = await stocksAPI.getBoards()
    boards.value = response.data
  } catch (err) {
    console.error('Failed to load boards:', err)
  }
}

const refreshData = () => {
  page.value = 1
  fetchStocks()
}

const handleBoardChange = () => {
  refreshData()
}

const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    refreshData()
  }, 500)
}

const handleDividendChange = () => {
  if (selectedBoard.value === 'bluechip') {
    selectedBoard.value = ''
  }
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    refreshData()
  }, 500)
}

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    fetchStocks()
  }
}

const nextPage = () => {
  if (page.value < totalPages.value) {
    page.value++
    fetchStocks()
  }
}

const getBoardClass = (board) => {
  const classMap = {
    '沪市主板': 'board-sh',
    '深市主板': 'board-sz',
    '创业板': 'board-cyb',
    '科创板': 'board-kcb',
    '北交所': 'board-bj'
  }
  return classMap[board] || 'board-default'
}

const getChangeClass = (value) => {
  if (value === null || value === undefined) return ''
  return value >= 0 ? 'change-positive' : 'change-negative'
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (num >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toFixed(2)
}

const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '-'
  if (amount >= 100000000) return (amount / 100000000).toFixed(2) + '亿'
  if (amount >= 10000) return (amount / 10000).toFixed(2) + '万'
  return amount.toFixed(2)
}

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  authStore.fetchCurrentUser()
  if (route.path === '/stocks/bluechip') {
    selectedBoard.value = 'bluechip'
  }
  fetchBoards()
  fetchStocks()
})
</script>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.top-bar h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.user-info {
  color: #666;
}

.content {
  padding: 2rem;
}

.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.card-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.board-select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
}

.search-input {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  width: 200px;
}

.dividend-filter {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.filter-label {
  color: #666;
  font-size: 0.9rem;
}

.dividend-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  width: 80px;
}

.filter-unit {
  color: #666;
  font-size: 0.9rem;
}

.btn-primary {
  padding: 0.5rem 1.5rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-primary:hover {
  background: #45a049;
}

.loading {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.error {
  padding: 1rem;
  margin: 1rem;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
}

.stocks-table {
  width: 100%;
  border-collapse: collapse;
}

.stocks-table th {
  background: #f5f5f5;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
}

.stocks-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e0e0e0;
  color: #666;
}

.stocks-table tr:hover {
  background: #fafafa;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 2rem !important;
}

.board-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.board-sh { background: #fff3e0; color: #e65100; }
.board-sz { background: #e3f2fd; color: #1565c0; }
.board-cyb { background: #f3e5f5; color: #7b1fa2; }
.board-kcb { background: #e8f5e9; color: #2e7d32; }
.board-bj { background: #fff8e1; color: #f9a825; }
.board-default { background: #eceff1; color: #546e7a; }

.change-positive { color: #e53935; }
.change-negative { color: #43a047; }

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.pagination-info {
  color: #666;
  font-size: 0.9rem;
}

.pagination-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-page {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-page:hover:not(:disabled) {
  background: #e0e0e0;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
