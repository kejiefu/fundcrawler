<template>
  <div>
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
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #e74c3c;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 14px 20px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.users-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.users-table td {
  color: #333;
  font-size: 14px;
}

.users-table tr:hover {
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

.role {
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
  background: rgba(108, 117, 125, 0.15);
  color: #6c757d;
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
