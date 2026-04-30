<template>
  <nav class="sidebar-nav">
    <template v-for="menu in menus" :key="menu.id">
      <div v-if="menu.children && menu.children.length > 0" class="nav-group">
        <div class="nav-group-header" @click="toggleMenu(menu.id)">
          <span class="nav-icon">{{ getIcon(menu.icon) }}</span>
          <span>{{ menu.name }}</span>
          <span class="nav-arrow" :class="{ expanded: expandedMenus.includes(menu.id) }">▼</span>
        </div>
        <div v-show="expandedMenus.includes(menu.id)" class="nav-group-items">
          <router-link
            v-for="child in menu.children"
            :key="child.id"
            :to="child.path || '#'"
            class="nav-item child"
            :class="{ 'router-link-active': $route.path === child.path }"
          >
            <span class="nav-icon">{{ getIcon(child.icon) }}</span>
            <span>{{ child.name }}</span>
          </router-link>
        </div>
      </div>
      <router-link
        v-else
        :to="menu.path || '#'"
        class="nav-item"
        :class="{ 'router-link-active': $route.path === menu.path }"
      >
        <span class="nav-icon">{{ getIcon(menu.icon) }}</span>
        <span>{{ menu.name }}</span>
      </router-link>
    </template>
  </nav>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { menusAPI } from '../api'

const route = useRoute()
const menus = ref([])
const expandedMenus = ref([])

const fetchMenus = async () => {
  try {
    const response = await menusAPI.getMenus()
    menus.value = response.data
    expandActiveParent()
  } catch (error) {
    console.error('Failed to fetch menus:', error)
  }
}

const expandActiveParent = () => {
  const currentPath = route.path
  for (const menu of menus.value) {
    if (menu.children && menu.children.length > 0) {
      const hasActiveChild = menu.children.some(child => child.path === currentPath)
      if (hasActiveChild && !expandedMenus.value.includes(menu.id)) {
        expandedMenus.value.push(menu.id)
      }
    }
  }
}

const toggleMenu = (menuId) => {
  const index = expandedMenus.value.indexOf(menuId)
  if (index === -1) {
    expandedMenus.value.push(menuId)
  } else {
    expandedMenus.value.splice(index, 1)
  }
}

watch(() => route.path, () => {
  expandActiveParent()
})

const getIcon = (iconName) => {
  const iconMap = {
    'LayoutDashboard': '📊',
    'Users': '👥',
    'Settings': '⚙️',
    'Menu': '📋',
    'Shield': '🛡️',
    'Profile': '👤',
    'TrendingUp': '📈',
    'LineChart': '📉',
    'BarChart': '📊',
    'Home': '🏠',
    'About': 'ℹ️',
    'Contact': '📧',
    'Logout': '🚪'
  }
  return iconMap[iconName] || '📄'
}

onMounted(() => {
  fetchMenus()
})
</script>

<style scoped>
.nav-group {
  margin-bottom: 4px;
}

.nav-group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-group-header:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-arrow {
  margin-left: auto;
  font-size: 10px;
  transition: transform 0.3s ease;
}

.nav-arrow.expanded {
  transform: rotate(180deg);
}

.nav-group-items {
  padding-left: 20px;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.router-link-active {
  background: rgba(102, 126, 234, 0.3);
  color: white;
}

.nav-item.child {
  padding-left: 32px;
  font-size: 14px;
}

.nav-icon {
  font-size: 20px;
}
</style>