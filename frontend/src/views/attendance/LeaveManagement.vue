<template>
  <div class="leave-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择" clearable>
              <el-option label="待审批" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">申请请假</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="student_id" label="学生" width="120">
          <template #default="{ row }">
            {{ getStudentName(row.student_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="leave_type" label="请假类型" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.leave_type === 'sick'" type="danger">病假</el-tag>
            <el-tag v-else-if="row.leave_type === 'personal'" type="warning">事假</el-tag>
            <el-tag v-else type="info">其他</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="请假时间" width="200">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }} - {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="days" label="天数" width="80" />
        <el-table-column prop="reason" label="请假原因" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="warning">待审批</el-tag>
            <el-tag v-else-if="row.status === 'approved'" type="success">已通过</el-tag>
            <el-tag v-else-if="row.status === 'rejected'" type="danger">已拒绝</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" type="primary" link @click="handleApprove(row)">审批</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="学生" prop="student_id">
          <el-select v-model="formData.student_id" placeholder="请选择学生" filterable>
            <el-option v-for="s in studentOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="请假类型" prop="leave_type">
          <el-select v-model="formData.leave_type">
            <el-option label="病假" value="sick" />
            <el-option label="事假" value="personal" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间" prop="start_date">
          <el-date-picker v-model="formData.start_date" type="datetime" placeholder="选择开始时间" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_date">
          <el-date-picker v-model="formData.end_date" type="datetime" placeholder="选择结束时间" />
        </el-form-item>
        <el-form-item label="请假原因" prop="reason">
          <el-input v-model="formData.reason" type="textarea" :rows="3" placeholder="请输入请假原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="approveDialogVisible" title="审批请假" width="500px">
      <el-form label-width="80px">
        <el-form-item label="审批结果">
          <el-radio-group v-model="approveForm.status">
            <el-radio value="approved">通过</el-radio>
            <el-radio value="rejected">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input v-model="approveForm.approver_comment" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleApproveSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getLeaveRequests,
  createLeaveRequest,
  approveLeave,
  getLeaveStats
} from '@/api/attendance/leave'
import { getStudentOptions } from '@/api/edu/student'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const studentOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({
  id: '',
  student_id: '',
  leave_type: 'personal',
  start_date: '',
  end_date: '',
  reason: ''
})

const approveDialogVisible = ref(false)
const currentLeaveId = ref('')
const approveForm = reactive({ status: 'approved', approver_comment: '' })

const formRules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  leave_type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getLeaveRequests({
      ...searchForm,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchStudents = async () => {
  try {
    const res = await getStudentOptions()
    studentOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const getStudentName = (id: string) => studentOptions.value.find(s => s.value === id)?.label || id

const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.status = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, {
    id: '',
    student_id: '',
    leave_type: 'personal',
    start_date: '',
    end_date: '',
    reason: ''
  })
  dialogTitle.value = '申请请假'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    await createLeaveRequest({
      ...formData,
      start_date: new Date(formData.start_date).toISOString(),
      end_date: new Date(formData.end_date).toISOString()
    })
    ElMessage.success('申请成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleApprove = (row: any) => {
  currentLeaveId.value = row.id
  approveForm.status = 'approved'
  approveForm.approver_comment = ''
  approveDialogVisible.value = true
}

const handleApproveSubmit = async () => {
  try {
    await approveLeave(currentLeaveId.value, approveForm)
    ElMessage.success('审批完成')
    approveDialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该请假申请吗？', '提示', { type: 'warning' })
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchStudents(); fetchData() })
</script>

<style scoped lang="scss">
.leave-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>