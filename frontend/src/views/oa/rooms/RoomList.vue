<template>
  <div class="room-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>教室管理</span>
          <el-button type="primary" @click="handleCreate">新增教室</el-button>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="教室名称">
          <el-input v-model="queryForm.name" placeholder="请输入教室名称" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryForm.type" placeholder="请选择类型" clearable>
            <el-option label="教室" value="classroom" />
            <el-option label="会议室" value="meeting_room" />
            <el-option label="实验室" value="laboratory" />
            <el-option label="活动室" value="activity_room" />
          </el-select>
        </el-form-item>
        <el-form-item label="楼栋">
          <el-input v-model="queryForm.building" placeholder="请输入楼栋" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable>
            <el-option label="可用" value="active" />
            <el-option label="维护中" value="maintenance" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="building" label="楼栋" width="100" />
        <el-table-column prop="floor" label="楼层" width="70" align="center" />
        <el-table-column prop="capacity" label="容量" width="80" align="center" />
        <el-table-column prop="equipment" label="设备" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatEquipment(row.equipment) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑教室弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="650px"
      @closed="resetForm"
      destroy-on-close
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入教室名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="教室" value="classroom" />
            <el-option label="会议室" value="meeting_room" />
            <el-option label="实验室" value="laboratory" />
            <el-option label="活动室" value="activity_room" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="楼栋" prop="building">
              <el-input v-model="formData.building" placeholder="请输入楼栋" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="楼层" prop="floor">
              <el-input-number v-model="formData.floor" :min="-3" :max="50" style="width: 100%" placeholder="楼层" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="容量" prop="capacity">
              <el-input-number v-model="formData.capacity" :min="1" :max="1000" style="width: 100%" placeholder="容量" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="面积" prop="area">
              <el-input-number v-model="formData.area" :min="1" :max="10000" style="width: 100%" placeholder="面积(m²)" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="位置描述" prop="location_desc">
          <el-input v-model="formData.location_desc" placeholder="请输入位置描述" />
        </el-form-item>
        <el-form-item label="设备清单" prop="equipment">
          <el-input
            v-model="formData.equipment"
            type="textarea"
            :rows="3"
            placeholder='请输入设备清单，JSON格式，如：["投影仪","白板","音响"]'
          />
        </el-form-item>
        <el-form-item label="预约规则" prop="booking_rules">
          <el-input
            v-model="formData.booking_rules"
            type="textarea"
            :rows="3"
            placeholder="请输入预约规则说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="detailVisible" title="教室详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getTypeTagType(detailData.type)">{{ getTypeLabel(detailData.type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="楼栋">{{ detailData.building || '-' }}</el-descriptions-item>
        <el-descriptions-item label="楼层">{{ detailData.floor ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="容量">{{ detailData.capacity ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="面积">{{ detailData.area ? `${detailData.area} m²` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(detailData.status)">{{ getStatusLabel(detailData.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="位置描述">{{ detailData.location_desc || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备清单" :span="2">
          {{ formatEquipment(detailData.equipment) }}
        </el-descriptions-item>
        <el-descriptions-item label="预约规则" :span="2">
          {{ detailData.booking_rules || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { roomApi } from '@/api/oa/rooms'

const loading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const dialogTitle = ref('新增教室')
const submitLoading = ref(false)
const tableData = ref([])
const formRef = ref()
const detailData = ref<any>({})

const queryForm = reactive({
  name: '',
  type: '',
  building: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  id: '' as string,
  name: '',
  type: '',
  building: '',
  floor: undefined as number | undefined,
  capacity: undefined as number | undefined,
  area: undefined as number | undefined,
  location_desc: '',
  equipment: '',
  booking_rules: ''
})

const formRules = {
  name: [{ required: true, message: '请输入教室名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const typeOptions = [
  { label: '教室', value: 'classroom', tagType: '' },
  { label: '会议室', value: 'meeting_room', tagType: 'success' },
  { label: '实验室', value: 'laboratory', tagType: 'warning' },
  { label: '活动室', value: 'activity_room', tagType: 'danger' }
]

const statusOptions = [
  { label: '可用', value: 'active', type: 'success' },
  { label: '维护中', value: 'maintenance', type: 'warning' },
  { label: '停用', value: 'disabled', type: 'danger' }
]

const getTypeLabel = (val: string) => typeOptions.find(o => o.value === val)?.label || val
const getTypeTagType = (val: string) => typeOptions.find(o => o.value === val)?.tagType || 'info'
const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const formatEquipment = (equipment: any) => {
  if (!equipment) return '-'
  if (typeof equipment === 'string') {
    try {
      const parsed = JSON.parse(equipment)
      if (Array.isArray(parsed)) return parsed.join('、')
      return equipment
    } catch {
      return equipment
    }
  }
  if (Array.isArray(equipment)) return equipment.join('、')
  return String(equipment)
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await roomApi.getList({
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

const handleQuery = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  queryForm.name = ''
  queryForm.type = ''
  queryForm.building = ''
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
  dialogTitle.value = '新增教室'
  dialogVisible.value = true
}

const handleView = async (row: any) => {
  try {
    const res = await roomApi.getById(row.id)
    detailData.value = res.data || row
    detailVisible.value = true
  } catch (error) {
    detailData.value = row
    detailVisible.value = true
  }
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑教室'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    type: row.type,
    building: row.building || '',
    floor: row.floor,
    capacity: row.capacity,
    area: row.area,
    location_desc: row.location_desc || '',
    equipment: typeof row.equipment === 'object' ? JSON.stringify(row.equipment, null, 2) : (row.equipment || ''),
    booking_rules: row.booking_rules || ''
  })
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除教室「${row.name}」吗？`, '确认删除', {
      type: 'warning'
    })
    await roomApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    id: '',
    name: '',
    type: '',
    building: '',
    floor: undefined,
    capacity: undefined,
    area: undefined,
    location_desc: '',
    equipment: '',
    booking_rules: ''
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitLoading.value = true

    const payload: any = {
      name: formData.name,
      type: formData.type,
      building: formData.building,
      floor: formData.floor,
      capacity: formData.capacity,
      area: formData.area,
      location_desc: formData.location_desc,
      equipment: formData.equipment,
      booking_rules: formData.booking_rules
    }

    if (formData.id) {
      await roomApi.update(formData.id, payload)
      ElMessage.success('更新成功')
    } else {
      await roomApi.create(payload)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadData()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(formData.id ? '更新失败' : '创建失败')
    }
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.room-list {
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
