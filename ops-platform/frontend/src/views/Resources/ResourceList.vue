<template>
  <div class="resource-list page-container">
    <div class="glass-panel">
      <div class="panel-header">
        <div class="header-left">
          <h2 class="panel-title">资源管理</h2>
          <span class="panel-subtitle">全网资产实时监控与调度</span>
        </div>
        <el-button type="primary" class="glow-button" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          接入资源
        </el-button>
      </div>

      <!-- Filters -->
      <div class="filter-bar">
        <el-select v-model="filters.type" placeholder="资源类型" clearable class="glass-input">
          <el-option label="物理机" value="physical" />
          <el-option label="虚拟机" value="virtual" />
          <el-option label="容器" value="container" />
          <el-option label="云主机" value="cloud" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable class="glass-input">
          <el-option label="活跃" value="active" />
          <el-option label="非活跃" value="inactive" />
          <el-option label="维护中" value="maintenance" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-button type="primary" plain @click="loadResources" class="glass-button">
          <el-icon><Search /></el-icon> 查询
        </el-button>
      </div>

      <!-- Table -->
      <el-table 
        :data="resources" 
        style="width: 100%" 
        v-loading="loading"
        class="transparent-table"
        :header-cell-style="{ background: 'transparent', color: '#94A3B8', borderBottom: '1px solid rgba(255,255,255,0.05)' }"
        :cell-style="{ background: 'transparent', color: '#F8FAFC', borderBottom: '1px solid rgba(255,255,255,0.05)' }"
      >
        <el-table-column prop="name" label="资源名称">
          <template #default="{ row }">
            <span class="resource-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag effect="dark" :type="getTypeTagEffect(row.type)" class="glass-tag">{{ typeLabels[row.type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <div class="status-indicator">
              <span class="dot" :class="row.status"></span>
              {{ statusLabels[row.status] }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="CPU 负载" width="200">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.cpu_usage" 
              :color="getProgressColor(row.cpu_usage)"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/resources/${row.id}`)">详情</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, prev, pager, next"
          @size-change="loadResources"
          @current-change="loadResources"
          background
        />
      </div>
    </div>

    <!-- Create/Edit Dialog (Smart Add) -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingResource ? '编辑资源配置' : '一键接入新资源'"
      width="600px"
      class="glass-dialog"
    >
      <el-form :model="resourceForm" label-width="120px" class="glass-form" style="margin-top: 20px">
        <el-alert
          v-if="!editingResource"
          title="智能接入模式"
          type="info"
          description="只需输入 IP 和 SSH 密码，系统将自动探测硬件配置并部署监控 Agent。"
          show-icon
          :closable="false"
          style="margin-bottom: 20px"
        />

        <el-form-item label="资源名称" required>
          <el-input v-model="resourceForm.name" placeholder="自定义名称（如：Web Server 01）" />
        </el-form-item>
        
        <el-form-item label="资源类型">
          <el-radio-group v-model="resourceForm.type">
            <el-radio-button label="physical">物理机</el-radio-button>
            <el-radio-button label="virtual">虚拟机</el-radio-button>
            <el-radio-button label="cloud">云主机</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="IP 地址" required>
           <el-input v-model="resourceForm.ip_address" placeholder="例如: 192.168.1.100" />
        </el-form-item>

        <!-- SSH Credentials Section -->
        <div v-if="!editingResource" class="ssh-section">
          <div class="section-title">SSH 凭证 (用于自动探测和 Agent 部署)</div>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="SSH 端口">
                <el-input-number v-model="resourceForm.ssh_port" :min="1" :max="65535" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="用户名">
                <el-input v-model="resourceForm.ssh_username" placeholder="root" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="认证方式">
            <el-radio-group v-model="authMethod">
              <el-radio-button label="password">密码</el-radio-button>
              <el-radio-button label="key">私钥</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="authMethod === 'password'" label="SSH 密码" required>
            <el-input v-model="resourceForm.ssh_password" type="password" show-password placeholder="输入密码以自动接入" />
          </el-form-item>
          
          <el-form-item v-else label="私钥路径">
            <el-input v-model="resourceForm.ssh_private_key" placeholder="/root/.ssh/id_rsa" />
          </el-form-item>
        </div>

        <el-form-item label="备注">
          <el-input v-model="resourceForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <div class="dialog-actions">
        <el-button @click="showCreateDialog = false" class="glass-button">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving" class="glow-button">
          {{ editingResource ? '保存修改' : '开始接入' }}
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { resourceApi } from '@/api/resources'

const loading = ref(false)
const saving = ref(false)
const resources = ref<any[]>([])
const showCreateDialog = ref(false)
const editingResource = ref<any>(null)
const authMethod = ref('password')

const filters = reactive({ type: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const resourceForm = reactive({
  name: '',
  type: 'physical',
  ip_address: '',
  ssh_port: 22,
  ssh_username: 'root',
  ssh_password: '',
  ssh_private_key: '',
  cpu_cores: 1,
  memory_gb: 0,
  disk_gb: 0,
  os_type: '',
  description: ''
})

const typeLabels: Record<string, string> = {
  physical: '物理机', virtual: '虚拟机', container: '容器', cloud: '云主机'
}

const statusLabels: Record<string, string> = {
  active: '活跃', inactive: '休眠', maintenance: '维护', offline: '离线'
}

const getTypeTagEffect = (type: string) => {
  return type === 'physical' ? 'danger' : type === 'cloud' ? 'success' : ''
}

const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#22C55E'
  if (percentage < 80) return '#EAB308'
  return '#EF4444'
}

const loadResources = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      ...(filters.type && { resource_type: filters.type }),
      ...(filters.status && { status: filters.status })
    }
    const { data } = await resourceApi.list(params)
    resources.value = data
    pagination.total = data.length
  } catch (error) {
    ElMessage.error('数据加载异常')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  resourceForm.name = ''
  resourceForm.type = 'physical'
  resourceForm.ip_address = ''
  resourceForm.ssh_port = 22
  resourceForm.ssh_username = 'root'
  resourceForm.ssh_password = ''
  resourceForm.ssh_private_key = ''
  resourceForm.cpu_cores = 1
  resourceForm.memory_gb = 0
  resourceForm.disk_gb = 0
  resourceForm.os_type = ''
  resourceForm.description = ''
  authMethod.value = 'password'
}

const openCreateDialog = () => {
  editingResource.value = null
  resetForm()
  showCreateDialog.value = true
}

const handleEdit = (row: any) => {
  editingResource.value = row
  Object.assign(resourceForm, row)
  showCreateDialog.value = true
}

const handleDelete = async (row: any) => {
  try {
    // 第一步：确认是否删除
    await ElMessageBox.confirm(
      '确认下线该资源节点？此操作不可逆。',
      '高危操作警告',
      {
        confirmButtonText: '确认下线',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 第二步：询问是否卸载 Agent
    const uninstallAgent = await ElMessageBox.confirm(
      '是否同时从服务器卸载监控 Agent？\n（需要提供 SSH 凭证）',
      '卸载 Agent',
      {
        confirmButtonText: '是，卸载 Agent',
        cancelButtonText: '否，仅删除记录',
        type: 'info',
        distinguishCancelAndClose: true
      }
    ).then(() => true).catch((action: string) => {
      if (action === 'cancel') return false
      throw 'close'
    })
    
    let deletePayload: any = null
    
    // 如果需要卸载 Agent，获取 SSH 凭证
    if (uninstallAgent) {
      const credentials = await ElMessageBox.prompt(
        `请输入 ${row.ip_address} 的 SSH 密码（用户: root）`,
        'SSH 认证',
        {
          confirmButtonText: '确认',
          cancelButtonText: '跳过卸载',
          inputType: 'password',
          inputPlaceholder: 'SSH 密码'
        }
      ).catch(() => null)
      
      if (credentials && credentials.value) {
        deletePayload = {
          uninstall_agent: true,
          ssh_port: 22,
          ssh_username: 'root',
          ssh_password: credentials.value
        }
      }
    }
    
    // 执行删除
    const { data } = await resourceApi.delete(row.id, deletePayload)
    
    if (data.agent_uninstalled) {
      ElMessage.success('资源已下线，Agent 已卸载')
    } else if (data.warning) {
      ElMessage.warning(data.warning)
    } else {
      ElMessage.success('资源已下线')
    }
    
    loadResources()
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('操作失败')
    }
  }
}

const handleSave = async () => {
  if (!resourceForm.name || !resourceForm.ip_address) {
    ElMessage.warning('请填写名称和 IP 地址')
    return
  }
  
  if (!editingResource.value && !resourceForm.ssh_password && !resourceForm.ssh_private_key) {
    ElMessage.warning('请输入 SSH 密码或私钥以进行自动接入')
    return
  }

  saving.value = true
  try {
    if (editingResource.value) {
      await resourceApi.update(editingResource.value.id, resourceForm)
      ElMessage.success('配置已更新')
    } else {
      // 自动获取当前 API 地址传给后端
      const currentApiUrl = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.host}/api/v1`
      const payload = {
        ...resourceForm,
        backend_url: currentApiUrl
      }
      
      ElMessage.info('正在连接服务器并部署 Agent，请稍候...')
      await resourceApi.create(payload)
      ElMessage.success('资源接入成功！Agent 已自动部署。')
    }
    
    showCreateDialog.value = false
    editingResource.value = null
    loadResources()
  } catch (error: any) {
    console.error(error)
    const msg = error.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

onMounted(() => loadResources())
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.glass-panel {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.panel-title {
  margin: 0;
  font-size: 24px;
  color: #F8FAFC;
  font-weight: 600;
}

.panel-subtitle {
  color: #64748B;
  font-size: 13px;
  margin-top: 4px;
  display: block;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.glass-input :deep(.el-input__wrapper) {
  background-color: rgba(2, 6, 23, 0.3);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.glow-button {
  background: #22C55E;
  border: none;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
  transition: all 0.3s;
}

.glow-button:hover {
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
  transform: translateY(-1px);
}

.resource-name {
  font-family: 'Fira Code', monospace;
  font-weight: 500;
  color: #38bdf8;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748B;
}

.dot.active { background: #22C55E; box-shadow: 0 0 8px #22C55E; }
.dot.maintenance { background: #EAB308; }
.dot.offline { background: #EF4444; }

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.transparent-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(30, 41, 59, 0.5);
  --el-table-border-color: transparent;
}

/* Dialog Styles */
.dialog-actions {
  margin-top: 30px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ssh-section {
  background: rgba(30, 41, 59, 0.3);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px dashed rgba(255, 255, 255, 0.1);
}

.section-title {
  font-size: 13px;
  color: #94A3B8;
  margin-bottom: 16px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background-color: rgba(2, 6, 23, 0.3) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

:deep(.el-input__wrapper:focus), :deep(.el-textarea__inner:focus) {
  border-color: #38bdf8 !important;
}
</style>