<template>
  <div class="dashboard">
    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #409EFF">
              <el-icon :size="32"><Server /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.total_resources || 0 }}</div>
              <div class="stat-label">总资源数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #67C23A">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.average_cpu_usage?.toFixed(1) || 0 }}%</div>
              <div class="stat-label">平均 CPU 使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #E6A23C">
              <el-icon :size="32"><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.average_memory_usage?.toFixed(1) || 0 }}%</div>
              <div class="stat-label">平均内存使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #F56C6C">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ alertStats.firing || 0 }}</div>
              <div class="stat-label">活跃告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>资源 CPU 使用率 TOP 5</span>
          </template>
          <div ref="cpuChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>资源类型分布</span>
          </template>
          <div ref="typeChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Top Resources Table -->
    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <span>资源使用率排行</span>
      </template>
      <el-table :data="dashboardData.top_cpu_resources || []" stripe>
        <el-table-column prop="name" label="资源名称" />
        <el-table-column prop="cpu_usage" label="CPU 使用率">
          <template #default="{ row }">
            <el-progress :percentage="row.cpu_usage" :color="getProgressColor(row.cpu_usage)" />
          </template>
        </el-table-column>
        <el-table-column prop="memory_usage" label="内存使用率">
          <template #default="{ row }">
            <el-progress :percentage="row.memory_usage" :color="getProgressColor(row.memory_usage)" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Server, CircleCheck, Cpu, Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { monitoringApi } from '@/api/monitoring'
import { resourceApi } from '@/api/resources'
import { alertApi } from '@/api/alerts'

const dashboardData = ref<any>({})
const resourceStats = ref<any>({})
const alertStats = ref<any>({})
const cpuChartRef = ref<HTMLElement>()
const typeChartRef = ref<HTMLElement>()

const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
}

const initCharts = () => {
  if (!cpuChartRef.value || !typeChartRef.value) return

  // CPU Usage Chart
  const cpuChart = echarts.init(cpuChartRef.value)
  const cpuData = dashboardData.value.top_cpu_resources || []
  cpuChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: cpuData.map((r: any) => r.name)
    },
    yAxis: { type: 'value', max: 100 },
    series: [{
      data: cpuData.map((r: any) => r.cpu_usage),
      type: 'bar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 1, color: '#188df0' }
        ])
      }
    }]
  })

  // Resource Type Chart
  const typeChart = echarts.init(typeChartRef.value)
  const typeData = Object.entries(resourceStats.value.by_type || {}).map(([name, value]) => ({
    name,
    value
  }))
  typeChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: typeData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  })
}

const loadData = async () => {
  try {
    const [dashboardRes, statsRes, alertStatsRes] = await Promise.all([
      monitoringApi.getDashboard(),
      resourceApi.getStats(),
      alertApi.getStats()
    ])
    
    dashboardData.value = dashboardRes.data
    resourceStats.value = statsRes.data
    alertStats.value = alertStatsRes.data
    
    initCharts()
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>
