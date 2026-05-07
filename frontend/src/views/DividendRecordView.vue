<template>
  <div class="dividend-record-container">
    <div class="page-header">
      <h2>分红记录管理</h2>
      <p>查看和管理股票分红历史数据</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索股票代码或名称"
        class="search-input"
        @keyup.enter="loadData"
      >
        <template #append>
          <el-button @click="loadData" type="primary">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <el-table
      :data="tableData"
      :loading="loading"
      border
      style="width: 100%"
      :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
    >
      <el-table-column prop="code" label="股票代码" width="100">
        <template #default="scope">
          <span class="code-cell">{{ scope.row.code }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="股票名称" width="100" />
      <el-table-column prop="announcement_date" label="公告日期" width="110">
        <template #default="scope">
          <span v-if="scope.row.announcement_date">{{ formatDate(scope.row.announcement_date) }}</span>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="dividend" label="派息(每10股)" width="130">
        <template #default="scope">
          <span v-if="scope.row.dividend !== null && scope.row.dividend !== undefined" class="highlight">
            {{ scope.row.dividend.toFixed(4) }}
          </span>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="bonus_share" label="送股(每10股)" width="120">
        <template #default="scope">
          <span v-if="scope.row.bonus_share">{{ scope.row.bonus_share.toFixed(4) }}</span>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="transfer_share" label="转增(每10股)" width="120">
        <template #default="scope">
          <span v-if="scope.row.transfer_share">{{ scope.row.transfer_share }}</span>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.progress" :type="scope.row.progress === '实施' ? 'success' : 'warning'" size="small">
            {{ scope.row.progress }}
          </el-tag>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="ex_dividend_date" label="除权除息日" width="110">
        <template #default="scope">
          <span v-if="scope.row.ex_dividend_date">{{ formatDate(scope.row.ex_dividend_date) }}</span>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="record_date" label="股权登记日" width="110">
        <template #default="scope">
          <span v-if="scope.row.record_date">{{ formatDate(scope.row.record_date) }}</span>
          <span v-else class="empty">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="170">
        <template #default="scope">
          <span>{{ formatDateTime(scope.row.updated_at) }}</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      :current-page="pagination.page"
      :page-size="pagination.pageSize"
      :total="total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { Search } from '@element-plus/icons-vue';
import { stocksAPI } from '../api';

const loading = ref(false);
const searchText = ref('');
const tableData = ref([]);
const total = ref(0);
const pagination = reactive({
  page: 1,
  pageSize: 50
});

const loadData = async () => {
  loading.value = true;
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    };
    if (searchText.value) {
      params.search = searchText.value;
    }
    const response = await stocksAPI.getDividendRecords(params);
    tableData.value = response.data.items;
    total.value = response.data.total;
    pagination.page = response.data.page;
    pagination.pageSize = response.data.pageSize;
  } catch (error) {
    console.error('Failed to load dividend records:', error);
    tableData.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const handleSizeChange = (val) => {
  pagination.pageSize = val;
  pagination.page = 1;
  loadData();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  loadData();
};

const formatDate = (dateStr) => {
  if (!dateStr || dateStr.length !== 8) return '-';
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
};

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-';
  const date = new Date(dateTimeStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

loadData();
</script>

<style scoped>
.dividend-record-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-header p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.search-bar {
  margin-bottom: 20px;
}

.search-input {
  width: 300px;
}

.code-cell {
  font-family: 'Monaco', 'Menlo', monospace;
  color: #606266;
}

.highlight {
  font-weight: 600;
  color: #e6a23c;
}

.empty {
  color: #c0c4cc;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th) {
  font-weight: 600;
}

:deep(.el-pagination) {
  margin-top: 20px;
  text-align: right;
}
</style>
