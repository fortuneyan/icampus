<template>
  <div class="classroom-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="教学楼">
            <el-select v-model="searchForm.building" placeholder="请选择" clearable>
              <el-option v-for="b in buildingOptions" :key="b" :label="b" :value="b" />
            </el-select>
          </el-form-item>
          <el-form-item label="教室类型">
            <el-select v-model="searchForm.room_type" placeholder="请选择" clearable>
              <el-option label="普通教室" value="普通教室" />
              <el-option label="实验室" value="实验室" />
              <el-option label="机房" value="机房" />
              <el-option label="多媒体" value="多媒体" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增教室</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="building" label="教学楼" width="120" />
        <el-table-column prop="room_no" label="教室号" width="100" />
        <el-table-column prop="capacity" label="容量" width="80" />
        <el-table-column prop="room_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoomTypeTag(row.room_type)">{{ row.room_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '可用' : '不可用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="教学楼" prop="building">
          <el-input v-model="formData.building" />
        </el-form-item>
        <el-form-item label="教室号" prop="room_no">
          <el-input v-model="formData.room_no" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="formData.capacity" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="类型" prop="room_type">
          <el-select v-model="formData.room_type">
            <el-option label="普通教室" value="普通教室" />
            <el-option label="实验室" value="实验室" />
            <el-option label="机房" value="机房" />
            <el-option label="多媒体" value="多媒体" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="可用" value="active" />
            <el-option label="不可用" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getClassroomList, createClassroom, updateClassroom, deleteClassroom, getBuildings } from '@/api/edu/classroom'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ building: '', room_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const buildingOptions = ref<string[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', building: '', room_no: '', capacity: 50, room_type: '普通教室', status: 'active' })

const formRules = {
  building: [{ required: true, message: '请输入教学楼', trigger: 'blur' }],
  room_no: [{ required: true, message: '请输入教室号', trigger: 'blur' }]
}

const getRoomTypeTag = (type: string) => {
  const map: Record<string, string> = { '普通教室': 'primary', '实验室': 'warning', '机房': 'info', '多媒体': 'success' }
  return map[type] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getClassroomList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchBuildings = async () => {
  try {
    const res = await getBuildings()
    buildingOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.building = ''; searchForm.room_type = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', building: '', room_no: '', capacity: 50, room_type: '普通教室', status: 'active' })
  dialogTitle.value = '新增教室'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑教室'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateClassroom(formData.id, formData); ElMessage.success('更新成功') }
    else { await createClassroom(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该教室吗？', '提示', { type: 'warning' })
    await deleteClassroom(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchBuildings(); fetchData() })
</script>

<style scoped lang="scss">
.classroom-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>