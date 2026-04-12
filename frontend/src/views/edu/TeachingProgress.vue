<template>
  <div class="teaching-progress-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>教学进度跟踪</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增进度
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="课程">
          <el-input v-model="searchForm.keyword" placeholder="课程名称" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable style="width: 120px">
            <el-option
              v-for="item in STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table v-loading="loading" :data="tableData" stripe border style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="course_id" label="课程ID" width="80" />
        <el-table-column prop="chapter" label="章节" min-width="150" show-overflow-tooltip />
        <el-table-column prop="unit_name" label="单元" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress_percentage" label="完成度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress_percentage || 0" :color="getProgressColor(row.progress_percentage)" />
          </template>
        </el-table-column>
        <el-table-column prop="planned_start_date" label="计划开始" width="110">
          <template #default="{ row }">
            {{ formatDate(row.planned_start_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="planned_end_date" label="计划完成" width="110">
          <template #default="{ row }">
            {{ formatDate(row.planned_end_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="planned_hours" label="计划课时" width="90" />
        <el-table-column prop="actual_hours" label="实际用时" width="90" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课程ID" prop="course_id">
              <el-input-number v-model="formData.course_id" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教师ID">
              <el-input-number v-model="formData.teacher_id" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="章节序号">
              <el-input-number v-model="formData.chapter_number" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="章节名称">
              <el-input v-model="formData.chapter" placeholder="请输入章节名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="单元序号">
              <el-input-number v-model="formData.unit_number" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单元名称">
              <el-input v-model="formData.unit_name" placeholder="请输入单元名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计划开始">
              <el-date-picker
                v-model="formData.planned_start_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划完成">
              <el-date-picker
                v-model="formData.planned_end_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计划课时">
              <el-input-number v-model="formData.planned_hours" :min="0" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际用时">
              <el-input-number v-model="formData.actual_hours" :min="0" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="状态">
          <el-select v-model="formData.status" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="item in STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="完成百分比">
          <el-slider v-model="formData.progress_percentage" :min="0" :max="100" show-input />
        </el-form-item>

        <el-form-item label="教学重点">
          <el-input v-model="formData.key_points" type="textarea" :rows="2" placeholder="请输入教学重点" />
        </el-form-item>

        <el-form-item label="教学难点">
          <el-input v-model="formData.difficult_points" type="textarea" :rows="2" placeholder="请输入教学难点" />
        </el-form-item>

        <el-form-item label="教学目标">
          <el-input v-model="formData.teaching_goals" type="textarea" :rows="2" placeholder="请输入教学目标" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="formData.notes" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="viewVisible" title="进度详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="课程ID">{{ viewData.course_id }}</el-descriptions-item>
        <el-descriptions-item label="教师ID">{{ viewData.teacher_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="章节">{{ viewData.chapter || '-' }}</el-descriptions-item>
        <el-descriptions-item label="单元">{{ viewData.unit_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(viewData.status)" size="small">
            {{ getStatusLabel(viewData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="完成度">{{ viewData.progress_percentage || 0 }}%</el-descriptions-item>
        <el-descriptions-item label="计划开始">{{ formatDate(viewData.planned_start_date) }}</el-descriptions-item>
        <el-descriptions-item label="计划完成">{{ formatDate(viewData.planned_end_date) }}</el-descriptions-item>
        <el-descriptions-item label="实际开始">{{ formatDate(viewData.actual_start_date) }}</el-descriptions-item>
        <el-descriptions-item label="实际完成">{{ formatDate(viewData.actual_end_date) }}</el-descriptions-item>
        <el-descriptions-item label="计划课时">{{ viewData.planned_hours || 0 }}</el-descriptions-item>
        <el-descriptions-item label="实际用时">{{ viewData.actual_hours || 0 }}</el-descriptions-item>
        <el-descriptions-item label="教学重点" :span="2">{{ viewData.key_points || '-' }}</el-descriptions-item>
        <el-descriptions-item label="教学难点" :span="2">{{ viewData.difficult_points || '-' }}</el-descriptions-item>
        <el-descriptions-item label="教学目标" :span="2">{{ viewData.teaching_goals || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ viewData.notes || '-' }}</el-descriptions-item>
        <el-descriptions-item label="延误原因" :span="2">{{ viewData.delay_reason || '-' }}</el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEditFromView">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 进度更新弹窗 -->
    <el-dialog v-model="progressDialogVisible" title="更新进度" width="400px">
      <el-form label-width="100px">
        <el-form-item label="当前进度">
          <el-progress :percentage="currentProgress" :color="getProgressColor(currentProgress)" />
        </el-form-item>
        <el-form-item label="新进度">
          <el-slider v-model="newProgress" :min="0" :max="100" show-input />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="progressDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateProgress" :loading="progressLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getTeachingProgressList,
  createTeachingProgress,
  updateTeachingProgress,
  deleteTeachingProgress,
  updateProgressPercentage,
  STATUS_OPTIONS,
  getStatusLabel,
  getStatusType,
  type TeachingProgress
} from '@/api/edu/teaching_progress'

// 表格数据
const loading = ref(false)
const tableData = ref<TeachingProgress[]>([])
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 搜索表单
const searchForm = reactive({
  keyword: '',
  status: ''
})

// 弹窗相关
const dialogVisible = ref(false)
const viewVisible = ref(false)
const progressDialogVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const progressLoading = ref(false)
const formRef = ref<FormInstance>()
const currentProgressId = ref<number>()
const currentProgress = ref(0)
const newProgress = ref(0)

// 表单数据
const formData = reactive<Partial<TeachingProgress>>({
  course_id: undefined,
  teacher_id: undefined,
  class_id: undefined,
  chapter: '',
  chapter_number: undefined,
  unit_name: '',
  unit_number: undefined,
  planned_start_date: '',
  planned_end_date: '',
  planned_hours: 0,
  actual_hours: 0,
  status: 'not_started',
  progress_percentage: 0,
  key_points: '',
  difficult_points: '',
  teaching_goals: '',
  notes: ''
})

// 查看数据
const viewData = ref<TeachingProgress>({})

// 表单验证规则
const formRules: FormRules = {
  course_id: [{ required: true, message: '请输入课程ID', trigger: 'blur' }]
}

// 获取列表数据
async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword || undefined,
      status: searchForm.status || undefined
    }
    const res = await getTeachingProgressList(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('获取教学进度列表失败', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchData()
}

// 重置
function handleReset() {
  searchForm.keyword = ''
  searchForm.status = ''
  pagination.page = 1
  fetchData()
}

// 分页
function handleSizeChange() {
  fetchData()
}

function handlePageChange() {
  fetchData()
}

// 新增
function handleAdd() {
  dialogTitle.value = '新增教学进度'
  resetForm()
  dialogVisible.value = true
}

// 编辑
function handleEdit(row: TeachingProgress) {
  dialogTitle.value = '编辑教学进度'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 查看
function handleView(row: TeachingProgress) {
  Object.assign(viewData, row)
  viewVisible.value = true
}

// 查看时编辑
function handleEditFromView() {
  handleEdit(viewData.value)
  viewVisible.value = false
}

// 删除
async function handleDelete(row: TeachingProgress) {
  try {
    await ElMessageBox.confirm('确定删除该教学进度吗？', '提示', { type: 'warning' })
    await deleteTeachingProgress(row.id!)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (formData.id) {
          await updateTeachingProgress(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await createTeachingProgress(formData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('保存失败', error)
        ElMessage.error('保存失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 更新进度
function handleUpdateProgressBtn(row: TeachingProgress) {
  currentProgressId.value = Number(row.id)
  currentProgress.value = row.progress_percentage || 0
  newProgress.value = row.progress_percentage || 0
  progressDialogVisible.value = true
}

async function handleUpdateProgress() {
  if (!currentProgressId.value) return

  progressLoading.value = true
  try {
    await updateProgressPercentage(currentProgressId.value, newProgress.value)
    ElMessage.success('进度更新成功')
    progressDialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('进度更新失败', error)
    ElMessage.error('进度更新失败')
  } finally {
    progressLoading.value = false
  }
}

// 重置表单
function resetForm() {
  Object.assign(formData, {
    id: undefined,
    course_id: undefined,
    teacher_id: undefined,
    class_id: undefined,
    chapter: '',
    chapter_number: undefined,
    unit_name: '',
    unit_number: undefined,
    planned_start_date: '',
    planned_end_date: '',
    planned_hours: 0,
    actual_hours: 0,
    status: 'not_started',
    progress_percentage: 0,
    key_points: '',
    difficult_points: '',
    teaching_goals: '',
    notes: ''
  })
}

// 导出
function handleExport() {
  ElMessage.info('导出功能开发中...')
}

// 辅助函数
function formatDate(dateStr?: string) {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

function getProgressColor(percentage?: number) {
  const p = percentage || 0
  if (p >= 100) return '#67c23a'
  if (p >= 70) return '#409eff'
  if (p >= 30) return '#e6a23c'
  return '#909399'
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.teaching-progress-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
