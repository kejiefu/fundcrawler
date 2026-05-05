<template>
  <div class="stock-detail">
    <header class="top-bar">
      <button @click="goBack" class="btn-back">← 返回</button>
      <div class="stock-title">
        <span class="stock-code">{{ stock.code }}</span>
        <span class="stock-name">{{ stock.name }}</span>
      </div>
      <div class="sync-buttons">
        <button @click="syncBasicData" :disabled="syncingBasic" class="btn-sync btn-sync-basic">
          {{ syncingBasic ? '同步中...' : '同步基础数据' }}
        </button>
        <button @click="syncAllIndicators" :disabled="syncing" class="btn-sync">
          {{ syncing ? '同步中...' : '同步全部指标' }}
        </button>
        <button @click="syncRecentData" :disabled="syncing" class="btn-sync">
          {{ syncing ? '同步中...' : '同步近30天' }}
        </button>
      </div>
    </header>

    <div class="content">
      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-if="loading" class="loading-message">加载中...</div>

      <div v-if="!loading && !error" class="data-section">
        <div class="period-tabs">
          <button 
            v-for="p in periods" 
            :key="p.value"
            @click="switchPeriod(p.value)"
            :class="['tab-btn', { active: currentPeriod === p.value }]"
          >
            {{ p.label }}
          </button>
        </div>

        <div class="stats-card">
          <div class="stat-row">
            <span class="stat-label">当前价格</span>
            <span class="stat-value price" :class="priceChange >= 0 ? 'up' : 'down'">
              {{ currentPrice.toFixed(2) }}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">涨跌幅</span>
            <span class="stat-value" :class="priceChange >= 0 ? 'up' : 'down'">
              {{ priceChange >= 0 ? '+' : '' }}{{ priceChangePct.toFixed(2) }}%
            </span>
          </div>
        </div>

        <div class="kline-table-container">
          <table class="kline-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>开盘</th>
                <th>收盘</th>
                <th>最高</th>
                <th>最低</th>
                <th>涨跌幅</th>
                <th>成交量</th>
                <th>KDJ</th>
                <th>RSI</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in klineData" :key="item.kline.trade_date">
                <td>{{ formatDate(item.kline.trade_date) }}</td>
                <td>{{ formatPrice(item.kline.open_price) }}</td>
                <td :class="getChangeClass(item.kline.change_pct)">{{ formatPrice(item.kline.close_price) }}</td>
                <td>{{ formatPrice(item.kline.high_price) }}</td>
                <td>{{ formatPrice(item.kline.low_price) }}</td>
                <td :class="getChangeClass(item.kline.change_pct)">
                  {{ formatChange(item.kline.change_pct) }}
                </td>
                <td>{{ formatVolume(item.kline.volume) }}</td>
                <td>
                  <span v-if="item.indicator">
                    K:{{ item.indicator.k_value?.toFixed(1) || '-' }}
                    D:{{ item.indicator.d_value?.toFixed(1) || '-' }}
                    J:{{ item.indicator.j_value?.toFixed(1) || '-' }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="item.indicator">
                    {{ item.indicator.rsi_6?.toFixed(1) || '-' }}/{{ item.indicator.rsi_12?.toFixed(1) || '-' }}/{{ item.indicator.rsi_24?.toFixed(1) || '-' }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
              <tr v-if="klineData.length === 0">
                <td colspan="9" class="no-data">暂无数据，请检查API连接</td>
              </tr>
            </tbody>
          </table>
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
const stock = ref({
  code: '',
  name: '',
  latest_price: 0,
  change_pct: 0,
  change_amount: 0
})

const klineData = ref([])
const currentPeriod = ref(1)
const loading = ref(false)
const error = ref('')
const syncing = ref(false)
const syncingBasic = ref(false)

const periods = [
  { label: '日线', value: 1 },
  { label: '周线', value: 2 },
  { label: '月线', value: 3 },
  { label: '年线', value: 4 }
]

const currentPrice = computed(() => stock.value.latest_price || 0)
const priceChange = computed(() => stock.value.change_amount || 0)
const priceChangePct = computed(() => stock.value.change_pct || 0)

const goBack = () => router.back()

const switchPeriod = async (period) => {
  currentPeriod.value = period
  await fetchKlineData()
}

const fetchStockInfo = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await stocksAPI.getStock(route.params.code)
    stock.value = response.data
  } catch (err) {
    error.value = '加载股票信息失败: ' + (err.message || err)
    console.error('Stock fetch error:', err)
  } finally {
    loading.value = false
  }
}

