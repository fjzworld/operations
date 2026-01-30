<template>
  <div class="dashboard-container">
    <!-- Header Stats Row -->
    <div class="stats-grid">
      <!-- Total Resources -->
      <div class="hud-card glass-panel" @click="handleCardClick">
        <div class="card-glow"></div>
        <div class="stat-content">
          <div class="icon-wrapper blue">
            <el-icon :size="24"><Box /></el-icon>
          </div>
          <div class="stat-text">
            <span class="label">资源状态</span>
            <div class="value-group">
              <span class="value">{{ dashboardData.online_resources || 0 }}</span>
              <span class="unit">/ {{ dashboardData.total_resources || 0 }} ONLINE</span>
            </div>
          </div>
        </div>
        <el-progress 
          :percentage="dashboardData.total_resources ? (dashboardData.online_resources / dashboardData.total_resources) * 100 : 0" 
          :show-text="false" 
          :stroke-width="4"
          color="#38bdf8"
          class="mini-progress"
        />
      </div>

      <!-- CPU Usage -->
      <div class="hud-card glass-panel">
        <div class="stat-content">
          <div class="icon-wrapper green">
            <el-icon :size="24"><Cpu /></el-icon>
          </div>
          <div class="stat-text">
            <span class="label">平均负载 (CPU)</span>
            <div class="value-group">
              <span class="value">{{ dashboardData.average_cpu_usage?.toFixed(1) || 0 }}</span>
              <span class="unit">%</span>
            </div>
          </div>
        </div>
        <el-progress 
          :percentage="dashboardData.average_cpu_usage || 0" 
          :show-text="false" 
          :stroke-width="4"
          color="#22C55E"
          class="mini-progress"
        />
      </div>

      <!-- Network Traffic -->
      <div class="hud-card glass-panel">
        <div class="stat-content">
          <div class="icon-wrapper orange">
            <el-icon :size="24"><Connection /></el-icon>
          </div>
          <div class="stat-text">
            <span class="label">实时流量</span>
            <div class="value-group">
              <span class="value">{{ dashboardData.total_network_traffic?.toFixed(1) || 0 }}</span>
              <span class="unit">MB/s</span>
            </div>
          </div>
        </div>
        <div class="trend-line orange-trend"></div>
      </div>

      <!-- Alerts (Placeholder) -->
      <div class="hud-card glass-panel alert-mode">
        <div class="stat-content">
          <div class="icon-wrapper red">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <div class="stat-text">
            <span class="label">系统状态</span>
            <div class="value-group">
              <span class="value success">NORMAL</span>
            </div>
          </div>
        </div>
        <div class="pulse-dot green-pulse"></div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <!-- CPU Trend (Left) -->
      <div class="hud-panel glass-panel large">
        <div class="panel-header">
          <h3 class="panel-title">
            <el-icon><TrendCharts /></el-icon> 负载 Top 5
          </h3>
          <div class="panel-actions">
            <span class="live-tag">LIVE</span>
          </div>
        </div>
        <div ref="cpuChartRef" class="chart-container"></div>
      </div>

      <!-- Hex Grid (Right) -->
      <div class="hud-panel glass-panel large">
        <div class="panel-header">
          <h3 class="panel-title">
            <el-icon><PieChart /></el-icon> 集群健康矩阵
          </h3>
        </div>
        <div class="hex-container">
          <HexGrid :nodes="dashboardData.all_resources_status || []" />
        </div>
      </div>
    </div>

    <!-- Table Row -->
    <div class="hud-panel glass-panel table-section">
      <div class="panel-header">
        <h3 class="panel-title">
          <el-icon><List /></el-icon> 资源性能排行
        </h3>
      </div>
      <el-table 
        :data="dashboardData.top_cpu_resources || []" 
        style="width: 100%" 
        class="transparent-table"
        :header-cell-style="{ background: 'transparent', color: '#94A3B8', borderBottom: '1px solid #1E293B' }"
        :cell-style="{ background: 'transparent', color: '#F8FAFC', borderBottom: '1px solid #1E293B' }"
      >
        <el-table-column prop="name" label="资源名称" width="220" />
        <el-table-column prop="cpu_usage" label="CPU 使用率">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress 
                :percentage="row.cpu_usage" 
                :color="getProgressColor(row.cpu_usage)"
                :stroke-width="8"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="memory_usage" label="内存使用率">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress 
                :percentage="row.memory_usage" 
                :color="getProgressColor(row.memory_usage)"
                :stroke-width="8"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Box, Connection, Cpu, Warning, TrendCharts, PieChart, List } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { monitoringApi } from '@/api/monitoring'
