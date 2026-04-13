<template>
  <div class="scheduler-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
        </div>
      </template>
      
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="name" label="任务名称" width="150" />
        <el-table-column prop="type" label="任务类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cron" label="Cron表达式" width="120" />
        <el-table-column prop="next_run" label="下次执行" width="180" />
        <el-table-column prop="last_run" label="上次执行" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="toggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="result" label="执行结果" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.last_result === 'success'" type="success">成功</el-tag>
            <el-tag v-else-if="row.last_result === 'failed'" type="danger">失败</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="runNow(row)">
              立即执行
            </el-button>
            <el-button type="primary" link size="small" @click="editTask(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="deleteTask(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 执行日志 -->
    <el-card class="log-card">
      <template #header>
        <span>执行日志</span>
      </template>
      <el-table :data="logData" stripe max-height="300">
        <el-table-column prop="task_name" label="任务名称" width="150" />
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="end_time" label="结束时间" width="180" />
        <el-table-column prop="duration" label="耗时" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="日志信息" show-overflow-tooltip />
      </el-table>
    </el-card>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="form.type" placeholder="请选择任务类型">
            <el-option label="数据备份" value="backup" />
            <el-option label="数据同步" value="sync" />
            <el-option label="缓存清理" value="cache" />
            <el-option label="报表生成" value="report" />
            <el-option label="通知推送" value="notification" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式">
          <el-input v-model="form.cron" placeholder="0 0 * * * *" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getSchedulerTasks,
  getSchedulerLogs,
  createSchedulerTask,
  updateSchedulerTask,
  deleteSchedulerTask,
  toggleSchedulerTask,
  runSchedulerTaskNow,
  getTaskTypes,
  type SchedulerTask,
  type TaskLog,
  type TaskType
} from '@/api/system/scheduler'

// 表格数据
const tableData = ref<SchedulerTask[]>([])

// 日志数据
const logData = ref<TaskLog[]>([])

// 任务类型
const taskTypes = ref<TaskType[]>([])

const loading = ref(false)
const logLoading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建任务')
const form = reactive({
  id: null as string | null,
  name: '',
  task_type: '',
  cron: '',
  description: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 获取类型颜色
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    backup: 'primary',
    sync: 'success',
    cache: 'warning',
    report: 'info',
    notification: '',
    cleanup: 'danger',
    custom: ''
  }
  return colorMap[type] || ''
}

// 加载任务数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await getSchedulerTasks({
      page: currentPage.value,
      page_size: pageSize.value
    })
    if (res.data.code === 200) {
      tableData.value = res.data.data || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载日志数据
const loadLogs = async () => {
  logLoading.value = true
  try {
    const res = await getSchedulerLogs({ page: 1, page_size: 20 })
    if (res.data.code === 200) {
      logData.value = res.data.data || []
    }
  } catch (error) {
    console.error('加载日志失败', error)
  } finally {
    logLoading.value = false
  }
}

// 加载任务类型
const loadTaskTypes = async () => {
  try {
    const res = await getTaskTypes()
    if (res.data.code === 200) {
      taskTypes.value = res.data.data || []
    }
  } catch (error) {
    console.error('加载任务类型失败', error)
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialogTitle.value = '新建任务'
  form.id = null
  form.name = ''
  form.task_type = ''
  form.cron = ''
  form.description = ''
  dialogVisible.value = true
}

// 编辑任务
const editTask = (row: SchedulerTask) => {
  dialogTitle.value = '编辑任务'
  form.id = row.id
  form.name = row.name
  form.task_type = row.task_type
  form.cron = row.cron
  form.description = row.description || ''
  dialogVisible.value = true
}

// 保存任务
const saveTask = async () => {
  if (!form.name || !form.task_type || !form.cron) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    if (form.id) {
      // 更新
      const res = await updateSchedulerTask(form.id, {
        name: form.name,
        task_type: form.task_type,
        cron: form.cron,
        description: form.description
      })
      if (res.data.code === 200) {
        ElMessage.success('更新成功')
      }
    } else {
      // 创建
      const res = await createSchedulerTask({
        name: form.name,
        task_type: form.task_type,
        cron: form.cron,
        description: form.description
      })
      if (res.data.code === 200) {
        ElMessage.success('创建成功')
      }
    }
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 删除任务
const deleteTask = async (row: SchedulerTask) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '确认删除')
    const res = await deleteSchedulerTask(row.id)
    if (res.data.code === 200) {
      ElMessage.success('删除成功')
      loadData()
    }
  } catch {
    // 取消操作
  }
}

// 切换状态
const toggleStatus = async (row: SchedulerTask) => {
  try {
    const res = await toggleSchedulerTask(row.id)
    if (res.data.code === 200) {
      ElMessage.success(`任务 "${row.name}" 已${row.enabled ? '启用' : '禁用'}`)
      loadData()
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 立即执行
const runNow = async (row: SchedulerTask) => {
  try {
    await ElMessageBox.confirm(`确定要立即执行任务 "${row.name}" 吗？`, '确认执行')
    const res = await runSchedulerTaskNow(row.id)
    if (res.data.code === 200) {
      ElMessage.success('任务已开始执行')
      loadData()
      loadLogs()
    }
  } catch {
    // 取消操作
  }
}

onMounted(() => {
  loadData()
  loadLogs()
  loadTaskTypes()
})
</script>

<style scoped lang="scss">
.scheduler-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .log-card {
    margin-top: 20px;
  }
}
</style>
