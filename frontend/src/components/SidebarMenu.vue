<template>
  <el-menu
    :default-active="activeMenu"
    class="sidebar-menu"
    mode="vertical"
    background-color="transparent"
    text-color="rgba(255,255,255,0.7)"
    active-text-color="#fff"
  >
    <template v-for="menu in menus" :key="menu.id">
      <el-sub-menu v-if="menu.children && menu.children.length > 0" :index="menu.id.toString()">
        <template #title>
          <el-icon><component :is="getIcon(menu.icon)" /></el-icon>
          <span>{{ menu.name }}</span>
        </template>
        <el-menu-item
          v-for="child in menu.children"
          :key="child.id"
          :index="child.path"
          @click="$router.push(child.path)"
        >
          <el-icon><component :is="getIcon(child.icon)" /></el-icon>
          <span>{{ child.name }}</span>
        </el-menu-item>
      </el-sub-menu>
      <el-menu-item
        v-else
        :index="menu.path"
        @click="$router.push(menu.path)"
      >
        <el-icon><component :is="getIcon(menu.icon)" /></el-icon>
        <span>{{ menu.name }}</span>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { menusAPI } from '../api'
import {
  DataBoard,
  Setting,
  List,
  Lock,
  User,
  TrendCharts,
  PieChart,
  HomeFilled,
  InfoFilled,
  Message,
  Switch
} from '@element-plus/icons-vue'

const route = useRoute()
const menus = ref([])

const activeMenu = computed(() => {
  return route.path
})

const fetchMenus = async () => {
  try {
    const response = await menusAPI.getMenus()
    menus.value = response.data
  } catch (error) {
    console.error('Failed to fetch menus:', error)
  }
}

const getIcon = (iconName) => {
  const iconMap = {
    'LayoutDashboard': DataBoard,
    'Users': User,
    'Settings': Setting,
    'Menu': List,
    'Shield': Lock,
    'Profile': User,
    'TrendingUp': TrendCharts,
    'LineChart': TrendCharts,
    'BarChart': PieChart,
    'Home': HomeFilled,
    'About': InfoFilled,
    'Contact': Message,
    'Logout': Switch
  }
  return iconMap[iconName] || HomeFilled
}

watch(() => route.path, () => {
})

onMounted(() => {
  fetchMenus()
})
</script>

<style scoped>
.sidebar-menu {
  border-right: none;
  padding: 16px;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  margin-bottom: 4px;
  border-radius: 8px;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-menu :deep(.el-menu-item.is-active),
.sidebar-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  background: rgba(102, 126, 234, 0.3);
}

.sidebar-menu :deep(.el-sub-menu__title) {
  padding: 12px 16px;
}

.sidebar-menu :deep(.el-menu-item) {
  padding: 12px 16px;
}

.sidebar-menu :deep(.el-menu-item__icon) {
  font-size: 18px;
  margin-right: 12px;
}

.sidebar-menu :deep(.el-sub-menu__icon) {
  font-size: 18px;
  margin-right: 12px;
}

.sidebar-menu :deep(.el-menu-item.is-active .el-menu-item__icon),
.sidebar-menu :deep(.el-sub-menu.is-active .el-sub-menu__icon) {
  color: #fff;
}
</style>