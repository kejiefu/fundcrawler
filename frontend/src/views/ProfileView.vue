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
        <router-link to="/users" class="nav-item">
          <span class="nav-icon">👥</span>
          <span>Users</span>
        </router-link>
        <router-link to="/profile" class="nav-item active">
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
        <h1>Profile</h1>
        <div class="user-info">
          <span>Welcome, {{ currentUser?.full_name || currentUser?.username }}</span>
        </div>
      </header>

      <div class="content">
        <div class="profile-card">
          <div class="profile-header">
            <div class="avatar">
              {{ currentUser?.username?.charAt(0).toUpperCase() }}
            </div>
            <div class="profile-info">
              <h2>{{ currentUser?.full_name || currentUser?.username }}</h2>
              <p>{{ currentUser?.email }}</p>
              <span :class="['role-badge', currentUser?.is_superuser ? 'admin' : 'user']">
                {{ currentUser?.is_superuser ? 'Administrator' : 'User' }}
              </span>
            </div>
          </div>

          <div class="profile-details">
            <div class="detail-item">
              <span class="label">Username</span>
              <span class="value">{{ currentUser?.username }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Email</span>
              <span class="value">{{ currentUser?.email }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Full Name</span>
              <span class="value">{{ currentUser?.full_name || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Status</span>
              <span :class="['status-badge', currentUser?.is_active ? 'active' : 'inactive']">
                {{ currentUser?.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">Account Created</span>
              <span class="value">{{ formatDate(currentUser?.created_at) }}</span>
            </div>
          </div>

          <div class="profile-actions">
            <button @click="showEditModal = true" class="btn-edit">
              Edit Profile
            </button>
          </div>
        </div>

        <div v-if="showEditModal" class="modal-overlay" @click="closeModal">
          <div class="modal" @click.stop>
            <h3>Edit Profile</h3>
            <form @submit.prevent="saveProfile">
              <div class="form-group">
                <label>Email</label>
                <input v-model="editForm.email" type="email" required />
              </div>
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="editForm.full_name" type="text" />
              </div>
              <div class="form-group">
                <label>New Password (leave blank to keep current)</label>
                <input v-model="editForm.password" type="password" />
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()

const currentUser = computed(() => authStore.user)
const showEditModal = ref(false)
const editForm = ref({
  email: '',
  full_name: '',
  password: ''
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const saveProfile = async () => {
  const userId = currentUser.value.id
  const updateData = {
    email: editForm.value.email,
    full_name: editForm.value.full_name
  }

  if (editForm.value.password) {
    updateData.password = editForm.value.password
  }

  const result = await userStore.updateUser(userId, updateData)

  if (result.success) {
    await authStore.fetchCurrentUser()
    closeModal()
  } else {
    alert(result.message)
  }
}

const closeModal = () => {
  showEditModal.value = false
  editForm.value = {
    email: currentUser.value?.email || '',
    full_name: currentUser.value?.full_name || '',
    password: ''
  }
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

  if (currentUser.value) {
    editForm.value = {
      email: currentUser.value.email || '',
      full_name: currentUser.value.full_name || '',
      password: ''
    }
  }
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

.profile-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  max-width: 800px;
}

.profile-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 600;
  color: white;
}

.profile-info h2 {
  font-size: 24px;
  color: white;
  margin-bottom: 4px;
}

.profile-info p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  margin-bottom: 8px;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: rgba(255, 255, 255, 0.3);
  color: white;
}

.role-badge.user {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.profile-details {
  padding: 32px 40px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  color: #666;
  font-size: 14px;
}

.detail-item .value {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: rgba(72, 199, 142, 0.15);
  color: #48c78e;
}

.status-badge.inactive {
  background: rgba(255, 99, 132, 0.15);
  color: #ff6384;
}

.profile-actions {
  padding: 24px 40px;
  background: #f8f9fa;
  border-top: 1px solid #f0f0f0;
}

.btn-edit {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-edit:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
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

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e1e1e1;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
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
