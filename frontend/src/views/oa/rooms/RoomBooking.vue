<template>
  <div class="room-booking">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>教室预约</span>
          <el-button type="primary" @click="handleCreate">新建预约</el-button>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="预约日期">
          <el-date-picker
            v-model="queryForm.date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item label="教室">
          <el-select v-model="queryForm.room_id" placeholder="请选择教室" clearable>
            <el-option
              v-for="room in roomList"
              :key="room.id"
              :label="room.name"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable>
            <el-option label="待审批" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="room_name" label="教室" width="120" />
        <el-table-column prop="title" label="预约主题" min-width="150" show-overflow-tooltip />
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column label="时间段" width="140">
          <template #default="{ row }">
            {{ row.start_time }} - {{ row.end_time }}
          </template>
        </el-table-column>
        <el-table-column prop="applicant_name" label="申请人" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="160" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button link type="danger" size="small" @click="handleCancel(row)" v-if="row.status === 'approved'">
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 预约表单弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" @closed="resetForm">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="选择教室" prop="room_id">
          <el-select v-model="formData.room_id" placeholder="请选择教室" @change="handleRoomChange">
            <el-option
              v-for="room in roomList"
              :key="room.id"
              :label="room.name"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预约日期" prop="date">
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            :disabled-date="disablePastDate"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item label="时间段" prop="time_range">
          <el-select v-model="formData.start_time" placeholder="开始时间" style="width: 120px">
            <el-option v-for="slot in filteredTimeSlots" :key="slot" :label="slot" :value="slot" />
          </el-select>
          <span style="margin: 0 10px">至</span>
          <el-select v-model="formData.end_time" placeholder="结束时间" style="width: 120px">
            <el-option v-for="slot in filteredTimeSlots" :key="slot" :label="slot" :value="slot" />
          </el-select>
        </el-form-item>
        <el-form-item label="预约主题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入预约主题" />
        </el-form-item>
        <el-form-item label="预约说明" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入预约说明" />
        </el-form-item>
        <el-form-item label="参与人数" prop="attendee_count">
          <el-input-number v-model="formData.attendee_count" :min="1" :max="500" />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            :auto-upload="false"
            :limit="5"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png"
          >
            <el-button type="primary">上传附件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { roomApi, bookingApi } from '@/api/oa/rooms'

const router = useRouter()

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建预约')
const submitLoading = ref(false)
const tableData = ref([])
const roomList = ref([])
const formRef = ref()
const filteredTimeSlots = ref<string[]>([...timeSlots])

const queryForm = reactive({
  date: '',
  room_id: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  room_id: '',
  date: '',
  start_time: '',
  end_time: '',
  title: '',
  description: '',
  attendee_count: 1
})

const formRules = {
  room_id: [{ required: true, message: '请选择教室', trigger: 'change' }],
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  title: [{ required: true, message: '请输入预约主题', trigger: 'blur' }]
}

const timeSlots = [
  '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
  '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
  '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
  '20:00', '20:30', '21:00'
]

const statusOptions = [
  { label: '待审批', value: 'pending', type: 'warning' },
  { label: '已通过', value: 'approved', type: 'success' },
  { label: '已拒绝', value: 'rejected', type: 'danger' },
  { label: '已取消', value: 'cancelled', type: 'info' }
]

const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const disablePastDate = (date: Date) => {
  return date.getTime() < Date.now() - 86400000
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await bookingApi.getList({
      ...queryForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    tableData.value = res.data?.list || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadRooms = async () => {
  try {
    const res = await roomApi.getList({ status: 'active' })
    roomList.value = res.data?.list || []
  } catch (error) {
    console.error('加载教室失败', error)
  }
}

const handleQuery = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  queryForm.date = ''
  queryForm.room_id = ''
  queryForm.status = ''
  handleQuery()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = () => {
  loadData()
}

const handleCreate = () => {
  dialogTitle.value = '新建预约'
  dialogVisible.value = true
}

const handleView = (row: any) => {
  router.push(`/oa/room-bookings/${row.id}`)
}

const handleCancel = async (row: any) => {
  try {
    await bookingApi.cancel(row.id)
    ElMessage.success('取消成功')
    loadData()
  } catch (error) {
    ElMessage.error('取消失败')
  }
}

const handleRoomChange = () => {
  formData.start_time = ''
  formData.end_time = ''
  loadAvailableSlots()
}

const handleDateChange = () => {
  formData.start_time = ''
  formData.end_time = ''
  loadAvailableSlots()
}

const loadAvailableSlots = async () => {
  if (!formData.room_id || !formData.date) return
  try {
    const res = await roomApi.getAvailableSlots(formData.room_id, { date: formData.date })
    const availableSlots: string[] = res.data?.slots || []
    // 过滤 timeSlots，仅保留可用的时间段
    filteredTimeSlots.value = timeSlots.filter(slot => availableSlots.includes(slot))
  } catch (error) {
    console.error('加载可用时间槽失败', error)
    filteredTimeSlots.value = [...timeSlots]
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    room_id: '',
    date: '',
    start_time: '',
    end_time: '',
    title: '',
    description: '',
    attendee_count: 1
  })
  filteredTimeSlots.value = [...timeSlots]
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitLoading.value = true
    await bookingApi.create(formData)
    ElMessage.success('预约成功')
    dialogVisible.value = false
    loadData()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('预约失败')
    }
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadRooms()
  loadData()
})
</script>

<style scoped>
.room-booking {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
