<template>
  <div class="task-board">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-select v-model="currentBoardId" placeholder="选择看板" @change="handleBoardChange">
              <el-option
                v-for="board in boardList"
                :key="board.id"
                :label="board.name"
                :value="board.id"
              />
            </el-select>
            <el-button link @click="handleBoardSettings">
              <el-icon><setting /></el-icon>
            </el-button>
          </div>
          <div class="header-right">
            <el-button @click="handleCreateBoard">新建看板</el-button>
            <el-button type="primary" @click="handleCreateTask">新建任务</el-button>
          </div>
        </div>
      </template>

      <div class="board-container" v-loading="loading">
        <div v-if="columns.length === 0" class="empty-state">
          <el-empty description="暂无看板列，请先添加列" />
          <el-button type="primary" @click="handleAddColumn">添加列</el-button>
        </div>
        <div v-else class="columns-wrapper">
          <div
            v-for="column in columns"
            :key="column.id"
            class="column"
            :style="{ backgroundColor: column.color || '#f5f5f5' }"
          >
            <div class="column-header">
              <span class="column-title">{{ column.name }}</span>
              <span class="column-count">{{ getTasksByColumn(column.id).length }}</span>
              <el-dropdown trigger="click" @command="(cmd) => handleColumnCommand(cmd, column)">
                <el-button link>
                  <el-icon><more-filled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="delete">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <div class="column-content">
              <div
                v-for="task in getTasksByColumn(column.id)"
                :key="task.id"
                class="task-card"
                @click="handleViewTask(task)"
              >
                <div class="task-priority" :class="task.priority"></div>
                <div class="task-title">{{ task.title }}</div>
                <div class="task-meta">
                  <el-tag v-if="task.due_date" size="small" :type="isOverdue(task.due_date) ? 'danger' : ''">
                    {{ formatDate(task.due_date) }}
                  </el-tag>
                  <div class="task-members">
                    <el-avatar
                      v-for="member in task.assignees?.slice(0, 3)"
                      :key="member.id"
                      :size="24"
                      :src="member.avatar"
                    >
                      {{ member.name?.charAt(0) }}
                    </el-avatar>
                  </div>
                </div>
                <div class="task-footer">
                  <span v-if="task.subtask_count">
                    <el-icon><check /></el-icon>
                    {{ task.completed_subtask_count }}/{{ task.subtask_count }}
                  </span>
                  <span v-if="task.comment_count">
                    <el-icon><chat-dot-round /></el-icon>
                    {{ task.comment_count }}
                  </span>
                  <span v-if="task.attachment_count">
                    <el-icon><paperclip /></el-icon>
                    {{ task.attachment_count }}
                  </span>
                </div>
              </div>
              <el-button link class="add-task-btn" @click.stop="handleCreateTask(column.id)">
                <el-icon><plus /></el-icon> 添加任务
              </el-button>
            </div>
          </div>
          <div class="column add-column" @click="handleAddColumn">
            <el-icon><plus /></el-icon>
            <span>添加列</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, MoreFilled, Plus, Check, ChatDotRound, Paperclip } from '@element-plus/icons-vue'
import { taskBoardApi, taskCardApi } from '@/api/oa/tasks'

const router = useRouter()

const loading = ref(false)
const currentBoardId = ref('')
const boardList = ref([])
const columns = ref([])
const tasks = ref([])

const loadBoards = async () => {
  try {
    const res = await taskBoardApi.getBoardList()
    boardList.value = res.data?.list || []
    if (boardList.value.length > 0 && !currentBoardId.value) {
      currentBoardId.value = boardList.value[0].id
      await loadBoardData()
    }
  } catch (error) {
    ElMessage.error('加载看板列表失败')
  }
}

const loadBoardData = async () => {
  if (!currentBoardId.value) return
  loading.value = true
  try {
    const [columnsRes, tasksRes] = await Promise.all([
      taskBoardApi.getColumns(currentBoardId.value),
      taskCardApi.getList({ board_id: currentBoardId.value })
    ])
    columns.value = columnsRes.data?.list || []
    tasks.value = tasksRes.data?.list || []
  } catch (error) {
    ElMessage.error('加载看板数据失败')
  } finally {
    loading.value = false
  }
}

const handleBoardChange = () => {
  loadBoardData()
}

const handleBoardSettings = () => {
  if (!currentBoardId.value) return
  router.push(`/oa/tasks/boards/${currentBoardId.value}/settings`)
}

const handleCreateBoard = () => {
  // TODO: 打开新建看板弹窗
}

const handleCreateTask = (columnId?: string) => {
  // TODO: 打开新建任务弹窗
}

const handleViewTask = (task: any) => {
  router.push(`/oa/tasks/${task.id}`)
}

const handleAddColumn = () => {
  // TODO: 打开添加列弹窗
}

const handleColumnCommand = async (command: string, column: any) => {
  if (command === 'edit') {
    // TODO: 打开编辑列弹窗
  } else if (command === 'delete') {
    try {
      await ElMessageBox.confirm('确定要删除该列吗？该列下的所有任务将被删除。', '提示', {
        type: 'warning'
      })
      await taskBoardApi.deleteColumn(currentBoardId.value, column.id)
      ElMessage.success('删除成功')
      loadBoardData()
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error('删除失败')
      }
    }
  }
}

const getTasksByColumn = (columnId: string) => {
  return tasks.value.filter(t => t.column_id === columnId)
}

const isOverdue = (date: string) => {
  return new Date(date) < new Date()
}

const formatDate = (date: string) => {
  const d = new Date(date)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

onMounted(() => {
  loadBoards()
})
</script>

<style scoped>
.task-board {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  gap: 8px;
}

.board-container {
  min-height: 400px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.columns-wrapper {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.column {
  min-width: 280px;
  max-width: 280px;
  border-radius: 8px;
  padding: 12px;
  flex-shrink: 0;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.column-title {
  font-weight: 600;
  flex: 1;
}

.column-count {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.column-content {
  min-height: 100px;
}

.task-card {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.task-priority {
  height: 3px;
  border-radius: 2px;
  margin-bottom: 8px;
}

.task-priority.high {
  background: #f56c6c;
}

.task-priority.medium {
  background: #e6a23c;
}

.task-priority.low {
  background: #67c23a;
}

.task-title {
  font-size: 14px;
  margin-bottom: 8px;
  line-height: 1.4;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-members {
  display: flex;
  gap: 4px;
}

.task-footer {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.task-footer span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.add-task-btn {
  width: 100%;
  justify-content: center;
  color: #909399;
}

.add-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  cursor: pointer;
  color: #909399;
  border: 2px dashed #dcdfe6;
  background: transparent;
}

.add-column:hover {
  border-color: #409eff;
  color: #409eff;
}
</style>
