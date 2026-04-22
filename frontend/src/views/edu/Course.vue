<template>
  <div class="course-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="课程名称">
            <el-input v-model="searchForm.name" placeholder="请输入" clearable />
          </el-form-item>
          <el-form-item label="课程类型">
            <el-select v-model="searchForm.category" placeholder="请选择" clearable>
              <el-option label="必修" value="required" />
              <el-option label="选修" value="elective" />
              <el-option label="校本课程" value="school" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增课程</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="课程名称" width="150" />
        <el-table-column prop="code" label="课程代码" width="100" />
        <el-table-column prop="course_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.course_type === 'REQUIRED' ? 'danger' : 'success'">
              {{ row.course_type === 'REQUIRED' ? '必修' : '选修' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="credits" label="学分" width="80" />
        <el-table-column prop="hours" label="课时" width="80" />
        <el-table-column label="授课教师" width="150">
          <template #default="{ row }">
            {{ getTeacherName(row.teacher_ids) }}
          </template>
        </el-table-column>
        <el-table-column prop="semester" label="适用学期" width="120" />
        <el-table-column label="适用年级" width="120">
          <template #default="{ row }">
            {{ getGradeLevelsText(row.grade_levels) }}
          </template>
        </el-table-column>
        <el-table-column label="前置课程" width="150">
          <template #default="{ row }">
            {{ getPrerequisiteNames(row.prerequisite_course_ids) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="课程简介" />
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
        <el-form-item label="课程名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="课程代码" prop="code">
          <el-input v-model="formData.code" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="课程类型" prop="category">
          <el-select v-model="formData.category">
            <el-option label="必修" value="required" />
            <el-option label="选修" value="elective" />
            <el-option label="校本课程" value="school" />
          </el-select>
        </el-form-item>
        <el-form-item label="学分" prop="credits">
          <el-input-number v-model="formData.credits" :min="0" :max="10" />
        </el-form-item>
        <el-form-item label="课时" prop="hours">
          <el-input-number v-model="formData.hours" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="授课教师" prop="teacher_ids">
          <el-select v-model="formData.teacher_ids" multiple clearable placeholder="请选择教师">
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用年级" prop="grade_levels">
          <el-select v-model="formData.grade_levels" multiple clearable placeholder="请选择适用年级">
            <el-option v-for="g in gradeLevelOptions" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-select v-model="formData.course_type" placeholder="请选择">
            <el-option label="必修" value="REQUIRED" />
            <el-option label="选修" value="ELECTIVE" />
          </el-select>
        <el-form-item label="前置课程" prop="prerequisite_course_ids">
          <el-select v-model="formData.prerequisite_course_ids" multiple clearable placeholder="请选择前置课程">
            <el-option v-for="c in courseOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用学期" prop="semester">
          <el-input v-model="formData.semester" placeholder="如: 第一学期" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程简介" prop="description">
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
import { getCourseList, createCourse, updateCourse, deleteCourse } from '@/api/edu/course'
import { getTeacherOptions, getGradeOptions } from '@/api/edu/grade'
import { getConfig } from '@/api/settings'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ name: '', category: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const teacherOptions = ref<any[]>([])
const gradeLevelOptions = ref<any[]>([])
const courseOptions = ref<any[]>([])
const gradeNames = ref<string[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({
  id: '', name: '', code: '', category: 'required', credits: 2, hours: 32,
  teacher_ids: [] as string[], grade_levels: [] as number[], course_type: 'ELECTIVE',
  prerequisite_course_ids: [] as string[], semester: '', status: 'active', description: ''
})

const formRules = {
  name: [{ required: true, message: '请输入课程名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入课程代码', trigger: 'blur' }],
  category: [{ required: true, message: '请选择课程类型', trigger: 'change' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getCourseList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
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

const fetchCourses = async () => {
  try {
    const res = await getCourseList({ page: 1, page_size: 1000 })
    courseOptions.value = (res.data.items || []).map((c: any) => ({ value: c.id, label: c.name }))
  } catch (e) { console.error(e) }
}

const fetchGradeLevels = async () => {
  try {
    const res = await getGradeOptions()
    const grades = res.data || []
    gradeLevelOptions.value = grades.map((g: any) => ({
      value: g.grade_level,
      label: gradeNames.value[g.grade_level - 1] || `年级${g.grade_level}`
    }))
  } catch (e) { console.error(e) }
}

const getTeacherName = (teacherIds: string[]) => {
  if (!teacherIds || teacherIds.length === 0) return '-'
  return teacherIds.map((id: string) => teacherOptions.value.find(t => t.value === id)?.label || '').join(', ')
}

const getGradeLevelsText = (levels: number[]) => {
  if (!levels || levels.length === 0) return '-'
  return levels.map((l: number) => gradeNames.value[l - 1] || `年级${l}`).join(', ')
}

const getPrerequisiteNames = (ids: string[]) => {
  if (!ids || ids.length === 0) return '-'
  return ids.map((id: string) => courseOptions.value.find(c => c.value === id)?.label || '').join(', ')
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
const handleReset = () => { searchForm.name = ''; searchForm.category = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, {
    id: '', name: '', code: '', category: 'required', credits: 2, hours: 32,
    teacher_ids: [], grade_levels: [], course_type: 'ELECTIVE', prerequisite_course_ids: [],
    semester: '', status: 'active', description: ''
  })
  dialogTitle.value = '新增课程'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑课程'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateCourse(formData.id, formData); ElMessage.success('更新成功') }
    else { await createCourse(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该课程吗？', '提示', { type: 'warning' })
    await deleteCourse(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(async () => {
  await fetchGradeNames()
  fetchTeachers()
  fetchCourses()
  fetchGradeLevels()
  fetchData()
})
</script>

<style scoped lang="scss">
.course-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>