<template>
  <div class="schedule-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="班级">
            <el-select v-model="searchForm.class_id" placeholder="请选择" clearable @change="handleClassChange">
              <el-option v-for="c in classOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="周次">
            <el-input-number v-model="searchForm.week" :min="1" :max="20" controls-position="right" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">添加课表</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="class_id" label="班级" width="120">
          <template #default="{ row }">
            {{ getClassName(row.class_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="course_id" label="课程" width="120">
          <template #default="{ row }">
            {{ getCourseName(row.course_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="teacher_id" label="教师" width="100">
          <template #default="{ row }">
            {{ getTeacherName(row.teacher_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="day_of_week" label="星期" width="80">
          <template #default="{ row }">
            {{ ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][row.day_of_week - 1] }}
          </template>
        </el-table-column>
        <el-table-column prop="period" label="节次" width="60" />
        <el-table-column prop="room_id" label="教室" width="100">
          <template #default="{ row }">
            {{ getRoomName(row.room_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="week" label="周次" width="80" />
        <el-table-column prop="semester" label="学期" width="150" />
        <el-table-column label="操作" width="120" fixed="right">
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="formData.class_id" placeholder="请选择">
            <el-option v-for="c in classOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" prop="course_id">
          <el-select v-model="formData.course_id" placeholder="请选择">
            <el-option v-for="c in courseOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师" prop="teacher_id">
          <el-select v-model="formData.teacher_id" placeholder="请选择">
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="星期" prop="day_of_week">
          <el-select v-model="formData.day_of_week">
            <el-option label="周一" :value="1" />
            <el-option label="周二" :value="2" />
            <el-option label="周三" :value="3" />
            <el-option label="周四" :value="4" />
            <el-option label="周五" :value="5" />
            <el-option label="周六" :value="6" />
            <el-option label="周日" :value="7" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次" prop="period">
          <el-input-number v-model="formData.period" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="教室" prop="room_id">
          <el-select v-model="formData.room_id" clearable placeholder="请选择">
            <el-option v-for="r in roomOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="周次" prop="week">
          <el-input-number v-model="formData.week" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-input v-model="formData.semester" placeholder="如: 2025-2026第一学期" />
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
import { getScheduleList, createSchedule, updateSchedule, deleteSchedule } from '@/api/edu/schedule'
import { getClassOptions } from '@/api/edu/class'
import { getCourseOptions } from '@/api/edu/course'
import { getTeacherOptions } from '@/api/edu/grade'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ class_id: '', week: 1 })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const classOptions = ref<any[]>([])
const courseOptions = ref<any[]>([])
const teacherOptions = ref<any[]>([])
const roomOptions = ref<any[]>([{ value: '101', label: '101教室' }, { value: '102', label: '102教室' }, { value: '201', label: '201教室' }, { value: '202', label: '202教室' }])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', class_id: '', course_id: '', teacher_id: '', day_of_week: 1, period: 1, room_id: '', week: 1, semester: '' })

const formRules = {
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  teacher_id: [{ required: true, message: '请选择教师', trigger: 'change' }],
  day_of_week: [{ required: true, message: '请选择星期', trigger: 'change' }],
  period: [{ required: true, message: '请输入节次', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getScheduleList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchClasses = async () => {
  try {
    const res = await getClassOptions()
    classOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const fetchCourses = async () => {
  try {
    const res = await getCourseOptions()
    courseOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const fetchTeachers = async () => {
  try {
    const res = await getTeacherOptions()
    teacherOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const getClassName = (id: string) => classOptions.value.find(c => c.value === id)?.label || ''
const getCourseName = (id: string) => courseOptions.value.find(c => c.value === id)?.label || ''
const getTeacherName = (id: string) => teacherOptions.value.find(t => t.value === id)?.label || ''
const getRoomName = (id: string) => roomOptions.value.find(r => r.value === id)?.label || id

const handleClassChange = () => { fetchData() }
const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.class_id = ''; searchForm.week = 1; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', class_id: '', course_id: '', teacher_id: '', day_of_week: 1, period: 1, room_id: '', week: 1, semester: '' })
  dialogTitle.value = '添加课表'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑课表'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateSchedule(formData.id, formData); ElMessage.success('更新成功') }
    else { await createSchedule(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该课表记录吗？', '提示', { type: 'warning' })
    await deleteSchedule(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchClasses(); fetchCourses(); fetchTeachers(); fetchData() })
</script>

<style scoped lang="scss">
.schedule-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>