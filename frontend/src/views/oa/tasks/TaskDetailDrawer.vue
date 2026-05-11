<template>
  <el-drawer
    :model-value="visible"
    title="任务详情"
    direction="rtl"
    size="560px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div v-loading="detailLoading" class="task-detail">
      <!-- 标题（可编辑） -->
      <div class="detail-section">
        <div
          v-if="!editingTitle"
          class="editable-title"
          @click="editingTitle = true"
        >
          <h2>{{ taskDetail.title || '未命名任务' }}</h2>
          <el-icon class="edit-icon"><edit /></el-icon>
        </div>
        <div v-else class="title-edit-row">
          <el-input
            v-model="taskDetail.title"
            placeholder="任务标题"
            size="large"
            @blur="editingTitle = false"
            @keyup.enter="editingTitle = false"
          />
        </div>
      </div>

      <!-- 状态 & 优先级 -->
      <div class="detail-section detail-row">
        <div class="field-group">
          <label>状态</label>
          <el-select v-model="taskDetail.status" placeholder="选择状态" style="width: 100%" @change="handleQuickSave">
            <el-option label="待办" value="todo" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="审核中" value="reviewing" />
            <el-option label="已完成" value="done" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </div>
        <div class="field-group">
          <label>优先级</label>
          <el-select v-model="taskDetail.priority" placeholder="选择优先级" style="width: 100%" @change="handleQuickSave">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </div>
      </div>

      <!-- 负责人 & 截止日期 -->
      <div class="detail-section detail-row">
        <div class="field-group">
          <label>负责人</label>
          <el-select
            v-model="taskDetail.assignee_id"
            placeholder="选择负责人"
            filterable
            style="width: 100%"
            @change="handleQuickSave"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.real_name || user.username"
              :value="user.id"
            />
          </el-select>
        </div>
        <div class="field-group">
          <label>截止日期</label>
          <el-date-picker
            v-model="taskDetail.due_date"
            type="date"
            placeholder="选择截止日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="handleQuickSave"
          />
        </div>
      </div>

      <!-- 进度条 -->
      <div class="detail-section">
        <label>进度</label>
        <div class="progress-row">
          <el-slider
            v-model="taskDetail.progress"
            :min="0"
            :max="100"
            :format-tooltip="(val: number) => val + '%'"
            @change="handleQuickSave"
          />
          <span class="progress-text">{{ taskDetail.progress || 0 }}%</span>
        </div>
      </div>

      <!-- 描述 -->
      <div class="detail-section">
        <label>描述</label>
        <el-input
          v-model="taskDetail.description"
          type="textarea"
          placeholder="添加任务描述..."
          :rows="6"
          @blur="handleQuickSave"
        />
      </div>

      <!-- 子任务列表 -->
      <div class="detail-section">
        <div class="section-header">
          <label>子任务</label>
          <el-button link type="primary" @click="handleAddSubTask">
            <el-icon><plus /></el-icon> 添加
          </el-button>
        </div>
        <div class="subtask-list">
          <div
            v-for="sub in subTaskList"
            :key="sub.id"
            class="subtask-item"
          >
            <el-checkbox
              :model-value="sub.completed"
              @change="(val: any) => handleToggleSubTask(sub, val)"
            />
            <span class="subtask-title" :class="{ completed: sub.completed }">{{ sub.title }}</span>
            <el-button link type="danger" @click="handleDeleteSubTask(sub)">
              <el-icon><delete /></el-icon>
            </el-button>
          </div>
          <div v-if="subTaskList.length === 0" class="empty-tip">
            暂无子任务
          </div>
        </div>
        <!-- 新增子任务输入 -->
        <div v-if="showSubTaskInput" class="subtask-input">
          <el-input
            v-model="newSubTaskTitle"
            placeholder="输入子任务标题，回车添加"
            size="small"
            @keyup.enter="submitSubTask"
            @blur="showSubTaskInput = false"
          />
        </div>
      </div>

      <!-- 评论区 -->
      <div class="detail-section">
        <label>评论</label>
        <div class="comment-list">
          <div
            v-for="comment in commentList"
            :key="comment.id"
            class="comment-item"
          >
            <el-avatar :size="32" :src="comment.user?.avatar">
              {{ comment.user?.name?.charAt(0) || 'U' }}
            </el-avatar>
            <div class="comment-body">
              <div class="comment-meta">
                <span class="comment-author">{{ comment.user?.name || comment.user_name || '匿名' }}</span>
                <span class="comment-time">{{ comment.created_at }}</span>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
          <div v-if="commentList.length === 0" class="empty-tip">
            暂无评论
          </div>
        </div>
        <div class="comment-input">
          <el-input
            v-model="newComment"
            type="textarea"
            placeholder="添加评论..."
            :rows="2"
          />
          <el-button type="primary" size="small" @click="handleAddComment" :disabled="!newComment.trim()">
            发送
          </el-button>
        </div>
      </div>

      <!-- 附件列表 -->
      <div class="detail-section">
        <label>附件</label>
        <div class="attachment-list">
          <div
            v-for="file in attachmentList"
            :key="file.id"
            class="attachment-item"
          >
            <el-icon><document /></el-icon>
            <span class="file-name">{{ file.name || file.file_name }}</span>
            <el-button link type="primary" @click="handleDownloadFile(file)">下载</el-button>
          </div>
          <div v-if="attachmentList.length === 0" class="empty-tip">
            暂无附件
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <div class="drawer-footer">
        <el-popconfirm
          title="确定要删除该任务吗？"
          @confirm="handleDelete"
        >
          <template #reference>
            <el-button type="danger" :loading="deleteLoading">删除任务</el-button>
          </template>
        </el-popconfirm>
        <el-button type="primary" :loading="saveLoading" @click="handleSave">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Plus, Delete, Document } from '@element-plus/icons-vue'
