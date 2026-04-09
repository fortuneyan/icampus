<template>
  <div class="score-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="学生姓名">
            <el-input v-model="searchForm.student_name" placeholder="请输入" clearable />
          </el-form-item>
          <el-form-item label="课程">
            <el-select v-model="searchForm.course_id" placeholder="请选择" clearable>
              <el-option v-for="c in courseOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="考试类型">
            <el-select v-model="searchForm.exam_type" placeholder="请选择" clearable>
              <el-option label="期中考试" value="midterm" />
              <el-option label="期末考试" value="final" />
              <el-option label="月考" value="monthly" />
              <el-option label="平时测验" value="quiz" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">录入成绩</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="student_id" label="学生" width="100">
          <template #default="{ row }">
            {{ getStudentName(row.student_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="course_id" label="课程" width="120">
          <template #default="{ row }">
            {{ getCourseName(row.course_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="score" label="成绩" width="80">
          <template #default="{ row }">
            <span :class="{ 'score-high': row.score >= 90, 'score-low': row.score < 60 }">
              {{ row.score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="full_score" label="满分" width="60" />
        <el-table-column prop="exam_type" label="考试类型" width="100">
          <template #default="{ row }">
            {{ getExamTypeName(row.exam_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="semester" label="学期" width="120" />
        <el-table-column prop="exam_date" label="考试日期" width="120" />
        <el-table-column prop="rank" label="班级排名" width="80" />
        <el-table-column prop="comment" label="评语" />
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
        <el-form-item label="学生" prop="student_id">
          <el-select v-model="formData.student_id" filterable placeholder="请选择">
            <el-option v-for="s in studentOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" prop="course_id">
          <el-select v-model="formData.course_id" placeholder="请选择">
            <el-option v-for="c in courseOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="成绩" prop="score">
          <el-input-number v-model="formData.score" :min="0" :max="formData.full_score || 100" />
        </el-form-item>
        <el-form-item label="满分" prop="full_score">
          <el-input-number v-model="formData.full_score" :min="0" />
        </el-form-item>
        <el-form-item label="考试类型" prop="exam_type">
          <el-select v-model="formData.exam_type">
            <el-option label="期中考试" value="midterm" />
            <el-option label="期末考试" value="final" />
            <el-option label="月考" value="monthly" />
            <el-option label="平时测验" value="quiz" />
          </el-select>
        </el-form-item>
        <el-form-item label="考试日期" prop="exam_date">
          <el-date-picker v-model="formData.exam_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-input v-model="formData.semester" placeholder="如: 2025-2026第一学期" />
        </el-form-item>
        <el-form-item label="班级排名" prop="rank">
          <el-input-number v-model="formData.rank" :min="1" />
        </el-form-item>
        <el-form-item label="评语" prop="comment">
          <el-input v-model="formData.comment" type="textarea" :rows="2" />
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
import { getScoreList, createScore, updateScore, deleteScore } from '@/api/edu/score'
import { getStudentOptions } from '@/api/edu/student'
import { getCourseOptions } from '@/api/edu/course'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ student_name: '', course_id: '', exam_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const studentOptions = ref<any[]>([])
const courseOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', student_id: '', course_id: '', score: 0, full_score: 100, exam_type: 'midterm', exam_date: '', semester: '', rank: null, comment: '' })

const formRules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  score: [{ required: true, message: '请输入成绩', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getScoreList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchStudents = async () => {
  try {
    const res = await getStudentOptions()
    studentOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const fetchCourses = async () => {
  try {
    const res = await getCourseOptions()
    courseOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const getStudentName = (id: string) => studentOptions.value.find(s => s.value === id)?.label || ''
const getCourseName = (id: string) => courseOptions.value.find(c => c.value === id)?.label || ''
const getExamTypeName = (type: string) => ({ midterm: '期中', final: '期末', monthly: '月考', quiz: '测验' }[type] || type)

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.student_name = ''; searchForm.course_id = ''; searchForm.exam_type = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', student_id: '', course_id: '', score: 0, full_score: 100, exam_type: 'midterm', exam_date: '', semester: '', rank: null, comment: '' })
  dialogTitle.value = '录入成绩'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑成绩'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateScore(formData.id, formData); ElMessage.success('更新成功') }
    else { await createScore(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该成绩记录吗？', '提示', { type: 'warning' })
    await deleteScore(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchStudents(); fetchCourses(); fetchData() })
</script>

<style scoped lang="scss">
.score-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
  .score-high { color: #67c23a; font-weight: bold; }
  .score-low { color: #f56c6c; }
}
</style>