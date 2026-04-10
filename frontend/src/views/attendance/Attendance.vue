<template>
  <div class="attendance-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="日期">
            <el-date-picker v-model="searchForm.date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="searchForm.attendance_type" placeholder="请选择" clearable>
              <el-option label="出勤" value="normal" />
              <el-option label="迟到" value="late" />
              <el-option label="请假" value="leave" />
              <el-option label="缺勤" value="absent" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="success" @click="handleCheckIn">签到</el-button>
            <el-button type="warning" @click="handleLeave">请假</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="user_name" label="姓名" width="120" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="check_in_time" label="签到时间" width="120" />
        <el-table-column prop="check_out_time" label="签退时间" width="120" />
        <el-table-column prop="attendance_type" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.attendance_type)">{{ getTypeName(row.attendance_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'normal' ? 'success' : 'danger'">{{ row.status === 'normal' ? '正常' : '异常' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" width="180" />
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <el-dialog v-model="leaveDialogVisible" title="请假申请" width="500px">
      <el-form ref="formRef" :model="leaveForm" :rules="leaveRules" label-width="100px">
        <el-form-item label="请假类型" prop="leave_type">
          <el-select v-model="leaveForm.leave_type">
            <el-option label="事假" value="personal" />
            <el-option label="病假" value="sick" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="leaveForm.start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="leaveForm.end_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="请假原因" prop="reason">
          <el-input v-model="leaveForm.reason" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="leaveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleLeaveSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getAttendanceList, createAttendance, createLeave } from '@/api/attendance'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ date: '', attendance_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const leaveDialogVisible = ref(false)
const formRef = ref<FormInstance>()
const leaveForm = reactive<any>({ leave_type: 'personal', start_date: '', end_date: '', reason: '' })
const leaveRules = {
  leave_type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  reason: [{ required: true, message: '请输入请假原因', trigger: 'blur' }]
}

const getTypeName = (type: string) => ({ normal: '出勤', late: '迟到', leave: '请假', absent: '缺勤' }[type] || type)
const getTypeTag = (type: string) => ({ normal: 'success', late: 'warning', leave: 'info', absent: 'danger' }[type] || '')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getAttendanceList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; fetchData() }

const handleCheckIn = async () => {
  try {
    await createAttendance({ attendance_type: 'normal' })
    ElMessage.success('签到成功')
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '签到失败') }
}

const handleLeave = () => {
  leaveDialogVisible.value = true
}

const handleLeaveSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    await createLeave(leaveForm)
    ElMessage.success('请假申请已提交')
    leaveDialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '提交失败') }
}

onMounted(() => { fetchData() })
</script>

<style scoped lang="scss">
.attendance-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>