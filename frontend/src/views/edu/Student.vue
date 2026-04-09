<template>
  <div class="student-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="学号/姓名" clearable />
          </el-form-item>
          <el-form-item label="年级">
            <el-select v-model="searchForm.grade_id" placeholder="请选择" clearable @change="handleGradeChange">
              <el-option v-for="g in gradeOptions" :key="g.value" :label="g.label" :value="g.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select v-model="searchForm.class_id" placeholder="请选择" clearable>
              <el-option v-for="c in classOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="grade_id" label="年级" width="100">
          <template #default="{ row }">
            {{ getGradeName(row.grade_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="class_id" label="班级" width="100">
          <template #default="{ row }">
            {{ getClassName(row.class_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '在读' : '离校' }}
            </el-tag>
          </template>
        </el-table-column>
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
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-form-item label="学号" prop="student_no">
          <el-input v-model="formData.student_no" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="formData.gender">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" />
        </el-form-item>
        <el-form-item label="年级" prop="grade_id">
          <el-select v-model="formData.grade_id" @change="handleFormGradeChange">
            <el-option v-for="g in gradeOptions" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="formData.class_id">
            <el-option v-for="c in formClassOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="在读" value="active" />
            <el-option label="离校" value="inactive" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getStudentList, createStudent, updateStudent, deleteStudent } from '@/api/edu/student'
import { getGradeOptions } from '@/api/edu/grade'
import { getClassOptions } from '@/api/edu/class'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ keyword: '', grade_id: '', class_id: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const formClassOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', student_no: '', name: '', gender: '', phone: '', grade_id: '', class_id: '', status: 'active' })

const formRules = {
  student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getStudentList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
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

const fetchClasses = async (gradeId?: string) => {
  try {
    const res = await getClassOptions(gradeId)
    classOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const handleGradeChange = () => {
  searchForm.class_id = ''
  fetchClasses(searchForm.grade_id)
}

const handleFormGradeChange = () => {
  formData.class_id = ''
  if (formData.grade_id) {
    getClassOptions(formData.grade_id).then(res => { formClassOptions.value = res.data || [] })
  }
}

const getGradeName = (id: string) => gradeOptions.value.find(g => g.value === id)?.label || ''
const getClassName = (id: string) => classOptions.value.find(c => c.value === id)?.label || ''

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.keyword = ''; searchForm.grade_id = ''; searchForm.class_id = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', student_no: '', name: '', gender: '', phone: '', grade_id: '', class_id: '', status: 'active' })
  dialogTitle.value = '新增学生'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  if (row.grade_id) getClassOptions(row.grade_id).then(res => { formClassOptions.value = res.data || [] })
  dialogTitle.value = '编辑学生'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateStudent(formData.id, formData); ElMessage.success('更新成功') }
    else { await createStudent(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该学生吗？', '提示', { type: 'warning' })
    await deleteStudent(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchGrades(); fetchClasses(); fetchData() })
</script>

<style scoped lang="scss">
.student-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>