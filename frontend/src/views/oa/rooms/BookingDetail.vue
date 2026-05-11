<template>
  <div class="booking-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-page-header @back="handleBack" title="返回列表">
            <template #content>
              <span class="page-title">预约详情</span>
              <el-tag
                v-if="detailData.status"
                :type="getStatusType(detailData.status)"
                class="status-tag"
              >
                {{ getStatusLabel(detailData.status) }}
              </el-tag>
            </template>
          </el-page-header>
          <div class="header-actions">
            <el-button
              v-if="detailData.status === 'pending' || detailData.status === 'approved'"
              type="danger"
              @click="handleCancel"
            >
              取消预约
            </el-button>
          </div>
        </div>
      </template>

      <div class="detail-content" v-loading="loading">
        <!-- 基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <label>教室名称：</label>
                <span>{{ detailData.room_name || '-' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>预约主题：</label>
                <span class="title-text">{{ detailData.title || '-' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>申请人：</label>
                <span>{{ detailData.applicant_name || '-' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>预约日期：</label>
                <span>{{ detailData.date || '-' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>时间段：</label>
                <span>{{ detailData.start_time || '-' }} - {{ detailData.end_time || '-' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>参与人数：</label>
                <span>{{ detailData.attendee_count ?? '-' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>当前状态：</label>
                <el-tag :type="getStatusType(detailData.status)">{{ getStatusLabel(detailData.status) }}</el-tag>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <label>申请时间：</label>
                <span>{{ formatDateTime(detailData.created_at) }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 议程（Markdown 渲染） -->
        <div class="agenda-section" v-if="detailData.agenda">
          <h3 class="section-title">议程</h3>
          <div class="agenda-content" v-html="renderedAgenda"></div>
        </div>

        <!-- 预约说明 -->
        <div class="description-section" v-if="detailData.description">
          <h3 class="section-title">预约说明</h3>
          <div class="description-content">{{ detailData.description }}</div>
        </div>

        <!-- 参与者列表 -->
        <div class="participants-section" v-if="detailData.participants && detailData.participants.length > 0">
          <h3 class="section-title">参与者列表</h3>
          <el-table :data="detailData.participants" border size="small">
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column prop="department" label="部门" width="150" />
            <el-table-column prop="role" label="角色" width="120" />
            <el-table-column prop="phone" label="联系方式" />
          </el-table>
        </div>

        <!-- 审批历史时间线 -->
        <div class="history-section" v-if="approvalHistory && approvalHistory.length > 0">
          <h3 class="section-title">审批历史</h3>
          <el-timeline>
            <el-timeline-item
              v-for="item in approvalHistory"
              :key="item.id"
              :timestamp="formatDateTime(item.created_at)"
              :type="getHistoryType(item.action)"
            >
              <div class="history-item">
                <div class="history-header">
                  <strong>{{ item.operator_name }}</strong>
                  <span class="history-action">{{ getActionLabel(item.action) }}</span>
                  <el-tag size="small" :type="getHistoryType(item.action)">
                    {{ item.node_name || '' }}
                  </el-tag>
                </div>
                <div v-if="item.comment" class="history-comment">
                  {{ item.comment }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bookingApi } from '@/api/oa/rooms'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const detailData = ref<any>({})
const approvalHistory = ref<any[]>([])

const statusOptions = [
  { label: '待审批', value: 'pending', type: 'warning' },
  { label: '已通过', value: 'approved', type: 'success' },
  { label: '已拒绝', value: 'rejected', type: 'danger' },
  { label: '已取消', value: 'cancelled', type: 'info' }
]

const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const formatDateTime = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 简易 Markdown 渲染（标题、列表、加粗、换行）
const renderedAgenda = computed(() => {
  if (!detailData.value.agenda) return ''
  let text = detailData.value.agenda
  // 转义 HTML
  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  // 标题
  text = text.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  text = text.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  text = text.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  // 加粗
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 无序列表
  text = text.replace(/^- (.+)$/gm, '<li>$1</li>')
  text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  // 有序列表
  text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  // 换行
  text = text.replace(/\n/g, '<br/>')
  return text
})

const getHistoryType = (action: string) => {
  const map: Record<string, string> = {
    APPROVE: 'success',
    REJECT: 'danger',
    TRANSFER: 'info',
    CREATE: 'primary',
    WITHDRAW: 'warning',
    CANCEL: 'info'
  }
  return map[action] || 'info'
}

const getActionLabel = (action: string) => {
  const map: Record<string, string> = {
    APPROVE: '同意了该申请',
    REJECT: '拒绝了该申请',
    TRANSFER: '转交了该任务',
    CREATE: '发起了预约申请',
    WITHDRAW: '撤回了该申请',
    CANCEL: '取消了该预约'
  }
  return map[action] || action
}

const loadDetail = async () => {
  loading.value = true
  try {
    const id = route.params.id as string
    const res = await bookingApi.getById(id)
    detailData.value = res.data || {}

    // 如果有关联的工作流实例，加载审批历史
    if (detailData.value.workflow_instance_id) {
      try {
        const { instanceApi } = await import('@/api/oa/workflows')
        const instanceRes = await instanceApi.getById(detailData.value.workflow_instance_id)
        approvalHistory.value = instanceRes.data?.histories || []
      } catch {
        // 审批历史加载失败不影响主页面
      }
    }
  } catch (error) {
    ElMessage.error('加载预约详情失败')
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.push('/oa/room-booking')
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消该预约吗？取消后不可恢复。', '确认取消', {
      type: 'warning'
    })
    await bookingApi.cancel(route.params.id as string)
    ElMessage.success('取消成功')
    await loadDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败')
    }
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.booking-detail {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  min-height: 300px;
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
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.agenda-content {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
  line-height: 1.8;
  color: #303133;
}

.agenda-content :deep(h2),
.agenda-content :deep(h3),
.agenda-content :deep(h4) {
  margin: 12px 0 8px 0;
  color: #303133;
}

.agenda-content :deep(ul) {
  padding-left: 20px;
  margin: 8px 0;
}

.agenda-content :deep(li) {
  margin-bottom: 4px;
}

.description-content {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
  line-height: 1.6;
  color: #606266;
}

.history-item {
  padding: 8px 0;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.history-action {
  color: #606266;
}

.history-comment {
  color: #909399;
  font-style: italic;
  margin-top: 4px;
}
</style>
