<template>
  <div class="alert-list">
    <el-card shadow="hover">
      <template #header>
        <span>告警列表</span>
      </template>

      <div class="filters">
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 150px">
          <el-option label="触发中" value="firing" />
          <el-option label="已确认" value="acknowledged" />
          <el-option label="已解决" value="resolved" />
        </el-select>
        <el-select v-model="filters.severity" placeholder="严重程度" clearable style="width: 150px; margin-left: 10px">
          <el-option label="严重" value="critical" />
          <el-option label="警告" value="warning" />
          <el-option label="信息" value="info" />
        </el-select>
        <el-button type="primary" @click="loadAlerts" style="margin-left: 10px">查询</el-button>
      </div>

      <el-table :data="alerts" stripe style="margin-top: 20px" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="message" label="告警信息" />
        <el-table-column prop="severity" label="严重程度">
          <template #default="{ row }">
            <el-tag :type="severityTypes[row.severity]">{{ severityLabels[row.severity] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="statusTypes[row.status]">{{ statusLabels[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fired_at" label="触发时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === 'firing'" size="small" @click="handleAcknowledge(row)">
              确认
            </el-button>
            <el-button v-if="row.status !== 'resolved'" size="small" type="success" @click="handleResolve(row)">
              解决
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { alertApi } from '@/api/alerts'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const alerts = ref<any[]>([])

const filters = reactive({
  status: '',
  severity: ''
})

const severityLabels: Record<string, string> = {
  critical: '严重',
  warning: '警告',
  info: '信息'
}

const severityTypes: Record<string, any> = {
  critical: 'danger',
  warning: 'warning',
  info: 'info'
}

const statusLabels: Record<string, string> = {
  firing: '触发中',
  acknowledged: '已确认',
  resolved: '已解决'
}

const statusTypes: Record<string, any> = {
  firing: 'danger',
  acknowledged: 'warning',
  resolved: 'success'
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const { data } = await alertApi.listAlerts(filters)
    alerts.value = data
  } catch (error) {
    ElMessage.error('加载告警列表失败')
  } finally {
    loading.value = false
  }
}

const handleAcknowledge = async (row: any) => {
  try {
    await alertApi.acknowledgeAlert(row.id, authStore.user?.username || 'unknown')
    ElMessage.success('已确认告警')
    loadAlerts()
  } catch (error) {
    ElMessage.error('确认失败')
  }
}

const handleResolve = async (row: any) => {
  try {
    await alertApi.resolveAlert(row.id)
    ElMessage.success('已解决告警')
    loadAlerts()
  } catch (error) {
    ElMessage.error('解决失败')
  }
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alert-list {
  width: 100%;
}

.filters {
  display: flex;
  align-items: center;
}
</style>
