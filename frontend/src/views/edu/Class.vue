<template>
  <div class="class-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="班级名称">
            <el-input v-model="searchForm.name" placeholder="请输入" clearable />
          </el-form-item>
          <el-form-item label="年级">
            <el-select v-model="searchForm.grade_id" placeholder="请选择" clearable @change="handleGradeChange">
              <el-option v-for="g in gradeOptions" :key="g.value" :label="g.label" :value="g.value" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增班级</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="班级名称" width="120" />
        <el-table-column prop="code" label="班级代码" width="100" />
        <el-table-column prop="grade_id" label="年级" width="120">
          <template #default="{ row }">
            {{ getGradeName(row.grade_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="head_teacher_id" label="班主任" width="100">
          <template #default="{ row }">
            {{ getTeacherName(row.head_teacher_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="student_count" label="学生人数" width="100" />
        <el-table-column prop="room_no" label="教室" width="100" />
        <el-table-column prop="academic_year" label="学年" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '在用' : '已毕业' }}
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="班级名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="班级代码" prop="code">
          <el-input v-model="formData.code" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="所属年级" prop="grade_id">
          <el-select v-model="formData.grade_id" @change="handleFormGradeChange">
            <el-option v-for="g in gradeOptions" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="班主任" prop="head_teacher_id">
          <el-select v-model="formData.head_teacher_id" clearable placeholder="请选择">
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="教室" prop="room_no">
          <el-input v-model="formData.room_no" />
        </el-form-item>
        <el-form-item label="学年" prop="academic_year">
          <el-input v-model="formData.academic_year" placeholder="如: 2025-2026" />
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-select v-model="formData.semester">
            <el-option label="第一学期" value="第一学期" />
            <el-option label="第二学期" value="第二学期" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="在用" value="active" />
            <el-option label="已毕业" value="graduated" />
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
import { getClassList, createClass, updateClass, deleteClass } from '@/api/edu/class'
import { getGradeOptions, getTeacherOptions } from '@/api/edu/grade'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ name: '', grade_id: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const gradeOptions = ref<any[]>([])
const teacherOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', name: '', code: '', grade_id: '', head_teacher_id: '', room_no: '', academic_year: '', semester: '第一学期', status: 'active' })

const formRules = {
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入班级代码', trigger: 'blur' }],
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getClassList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchGrades = async () => {
  try {
    const res = await getGradeOptions()
    gradeOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const fetchTeachers = async () => {
  try {
    const res = await getTeacherOptions()
    teacherOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const getGradeName = (id: string) => gradeOptions.value.find(g => g.value === id)?.label || ''
const getTeacherName = (id: string) => teacherOptions.value.find(t => t.value === id)?.label || ''

const handleGradeChange = () => { fetchData() }
const handleFormGradeChange = () => { formData.head_teacher_id = '' }

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.name = ''; searchForm.grade_id = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', name: '', code: '', grade_id: '', head_teacher_id: '', room_no: '', academic_year: '', semester: '第一学期', status: 'active' })
  dialogTitle.value = '新增班级'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑班级'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateClass(formData.id, formData); ElMessage.success('更新成功') }
    else { await createClass(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该班级吗？', '提示', { type: 'warning' })
    await deleteClass(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchGrades(); fetchTeachers(); fetchData() })
</script>

<style scoped lang="scss">
.class-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>