<template>
  <div class="approval-timeline">
    <el-timeline>
      <!-- 流程发起 -->
      <el-timeline-item
        :timestamp="formatDateTime(instance.created_at)"
        type="primary"
        size="large"
      >
        <div class="timeline-card">
          <div class="timeline-header">
            <el-icon :size="20" color="#409eff"><CircleCheckFilled /></el-icon>
            <strong>{{ instance.initiator_name || '发起人' }}</strong>
            <el-tag size="small" type="primary">发起申请</el-tag>
          </div>
          <div class="timeline-body" v-if="instance.title">
            <div class="timeline-title">{{ instance.title }}</div>
            <div class="timeline-desc" v-if="instance.description">{{ instance.description }}</div>
          </div>
        </div>
      </el-timeline-item>

      <!-- 审批节点时间线 -->
      <el-timeline-item
        v-for="(node, index) in processedNodes"
        :key="node.id || `node-${index}`"
        :timestamp="node.timestamp"
        :type="node.statusType"
        :color="node.color"
        :size="node.is_current ? 'large' : 'normal'"
      >
        <div class="timeline-card" :class="{ 'is-current': node.is_current, 'is-overdue': node.is_overdue }">
          <!-- 节点头部 -->
          <div class="timeline-header">
            <el-icon :size="18" :color="node.color">
              <VideoPlay v-if="node.node_type === 'START'" />
              <CircleCheck v-else-if="node.node_type === 'END'" />
              <User v-else-if="node.node_type === 'APPROVAL'" />
              <Switch v-else-if="node.node_type === 'CONDITION'" />
              <Message v-else-if="node.node_type === 'CC'" />
            </el-icon>
            <strong>{{ node.name }}</strong>
            <el-tag size="small" :type="node.statusType">{{ node.statusLabel }}</el-tag>
            <el-tag v-if="node.is_overdue" size="small" type="danger">超时</el-tag>
          </div>

          <!-- 审批人信息 -->
          <div class="timeline-approvers" v-if="node.approvers && node.approvers.length > 0">
            <div class="approver-list">
              <el-avatar
                v-for="approver in node.approvers"
                :key="approver.id"
                :size="28"
                class="approver-avatar"
              >
                {{ (approver.name || '?').substring(0, 1) }}
              </el-avatar>
              <span class="approver-names">
                {{ node.approvers.map(a => a.name).join('、') }}
              </span>
            </div>
          </div>

          <!-- 审批意见 -->
          <div class="timeline-comment" v-if="node.comment">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ node.comment }}</span>
          </div>

          <!-- 节点描述 -->
          <div class="timeline-body" v-if="node.node_description">
            {{ node.node_description }}
          </div>
        </div>
      </el-timeline-item>

      <!-- 流程结束 -->
      <el-timeline-item
        v-if="instance.status === 'APPROVED' || instance.status === 'REJECTED'"
        :timestamp="formatDateTime(instance.completed_at)"
        :type="instance.status === 'APPROVED' ? 'success' : 'danger'"
        size="large"
      >
        <div class="timeline-card">
          <div class="timeline-header">
            <el-icon :size="20" :color="instance.status === 'APPROVED' ? '#67c23a' : '#f56c6c'">
              <CircleCheckFilled v-if="instance.status === 'APPROVED'" />
              <CircleCloseFilled v-else />
            </el-icon>
            <strong>{{ instance.status === 'APPROVED' ? '审批通过' : '审批拒绝' }}</strong>
            <el-tag size="small" :type="instance.status === 'APPROVED' ? 'success' : 'danger'">
              {{ instance.status === 'APPROVED' ? '已通过' : '已拒绝' }}
            </el-tag>
          </div>
          <div class="timeline-body" v-if="instance.result">
            {{ instance.result }}
          </div>
        </div>
      </el-timeline-item>

      <!-- 已撤回 -->
      <el-timeline-item
        v-if="instance.status === 'CANCELLED'"
        :timestamp="formatDateTime(instance.completed_at)"
        type="info"
        size="large"
      >
        <div class="timeline-card">
          <div class="timeline-header">
            <el-icon :size="20" color="#909399"><CircleClose /></el-icon>
            <strong>已撤回</strong>
            <el-tag size="small" type="info">已撤回</el-tag>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>

    <!-- 空状态 -->
    <el-empty v-if="processedNodes.length === 0 && !instance.created_at" description="暂无审批记录" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  CircleClose,
  VideoPlay,
  CircleCheck,
  User,
  Switch,
  Message,
  ChatDotRound,
} from '@element-plus/icons-vue'
import type {
  WorkflowNode,
  WorkflowHistory,
  WorkflowInstance,
  ApproveAction,
  NodeType,
} from '@/types/workflow'

// ============================================================
// Props
// ============================================================

const props = defineProps<{
  instance: Partial<WorkflowInstance>
  nodes?: Partial<WorkflowNode>[]
  histories?: Partial<WorkflowHistory>[]
}>()

