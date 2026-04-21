<template>
  <div class="homework-management">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="作业管理" name="homework">
        <el-card>
          <div class="toolbar">
            <el-form :inline="true" :model="searchForm">
              <el-form-item label="状态">
                <el-select v-model="searchForm.status" placeholder="请选择" clearable>
                  <el-option label="草稿" value="draft" />
                  <el-option label="已发布" value="published" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSearch">搜索</el-button>
                <el-button @click="handleReset">重置</el-button>
                <el-button type="success" @click="handleAdd">布置作业</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-row :gutter="20" class="stats-row">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.draft || 0 }}</div>
                <div class="stat-label">待发布</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.published || 0 }}</div>
                <div class="stat-label">已发布</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.submitted || 0 }}</div>
                <div class="stat-label">已提交</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.wrong_questions || 0 }}</div>
                <div class="stat-label">错题数</div>
              </div>
            </el-col>
          </el-row>

          <el-table :data="tableData" v-loading="loading" stripe>
            <el-table-column prop="title" label="作业标题" width="200" />
            <el-table-column prop="homework_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.homework_type === 'online'" type="success">在线</el-tag>
                <el-tag v-else type="info">线下</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_score" label="总分" width="80" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'draft'" type="info">草稿</el-tag>
                <el-tag v-else type="success">已发布</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
                <el-button v-if="row.status === 'draft'" type="success" link @click="handlePublish(row)">发布</el-button>
                <el-button type="primary" link @click="handleViewSubmissions(row)">查看提交</el-button>
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
      </el-tab-pane>

      <el-tab-pane label="错题本" name="wrong">
        <el-card>
          <div class="toolbar">
            <el-form :inline="true">
              <el-form-item label="掌握状态">
                <el-select v-model="wrongFilter.is_mastered" placeholder="请选择" clearable>
                  <el-option label="未掌握" :value="false" />
                  <el-option label="已掌握" :value="true" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="fetchWrongQuestions">搜索</el-button>
                <el-button type="success" @click="handleAddWrong">添加错题</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-table :data="wrongTableData" v-loading="wrongLoading" stripe>
            <el-table-column prop="question_content" label="题目内容" />
            <el-table-column prop="question_type" label="题型" width="100" />
            <el-table-column prop="correct_answer" label="正确答案" width="120" />
            <el-table-column prop="is_mastered" label="掌握状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_mastered" type="success">已掌握</el-tag>
                <el-tag v-else type="danger">未掌握</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_count" label="复习次数" width="100" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="success" link @click="handleMarkMastered(row)">标记掌握</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="wrongPagination.page"
              v-model:page-size="wrongPagination.pageSize"
              :total="wrongPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="fetchWrongQuestions"
              @current-change="fetchWrongQuestions"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="家长反馈" name="feedback">
        <el-card>
          <el-table :data="feedbackTableData" v-loading="feedbackLoading" stripe>
            <el-table-column prop="homework_title" label="作业" width="200" />
            <el-table-column prop="feedback_type" label="反馈类型" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.feedback_type === 'question'" type="warning">问题</el-tag>
                <el-tag v-else type="info">建议</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" />
            <el-table-column prop="is_resolved" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_resolved" type="success">已解决</el-tag>
                <el-tag v-else type="warning">待处理</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="反馈时间" width="180" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="课程">
          <el-select v-model="formData.course_id" placeholder="请选择课程" @change="onCourseChange">
            <el-option v-for="c in courseOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="formData.grade_id" placeholder="请选择年级" @change="onGradeChange">
            <el-option v-for="g in gradeOptions" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="formData.class_id" placeholder="请选择班级" multiple>
            <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="作业标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="作业类型">
          <el-radio-group v-model="formData.homework_type">
            <el-radio value="online">在线作业</el-radio>
            <el-radio value="offline">线下作业</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="作业内容">
          <el-input v-model="formData.content" type="textarea" :rows="4" placeholder="请输入作业内容" />
        </el-form-item>
        <el-form-item label="总分">
          <el-input-number v-model="formData.total_score" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="提交截止">
          <el-date-picker v-model="formData.submit_end" type="datetime" placeholder="选择时间" />
        </el-form-item>
        <el-form-item label="发送通知">
          <el-switch v-model="formData.notify_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="submissionDialogVisible" title="提交记录" width="800px">
      <el-table :data="submissionTableData" stripe>
        <el-table-column prop="student_name" label="学生" width="120" />
        <el-table-column prop="content" label="提交内容" />
        <el-table-column prop="score" label="得分" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'submitted'" type="warning">待批改</el-tag>
            <el-tag v-else type="success">已批改</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleGrade(row)">批改</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="gradeDialogVisible" title="批改作业" width="400px">
      <el-form label-width="80px">
        <el-form-item label="得分">
          <el-input-number v-model="gradeData.score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="评语">
          <el-input v-model="gradeData.feedback" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="gradeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGradeSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import {
  getHomeworks,
  createHomework,
  updateHomework,
  getSubmissions,
  gradeSubmission,
  getWrongQuestions,
  createWrongQuestion,
  getHomeworkStats
} from '@/api/homework'

