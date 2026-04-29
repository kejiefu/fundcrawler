<template>
  <div>
    <header class="top-bar">
      <h1>Menu Management</h1>
      <div class="user-info">
        <span>Welcome, {{ user?.full_name || user?.username }}</span>
      </div>
    </header>

    <div class="content">
      <div class="card">
        <div class="card-header">
          <h2>All Menus</h2>
          <button @click="openCreateModal" class="btn-primary">Add Menu</button>
        </div>

          <div v-if="loading" class="loading">Loading menus...</div>
          <div v-else-if="error" class="error">{{ error }}</div>
          <table v-else class="menus-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Path</th>
                <th>Icon</th>
                <th>Parent</th>
                <th>Order</th>
                <th>Status</th>
                <th>Permission</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="menu in menus" :key="menu.id">
                <td>{{ menu.id }}</td>
                <td>{{ menu.name }}</td>
                <td>{{ menu.path || '-' }}</td>
                <td>{{ menu.icon || '-' }}</td>
                <td>{{ getParentName(menu.parent_id) }}</td>
                <td>{{ menu.order }}</td>
                <td>
                  <span :class="['status', menu.is_active ? 'active' : 'inactive']">
                    {{ menu.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>{{ menu.permission || '-' }}</td>
                <td>
                  <button @click="editMenu(menu)" class="action-btn edit">Edit</button>
                  <button @click="deleteMenuConfirm(menu)" class="action-btn delete">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="showModal" class="modal-overlay" @click="closeModal">
          <div class="modal" @click.stop>
            <h3>{{ isEditing ? 'Edit Menu' : 'Create Menu' }}</h3>
            <form @submit.prevent="saveMenu">
              <div class="form-group">
                <label>Name</label>
                <input v-model="form.name" type="text" required />
              </div>
              <div class="form-group">
                <label>Path</label>
                <input v-model="form.path" type="text" placeholder="/example" />
              </div>
              <div class="form-group">
                <label>Icon</label>
                <input v-model="form.icon" type="text" placeholder="IconName" />
              </div>
              <div class="form-group">
                <label>Parent Menu</label>
                <select v-model="form.parent_id">
                  <option :value="null">No Parent (Root)</option>
                  <option v-for="menu in flatMenus" :key="menu.id" :value="menu.id">
                    {{ menu.name }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Order</label>
                <input v-model.number="form.order" type="number" min="0" />
              </div>
              <div class="form-group">
                <label>Permission</label>
                <input v-model="form.permission" type="text" placeholder="e.g., menu.view" />
              </div>
              <div class="form-group">
                <label>Active</label>
                <select v-model="form.is_active">
                  <option :value="true">Active</option>
                  <option :value="false">Inactive</option>
                </select>
              </div>
              <div class="modal-actions">
                <button type="button" @click="closeModal" class="btn-cancel">Cancel</button>
                <button type="submit" class="btn-save">Save</button>
              </div>
            </form>
          </div>
        </div>
      </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { menusAPI } from '../api'

const router = useRouter()
const authStore = useAuthStore()

const user = authStore.user
const menus = ref([])
const loading = ref(true)
const error = ref('')
const showModal = ref(false)
const isEditing = ref(false)
const form = ref({
  id: null,
  name: '',
  path: '',
  icon: '',
  parent_id: null,
  order: 0,
  is_active: true,
  permission: ''
})

const flatMenus = computed(() => {
  const result = []
  const flatten = (menuList, level = 0) => {
    for (const menu of menuList) {
      result.push(menu)
      if (menu.children && menu.children.length > 0) {
        flatten(menu.children, level + 1)
      }
    }
  }
  flatten(menus.value)
  return result
})

const getParentName = (parentId) => {
  if (!parentId) return '-'
  const parent = flatMenus.value.find(m => m.id === parentId)
  return parent ? parent.name : '-'
}

const fetchMenus = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await menusAPI.getAllMenus()
    menus.value = response.data
  } catch (err) {
    error.value = 'Failed to load menus'
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = {
    id: null,
    name: '',
    path: '',
    icon: '',
    parent_id: null,
    order: 0,
    is_active: true,
    permission: ''
  }
  showModal.value = true
}

const editMenu = (menu) => {
  isEditing.value = true
  form.value = {
    id: menu.id,
    name: menu.name,
    path: menu.path || '',
    icon: menu.icon || '',
    parent_id: menu.parent_id,
    order: menu.order,
    is_active: menu.is_active,
    permission: menu.permission || ''
  }
  showModal.value = true
}

const saveMenu = async () => {
  try {
    if (isEditing.value) {
      await menusAPI.updateMenu(form.value.id, form.value)
    } else {
      await menusAPI.createMenu(form.value)
    }
    closeModal()
    await fetchMenus()
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to save menu')
  }
}

const deleteMenuConfirm = async (menu) => {
  if (confirm(`Are you sure you want to delete menu "${menu.name}"?`)) {
    try {
      await menusAPI.deleteMenu(menu.id)
      await fetchMenus()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete menu')
    }
  }
}

const closeModal = () => {
  showModal.value = false
}

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  authStore.fetchCurrentUser()
  fetchMenus()
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
.error {
  padding: 40px;
  text-align: center;
  color: #666;
}

.error {
  color: #e74c3c;
}

.menus-table {
  width: 100%;
  border-collapse: collapse;
}

.menus-table th,
.menus-table td {
  padding: 14px 20px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.menus-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menus-table td {
  color: #333;
  font-size: 14px;
}

.menus-table tr:hover {
  background: #f8f9fa;
}

.status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status.active {
  background: rgba(72, 199, 142, 0.15);
  color: #48c78e;
}

.status.inactive {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  margin-right: 8px;
  transition: all 0.3s ease;
}

.action-btn.edit {
  background: #f0f4ff;
  color: #667eea;
}

.action-btn.edit:hover {
  background: #667eea;
  color: white;
}

.action-btn.delete {
  background: #fff0f0;
  color: #e74c3c;
}

.action-btn.delete:hover {
  background: #e74c3c;
  color: white;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 32px;
  width: 480px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h3 {
  margin: 0 0 24px;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-save {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
  border: none;
}

.btn-cancel:hover {
  background: #e5e5e5;
}

.btn-save {
  background: #667eea;
  color: white;
  border: none;
}

.btn-save:hover {
  background: #5568d3;
}
</style>
