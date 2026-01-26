<template>
  <div class="resource-list">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>资源列表</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            添加资源
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <div class="filters">
        <el-select v-model="filters.type" placeholder="资源类型" clearable style="width: 150px">
          <el-option label="物理机" value="physical" />
          <el-option label="虚拟机" value="virtual" />
          <el-option label="容器" value="container" />
          <el-option label="云主机" value="cloud" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 150px; margin-left: 10px">
          <el-option label="活跃" value="active" />
          <el-option label="非活跃" value="inactive" />
          <el-option label="维护中" value="maintenance" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-button type="primary" @click="loadResources" style="margin-left: 10px">查询</el-button>
      </div>

      <!-- Table -->
      <el-table :data="resources" stripe style="margin-top: 20px" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="资源名称" />
        <el-table-column prop="type" label="类型">
          <template #default="{ row }">
            <el-tag>{{ typeLabels[row.type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" />
        <el-table-column prop="cpu_cores" label="CPU 核数" />
        <el-table-column prop="memory_gb" label="内存 (GB)" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="statusTypes[row.status]">{{ statusLabels[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="CPU 使用率">
          <template #default="{ row }">
            <el-progress :percentage="row.cpu_usage" :color="getProgressColor(row.cpu_usage)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadResources"
        @current-change="loadResources"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingResource ? '编辑资源' : '添加资源'"
      width="600px"
    >
      <el-form :model="resourceForm" label-width="120px">
        <el-form-item label="资源名称" required>
          <el-input v-model="resourceForm.name" />
        </el-form-item>
        <el-form-item label="资源类型" required>
          <el-select v-model="resourceForm.type" style="width: 100%">
            <el-option label="物理机" value="physical" />
            <el-option label="虚拟机" value="virtual" />
            <el-option label="容器" value="container" />
            <el-option label="云主机" value="cloud" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP 地址">
          <el-input v-model="resourceForm.ip_address" />
        </el-form-item>
        <el-form-item label="主机名">
          <el-input v-model="resourceForm.hostname" />
        </el-form-item>
        <el-form-item label="CPU 核数">
          <el-input-number v-model="resourceForm.cpu_cores" :min="1" />
        </el-form-item>
        <el-form-item label="内存 (GB)">
          <el-input-number v-model="resourceForm.memory_gb" :min="1" />
        </el-form-item>
        <el-form-item label="磁盘 (GB)">
          <el-input-number v-model="resourceForm.disk_gb" :min="1" />
        </el-form-item>
        <el-form-item label="操作系统">
          <el-input v-model="resourceForm.os_type" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="resourceForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { resourceApi } from '@/api/resources'

const loading = ref(false)
const resources = ref<any[]>([])
const showCreateDialog = ref(false)
const editingResource = ref<any>(null)

const filters = reactive({
  type: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const resourceForm = reactive({
  name: '',
  type: 'physical',
  ip_address: '',
  hostname: '',
  cpu_cores: 4,
  memory_gb: 8,
  disk_gb: 100,
  os_type: '',
  description: ''
})

const typeLabels: Record<string, string> = {
  physical: '物理机',
  virtual: '虚拟机',
  container: '容器',
  cloud: '云主机'
}

const statusLabels: Record<string, string> = {
  active: '活跃',
  inactive: '非活跃',
  maintenance: '维护中',
  offline: '离线'
}

const statusTypes: Record<string, any> = {
  active: 'success',
  inactive: 'info',
  maintenance: 'warning',
  offline: 'danger'
}

const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
}

const loadResources = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      ...filters
    }
    const { data } = await resourceApi.list(params)
    resources.value = data
    // Note: In production, backend should return total count
    pagination.total = data.length
  } catch (error) {
    ElMessage.error('加载资源列表失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = (row: any) => {
  editingResource.value = row
  Object.assign(resourceForm, row)
  showCreateDialog.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此资源吗?', '提示', {
      type: 'warning'
    })
    await resourceApi.delete(row.id)
    ElMessage.success('删除成功')
    loadResources()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSave = async () => {
  try {
    if (editingResource.value) {
      await resourceApi.update(editingResource.value.id, resourceForm)
      ElMessage.success('更新成功')
    } else {
      await resourceApi.create(resourceForm)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    editingResource.value = null
    loadResources()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadResources()
})
</script>

<style scoped>
.resource-list {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  align-items: center;
}
</style>
