<template>
  <div class="monitoring-dashboard">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>监控中心</span>
          <el-button @click="loadData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <div class="metric-card">
            <h3>平均 CPU 使用率</h3>
            <div class="metric-value">{{ dashboardData.average_cpu_usage?.toFixed(1) || 0 }}%</div>
            <el-progress :percentage="dashboardData.average_cpu_usage || 0" />
          </div>
        </el-col>
        <el-col :span="8">
          <div class="metric-card">
            <h3>平均内存使用率</h3>
            <div class="metric-value">{{ dashboardData.average_memory_usage?.toFixed(1) || 0 }}%</div>
            <el-progress :percentage="dashboardData.average_memory_usage || 0" />
          </div>
        </el-col>
        <el-col :span="8">
          <div class="metric-card">
            <h3>平均磁盘使用率</h3>
            <div class="metric-value">{{ dashboardData.average_disk_usage?.toFixed(1) || 0 }}%</div>
            <el-progress :percentage="dashboardData.average_disk_usage || 0" />
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <h3>资源使用率 TOP 5</h3>
      <el-table :data="dashboardData.top_cpu_resources || []" stripe>
        <el-table-column prop="name" label="资源名称" />
        <el-table-column label="CPU 使用率">
          <template #default="{ row }">
            <el-progress :percentage="row.cpu_usage" />
          </template>
        </el-table-column>
        <el-table-column label="内存使用率">
          <template #default="{ row }">
            <el-progress :percentage="row.memory_usage" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { monitoringApi } from '@/api/monitoring'

const dashboardData = ref<any>({})

const loadData = async () => {
  try {
    const { data } = await monitoringApi.getDashboard()
    dashboardData.value = data
  } catch (error) {
    console.error('Failed to load monitoring data:', error)
  }
}

onMounted(() => {
  loadData()
  // Auto refresh every 30 seconds
  setInterval(loadData, 30000)
})
</script>

<style scoped>
.monitoring-dashboard {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-card {
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.metric-card h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.metric-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}
</style>
