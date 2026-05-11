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
            <el-button type="primary" @click="handleCreateTask()">新建任务</el-button>
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

    <!-- 新建看板弹窗 -->
    <el-dialog
      v-model="boardDialogVisible"
      title="新建看板"
      width="480px"
      destroy-on-close
    >
      <el-form
        ref="boardFormRef"
        :model="boardForm"
        :rules="boardFormRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="boardForm.name" placeholder="请输入看板名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="boardForm.description"
            type="textarea"
            placeholder="请输入看板描述"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="boardDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="boardSubmitLoading" @click="submitBoard">创建</el-button>
      </template>
    </el-dialog>

    <!-- 新建任务弹窗 -->
    <el-dialog
      v-model="taskDialogVisible"
      title="新建任务"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="taskFormRules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            placeholder="请输入任务描述"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="负责人" prop="assignee_id">
          <el-select
            v-model="taskForm.assignee_id"
            placeholder="请选择负责人"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.real_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="taskForm.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期" prop="due_date">
          <el-date-picker
            v-model="taskForm.due_date"
            type="date"
            placeholder="请选择截止日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="taskSubmitLoading" @click="submitTask">创建</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑列弹窗 -->
    <el-dialog
      v-model="columnDialogVisible"
      :title="isEditingColumn ? '编辑列' : '添加列'"
      width="420px"
      destroy-on-close
    >
      <el-form
        ref="columnFormRef"
        :model="columnForm"
        :rules="columnFormRules"
        label-width="80px"
      >
        <el-form-item label="列名称" prop="name">
          <el-input v-model="columnForm.name" placeholder="请输入列名称" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-color-picker v-model="columnForm.color" show-alpha />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="columnDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="columnSubmitLoading" @click="submitColumn">
          {{ isEditingColumn ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 任务详情抽屉 -->
    <TaskDetailDrawer
      v-model:visible="drawerVisible"
      :task-id="currentTaskId"
      @updated="handleTaskUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Setting, MoreFilled, Plus, Check, ChatDotRound, Paperclip } from '@element-plus/icons-vue'
import { taskBoardApi, taskCardApi } from '@/api/oa/tasks'
import { getUserList } from '@/api/system/user'
import TaskDetailDrawer from './TaskDetailDrawer.vue'

const router = useRouter()

const loading = ref(false)
const currentBoardId = ref('')
const boardList = ref<any[]>([])
const columns = ref<any[]>([])
const tasks = ref<any[]>([])
const userList = ref<any[]>([])

// --- 新建看板 ---
const boardDialogVisible = ref(false)
const boardSubmitLoading = ref(false)
const boardFormRef = ref<FormInstance>()
const boardForm = reactive({
  name: '',
  description: '',
})
const boardFormRules: FormRules = {
  name: [{ required: true, message: '请输入看板名称', trigger: 'blur' }],
}

// --- 新建任务 ---
const taskDialogVisible = ref(false)
const taskSubmitLoading = ref(false)
const taskFormRef = ref<FormInstance>()
const taskForm = reactive({
  title: '',
  description: '',
  assignee_id: '',
  priority: 'medium',
  due_date: '',
  column_id: '',
})
const taskFormRules: FormRules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
}

// --- 添加/编辑列 ---
const columnDialogVisible = ref(false)
const columnSubmitLoading = ref(false)
const columnFormRef = ref<FormInstance>()
const isEditingColumn = ref(false)
const editingColumnId = ref('')
const columnForm = reactive({
  name: '',
  color: '#f5f5f5',
})
const columnFormRules: FormRules = {
  name: [{ required: true, message: '请输入列名称', trigger: 'blur' }],
}

// --- 任务详情抽屉 ---
const drawerVisible = ref(false)
const currentTaskId = ref('')

const loadUsers = async () => {
  try {
    const res = await getUserList({ page: 1, page_size: 100 })
    userList.value = res.data?.list || res.data || []
  } catch (error) {
    // 静默处理
  }
}

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

// --- 新建看板 ---
const handleCreateBoard = () => {
  boardForm.name = ''
  boardForm.description = ''
  boardDialogVisible.value = true
}

const submitBoard = async () => {
  if (!boardFormRef.value) return
  await boardFormRef.value.validate(async (valid) => {
    if (!valid) return
    boardSubmitLoading.value = true
    try {
      await taskBoardApi.createBoard({ ...boardForm })
      ElMessage.success('看板创建成功')
      boardDialogVisible.value = false
      await loadBoards()
    } catch (error) {
      ElMessage.error('创建看板失败')
    } finally {
      boardSubmitLoading.value = false
    }
  })
}

// --- 新建任务 ---
const handleCreateTask = (columnId?: string) => {
  taskForm.title = ''
  taskForm.description = ''
  taskForm.assignee_id = ''
  taskForm.priority = 'medium'
  taskForm.due_date = ''
  taskForm.column_id = columnId || ''
  taskDialogVisible.value = true
}

const submitTask = async () => {
  if (!taskFormRef.value) return
  await taskFormRef.value.validate(async (valid) => {
    if (!valid) return
    taskSubmitLoading.value = true
    try {
      const data: any = {
        title: taskForm.title,
        description: taskForm.description,
        assignee_id: taskForm.assignee_id,
        priority: taskForm.priority,
        due_date: taskForm.due_date,
        board_id: currentBoardId.value,
      }
      if (taskForm.column_id) {
        data.column_id = taskForm.column_id
      }
      await taskCardApi.create(data)
      ElMessage.success('任务创建成功')
      taskDialogVisible.value = false
      await loadBoardData()
    } catch (error) {
      ElMessage.error('创建任务失败')
    } finally {
      taskSubmitLoading.value = false
    }
  })
}

// --- 查看任务详情 ---
const handleViewTask = (task: any) => {
  currentTaskId.value = task.id
  drawerVisible.value = true
}

const handleTaskUpdated = () => {
  loadBoardData()
}

// --- 添加列 ---
const handleAddColumn = () => {
  isEditingColumn.value = false
  editingColumnId.value = ''
  columnForm.name = ''
  columnForm.color = '#f5f5f5'
  columnDialogVisible.value = true
}

// --- 编辑列 ---
const handleEditColumn = (column: any) => {
  isEditingColumn.value = true
  editingColumnId.value = column.id
  columnForm.name = column.name || ''
  columnForm.color = column.color || '#f5f5f5'
  columnDialogVisible.value = true
}

const submitColumn = async () => {
  if (!columnFormRef.value) return
  await columnFormRef.value.validate(async (valid) => {
    if (!valid) return
    columnSubmitLoading.value = true
    try {
      if (isEditingColumn.value) {
        await taskBoardApi.updateColumn(currentBoardId.value, editingColumnId.value, {
          name: columnForm.name,
          color: columnForm.color,
        })
        ElMessage.success('列更新成功')
      } else {
        await taskBoardApi.createColumn(currentBoardId.value, {
          name: columnForm.name,
          color: columnForm.color,
        })
        ElMessage.success('列添加成功')
      }
      columnDialogVisible.value = false
      await loadBoardData()
    } catch (error) {
      ElMessage.error(isEditingColumn.value ? '更新列失败' : '添加列失败')
    } finally {
      columnSubmitLoading.value = false
    }
  })
}

const handleColumnCommand = async (command: string, column: any) => {
  if (command === 'edit') {
    handleEditColumn(column)
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
  loadUsers()
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

.task-priority.urgent {
  background: #f56c6c;
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
