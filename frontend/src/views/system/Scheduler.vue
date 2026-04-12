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

// 表格数据
const tableData = ref([
  { id: 1, name: '每日数据备份', type: 'backup', cron: '0 0 2 * * *', next_run: '2026-04-13 02:00:00', last_run: '2026-04-12 02:00:00', enabled: true, last_result: 'success' },
  { id: 2, name: '缓存清理', type: 'cache', cron: '0 0 0 * * *', next_run: '2026-04-13 00:00:00', last_run: '2026-04-12 00:00:00', enabled: true, last_result: 'success' },
  { id: 3, name: '学习数据同步', type: 'sync', cron: '0 */30 * * * *', next_run: '2026-04-12 17:00:00', last_run: '2026-04-12 16:30:00', enabled: true, last_result: 'success' },
  { id: 4, name: '周报生成', type: 'report', cron: '0 0 8 * * 1', next_run: '2026-04-14 08:00:00', last_run: '-', enabled: false, last_result: null },
])

// 日志数据
const logData = ref([
  { task_name: '每日数据备份', start_time: '2026-04-12 02:00:00', end_time: '2026-04-12 02:15:30', duration: '15分30秒', status: 'success', message: '备份完成，共备份 128 个文件' },
  { task_name: '缓存清理', start_time: '2026-04-12 00:00:00', end_time: '2026-04-12 00:01:15', duration: '1分15秒', status: 'success', message: '清理过期缓存 2345 条' },
  { task_name: '学习数据同步', start_time: '2026-04-12 16:30:00', end_time: '2026-04-12 16:30:05', duration: '5秒', status: 'success', message: '同步完成' },
])

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建任务')
const form = reactive({
  id: null,
  name: '',
  type: '',
  cron: '',
  description: ''
})

// 获取类型颜色
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    backup: 'primary',
    sync: 'success',
    cache: 'warning',
    report: 'info',
    notification: ''
  }
  return colorMap[type] || ''
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // TODO: 替换为真实 API 调用
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialogTitle.value = '新建任务'
  form.id = null
  form.name = ''
  form.type = ''
  form.cron = ''
  form.description = ''
  dialogVisible.value = true
}

// 编辑任务
const editTask = (row: any) => {
  dialogTitle.value = '编辑任务'
  form.id = row.id
  form.name = row.name
  form.type = row.type
  form.cron = row.cron
  form.description = ''
  dialogVisible.value = true
}

// 保存任务
const saveTask = () => {
  if (!form.name || !form.type || !form.cron) {
    ElMessage.warning('请填写完整信息')
    return
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

// 删除任务
const deleteTask = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '确认删除')
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // 取消操作
  }
}

// 切换状态
const toggleStatus = (row: any) => {
  ElMessage.success(`任务 "${row.name}" 已${row.enabled ? '启用' : '禁用'}`)
}

// 立即执行
const runNow = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要立即执行任务 "${row.name}" 吗？`, '确认执行')
    ElMessage.success('任务已开始执行')
  } catch {
    // 取消操作
  }
}

onMounted(() => {
  loadData()
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
