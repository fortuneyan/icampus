<template>
  <div class="instance-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-page-header @back="handleBack" title="返回">
            <template #content>
              <span class="page-title">审批实例详情</span>
              <el-tag v-if="instanceData.status" :type="getStatusTagType(instanceData.status)" class="status-tag">
                {{ getStatusLabel(instanceData.status) }}
              </el-tag>
              <el-tag v-if="instanceData.is_overdue" type="danger" class="status-tag">
                已超时
              </el-tag>
            </template>
          </el-page-header>
          <div class="header-actions">
            <el-button
              v-if="['PENDING','APPROVING'].includes(instanceData.status)"
              @click="handleUrge"
              type="primary"
              plain
              :disabled="urgeDisabled"
            >
              <el-icon><Bell /></el-icon>
              {{ urgeButtonText }}
            </el-button>
            <el-button
              v-if="['PENDING','APPROVING'].includes(instanceData.status) && instanceData.can_withdraw"
              @click="handleWithdraw"
              type="warning"
            >
              <el-icon><Back /></el-icon> 撤回
            </el-button>
            <el-button @click="handlePrint" type="info">
              <el-icon><Printer /></el-icon> 打印
            </el-button>
            <el-button @click="showStatistics = !showStatistics" type="success" plain>
              <el-icon><DataAnalysis /></el-icon> 统计
            </el-button>
          </div>
        </div>
      </template>

      <div class="instance-content" v-loading="loading">

        <!-- 超时警告 -->
        <el-alert
          v-if="instanceData.is_overdue"
          title="该申请已超时，请及时审批"
          type="error"
          :closable="false"
          show-icon
          class="timeout-alert"
        />

        <!-- 实例基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <label>实例编号：</label>
                <span>{{ instanceData.instance_id || '无' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>工作流：</label>
                <span>{{ instanceData.workflow_name || '未知' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>发起人：</label>
                <span>{{ instanceData.initiator_name || '未知' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>发起时间：</label>
                <span>{{ formatDateTime(instanceData.created_at) }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>当前节点：</label>
                <span>{{ instanceData.current_node_name || '未知' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>完成时间：</label>
                <span>{{ formatDateTime(instanceData.completed_at) || '进行中' }}</span>
              </div>
            </el-col>
            <el-col :span="8" v-if="instanceData.urge_count">
              <div class="info-item">
                <label>催办次数：</label>
                <span>{{ instanceData.urge_count }} 次</span>
              </div>
            </el-col>
            <el-col :span="8" v-if="instanceData.last_urge_at">
              <div class="info-item">
                <label>最后催办：</label>
                <span>{{ formatDateTime(instanceData.last_urge_at) }}</span>
              </div>
            </el-col>
            <el-col :span="24">
              <div class="info-item">
                <label>申请标题：</label>
                <span class="title-text">{{ instanceData.title || '无标题' }}</span>
              </div>
            </el-col>
            <el-col :span="24">
              <div class="info-item">
                <label>申请说明：</label>
                <span class="description-text">{{ instanceData.description || '无说明' }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 统计面板（可折叠） -->
        <div v-if="showStatistics" class="statistics-section">
          <h3 class="section-title">审批统计</h3>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-value">{{ statistics.summary?.total || 0 }}</div>
                <div class="stat-label">总申请数</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-approved">
                <div class="stat-value">{{ statistics.summary?.approved || 0 }}</div>
                <div class="stat-label">已通过</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-rejected">
                <div class="stat-value">{{ statistics.summary?.rejected || 0 }}</div>
                <div class="stat-label">已拒绝</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover" class="stat-card stat-rate">
                <div class="stat-value">{{ ((statistics.summary?.approve_rate || 0) * 100).toFixed(1) }}%</div>
                <div class="stat-label">通过率</div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 16px;">
            <el-col :span="8">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-value">{{ statistics.summary?.in_progress || 0 }}</div>
                <div class="stat-label">进行中</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-value">{{ statistics.summary?.cancelled || 0 }}</div>
                <div class="stat-label">已撤回</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-value">{{ (statistics.summary?.avg_duration_hours || 0).toFixed(1) }}h</div>
                <div class="stat-label">平均审批时长</div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 审批时间线（使用ApprovalTimeline组件） -->
        <div class="timeline-section">
          <h3 class="section-title">审批时间线</h3>
          <ApprovalTimeline
            :instance="instanceData"
            :nodes="instanceData.nodes"
            :histories="instanceData.histories"
          />
        </div>

        <!-- 节点条件表达式（可视化） -->
        <div v-if="hasConditionNodes" class="condition-section">
          <h3 class="section-title">条件节点配置</h3>
          <el-card>
            <el-descriptions :column="1" border>
              <el-descriptions-item
                v-for="node in conditionNodes"
                :key="node.id"
                :label="node.name"
              >
                <el-tag v-if="node.condition_expression" type="warning">
                  {{ formatCondition(node.condition_expression) }}
                </el-tag>
                <span v-else class="text-muted">无配置条件</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>

        <!-- 表单数据 -->
        <div class="form-section" v-if="instanceData.form_data">
          <h3 class="section-title">表单数据</h3>
          <el-card>
            <el-form :model="instanceData.form_data" label-width="120px" class="instance-form">
              <el-row :gutter="20">
                <el-col :span="12" v-for="field in instanceData.form_fields" :key="field.name">
                  <el-form-item :label="field.label">
                    <template v-if="field.type === 'text' || field.type === 'textarea'">
                      <span>{{ instanceData.form_data[field.name] || '无' }}</span>
                    </template>
                    <template v-else-if="field.type === 'number'">
                      <span>{{ instanceData.form_data[field.name] || '0' }}</span>
                    </template>
                    <template v-else-if="field.type === 'date'">
                      <span>{{ formatDate(instanceData.form_data[field.name]) || '无' }}</span>
                    </template>
                    <template v-else-if="field.type === 'datetime'">
                      <span>{{ formatDateTime(instanceData.form_data[field.name]) || '无' }}</span>
                    </template>
                    <template v-else-if="field.type === 'file'">
                      <el-link
                        v-if="instanceData.form_data[field.name]"
                        :href="instanceData.form_data[field.name]"
                        target="_blank"
                      >
                        下载附件
                      </el-link>
                      <span v-else>无附件</span>
                    </template>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>
        </div>

        <!-- 附件列表 -->
        <div class="attachment-section" v-if="instanceData.attachments && instanceData.attachments.length > 0">
          <h3 class="section-title">附件列表</h3>
          <el-table :data="instanceData.attachments" border>
            <el-table-column label="文件名" prop="filename" />
            <el-table-column label="大小" prop="size" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column label="上传时间" prop="uploaded_at" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.uploaded_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleDownload(row)">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Back, Printer, Bell, DataAnalysis, Document
} from '@element-plus/icons-vue'
import { instanceApi } from '@/api/oa/workflows'
import { formatConditionExpression } from '@/api/oa/workflows'  // 导入条件表达式格式化函数
import ApprovalTimeline from '@/components/ApprovalTimeline.vue'
import type { WorkflowInstance } from '@/types/workflow'

const router = useRouter()
const route = useRoute()

// ============================================================
// 状态
// ============================================================

const loading = ref(false)
const showStatistics = ref(false)
const statistics = ref<any>({})
const urgeDisabled = ref(false)
const urgeButtonText = ref('催办')

// 数据
const instanceData = ref<Partial<WorkflowInstance>>({})

// ============================================================
// 计算属性
// ============================================================

/** 是否有条件节点 */
const hasConditionNodes = computed(() => {
  return conditionNodes.value.length > 0
})

/** 条件节点列表 */
const conditionNodes = computed(() => {
  return (instanceData.value.nodes || []).filter(n => n.node_type === 'CONDITION')
})

// ============================================================
// 数据加载
// ============================================================

/** 获取实例详情 */
const loadInstanceDetail = async () => {
  loading.value = true
  try {
    const instanceId = route.params.id as string
    const res = await instanceApi.getById(instanceId)
    instanceData.value = res.data || {}
  } catch (error) {
    ElMessage.error('加载实例详情失败')
  } finally {
    loading.value = false
  }
}

/** 获取统计数据 */
const loadStatistics = async () => {
  try {
    const res = await instanceApi.getStatistics({
      business_type: instanceData.value.business_type || undefined,
    })
    statistics.value = res.data || {}
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

// ============================================================
// 操作处理
// ============================================================

/** 催办 */
const handleUrge = async () => {
  try {
    await ElMessageBox.confirm('确定要催办该申请吗？催办后会通知当前审批人。', '确认催办', {
      type: 'warning'
    })

    const res = await instanceApi.urge(route.params.id as string, {
      message: '请尽快处理该审批申请'
    })

    ElMessage.success(`催办成功，已通知 ${res.data?.notified_users || 0} 人`)
    urgeDisabled.value = true
    urgeButtonText.value = `已催办(${res.data?.urge_count || 1})`

    await loadInstanceDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('催办失败')
    }
  }
}

/** 撤回实例 */
const handleWithdraw = async () => {
  try {
    await ElMessageBox.confirm('确定要撤回该申请吗？撤回后将无法恢复。', '确认撤回', {
      type: 'warning'
    })

    await instanceApi.withdraw(route.params.id as string)
    ElMessage.success('撤回成功')
    await loadInstanceDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('撤回失败')
    }
  }
}

/** 查看任务 */
const handleViewTask = (task: any) => {
  router.push(`/oa/tasks/${task.id}`)
}

/** 下载附件 */
const handleDownload = (attachment: any) => {
  window.open(attachment.url, '_blank')
}

/** 打印 */
const handlePrint = () => {
  window.print()
}

/** 返回 */
const handleBack = () => {
  router.push('/oa/workflows/instances')
}

// ============================================================
// 工具函数
// ============================================================

/** 状态标签类型 */
const getStatusTagType = (status: string) => {
  const map: Record<string, string> = {
    PENDING:   'warning',
    APPROVING: 'warning',
    APPROVED:  'success',
    REJECTED:  'danger',
    CANCELLED: 'info',
    EXPIRED:   'danger',
  }
  return map[status] || 'info'
}

/** 状态标签文本 */
const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    PENDING:   '待审批',
    APPROVING: '审批中',
    APPROVED:  '已通过',
    REJECTED:  '已拒绝',
    CANCELLED: '已撤回',
    EXPIRED:   '已超时',
  }
  return map[status] || status
}

/** 格式化条件表达式 */
const formatCondition = (expression: any): string => {
  return formatConditionExpression(expression)
}

/** 日期格式化 */
const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

/** 日期时间格式化 */
const formatDateTime = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/** 文件大小格式化 */
const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// ============================================================
// 生命周期
// ============================================================

onMounted(() => {
  loadInstanceDetail()
})
</script>

<style scoped>
.instance-detail {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin-left: 16px;
}

.status-tag {
  margin-left: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.instance-content {
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

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.description-text {
  color: #606266;
  line-height: 1.5;
}

.text-muted {
  color: #c0c4cc;
}

/* 超时警告 */
.timeout-alert {
  margin-bottom: 20px;
}

/* 统计面板 */
.statistics-section {
  margin: 24px 0;
}

.stat-card {
  text-align: center;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-card.stat-approved .stat-value {
  color: #67c23a;
}

.stat-card.stat-rejected .stat-value {
  color: #f56c6c;
}

.stat-card.stat-rate .stat-value {
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

/* 时间线区域 */
.timeline-section {
  margin: 24px 0;
}

/* 条件表达式区域 */
.condition-section {
  margin: 24px 0;
}

/* 表单区域 */
.instance-form {
  padding: 20px;
}

/* 打印样式 */
@media print {
  .header-actions {
    display: none;
  }
}
</style>