// ============================================================
// 计算属性：处理节点数据，生成时间线条目
// ============================================================

const processedNodes = computed(() => {
  const items: Array<{
    id?: string
    name: string
    node_type?: NodeType
    timestamp?: string
    statusLabel: string
    statusType: 'primary' | 'success' | 'warning' | 'danger' | 'info'
    color: string
    is_current: boolean
    is_overdue: boolean
    is_completed: boolean
    approvers?: { id?: string; name?: string }[]
    comment?: string
    node_description?: string
  }> = []

  // 优先使用 nodes 属性，否则使用 instance.nodes
  const nodes = props.nodes || props.instance?.nodes || []

  for (const node of nodes) {
    const isCurrent = !!node.is_current
    const isCompleted = !!node.is_completed
    const isPending = !!node.is_pending
    const isOverdue = !!node.is_overdue

    let statusLabel = '未开始'
    let statusType: 'primary' | 'success' | 'warning' | 'danger' | 'info' = 'info'
    let color = '#c0c4cc'

    if (isCurrent) {
      statusLabel = '审批中'
      statusType = 'warning'
      color = '#e6a23c'
    } else if (isCompleted) {
      statusLabel = '已通过'
      statusType = 'success'
      color = '#67c23a'
    } else if (isPending) {
      statusLabel = '待处理'
      statusType = 'warning'
      color = '#e6a23c'
    }

    // 获取审批人
    const approvers = node.tasks?.map(t => ({
      id: t.assignee_id,
      name: t.assignee_name || '未知',
    })) || []

    // 获取最新评论
    const latestTask = node.tasks?.filter(t => t.comment).pop()
    const comment = latestTask?.comment

    // 获取时间戳（最近的任务处理时间）
    const latestProcessed = node.tasks?.filter(t => t.processed_at).pop()
    const timestamp = latestProcessed?.processed_at || node.completed_at

    items.push({
      id: node.id,
      name: node.name || '未知节点',
      node_type: node.node_type,
      timestamp: timestamp ? formatDateTime(timestamp) : undefined,
      statusLabel,
      statusType,
      color,
      is_current: isCurrent,
      is_overdue: isOverdue,
      is_completed: isCompleted,
      approvers: approvers.length > 0 ? approvers : undefined,
      comment,
      node_description: node.condition_expression
        ? `条件: ${JSON.stringify(node.condition_expression)}`
        : undefined,
    })
  }

  // 如果有 histories，也添加到时间线
  const histories = props.histories || props.instance?.histories || []
  for (const history of histories) {
    if (!history.node_name) continue

    let statusType: 'primary' | 'success' | 'warning' | 'danger' | 'info' = 'info'
    let color = '#909399'

    switch (history.action) {
      case 'APPROVE':
        statusType = 'success'
        color = '#67c23a'
        break
      case 'REJECT':
        statusType = 'danger'
        color = '#f56c6c'
        break
      case 'TRANSFER':
        statusType = 'warning'
        color = '#e6a23c'
        break
      case 'CREATE':
        statusType = 'primary'
        color = '#409eff'
        break
      case 'WITHDRAW':
        statusType = 'info'
        color = '#909399'
        break
    }

    items.push({
      name: history.node_name,
      timestamp: history.created_at ? formatDateTime(history.created_at) : undefined,
      statusLabel: getActionLabel(history.action),
      statusType,
      color,
      is_current: false,
      is_overdue: false,
      is_completed: true,
      approvers: history.operator_name ? [{ name: history.operator_name }] : undefined,
      comment: history.comment,
    })
  }

  return items
})

// ============================================================
// 工具函数
// ============================================================

const getActionLabel = (action?: string): string => {
  const map: Record<string, string> = {
    APPROVE: '通过',
    REJECT: '拒绝',
    TRANSFER: '转交',
    DELEGATE: '转派',
    CREATE: '发起',
    WITHDRAW: '撤回',
    URGE: '催办',
  }
  return map[action || ''] || action || ''
}

const formatDateTime = (date: string | Date | undefined): string => {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return ''
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.approval-timeline {
  padding: 16px 0;
}

.timeline-card {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 3px solid transparent;
  transition: all 0.3s;
}

.timeline-card.is-current {
  background: #f0f9ff;
  border-left-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.timeline-card.is-overdue {
  border-left-color: #f56c6c;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.timeline-header strong {
  font-size: 14px;
  color: #303133;
}

.timeline-approvers {
  margin-top: 8px;
}

.approver-list {
  display: flex;
  align-items: center;
  gap: 8px;
}

.approver-avatar {
  background-color: #409eff;
  font-size: 12px;
}

.approver-names {
  font-size: 13px;
  color: #606266;
}

.timeline-comment {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.timeline-comment .el-icon {
  margin-top: 2px;
  color: #909399;
}

.timeline-body {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}

.timeline-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.timeline-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
</style>
