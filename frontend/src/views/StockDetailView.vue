<template>
  <div class="stock-detail">
    <header class="top-bar">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← 返回</button>
        <div class="stock-title">
          <span class="stock-code">{{ stock.code }}</span>
          <span class="stock-name">{{ stock.name }}</span>
        </div>
      </div>
      <div class="user-info">
        <span>Welcome, {{ user?.full_name || user?.username }}</span>
      </div>
    </header>

    <div class="content">
      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-if="loading" class="loading-message">加载中...</div>
      
      <div class="stock-header">
        <div class="price-section">
          <div class="current-price" :class="priceChangeClass">
            {{ currentPrice.toFixed(2) }}
          </div>
          <div class="price-change" :class="priceChangeClass">
            {{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2) }}
            <span class="change-pct">({{ priceChange >= 0 ? '+' : '' }}{{ priceChangePct.toFixed(2) }}%)</span>
          </div>
        </div>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">开盘</span>
            <span class="value">{{ stock.open_price !== null ? stock.open_price.toFixed(2) : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">最高</span>
            <span class="value change-positive">{{ stock.high !== null ? stock.high.toFixed(2) : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">最低</span>
            <span class="value change-negative">{{ stock.low !== null ? stock.low.toFixed(2) : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">昨收</span>
            <span class="value">{{ stock.prev_close !== null ? stock.prev_close.toFixed(2) : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">成交量</span>
            <span class="value">{{ formatNumber(stock.volume) }}</span>
          </div>
          <div class="info-item">
            <span class="label">成交额</span>
            <span class="value">{{ formatAmount(stock.amount) }}</span>
          </div>
          <div class="info-item">
            <span class="label">换手率</span>
            <span class="value">{{ stock.turnover_rate !== null ? stock.turnover_rate.toFixed(2) + '%' : '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">振幅</span>
            <span class="value">{{ stock.amplitude !== null ? stock.amplitude.toFixed(2) + '%' : '-' }}</span>
          </div>
        </div>
      </div>

      <div class="chart-container">
        <div class="chart-tabs">
          <button 
            v-for="p in periods" 
            :key="p.value"
            @click="switchPeriod(p.value)"
            :class="['tab-btn', { active: currentPeriod === p.value }]"
          >
            {{ p.label }}
          </button>
        </div>

        <div class="chart-area">
          <canvas ref="klineCanvas" class="kline-canvas"></canvas>
          <canvas ref="volumeCanvas" class="volume-canvas"></canvas>
        </div>

        <div class="indicator-tabs">
          <button 
            v-for="ind in indicators" 
            :key="ind.value"
            @click="switchIndicator(ind.value)"
            :class="['tab-btn', { active: currentIndicator === ind.value }]"
          >
            {{ ind.label }}
          </button>
        </div>

        <div class="indicator-area">
          <canvas ref="indicatorCanvas" class="indicator-canvas"></canvas>
        </div>

        <div class="data-table">
          <table class="kline-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>开盘</th>
                <th>收盘</th>
                <th>最高</th>
                <th>最低</th>
                <th>成交量</th>
                <th>成交额</th>
                <th>涨跌幅</th>
                <th>KDJ</th>
                <th>RSI</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in klineData" :key="item.kline.trade_date">
                <td>{{ formatDate(item.kline.trade_date) }}</td>
                <td>{{ item.kline.open_price !== null ? item.kline.open_price.toFixed(2) : '-' }}</td>
                <td :class="getChangeClass(item.kline.change_pct)">{{ item.kline.close_price !== null ? item.kline.close_price.toFixed(2) : '-' }}</td>
                <td>{{ item.kline.high_price !== null ? item.kline.high_price.toFixed(2) : '-' }}</td>
                <td>{{ item.kline.low_price !== null ? item.kline.low_price.toFixed(2) : '-' }}</td>
                <td>{{ formatNumber(item.kline.volume) }}</td>
                <td>{{ formatAmount(item.kline.amount) }}</td>
                <td :class="getChangeClass(item.kline.change_pct)">
                  {{ item.kline.change_pct !== null ? (item.kline.change_pct >= 0 ? '+' : '') + item.kline.change_pct.toFixed(2) + '%' : '-' }}
                </td>
                <td v-if="item.indicator">
                  K:{{ item.indicator.k_value?.toFixed(1) || '-' }}
                  D:{{ item.indicator.d_value?.toFixed(1) || '-' }}
                  J:{{ item.indicator.j_value?.toFixed(1) || '-' }}
                </td>
                <td v-else>-</td>
                <td v-if="item.indicator">
                  {{ item.indicator.rsi_6?.toFixed(1) || '-' }}/{{ item.indicator.rsi_12?.toFixed(1) || '-' }}/{{ item.indicator.rsi_24?.toFixed(1) || '-' }}
                </td>
                <td v-else>-</td>
              </tr>
              <tr v-if="klineData.length === 0">
                <td colspan="10" class="no-data">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
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
  open_price: null,
  high: null,
  low: null,
  prev_close: null,
  latest_price: null,
  volume: null,
  amount: null,
  turnover_rate: null,
  amplitude: null,
  change_pct: null,
  change_amount: null
})

const klineData = ref([])
const currentPeriod = ref(1)
const currentIndicator = ref('kdj')
const loading = ref(false)
const error = ref('')

const klineCanvas = ref(null)
const volumeCanvas = ref(null)
const indicatorCanvas = ref(null)

const periods = [
  { label: '日线', value: 1 },
  { label: '周线', value: 2 },
  { label: '月线', value: 3 },
  { label: '年线', value: 4 }
]

const indicators = [
  { label: 'KDJ', value: 'kdj' },
  { label: 'RSI', value: 'rsi' }
]

const currentPrice = computed(() => {
  return stock.value.latest_price !== null ? stock.value.latest_price : 0
})

const priceChange = computed(() => {
  return stock.value.change_amount !== null ? stock.value.change_amount : 0
})

const priceChangePct = computed(() => {
  return stock.value.change_pct !== null ? stock.value.change_pct : 0
})

const priceChangeClass = computed(() => {
  return priceChange.value >= 0 ? 'price-up' : 'price-down'
})

const goBack = () => {
  router.back()
}

const switchPeriod = async (period) => {
  console.log(`Switching to period: ${period}`)
  currentPeriod.value = period
  await fetchKlineData()
}

const switchIndicator = (indicator) => {
  console.log(`Switching to indicator: ${indicator}`)
  currentIndicator.value = indicator
  drawIndicator()
}

const fetchStockInfo = async () => {
  loading.value = true
  try {
    console.log(`Fetching stock info for: ${route.params.code}`)
    const response = await stocksAPI.getStock(route.params.code)
    console.log('Stock info response:', response.data)
    stock.value = response.data
  } catch (err) {
    error.value = '加载股票信息失败: ' + (err.message || err)
    console.error('Failed to load stock:', err)
  } finally {
    loading.value = false
  }
}

const fetchKlineData = async () => {
  loading.value = true
  try {
    console.log(`Fetching kline data for: ${route.params.code}, period: ${currentPeriod.value}`)
    const response = await stocksAPI.getKline(route.params.code, currentPeriod.value, 100)
    console.log('Kline response:', response.data)
    klineData.value = response.data.items
    console.log(`Kline data items count: ${klineData.value.length}`)
    await nextTick()
    drawKline()
    drawIndicator()
  } catch (err) {
    error.value = '加载K线数据失败: ' + (err.message || err)
    console.error('Failed to load kline:', err)
  } finally {
    loading.value = false
  }
}

const drawKline = () => {
  if (!klineData.value.length) {
    console.log('No kline data to draw')
    return
  }
  
  const klineCtx = klineCanvas.value?.getContext('2d')
  const volumeCtx = volumeCanvas.value?.getContext('2d')
  
  if (!klineCtx || !volumeCtx) {
    console.log('Canvas context not available')
    return
  }

  const klineDataReversed = [...klineData.value].reverse()
  const prices = klineDataReversed.map(item => ({
    high: item.kline.high_price || 0,
    low: item.kline.low_price || 0,
    open: item.kline.open_price || 0,
    close: item.kline.close_price || 0
  }))

  const volumes = klineDataReversed.map(item => item.kline.volume || 0)

  const klineWidth = klineCanvas.value.width
  const klineHeight = klineCanvas.value.height
  const volumeHeight = volumeCanvas.value.height

  const maxPrice = Math.max(...prices.map(p => p.high))
  const minPrice = Math.min(...prices.map(p => p.low))
  const priceRange = maxPrice - minPrice || 1

  const maxVolume = Math.max(...volumes) || 1

  const candleWidth = Math.max(3, Math.floor(klineWidth / klineDataReversed.length) - 2)
  const gap = 2

  klineCtx.clearRect(0, 0, klineWidth, klineHeight)
  volumeCtx.clearRect(0, 0, klineWidth, volumeHeight)

  klineCtx.strokeStyle = '#ccc'
  klineCtx.lineWidth = 1
  const gridLines = 5
  for (let i = 0; i <= gridLines; i++) {
    const y = (klineHeight / gridLines) * i
    klineCtx.beginPath()
    klineCtx.moveTo(0, y)
    klineCtx.lineTo(klineWidth, y)
    klineCtx.stroke()
  }

  klineDataReversed.forEach((item, index) => {
    const x = index * (candleWidth + gap) + gap
    const h = item.kline.high_price || 0
    const l = item.kline.low_price || 0
    const o = item.kline.open_price || 0
    const c = item.kline.close_price || 0

    const isUp = c >= o
    const color = isUp ? '#e53935' : '#43a047'

    const topY = klineHeight - ((h - minPrice) / priceRange) * (klineHeight - 20)
    const bottomY = klineHeight - ((l - minPrice) / priceRange) * (klineHeight - 20)
    const openY = klineHeight - ((o - minPrice) / priceRange) * (klineHeight - 20)
    const closeY = klineHeight - ((c - minPrice) / priceRange) * (klineHeight - 20)

    klineCtx.strokeStyle = color
    klineCtx.lineWidth = 1
    klineCtx.beginPath()
    klineCtx.moveTo(x + candleWidth / 2, topY)
    klineCtx.lineTo(x + candleWidth / 2, bottomY)
    klineCtx.stroke()

    klineCtx.fillStyle = color
    const bodyTop = Math.min(openY, closeY)
    const bodyHeight = Math.abs(closeY - openY) || 1
    klineCtx.fillRect(x, bodyTop, candleWidth, bodyHeight)

    const volume = item.kline.volume || 0
    const volY = volumeHeight - (volume / maxVolume) * (volumeHeight - 10)
    volumeCtx.fillStyle = color
    volumeCtx.fillRect(x, volY, candleWidth, volumeHeight - volY)
  })
  
  console.log('Kline drawing completed')
}

const drawIndicator = () => {
  if (!klineData.value.length) {
    console.log('No data for indicator')
    return
  }
  
  const ctx = indicatorCanvas.value?.getContext('2d')
  if (!ctx) {
    console.log('Indicator canvas context not available')
    return
  }

  const data = [...klineData.value].reverse()
  const width = indicatorCanvas.value.width
  const height = indicatorCanvas.value.height

  ctx.clearRect(0, 0, width, height)

  ctx.strokeStyle = '#ccc'
  ctx.lineWidth = 1
  const gridLines = 4
  for (let i = 0; i <= gridLines; i++) {
    const y = (height / gridLines) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }

  ctx.strokeStyle = '#999'
  ctx.setLineDash([5, 5])
  const overboughtY = height * 0.2
  const oversoldY = height * 0.8
  ctx.beginPath()
  ctx.moveTo(0, overboughtY)
  ctx.lineTo(width, overboughtY)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(0, oversoldY)
  ctx.lineTo(width, oversoldY)
  ctx.stroke()
  ctx.setLineDash([])

  const candleWidth = Math.max(3, Math.floor(width / data.length) - 2)
  const gap = 2

  if (currentIndicator.value === 'kdj') {
    const kValues = data.map(item => item.indicator?.k_value || 0)
    const dValues = data.map(item => item.indicator?.d_value || 0)
    const jValues = data.map(item => item.indicator?.j_value || 0)

    const drawLine = (values, color) => {
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.beginPath()
      values.forEach((v, i) => {
        const x = i * (candleWidth + gap) + gap + candleWidth / 2
        const y = height - (v / 100) * (height - 20)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.stroke()
    }

    drawLine(kValues, '#e53935')
    drawLine(dValues, '#1e88e5')
    drawLine(jValues, '#43a047')
  } else {
    const rsi6Values = data.map(item => item.indicator?.rsi_6 || 0)
    const rsi12Values = data.map(item => item.indicator?.rsi_12 || 0)
    const rsi24Values = data.map(item => item.indicator?.rsi_24 || 0)

    const drawLine = (values, color) => {
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.beginPath()
      values.forEach((v, i) => {
        const x = i * (candleWidth + gap) + gap + candleWidth / 2
        const y = height - (v / 100) * (height - 20)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.stroke()
    }

    drawLine(rsi6Values, '#e53935')
    drawLine(rsi12Values, '#1e88e5')
    drawLine(rsi24Values, '#fb8c00')
  }
  
  console.log('Indicator drawing completed')
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 4) + '-' + dateStr.substring(4, 6) + '-' + dateStr.substring(6, 8)
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

const getChangeClass = (value) => {
  if (value === null || value === undefined) return ''
  return value >= 0 ? 'change-positive' : 'change-negative'
}

onMounted(() => {
  console.log('StockDetailView mounted')
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  authStore.fetchCurrentUser()
  
  const resizeCanvas = () => {
    if (klineCanvas.value) {
      klineCanvas.value.width = klineCanvas.value.offsetWidth * 2
      klineCanvas.value.height = 300 * 2
    }
    if (volumeCanvas.value) {
      volumeCanvas.value.width = volumeCanvas.value.offsetWidth * 2
      volumeCanvas.value.height = 100 * 2
    }
    if (indicatorCanvas.value) {
      indicatorCanvas.value.width = indicatorCanvas.value.offsetWidth * 2
      indicatorCanvas.value.height = 150 * 2
    }
    drawKline()
    drawIndicator()
  }

  fetchStockInfo()
  fetchKlineData()
  
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
})

watch(currentPeriod, () => {
  drawKline()
})
</script>

<style scoped>
.stock-detail {
  min-height: 100vh;
  background: #f5f5f5;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-back:hover {
  background: #e0e0e0;
}

.stock-title {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.stock-code {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.stock-name {
  font-size: 1.25rem;
  color: #666;
}

.user-info {
  color: #666;
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
  color: #666;
}

.stock-header {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.price-section {
  text-align: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.current-price {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.price-up {
  color: #e53935;
}

.price-down {
  color: #43a047;
}

.price-change {
  font-size: 1.25rem;
  font-weight: 600;
}

.change-pct {
  margin-left: 0.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item .label {
  color: #999;
  font-size: 0.9rem;
}

.info-item .value {
  font-weight: 600;
  color: #333;
}

.change-positive {
  color: #e53935;
}

.change-negative {
  color: #43a047;
}

.chart-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-tabs {
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
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #333;
}

.tab-btn.active {
  color: #4CAF50;
  border-bottom-color: #4CAF50;
}

.chart-area {
  position: relative;
  border-bottom: 1px solid #e0e0e0;
}

.kline-canvas {
  width: 100%;
  height: 300px;
  display: block;
}

.volume-canvas {
  width: 100%;
  height: 100px;
  display: block;
  border-top: 1px solid #f0f0f0;
}

.indicator-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
}

.indicator-area {
  border-bottom: 1px solid #e0e0e0;
}

.indicator-canvas {
  width: 100%;
  height: 150px;
  display: block;
}

.data-table {
  max-height: 300px;
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
  font-weight: 600;
  color: #666;
  position: sticky;
  top: 0;
  z-index: 1;
}

.kline-table td {
  padding: 0.5rem;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  color: #666;
}

.kline-table tr:hover {
  background: #fafafa;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 2rem !important;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .kline-table {
    font-size: 0.7rem;
  }
  
  .kline-table td, .kline-table th {
    padding: 0.3rem 0.2rem;
  }
}
</style>