import { taskCardApi } from '@/api/oa/tasks'
import { getUserList } from '@/api/system/user'

const props = defineProps<{
  visible: boolean
  taskId: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'updated'): void
}>()

const detailLoading = ref(false)
const saveLoading = ref(false)
const deleteLoading = ref(false)
const editingTitle = ref(false)
const userList = ref<any[]>([])
const subTaskList = ref<any[]>([])
const commentList = ref<any[]>([])
const attachmentList = ref<any[]>([])
const newSubTaskTitle = ref('')
const showSubTaskInput = ref(false)
const newComment = ref('')

const taskDetail = ref<any>({
  title: '',
  status: 'todo',
  priority: 'medium',
  assignee_id: '',
  due_date: '',
  description: '',
  progress: 0,
})

const loadUsers = async () => {
  try {
    const res = await getUserList({ page: 1, page_size: 100 })
    userList.value = res.data?.list || res.data || []
  } catch (error) {
    // 静默处理
  }
}

const loadTaskDetail = async () => {
  if (!props.taskId) return
  detailLoading.value = true
  try {
    const res = await taskCardApi.getById(props.taskId)
    const data = res.data || {}
    taskDetail.value = {
      title: data.title || '',
      status: data.status || 'todo',
      priority: data.priority || 'medium',
      assignee_id: data.assignee_id || data.assignee || '',
      due_date: data.due_date || '',
      description: data.description || '',
      progress: data.progress || 0,
    }
    subTaskList.value = data.subtasks || []
    commentList.value = data.comments || []
    attachmentList.value = data.attachments || []
  } catch (error) {
    ElMessage.error('加载任务详情失败')
  } finally {
    detailLoading.value = false
  }
}

const loadSubTasks = async () => {
  if (!props.taskId) return
  try {
    const res = await taskCardApi.getSubTasks(props.taskId)
    subTaskList.value = res.data?.list || res.data || []
  } catch (error) {
    // 静默处理
  }
}

const loadComments = async () => {
  if (!props.taskId) return
  try {
    const res = await taskCardApi.getComments(props.taskId)
    commentList.value = res.data?.list || res.data || []
  } catch (error) {
    // 静默处理
  }
}

const handleQuickSave = async () => {
  if (!props.taskId) return
  try {
    await taskCardApi.update(props.taskId, {
      title: taskDetail.value.title,
      status: taskDetail.value.status,
      priority: taskDetail.value.priority,
      assignee_id: taskDetail.value.assignee_id,
      due_date: taskDetail.value.due_date,
      progress: taskDetail.value.progress,
      description: taskDetail.value.description,
    })
  } catch (error) {
    // 静默保存，不打扰用户
  }
}

