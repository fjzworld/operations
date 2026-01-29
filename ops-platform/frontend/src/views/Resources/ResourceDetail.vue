<template>
  <div class="resource-detail page-container">
    <div class="glass-panel">
      <div class="panel-header">
        <h2 class="panel-title">{{ resource?.name }} - 性能监控</h2>
        <el-button @click="$router.back()" class="glass-button">返回</el-button>
      </div>

      <!-- Real-time Stats -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="label">CPU 使用率</span>
          <span class="value" :class="{ danger: resource?.cpu_usage > 80 }">
            {{ resource?.cpu_usage?.toFixed(1) }}%
          </span>
        </div>
        <div class="stat-card">
          <span class="label">内存使用率</span>
          <span class="value" :class="{ danger: resource?.memory_usage > 80 }">
            {{ resource?.memory_usage?.toFixed(1) }}%
          </span>
        </div>
        <div class="stat-card">
          <span class="label">磁盘使用率</span>
          <span class="value" :class="{ danger: resource?.disk_usage > 85 }">
            {{ resource?.disk_usage?.toFixed(1) }}%
          </span>
        </div>
      </div>

      <!-- Historical Charts -->
      <div class="charts-section">
        <h3 class="section-title">历史趋势 (最近24小时)</h3>
        <div ref="trendChartRef" class="trend-chart"></div>
      </div>

      <!-- Top Processes -->
      <div class="processes-section">
        <h3 class="section-title">Top 进程</h3>
        <el-table 
          :data="topProcesses" 
          class="transparent-table"
          :header-cell-style="{ background: 'transparent', color: '#94A3B8' }"
          :cell-style="{ background: 'transparent', color: '#F8FAFC' }"
        >
          <el-table-column prop="name" label="进程名称" />
          <el-table-column prop="pid" label="PID" width="100" />
          <el-table-column label="CPU %">
            <template #default="{ row }">
              <el-progress :percentage="Math.min(row.cpu_percent, 100)" :stroke-width="6" />
            </template>
          </el-table-column>
          <el-table-column label="内存 %">
            <template #default="{ row }">
              <el-progress :percentage="Math.min(row.memory_percent, 100)" :stroke-width="6" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { resourceApi } from '@/api/resources'

const route = useRoute()
const resourceId = parseInt(route.params.id as string)

const resource = ref<any>(null)
const topProcesses = ref<any[]>([])
const trendChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let refreshTimer: any = null

const loadResource = async () => {
  try {
    const { data } = await resourceApi.get(resourceId)
    resource.value = data
  } catch (error) {
    console.error('Failed to load resource:', error)
  }
}

const loadHistory = async () => {
  try {
    const { data } = await resourceApi.getHistory(resourceId, 24)
    renderTrendChart(data.metrics)
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

const loadProcesses = async () => {
  try {
    const { data } = await resourceApi.getProcesses(resourceId)
    topProcesses.value = data.processes
  } catch (error) {
    console.error('Failed to load processes:', error)
  }
}

const renderTrendChart = (metrics: any[]) => {
  if (!trendChartRef.value) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const timestamps = metrics.map(m => new Date(m.timestamp).toLocaleTimeString())
  const cpuData = metrics.map(m => m.cpu_usage)
  const memData = metrics.map(m => m.memory_usage)
  const diskData = metrics.map(m => m.disk_usage)

  trendChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: { color: '#F8FAFC' }
    },
    legend: {
      data: ['CPU', '内存', '磁盘'],
      textStyle: { color: '#94A3B8' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timestamps,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#64748B' }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
      axisLabel: { color: '#64748B', formatter: '{value}%' }
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        smooth: true,
        data: cpuData,
        itemStyle: { color: '#38bdf8' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(56, 189, 248, 0.3)' },
            { offset: 1, color: 'rgba(56, 189, 248, 0.05)' }
          ])
        }
      },
      {
        name: '内存',
        type: 'line',
        smooth: true,
        data: memData,
        itemStyle: { color: '#a855f7' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(168, 85, 247, 0.3)' },
            { offset: 1, color: 'rgba(168, 85, 247, 0.05)' }
          ])
        }
      },
      {
        name: '磁盘',
        type: 'line',
        smooth: true,
        data: diskData,
        itemStyle: { color: '#eab308' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(234, 179, 8, 0.3)' },
            { offset: 1, color: 'rgba(234, 179, 8, 0.05)' }
          ])
        }
      }
    ]
  })
}

const refreshData = () => {
  loadResource()
  loadHistory()
  loadProcesses()
}

onMounted(() => {
  refreshData()
  refreshTimer = setInterval(refreshData, 30000) // Refresh every 30s
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (trendChart) trendChart.dispose()
})
</script>

<style scoped>
.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

.glass-panel {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 30px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.panel-title {
  font-size: 24px;
  color: #fff;
  margin: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(30, 41, 59, 0.4);
  padding: 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.label {
  font-size: 14px;
  color: #94A3B8;
  text-transform: uppercase;
}

.value {
  font-family: 'Fira Code', monospace;
  font-size: 36px;
  font-weight: 600;
  color: #22C55E;
}

.value.danger {
  color: #EF4444;
}

.charts-section, .processes-section {
  margin-top: 40px;
}

.section-title {
  font-size: 18px;
  color: #fff;
  margin-bottom: 20px;
}

.trend-chart {
  height: 400px;
  width: 100%;
}

.transparent-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(30, 41, 59, 0.5);
}
</style>
