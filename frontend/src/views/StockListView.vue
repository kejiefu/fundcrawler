<template>
  <div class="stock-list">
    <el-page-header @back="goBack" :content="title">
      <template #extra>
        <span class="user-info">Welcome, {{ user?.full_name || user?.username }}</span>
      </template>
    </el-page-header>

    <div class="content">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">{{ title }}</span>
            <div class="header-actions">
              <el-select
                v-model="selectedBoard"
                placeholder="全部板块"
                @change="handleBoardChange"
              >
                <el-option label="全部板块" value="" />
                <el-option label="蓝筹股票(股息率>3.5%)" value="bluechip" />
                <el-option
                  v-for="board in boards"
                  :key="board"
                  :label="board"
                  :value="board"
                />
              </el-select>

              <el-input
                v-model="searchQuery"
                placeholder="代码或名称"
                @input="handleSearch"
                class="search-input"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>

              <el-input
                v-model="dividendFilter"
                type="number"
                step="0.1"
                min="0"
                placeholder="股息率>"
                @input="handleDividendChange"
                class="dividend-input"
              />

              <el-button type="primary" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          v-loading="loading"
          :data="stocks"
          border
          style="width: 100%"
          :empty-text="error || '暂无数据，请等待数据同步...'"
          @row-click="goToDetail"
        >
          <el-table-column prop="code" label="代码" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="board_label" label="板块">
            <template #default="scope">
              <el-tag :type="getBoardTagType(scope.row.board_label)">
                {{ scope.row.board_label || '其他' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="latest_price" label="最新价">
            <template #default="scope">
              {{ scope.row.latest_price !== null ? scope.row.latest_price.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="change_pct" label="涨跌幅">
            <template #default="scope">
              <span :class="scope.row.change_pct >= 0 ? 'text-red' : 'text-green'">
                {{ scope.row.change_pct !== null ? (scope.row.change_pct >= 0 ? '+' : '') + scope.row.change_pct.toFixed(2) + '%' : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_amount" label="涨跌额">
            <template #default="scope">
              <span :class="scope.row.change_amount >= 0 ? 'text-red' : 'text-green'">
                {{ scope.row.change_amount !== null ? (scope.row.change_amount >= 0 ? '+' : '') + scope.row.change_amount.toFixed(2) : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="volume" label="成交量">
            <template #default="scope">
              {{ formatNumber(scope.row.volume) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="成交额">
            <template #default="scope">
              {{ formatAmount(scope.row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="pe_dynamic" label="市盈率">
            <template #default="scope">
              {{ scope.row.pe_dynamic !== null ? scope.row.pe_dynamic.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="pb" label="市净率">
            <template #default="scope">
              {{ scope.row.pb !== null ? scope.row.pb.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="dividend_yield" label="股息率">
            <template #default="scope">
              {{ scope.row.dividend_yield !== null ? scope.row.dividend_yield.toFixed(2) + '%' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间">
            <template #default="scope">
              {{ formatDateTime(scope.row.updated_at) }}
            </template>
          </el-table-column>
        </el-table>

        <div v-if="total > 0" class="pagination-container">
          <el-pagination
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { stocksAPI } from '../api'
import { Search, Refresh } from '@element-plus/icons-vue'

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

const title = computed(() => {
  if (selectedBoard.value === 'bluechip') {
    return '蓝筹股票(股息率>3.5%)'
  }
  return 'A 股股票列表'
})

const isBluechipRoute = computed(() => route.path === '/stocks/bluechip')

watch(isBluechipRoute, (newVal) => {
  if (newVal) {
    selectedBoard.value = 'bluechip'
    refreshData()
  } else if (selectedBoard.value === 'bluechip') {
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

const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1
  fetchStocks()
}

const handleCurrentChange = (currentPage) => {
  page.value = currentPage
  fetchStocks()
}

const goToDetail = (row) => {
  router.push(`/stocks/detail/${row.code}`)
}

const goBack = () => {
  router.back()
}

const getBoardTagType = (board) => {
  const typeMap = {
    '沪市主板': 'warning',
    '深市主板': 'primary',
    '创业板': 'danger',
    '科创板': 'success',
    '北交所': 'info'
  }
  return typeMap[board] || 'info'
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

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
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
.stock-list {
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

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.search-input ::v-deep .el-input__inner {
  color: #333;
  background-color: #fff;
}

.search-input ::v-deep .el-input__placeholder {
  color: #999;
}

.dividend-input {
  width: 180px;
}

.dividend-input ::v-deep .el-input__inner {
  color: #333;
  background-color: #fff;
}

.dividend-input ::v-deep .el-input__placeholder {
  color: #999;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.text-red {
  color: #e53935;
}

.text-green {
  color: #43a047;
}
</style>