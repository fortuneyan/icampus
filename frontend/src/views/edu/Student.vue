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
        <el-table-column prop="gender" label="性别" width="60">
          <template #default="{ row }">
            {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="届别" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.enrollment_cohort" type="info">{{ row.enrollment_cohort }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="年级" width="120">
          <template #default="{ row }">
            <span>{{ row.grade_name || getGradeName(row.grade_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="class_id" label="班级" width="100">
          <template #default="{ row }">
            {{ getClassName(row.class_id) }}
          </template>
        </el-table-column>
        <el-table-column label="学籍状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.enrollment_status)">
              {{ getStatusText(row.enrollment_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
                <span class="more-link">
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item v-if="row.enrollment_status === 'in_school'" command="repeat">留级</el-dropdown-item>
                    <el-dropdown-item v-if="row.enrollment_status === 'in_school'" command="suspend">休学</el-dropdown-item>
                    <el-dropdown-item v-if="row.enrollment_status === 'suspended'" command="resume">复学</el-dropdown-item>
                    <el-dropdown-item v-if="row.enrollment_status === 'in_school'" command="graduate">毕业</el-dropdown-item>
                    <el-dropdown-item v-if="row.enrollment_status === 'in_school'" command="quit">退学</el-dropdown-item>
                    <el-dropdown-item command="history">变动历史</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
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
        <el-form-item label="入学年份">
          <el-input-number v-model="formData.enrollment_year" :min="2000" :max="2100" />
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
import { ArrowDown } from '@element-plus/icons-vue'
import { getStudentList, createStudent, updateStudent, deleteStudent } from '@/api/edu/student'
import { getGradeOptions } from '@/api/edu/grade'
import { getClassOptions } from '@/api/edu/class'
import { getConfig } from '@/api/settings'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ keyword: '', grade_id: '', class_id: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const formClassOptions = ref<any[]>([])
const gradeNames = ref<string[]>([])
const gradeLevelMap = ref<Record<string, number>>({})

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
    const grades = res.data || []
    gradeOptions.value = grades.map((g: any) => {
      if (g.grade_level) gradeLevelMap.value[g.value] = g.grade_level
      let label = g.label
      if (g.grade_level && g.grade_level >= 1 && g.grade_level <= 12 && gradeNames.value[g.grade_level - 1]) {
        label = gradeNames.value[g.grade_level - 1]
      }
      return { ...g, label }
    })
  } catch (e) { console.error(e) }
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

const getGradeName = (id: string) => {
  const grade = gradeOptions.value.find(g => g.value === id)
  const gradeLevel = gradeLevelMap.value[id]
  if (gradeLevel && gradeLevel >= 1 && gradeLevel <= 12 && gradeNames.value[gradeLevel - 1]) {
    return gradeNames.value[gradeLevel - 1]
  }
  return grade?.label || ''
}
const getClassName = (id: string) => classOptions.value.find(c => c.value === id)?.label || ''

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    'in_school': 'success',
    'suspended': 'warning',
    'graduated': 'info',
    'leave': 'danger',
    'repeating': 'warning',
  }
  return map[status || 'in_school'] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    'in_school': '在校',
    'suspended': '休学',
    'graduated': '已毕业',
    'leave': '离校',
    'repeating': '留级',
  }
  return map[status || 'in_school'] || '在校'
}

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

const handleCommand = async (command: string, row: any) => {
  switch (command) {
    case 'edit':
      handleEdit(row)
      break
    case 'repeat':
      try {
        await ElMessageBox.confirm(`确定要将 ${row.name} 留级吗？`, '留级确认', { type: 'warning' })
        await request.post(`/enrollment/students/${row.id}/repeat`)
        ElMessage.success('留级成功')
        fetchData()
      } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
      break
    case 'suspend':
      try {
        await ElMessageBox.confirm(`确定要将 ${row.name} 休学吗？`, '休学确认', { type: 'warning' })
        await request.post(`/enrollment/students/${row.id}/suspend?reason=因故休学`)
        ElMessage.success('休学成功')
        fetchData()
      } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
      break
    case 'resume':
      try {
        await request.post(`/enrollment/students/${row.id}/resume`)
        ElMessage.success('复学成功')
        fetchData()
      } catch (e: any) { ElMessage.error(e.message || '操作失败') }
      break
    case 'graduate':
      try {
        await ElMessageBox.confirm(`确定要将 ${row.name} 标记为毕业吗？`, '毕业确认', { type: 'warning' })
        await request.post(`/enrollment/students/${row.id}/graduate`)
        ElMessage.success('毕业办理成功')
        fetchData()
      } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
      break
    case 'quit':
      try {
        await ElMessageBox.confirm(`确定要将 ${row.name} 退学吗？`, '退学确认', { type: 'warning' })
        await request.post(`/enrollment/students/${row.id}/quit?reason=主动退学`)
        ElMessage.success('退学办理成功')
        fetchData()
      } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
      break
    case 'history':
      try {
        const res = await request.get(`/enrollment/students/${row.id}/history`)
        const changes = res.data?.changes || []
        let msg = `${row.name} 学籍变动历史:\n`
        changes.forEach((c: any) => {
          msg += `${c.change_date?.slice(0,10)} ${c.change_type_name} ${c.reason || ''}\n`
        })
        if (changes.length === 0) msg += '暂无变动记录'
        ElMessageBox.alert(msg, '学籍变动历史')
      } catch (e: any) { ElMessage.error(e.message || '获取失败') }
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

onMounted(() => { fetchGradeNames(); fetchGrades(); fetchClasses(); fetchData() })
</script>

<style scoped lang="scss">
.student-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }

  .action-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .more-link {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: #409eff;
    &:hover { color: #66b1ff; }
  }

  .el-icon--right {
    margin-left: 2px;
  }
}
</style>