<template>
  <div class="task-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-page-header @back="handleBack" title="返回">
            <template #content>
              <span class="page-title">审批任务详情</span>
              <el-tag v-if="taskData.status" :type="getStatusTagType(taskData.status)" class="status-tag">
                {{ getStatusLabel(taskData.status) }}
              </el-tag>
            </template>
          </el-page-header>
        </div>
      </template>

      <div class="task-content" v-loading="loading">
        <!-- 任务基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <label>任务标题：</label>
                <span>{{ taskData.title || '无' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>发起人：</label>
                <span>{{ taskData.initiator_name || '未知' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>发起时间：</label>
                <span>{{ formatDate(taskData.created_at) }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>工作流：</label>
                <span>{{ taskData.workflow_name || '未知' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>当前节点：</label>
                <span>{{ taskData.current_node_name || '未知' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>优先级：</label>
                <el-tag :type="getPriorityTagType(taskData.priority)">
                  {{ getPriorityLabel(taskData.priority) }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 审批表单 -->
        <div class="form-section" v-if="taskData.form_data">
          <h3 class="section-title">审批表单</h3>
          <el-form :model="taskData.form_data" label-width="120px" class="task-form">
            <el-form-item v-for="field in taskData.form_fields" :key="field.name" :label="field.label">
              <template v-if="field.type === 'text'">
                <el-input v-model="taskData.form_data[field.name]" :readonly="!field.editable" />
              </template>
              <template v-else-if="field.type === 'textarea'">
                <el-input v-model="taskData.form_data[field.name]" type="textarea" :rows="3" :readonly="!field.editable" />
              </template>
              <template v-else-if="field.type === 'number'">
                <el-input-number v-model="taskData.form_data[field.name]" :readonly="!field.editable" />
              </template>
              <template v-else-if="field.type === 'date'">
                <el-date-picker v-model="taskData.form_data[field.name]" type="date" :readonly="!field.editable" />
              </template>
              <template v-else-if="field.type === 'datetime'">
                <el-date-picker v-model="taskData.form_data[field.name]" type="datetime" :readonly="!field.editable" />
              </template>
            </el-form-item>
          </el-form>
        </div>

        <!-- 审批意见 -->
        <div class="comment-section">
          <h3 class="section-title">审批意见</h3>
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="3"
            placeholder="请输入审批意见（可选）"
            maxlength="500"
            show-word-limit
          />
        </div>

        <!-- 审批操作 -->
        <div class="action-section" v-if="taskData.status === 'PENDING'">
          <h3 class="section-title">审批操作</h3>
          <div class="action-buttons">
            <el-button type="success" @click="handleApprove" :loading="processing">
              <el-icon><CircleCheck /></el-icon> 同意
            </el-button>
            <el-button type="danger" @click="handleReject" :loading="processing">
              <el-icon><Close /></el-icon> 拒绝
            </el-button>
            <el-button type="warning" @click="handleTransfer" :loading="processing">
              <el-icon><Share /></el-icon> 转交
            </el-button>
            <el-button type="info" @click="handleUrge" :loading="processing">
              <el-icon><Bell /></el-icon> 催办
            </el-button>
          </div>
        </div>

        <!-- 审批历史 -->
        <div class="history-section" v-if="taskData.histories && taskData.histories.length > 0">
          <h3 class="section-title">审批历史</h3>
          <el-timeline>
            <el-timeline-item
              v-for="history in taskData.histories"
              :key="history.id"
              :timestamp="formatDateTime(history.created_at)"
              :type="getHistoryType(history.action)"
            >
              <p><strong>{{ history.operator_name }}</strong> {{ getActionLabel(history.action) }}</p>
              <p v-if="history.comment" class="history-comment">{{ history.comment }}</p>
              <p v-if="history.node_name" class="history-node">节点：{{ history.node_name }}</p>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>

    <!-- 转交对话框 -->
    <el-dialog v-model="transferDialogVisible" title="转交任务" width="400px">
      <el-form :model="transferForm" label-width="80px">
        <el-form-item label="转交给">
          <el-select v-model="transferForm.target_user_id" placeholder="请选择转交人" style="width: 100%">
            <el-option v-for="user in userList" :key="user.id" :label="user.name" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="转交说明">
          <el-input v-model="transferForm.reason" type="textarea" :rows="3" placeholder="请输入转交说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmTransfer" :loading="processing">确定转交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CircleCheck, Close, Share, Bell
} from '@element-plus/icons-vue'
import { taskApi } from '@/api/oa/workflows'
import { getUserOptions } from '@/api/system/user'

const router = useRouter()
const route = useRoute()

// 状态
const loading = ref(false)
const processing = ref(false)
const transferDialogVisible = ref(false)

// 数据
const taskData = ref<any>({})
const userList = ref<any[]>([])
const commentText = ref('')

// 转交表单
const transferForm = reactive({
  target_user_id: '',
  reason: ''
})

// 获取任务详情
const loadTaskDetail = async () => {
  loading.value = true
  try {
    const taskId = route.params.id as string
    const res = await taskApi.getById(taskId)
    taskData.value = res.data || {}
  } catch (error) {
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

// 加载用户列表
const loadUserList = async () => {
  try {
    const res = await getUserOptions()
    userList.value = res.data || []
  } catch (error) {
    console.warn('加载用户列表失败')
    userList.value = []
  }
}

// 状态标签类型
const getStatusTagType = (status: string) => {
  const map: Record<string, string> = {
    PENDING: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger',
    CANCELLED: 'info',
    TRANSFERRED: 'info'
  }
  return map[status] || 'info'
}

// 状态标签文本
const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    PENDING: '待审批',
    APPROVED: '已同意',
    REJECTED: '已拒绝',
    CANCELLED: '已取消',
    TRANSFERRED: '已转交'
  }
  return map[status] || status
}

// 优先级标签类型
const getPriorityTagType = (priority: string) => {
  const map: Record<string, string> = {
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'success'
  }
  return map[priority] || 'info'
}

// 优先级标签文本
const getPriorityLabel = (priority: string) => {
  const map: Record<string, string> = {
    HIGH: '高',
    MEDIUM: '中',
    LOW: '低'
  }
  return map[priority] || priority
}

// 审批历史类型
const getHistoryType = (action: string) => {
  const map: Record<string, string> = {
    APPROVE: 'success',
    REJECT: 'danger',
    TRANSFER: 'info'
  }
  return map[action] || 'info'
}

// 审批动作标签
const getActionLabel = (action: string) => {
  const map: Record<string, string> = {
    APPROVE: '同意了该申请',
    REJECT: '拒绝了该申请',
    TRANSFER: '转交了该任务',
    CREATE: '发起了审批申请'
  }
  return map[action] || action
}

// 日期格式化
const formatDate = (date: string) => {
  if (!date) return '未知'
  return new Date(date).toLocaleString('zh-CN')
}

// 日期时间格式化
const formatDateTime = (date: string) => {
  if (!date) return '未知'
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 同意审批
const handleApprove = async () => {
  try {
    await ElMessageBox.confirm('确定同意该申请吗？', '确认审批', {
      type: 'warning'
    })

    processing.value = true
    await taskApi.approve(route.params.id as string, {
      comment: commentText.value
    })
    
    ElMessage.success('审批通过')
    await loadTaskDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('审批失败')
    }
  } finally {
    processing.value = false
  }
}

// 拒绝审批
const handleReject = async () => {
  try {
    await ElMessageBox.confirm('确定拒绝该申请吗？', '确认审批', {
      type: 'warning'
    })

    processing.value = true
    await taskApi.reject(route.params.id as string, {
      comment: commentText.value
    })
    
    ElMessage.success('已拒绝')
    await loadTaskDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    processing.value = false
  }
}

// 转交任务
const handleTransfer = () => {
  transferForm.target_user_id = ''
  transferForm.reason = ''
  transferDialogVisible.value = true
}

// 确认转交
const handleConfirmTransfer = async () => {
  if (!transferForm.target_user_id) {
    ElMessage.warning('请选择转交人')
    return
  }

  try {
    processing.value = true
    await taskApi.transfer(route.params.id as string, {
      target_user_id: transferForm.target_user_id,
      reason: transferForm.reason,
      comment: commentText.value
    })
    
    ElMessage.success('转交成功')
    transferDialogVisible.value = false
    await loadTaskDetail()
  } catch (error) {
    ElMessage.error('转交失败')
  } finally {
    processing.value = false
  }
}

// 催办
const handleUrge = async () => {
  try {
    processing.value = true
    await taskApi.urge(route.params.id as string)
    ElMessage.success('催办成功')
  } catch (error) {
    ElMessage.error('催办失败')
  } finally {
    processing.value = false
  }
}

// 返回
const handleBack = () => {
  router.push('/oa/tasks')
}

// 组件挂载时加载数据
onMounted(() => {
  loadTaskDetail()
  loadUserList()
})
</script>

<style scoped>
.task-detail {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin-left: 16px;
}

.status-tag {
  margin-left: 12px;
}

.task-content {
  min-height: 400px;
}

.section-title {
  margin: 24px 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 12px;
}

.info-section {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
}

.info-item {
  margin-bottom: 12px;
}

.info-item label {
  color: #606266;
  font-weight: 500;
  margin-right: 8px;
}

.info-item span {
  color: #303133;
}

.task-form {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.comment-section {
  margin: 24px 0;
}

.action-section {
  margin: 24px 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.history-section {
  margin-top: 32px;
}

.history-comment {
  color: #606266;
  font-style: italic;
  margin-top: 4px;
}

.history-node {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}
</style>