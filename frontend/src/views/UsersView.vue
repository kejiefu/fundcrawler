<template>
  <div class="users-view">
    <el-page-header @back="goBack" content="User Management">
      <template #extra>
        <span class="user-info">Welcome, {{ user?.full_name || user?.username }}</span>
      </template>
    </el-page-header>

    <div class="content">
      <el-card title="All Users" shadow="hover">
        <el-table
          v-loading="loading"
          :data="users"
          border
          style="width: 100%"
          :empty-text="error || 'No users found'"
        >
          <el-table-column prop="id" label="ID" />
          <el-table-column prop="username" label="Username" />
          <el-table-column prop="email" label="Email" />
          <el-table-column prop="full_name" label="Full Name">
            <template #default="scope">
              {{ scope.row.full_name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="Status">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'warning'">
                {{ scope.row.is_active ? 'Active' : 'Inactive' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_superuser" label="Role">
            <template #default="scope">
              <el-tag :type="scope.row.is_superuser ? 'primary' : 'info'">
                {{ scope.row.is_superuser ? 'Admin' : 'User' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="Created">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="Actions">
            <template #default="scope">
              <el-button size="small" @click="editUser(scope.row)">
                <el-icon><Edit /></el-icon>
                Edit
              </el-button>
              <el-button
                v-if="!scope.row.is_superuser"
                size="small"
                type="danger"
                @click="deleteUserConfirm(scope.row)"
              >
                <el-icon><Delete /></el-icon>
                Delete
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-dialog title="Edit User" v-model="showEditModal" width="480px">
        <el-form :model="editForm" label-width="80px">
          <el-form-item label="Email">
            <el-input v-model="editForm.email" type="email" />
          </el-form-item>
          <el-form-item label="Full Name">
            <el-input v-model="editForm.full_name" />
          </el-form-item>
          <el-form-item label="Active">
            <el-switch v-model="editForm.is_active" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="closeModal">Cancel</el-button>
          <el-button type="primary" @click="saveUser">Save</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useUserStore } from '../stores/user'
import { Edit, Delete } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()

const user = authStore.user
const users = ref([])
const loading = ref(true)
const error = ref('')
const showEditModal = ref(false)
const editForm = reactive({
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
  editForm.id = userItem.id
  editForm.email = userItem.email
  editForm.full_name = userItem.full_name || ''
  editForm.is_active = userItem.is_active
  showEditModal.value = true
}

const saveUser = async () => {
  const result = await userStore.updateUser(editForm.id, {
    email: editForm.email,
    full_name: editForm.full_name,
    is_active: editForm.is_active
  })

  if (result.success) {
    closeModal()
    await fetchUsers()
  } else {
    ElMessage.error(result.message)
  }
}

const deleteUserConfirm = async (userItem) => {
  ElMessageBox.confirm(
    `Are you sure you want to delete user "${userItem.username}"?`,
    'Confirm Delete',
    {
      confirmButtonText: 'Yes',
      cancelButtonText: 'No',
      type: 'warning'
    }
  ).then(async () => {
    const result = await userStore.deleteUser(userItem.id)
    if (result.success) {
      ElMessage.success('User deleted successfully')
      await fetchUsers()
    } else {
      ElMessage.error(result.message)
    }
  }).catch(() => {
    ElMessage.info('Delete cancelled')
  })
}

const closeModal = () => {
  showEditModal.value = false
}

const goBack = () => {
  router.back()
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
.users-view {
  padding: 24px;
}

.user-info {
  color: #666;
  font-size: 14px;
}

.content {
  margin-top: 24px;
}
</style>