const fetchKlineData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await stocksAPI.getKline(route.params.code, currentPeriod.value, 50)
    klineData.value = response.data.items
  } catch (err) {
    error.value = '加载K线数据失败: ' + (err.message || err)
    console.error('Kline fetch error:', err)
  } finally {
    loading.value = false
  }
}

const syncBasicData = async () => {
  syncingBasic.value = true
  error.value = ''
  try {
    const response = await stocksAPI.syncBasicData(route.params.code)
    alert('同步完成: ' + response.data.message)
    await fetchStockData()
  } catch (err) {
    error.value = '同步失败: ' + (err.message || err)
    console.error('Sync error:', err)
  } finally {
    syncingBasic.value = false
  }
}

const syncAllIndicators = async () => {
  syncing.value = true
  error.value = ''
  try {
    const response = await stocksAPI.syncAllIndicators(route.params.code)
    alert('同步完成: ' + response.data.message)
    await fetchKlineData()
  } catch (err) {
    error.value = '同步失败: ' + (err.message || err)
    console.error('Sync error:', err)
  } finally {
    syncing.value = false
  }
}

const syncRecentData = async () => {
  syncing.value = true
  error.value = ''
  try {
    const response = await stocksAPI.syncRecentData(route.params.code)
    alert('同步完成: ' + response.data.message)
    await fetchKlineData()
  } catch (err) {
    error.value = '同步失败: ' + (err.message || err)
    console.error('Sync error:', err)
  } finally {
    syncing.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 4) + '-' + dateStr.substring(4, 6) + '-' + dateStr.substring(6, 8)
}

const formatPrice = (price) => {
  return price !== null ? price.toFixed(2) : '-'
}

const formatChange = (change) => {
  if (change === null) return '-'
  return (change >= 0 ? '+' : '') + change.toFixed(2) + '%'
}

const formatVolume = (volume) => {
  if (volume === null) return '-'
  if (volume >= 100000000) return (volume / 100000000).toFixed(2) + '亿'
  if (volume >= 10000) return (volume / 10000).toFixed(2) + '万'
  return volume.toFixed(2)
}

const getChangeClass = (value) => {
  if (value === null) return ''
  return value >= 0 ? 'change-up' : 'change-down'
}

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  authStore.fetchCurrentUser()
  fetchStockInfo()
  fetchKlineData()
})

watch(() => route.params.code, async (newCode) => {
  if (newCode) {
    stock.value = { code: '', name: '', latest_price: 0, change_pct: 0, change_amount: 0 }
    klineData.value = []
    await fetchStockInfo()
    await fetchKlineData()
  }
})
</script>

<style scoped>
.stock-detail {
  min-height: 100vh;
  background: #f5f5f5;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.stock-title {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.stock-code {
  font-size: 1.5rem;
  font-weight: 600;
}

.stock-name {
  font-size: 1.25rem;
  color: #666;
}

.sync-buttons {
  margin-left: auto;
  display: flex;
  gap: 0.5rem;
}

.btn-sync {
  padding: 0.5rem 1rem;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-sync:hover:not(:disabled) {
  background: #1976D2;
}

.btn-sync:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.content {
  padding: 1rem 2rem;
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.loading-message {
  text-align: center;
  padding: 2rem;
}

.data-section {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.period-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 0.95rem;
  color: #666;
}

.tab-btn.active {
  color: #4CAF50;
  border-bottom-color: #4CAF50;
}

.stats-card {
  padding: 1rem;
  display: flex;
  gap: 2rem;
}

.stat-row {
  display: flex;
  gap: 1rem;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: 600;
}

.stat-value.price {
  font-size: 1.5rem;
}

.up {
  color: #e53935;
}

.down {
  color: #43a047;
}

.kline-table-container {
  max-height: 500px;
  overflow-y: auto;
}

.kline-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.kline-table th {
  background: #f5f5f5;
  padding: 0.75rem 0.5rem;
  text-align: center;
  position: sticky;
  top: 0;
}

.kline-table td {
  padding: 0.5rem;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}

.change-up {
  color: #e53935;
}

.change-down {
  color: #43a047;
}

.no-data {
  color: #999;
  padding: 2rem !important;
}
</style>