const handleSave = async () => {
  if (!props.taskId) return
  saveLoading.value = true
  try {
    await taskCardApi.update(props.taskId, {
      title: taskDetail.value.title,
      status: taskDetail.value.status,
      priority: taskDetail.value.priority,
      assignee_id: taskDetail.value.assignee_id,
      due_date: taskDetail.value.due_date,
      progress: taskDetail.value.progress,
      description: taskDetail.value.description,
    })
    ElMessage.success('保存成功')
    emit('updated')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saveLoading.value = false
  }
}

const handleDelete = async () => {
  if (!props.taskId) return
  deleteLoading.value = true
  try {
    await taskCardApi.delete(props.taskId)
    ElMessage.success('任务已删除')
    handleClose()
    emit('updated')
  } catch (error) {
    ElMessage.error('删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const handleAddSubTask = () => {
  showSubTaskInput.value = true
  newSubTaskTitle.value = ''
}

const submitSubTask = async () => {
  if (!props.taskId || !newSubTaskTitle.value.trim()) return
  try {
    await taskCardApi.addSubTask(props.taskId, { title: newSubTaskTitle.value.trim() })
    newSubTaskTitle.value = ''
    showSubTaskInput.value = false
    loadSubTasks()
    emit('updated')
  } catch (error) {
    ElMessage.error('添加子任务失败')
  }
}

const handleToggleSubTask = async (sub: any, completed: boolean) => {
  try {
    await taskCardApi.update(props.taskId, {
      subtasks: subTaskList.value.map((s: any) =>
        s.id === sub.id ? { ...s, completed } : s
      ),
    })
    sub.completed = completed
    emit('updated')
  } catch (error) {
    ElMessage.error('更新子任务失败')
  }
}

const handleDeleteSubTask = async (sub: any) => {
  try {
    await taskCardApi.update(props.taskId, {
      subtasks: subTaskList.value.filter((s: any) => s.id !== sub.id),
    })
    subTaskList.value = subTaskList.value.filter((s: any) => s.id !== sub.id)
    emit('updated')
  } catch (error) {
    ElMessage.error('删除子任务失败')
  }
}

const handleAddComment = async () => {
  if (!props.taskId || !newComment.value.trim()) return
  try {
    await taskCardApi.addComment(props.taskId, { content: newComment.value.trim() })
    newComment.value = ''
    loadComments()
    emit('updated')
  } catch (error) {
    ElMessage.error('添加评论失败')
  }
}

const handleDownloadFile = (file: any) => {
  const url = file.url || file.file_url
  if (url) {
    window.open(url, '_blank')
  } else {
    ElMessage.warning('暂无可下载的文件')
  }
}

const handleClose = () => {
  emit('update:visible', false)
}

watch(
  () => props.visible,
  (val) => {
    if (val && props.taskId) {
      loadUsers()
      loadTaskDetail()
    }
  }
)

watch(
  () => props.taskId,
  (val) => {
    if (val && props.visible) {
      loadTaskDetail()
    }
  }
)
</script>

<style scoped>
.task-detail {
  padding: 0 4px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.editable-title {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.editable-title h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
  flex: 1;
}

.edit-icon {
  color: #c0c4cc;
  font-size: 16px;
}

.editable-title:hover .edit-icon {
  color: #409eff;
}

.title-edit-row {
  width: 100%;
}

.detail-row {
  display: flex;
  gap: 16px;
}

.field-group {
  flex: 1;
}

.field-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-row .el-slider {
  flex: 1;
}

.progress-text {
  font-size: 13px;
  color: #606266;
  min-width: 40px;
  text-align: right;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-header label {
  margin-bottom: 0;
}

.subtask-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.subtask-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.subtask-item:hover {
  background: #f5f7fa;
}

.subtask-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
}

.subtask-title.completed {
  text-decoration: line-through;
  color: #c0c4cc;
}

.subtask-input {
  margin-top: 8px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.comment-item {
  display: flex;
  gap: 10px;
}

.comment-body {
  flex: 1;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.comment-author {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.comment-time {
  font-size: 12px;
  color: #c0c4cc;
}

.comment-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.comment-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.attachment-item .el-icon {
  color: #909399;
}

.file-name {
  flex: 1;
  font-size: 13px;
  color: #606266;
}

.empty-tip {
  font-size: 13px;
  color: #c0c4cc;
  text-align: center;
  padding: 12px 0;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