import { resourceApi } from '@/api/resources'
import HexGrid from '@/components/HexGrid.vue'

// --- State ---
const dashboardData = ref<any>({})
const resourceStats = ref<any>({})
const alertStats = ref<any>({})
const cpuChartRef = ref<HTMLElement>()

let cpuChart: echarts.ECharts | null = null

// --- Helpers ---
const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#22C55E'
  if (percentage < 80) return '#EAB308'
  return '#EF4444'
}

const handleCardClick = () => {
  // Add interactive logic here if needed
}

// --- Charts ---
const initCharts = () => {
  if (!cpuChartRef.value) return

  // 1. CPU Bar Chart (Cyberpunk Style)
  cpuChart = echarts.init(cpuChartRef.value)
  const cpuData = dashboardData.value.top_cpu_resources || []
  
  cpuChart.setOption({
    grid: { top: 30, right: 20, bottom: 20, left: 40, containLabel: true },
    tooltip: { 
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: { color: '#F8FAFC' }
    },
    xAxis: {
      type: 'category',
      data: cpuData.map((r: any) => r.name),
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94A3B8' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
      axisLabel: { color: '#64748B' }
    },
    series: [{
      data: cpuData.map((r: any) => r.cpu_usage),
      type: 'bar',
      barWidth: '30%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#38bdf8' },
          { offset: 1, color: 'rgba(56, 189, 248, 0.1)' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: '#38bdf8',
          shadowBlur: 10,
          shadowColor: 'rgba(56, 189, 248, 0.5)'
        }
      }
    }]
  })
}

const loadData = async () => {
  try {
    const [dashboardRes, statsRes] = await Promise.all([
      monitoringApi.getDashboard(),
      resourceApi.getStats(),
    ])
    
    dashboardData.value = dashboardRes.data
    resourceStats.value = statsRes.data
    
    initCharts()
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

// --- Lifecycle ---
const resizeHandler = () => {
  cpuChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  cpuChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* --- HUD Cards --- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.hud-card {
  position: relative;
  height: 120px;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.hud-card:hover {
  transform: translateY(-4px);
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.stat-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  z-index: 2;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Glass effect icons */
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.icon-wrapper.blue { color: #38bdf8; background: rgba(56, 189, 248, 0.1); }
.icon-wrapper.green { color: #22c55e; background: rgba(34, 197, 94, 0.1); }
.icon-wrapper.orange { color: #eab308; background: rgba(234, 179, 8, 0.1); }
.icon-wrapper.red { color: #ef4444; background: rgba(239, 68, 68, 0.1); }

.stat-text {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 13px;
  color: #94A3B8;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value-group {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.value {
  font-family: 'Fira Code', monospace;
  font-size: 28px;
  font-weight: 600;
  color: #F8FAFC;
  line-height: 1.2;
}

.value.danger { color: #EF4444; text-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }
.value.success { color: #22C55E; text-shadow: 0 0 10px rgba(34, 197, 94, 0.4); }

.unit {
  font-size: 12px;
  color: #64748B;
  font-weight: 600;
}

/* Mini Progress */
.mini-progress {
  margin-top: 12px;
}

/* --- Panels --- */
.glass-panel {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.hud-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.hex-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
  min-height: 300px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #F8FAFC;
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-tag {
  font-size: 10px;
  background: rgba(34, 197, 94, 0.2);
  color: #22C55E;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(34, 197, 94, 0.3);
  animation: pulse 2s infinite;
}

.chart-container {
  height: 300px;
  width: 100%;
}

/* --- Table --- */
.transparent-table {
  --el-table-border-color: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(30, 41, 59, 0.5);
}

.progress-cell {
  padding-right: 20px;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}
</style>