const activeTab = ref('homework')

const searchForm = reactive({ status: '' })
const tableData = ref([])
const loading = ref(false)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const stats = reactive({ draft: 0, published: 0, submitted: 0, wrong_questions: 0 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const formData = reactive({
  id: '',
  course_id: '',
  grade_id: '',
  class_id: [] as string[],
  title: '',
  content: '',
  homework_type: 'online',
  total_score: 100,
  submit_end: '',
  notify_enabled: true
})
const formRules = {
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }],
  title: [{ required: true, message: '请输入作业标题', trigger: 'blur' }]
}

const courseOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])

const loadOptions = async () => {
  try {
    const userRes = await request.get('/auth/me')
    const userId = userRes.data?.id
    
    const deptRes = await request.get(`/system/users/${userId}/profile`)
    const profile = deptRes.data
    
    if (profile?.courses?.length) {
      courseOptions.value = profile.courses
    }
    if (profile?.grades?.length) {
      gradeOptions.value = profile.grades
    }
    if (profile?.classes?.length) {
      classOptions.value = profile.classes
    }
  } catch (e) {
    console.error('加载选项失败', e)
  }
}

const onCourseChange = () => {
  formData.class_id = []
}

const onGradeChange = () => {
  formData.class_id = []
}

const wrongFilter = reactive({ is_mastered: null as boolean | null })
const wrongTableData = ref([])
const wrongLoading = ref(false)
const wrongPagination = reactive({ page: 1, pageSize: 20, total: 0 })

const feedbackTableData = ref([])
const feedbackLoading = ref(false)

const submissionDialogVisible = ref(false)
const submissionTableData = ref([])
const currentHomeworkId = ref('')

const gradeDialogVisible = ref(false)
const currentSubmissionId = ref('')
const gradeData = reactive({ score: 0, feedback: '' })

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getHomeworks({
      status: searchForm.status || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) {
    ElMessage.error('获取作业列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getHomeworkStats()
    Object.assign(stats, res.data)
  } catch (e) {
    console.error('获取统计失败', e)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.status = ''
  handleSearch()
}

const handleAdd = () => {
  dialogTitle.value = '布置作业'
  formData.id = ''
  formData.title = ''
  formData.content = ''
  formData.homework_type = 'online'
  formData.total_score = 100
  formData.submit_end = ''
  formData.notify_enabled = true
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑作业'
  formData.id = row.id
  formData.title = row.title
  formData.content = row.content
  formData.homework_type = row.homework_type
  formData.total_score = row.total_score
  formData.notify_enabled = true
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (formData.id) {
          await updateHomework(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await createHomework(formData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchData()
        fetchStats()
      } catch (e: any) {
        ElMessage.error(e.message || '操作失败')
      }
    }
  })
}

const handlePublish = async (row: any) => {
  try {
    await updateHomework(row.id, { status: 'published' })
    ElMessage.success('发布成功')
    fetchData()
    fetchStats()
  } catch (e) {
    ElMessage.error('发布失败')
  }
}

const handleViewSubmissions = async (row: any) => {
  currentHomeworkId.value = row.id
  try {
    const res = await getSubmissions(row.id)
    submissionTableData.value = res.data
    submissionDialogVisible.value = true
  } catch (e) {
    ElMessage.error('获取提交记录失败')
  }
}

const handleGrade = (row: any) => {
  currentSubmissionId.value = row.id
  gradeData.score = row.score || 0
  gradeData.feedback = row.feedback || ''
  gradeDialogVisible.value = true
}

const handleGradeSubmit = async () => {
  try {
    await gradeSubmission(currentSubmissionId.value, gradeData.score, gradeData.feedback)
    ElMessage.success('批改成功')
    gradeDialogVisible.value = false
    handleViewSubmissions({ id: currentHomeworkId.value })
  } catch (e) {
    ElMessage.error('批改失败')
  }
}

const fetchWrongQuestions = async () => {
  wrongLoading.value = true
  try {
    const res = await getWrongQuestions({
      is_mastered: wrongFilter.is_mastered ?? undefined,
      page: wrongPagination.page,
      page_size: wrongPagination.pageSize
    })
    wrongTableData.value = res.data.items
    wrongPagination.total = res.data.total
  } catch (e) {
    ElMessage.error('获取错题列表失败')
  } finally {
    wrongLoading.value = false
  }
}

const handleAddWrong = () => {
  ElMessage.info('添加错题功能开发中')
}

const handleMarkMastered = async (row: any) => {
  ElMessage.info('标记掌握功能开发中')
}

const handleTabChange = (tab: string) => {
  if (tab === 'homework') {
    fetchData()
    fetchStats()
  } else if (tab === 'wrong') {
    fetchWrongQuestions()
  }
}

onMounted(() => {
  fetchData()
  fetchStats()
  loadOptions()
})
</script>

<style scoped>
.homework-management {
  padding: 16px;
}
.toolbar {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.stats-row {
  margin-bottom: 20px;
}
.stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}
.stat-label {
  margin-top: 8px;
  color: #909399;
}
</style>