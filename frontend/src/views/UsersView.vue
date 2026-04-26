<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item">
          <span class="nav-icon">📊</span>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/users" class="nav-item active">
          <span class="nav-icon">👥</span>
          <span>Users</span>
        </router-link>
        <router-link to="/profile" class="nav-item">
          <span class="nav-icon">👤</span>
          <span>Profile</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <button @click="handleLogout" class="logout-button">
          <span class="nav-icon">🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <h1>User Management</h1>
        <div class="user-info">
          <span>Welcome, {{ user?.full_name || user?.username }}</span>
        </div>
      </header>

      <div class="content">
        <div class="card">
          <div class="card-header">
            <h2>All Users</h2>
          </div>

          <div v-if="loading" class="loading">Loading users...</div>
          <div v-else-if="error" class="error">{{ error }}</div>
          <table v-else class="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Full Name</th>
                <th>Status</th>
                <th>Role</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="userItem in users" :key="userItem.id">
                <td>{{ userItem.id }}</td>
                <td>{{ userItem.username }}</td>
                <td>{{ userItem.email }}</td>
                <td>{{ userItem.full_name || '-' }}</td>
                <td>
                  <span :class="['status', userItem.is_active ? 'active' : 'inactive']">
                    {{ userItem.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <span :class="['role', userItem.is_superuser ? 'admin' : 'user']">
                    {{ userItem.is_superuser ? 'Admin' : 'User' }}
                  </span>
                </td>
                <td>{{ formatDate(userItem.created_at) }}</td>
                <td>
                  <button @click="editUser(userItem)" class="action-btn edit">Edit</button>
                  <button
                    v-if="!userItem.is_superuser"
                    @click="deleteUserConfirm(userItem)"
                    class="action-btn delete"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="showEditModal" class="modal-overlay" @click="closeModal">
          <div class="modal" @click.stop>
            <h3>Edit User</h3>
            <form @submit.prevent="saveUser">
              <div class="form-group">
                <label>Email</label>
                <input v-model="editForm.email" type="email" required />
              </div>
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="editForm.full_name" type="text" />
              </div>
              <div class="form-group">
                <label>Active</label>
                <select v-model="editForm.is_active">
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
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()

const user = authStore.user
const users = ref([])
const loading = ref(true)
const error = ref('')
const showEditModal = ref(false)
const editForm = ref({
  id: null,
  email: '',
  full_name: '',
  is_active: true
})

const fetchUsers = async () => {
  loading.value = true
  error.value = ''
  try {
    await userStore.fetchUsers()
    users.value = userStore.users
  } catch (err) {
    error.value = 'Failed to load users'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const editUser = (userItem) => {
  editForm.value = {
    id: userItem.id,
    email: userItem.email,
    full_name: userItem.full_name,
    is_active: userItem.is_active
  }
  showEditModal.value = true
}

const saveUser = async () => {
  const result = await userStore.updateUser(editForm.value.id, {
    email: editForm.value.email,
    full_name: editForm.value.full_name,
    is_active: editForm.value.is_active
  })

  if (result.success) {
    closeModal()
    await fetchUsers()
  } else {
    alert(result.message)
  }
}

const deleteUserConfirm = async (userItem) => {
  if (confirm(`Are you sure you want to delete user "${userItem.username}"?`)) {
    const result = await userStore.deleteUser(userItem.id)
    if (result.success) {
      await fetchUsers()
    } else {
      alert(result.message)
    }
  }
}

const closeModal = () => {
  showEditModal.value = false
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  authStore.fetchCurrentUser()
  fetchUsers()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
}

.sidebar-header {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 20px;
  font-weight: 600;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
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

.nav-item.router-link-active,
.nav-item.active {
  background: rgba(102, 126, 234, 0.3);
  color: white;
}

.nav-icon {
  font-size: 20px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.logout-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.main-content {
  flex: 1;
  margin-left: 260px;
  background: #f5f5f5;
  min-height: 100vh;
}

.top-bar {
  background: white;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.top-bar h1 {
  font-size: 24px;
  color: #1a1a2e;
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
  border-bottom: 1px solid #f0f0f0;
}

.card-header h2 {
  font-size: 18px;
  color: #1a1a2e;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #c33;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background: #f8f9fa;
}

.users-table th {
  text-align: left;
  padding: 14px 16px;
  font-weight: 600;
  color: #333;
  font-size: 13px;
  text-transform: uppercase;
}

.users-table tbody tr {
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.users-table tbody tr:hover {
  background: #f8f9fa;
}

.users-table td {
  padding: 14px 16px;
  color: #333;
  font-size: 14px;
}

.status {
  display: inline-block;
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
  background: rgba(255, 99, 132, 0.15);
  color: #ff6384;
}

.role {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role.admin {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.role.user {
  background: rgba(255, 165, 2, 0.15);
  color: #ffa502;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}

.action-btn.edit {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.action-btn.edit:hover {
  background: rgba(102, 126, 234, 0.3);
}

.action-btn.delete {
  background: rgba(255, 99, 132, 0.15);
  color: #ff6384;
}

.action-btn.delete:hover {
  background: rgba(255, 99, 132, 0.3);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 32px;
  width: 100%;
  max-width: 480px;
}

.modal h3 {
  font-size: 20px;
  color: #1a1a2e;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e1e1e1;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-cancel,
.btn-save {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
  border: none;
}

.btn-cancel:hover {
  background: #e8e8e8;
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.btn-save:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
