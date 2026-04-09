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
        <el-table-column prop="category" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.category === 'required' ? 'danger' : 'success'">
              {{ row.category === 'required' ? '必修' : row.category === 'elective' ? '选修' : '校本' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="credits" label="学分" width="80" />
        <el-table-column prop="hours" label="课时" width="80" />
        <el-table-column prop="teacher_id" label="授课教师" width="120">
          <template #default="{ row }">
            {{ getTeacherName(row.teacher_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="semester" label="适用学期" width="120" />
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
        <el-form-item label="授课教师" prop="teacher_id">
          <el-select v-model="formData.teacher_id" clearable placeholder="请选择">
            <el-option v-for="t in teacherOptions" :key="t.value" :label="t.label" :value="t.value" />
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
import { getTeacherOptions } from '@/api/edu/grade'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ name: '', category: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const teacherOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', name: '', code: '', category: 'required', credits: 2, hours: 32, teacher_id: '', semester: '', status: 'active', description: '' })

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

const getTeacherName = (id: string) => teacherOptions.value.find(t => t.value === id)?.label || ''

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.name = ''; searchForm.category = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', name: '', code: '', category: 'required', credits: 2, hours: 32, teacher_id: '', semester: '', status: 'active', description: '' })
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

onMounted(() => { fetchTeachers(); fetchData() })
</script>

<style scoped lang="scss">
.course-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>