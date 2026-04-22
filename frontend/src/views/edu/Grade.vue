<template>
  <div class="grade-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="年级名称">
            <el-input v-model="searchForm.name" placeholder="请输入" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增年级</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column label="名称" width="120">
          <template #default="{ row }">
            {{ getGradeName(row.grade_level) }}
          </template>
        </el-table-column>
        <el-table-column prop="name" label="年级名称" width="150" />
        <el-table-column prop="code" label="年级代码" width="120" />
        <el-table-column prop="academic_year" label="学年" width="120" />
        <el-table-column prop="head_teacher_id" label="年级主任" width="120">
          <template #default="{ row }">
            {{ getTeacherName(row.head_teacher_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="student_count" label="学生人数" width="100" />
        <el-table-column prop="class_count" label="班级数" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '在用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" />
        <el-table-column label="操作" width="180" fixed="right">
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
        <el-form-item label="年级" prop="grade_level">
          <el-select v-model="formData.grade_level" placeholder="请选择">
            <el-option v-for="name in gradeNames" :key="gradeNames.indexOf(name)" :label="name" :value="gradeNames.indexOf(name) + 1" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="年级代码" prop="code">
          <el-input v-model="formData.code" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="学年" prop="academic_year">
          <el-input v-model="formData.academic_year" placeholder="如: 2025-2026" />
        </el-form-item>
        <el-form-item label="年级主任" prop="head_teacher_id">
          <el-select v-model="formData.head_teacher_id" clearable placeholder="请选择">
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="在用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
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
import { getGradeList, createGrade, updateGrade, deleteGrade, getGradeOptions, getTeacherOptions } from '@/api/edu/grade'
import { getConfig } from '@/api/settings'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ name: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const teacherOptions = ref<any[]>([])
const gradeNames = ref<string[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', grade_level: '', name: '', code: '', academic_year: '', head_teacher_id: '', status: 'active', description: '' })

const formRules = {
  grade_level: [{ required: true, message: '请选择年级', trigger: 'change' }],
  name: [{ required: true, message: '请输入年级名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入年级代码', trigger: 'blur' }],
  academic_year: [{ required: true, message: '请输入学年', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getGradeList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchTeachers = async () => {
  try {
    const res = await getTeacherOptions()
    teacherOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const getTeacherName = (id: string) => teacherOptions.value.find(t => t.value === id)?.label || ''

const getGradeName = (gradeLevel: number) => {
  if (!gradeLevel || gradeLevel < 1) return '-'
  return gradeNames.value[gradeLevel - 1] || `年级${gradeLevel}`
}

const fetchGradeNames = async () => {
  try {
    const res = await getConfig('grade_names')
    if (res.code === 200 && res.data) {
      const setting = Array.isArray(res.data) ? res.data.find((s: any) => s.setting_key === 'grade_names') : res.data
      if (setting?.setting_value) {
        gradeNames.value = setting.setting_value.split(',')
      }
    }
  } catch (e) { console.error(e) }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.name = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', grade_level: '', name: '', code: '', academic_year: '', head_teacher_id: '', status: 'active', description: '' })
  dialogTitle.value = '新增年级'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑年级'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    const payload: any = { ...formData }
    if (payload.grade_level === '' || payload.grade_level === null) {
      delete payload.grade_level
    }
    if (formData.id) { await updateGrade(formData.id, payload); ElMessage.success('更新成功') }
    else { await createGrade(payload); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该年级吗？', '提示', { type: 'warning' })
    await deleteGrade(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchGradeNames(); fetchTeachers(); fetchData() })
</script>

<style scoped lang="scss">
.grade-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>