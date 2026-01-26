<template>
  <div class="alert-rules">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>告警规则</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            添加规则
          </el-button>
        </div>
      </template>

      <el-table :data="rules" stripe v-loading="loading">
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="metric" label="监控指标" />
        <el-table-column label="条件">
          <template #default="{ row }">
            {{ row.condition }} {{ row.threshold }}
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度">
          <template #default="{ row }">
            <el-tag :type="severityTypes[row.severity]">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showCreateDialog" title="告警规则" width="600px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" />
        </el-form-item>
        <el-form-item label="监控指标" required>
          <el-select v-model="ruleForm.metric" style="width: 100%">
            <el-option label="CPU 使用率" value="cpu_usage" />
            <el-option label="内存使用率" value="memory_usage" />
            <el-option label="磁盘使用率" value="disk_usage" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件" required>
          <el-select v-model="ruleForm.condition" style="width: 100%">
            <el-option label="大于" value=">" />
            <el-option label="小于" value="<" />
            <el-option label="大于等于" value=">=" />
            <el-option label="小于等于" value="<=" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值" required>
          <el-input-number v-model="ruleForm.threshold" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="严重程度" required>
          <el-select v-model="ruleForm.severity" style="width: 100%">
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="ruleForm.description" type="textarea" />
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
import { alertApi } from '@/api/alerts'

const loading = ref(false)
const rules = ref<any[]>([])
const showCreateDialog = ref(false)
const editingRule = ref<any>(null)

const ruleForm = reactive({
  name: '',
  metric: 'cpu_usage',
  condition: '>',
  threshold: 80,
  severity: 'warning',
  description: '',
  notification_channels: []
})

const severityTypes: Record<string, any> = {
  critical: 'danger',
  warning: 'warning',
  info: 'info'
}

const loadRules = async () => {
  loading.value = true
  try {
    const { data } = await alertApi.listRules()
    rules.value = data
  } catch (error) {
    ElMessage.error('加载规则列表失败')
  } finally {
    loading.value = false
  }
}

const handleToggle = async (row: any) => {
  try {
    await alertApi.updateRule(row.id, { enabled: row.enabled })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    row.enabled = !row.enabled
  }
}

const handleEdit = (row: any) => {
  editingRule.value = row
  Object.assign(ruleForm, row)
  showCreateDialog.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此规则吗?', '提示', { type: 'warning' })
    await alertApi.deleteRule(row.id)
    ElMessage.success('删除成功')
    loadRules()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSave = async () => {
  try {
    if (editingRule.value) {
      await alertApi.updateRule(editingRule.value.id, ruleForm)
      ElMessage.success('更新成功')
    } else {
      await alertApi.createRule(ruleForm)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    editingRule.value = null
    loadRules()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.alert-rules {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
