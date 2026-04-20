<template>
  <div class="recruitment-management">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="招生计划" name="plans">
        <el-card>
          <div class="toolbar">
            <el-form :inline="true" :model="planSearchForm">
              <el-form-item label="年份">
                <el-input v-model="planSearchForm.year" placeholder="请输入年份" clearable />
              </el-form-item>
              <el-form-item label="状态">
                <el-select v-model="planSearchForm.status" placeholder="请选择" clearable>
                  <el-option label="草稿" value="draft" />
                  <el-option label="已发布" value="published" />
                  <el-option label="已结束" value="closed" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handlePlanSearch">搜索</el-button>
                <el-button @click="handlePlanReset">重置</el-button>
                <el-button type="success" @click="handleAddPlan">新增计划</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-table :data="planTableData" v-loading="planLoading" stripe>
            <el-table-column prop="name" label="计划名称" width="200" />
            <el-table-column prop="year" label="年份" width="100" />
            <el-table-column prop="quota" label="招生名额" width="100" />
            <el-table-column label="报名时间" width="220">
              <template #default="{ row }">
                {{ formatDate(row.start_date) }} - {{ formatDate(row.end_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'draft'" type="info">草稿</el-tag>
                <el-tag v-else-if="row.status === 'published'" type="success">已发布</el-tag>
                <el-tag v-else type="warning">已结束</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleEditPlan(row)">编辑</el-button>
                <el-button type="danger" link @click="handleDeletePlan(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="planPagination.page"
              v-model:page-size="planPagination.pageSize"
              :total="planPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="fetchPlans"
              @current-change="fetchPlans"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="报名管理" name="applicants">
        <el-card>
          <div class="toolbar">
            <el-form :inline="true" :model="applicantSearchForm">
              <el-form-item label="状态">
                <el-select v-model="applicantSearchForm.status" placeholder="请选择" clearable>
                  <el-option label="待联系" value="pending" />
                  <el-option label="已联系" value="contacted" />
                  <el-option label="已面试" value="interviewed" />
                  <el-option label="已录取" value="admitted" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleApplicantSearch">搜索</el-button>
                <el-button @click="handleApplicantReset">重置</el-button>
              </el-form-item>
              <el-form-item>
                <el-button type="success" @click="fetchStats">刷新统计</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-row :gutter="20" class="stats-row">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.pending }}</div>
                <div class="stat-label">待联系</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.contacted }}</div>
                <div class="stat-label">已联系</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.interviewed }}</div>
                <div class="stat-label">已面试</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.admitted }}</div>
                <div class="stat-label">已录取</div>
              </div>
            </el-col>
          </el-row>

          <el-table :data="applicantTableData" v-loading="applicantLoading" stripe>
            <el-table-column prop="student_name" label="学生姓名" width="120" />
            <el-table-column prop="gender" label="性别" width="80">
              <template #default="{ row }">
                {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="phone" label="联系电话" width="120" />
            <el-table-column prop="guardian_name" label="监护人" width="100" />
            <el-table-column prop="source" label="来源" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'pending'" type="warning">待联系</el-tag>
                <el-tag v-else-if="row.status === 'contacted'" type="info">已联系</el-tag>
                <el-tag v-else-if="row.status === 'interviewed'" type="primary">已面试</el-tag>
                <el-tag v-else-if="row.status === 'admitted'" type="success">已录取</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="报名时间" width="180" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleViewApplicant(row)">查看</el-button>
                <el-button type="success" link @click="handleAddFollowUp(row)">跟进</el-button>
                <el-button type="warning" link @click="handleChangeStatus(row)">状态</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="applicantPagination.page"
              v-model:page-size="applicantPagination.pageSize"
              :total="applicantPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="fetchApplicants"
              @current-change="fetchApplicants"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="planDialogVisible" :title="planDialogTitle" width="600px">
      <el-form ref="planFormRef" :model="planFormData" :rules="planFormRules" label-width="100px">
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="planFormData.name" placeholder="请输入计划名称" />
        </el-form-item>
        <el-form-item label="招生年份" prop="year">
          <el-input-number v-model="planFormData.year" :min="2020" :max="2030" />
        </el-form-item>
        <el-form-item label="招生名额" prop="quota">
          <el-input-number v-model="planFormData.quota" :min="0" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="planFormData.start_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="planFormData.end_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="planFormData.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePlanSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="followUpDialogVisible" title="添加跟进记录" width="500px">
      <el-form ref="followUpFormRef" :model="followUpFormData" :rules="followUpFormRules" label-width="100px">
        <el-form-item label="跟进类型" prop="follow_type">
          <el-select v-model="followUpFormData.follow_type">
            <el-option label="电话沟通" value="phone" />
            <el-option label="微信沟通" value="wechat" />
            <el-option label="上门拜访" value="visit" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="跟进内容" prop="content">
          <el-input v-model="followUpFormData.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="下次跟进">
          <el-date-picker v-model="followUpFormData.next_follow_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="followUpDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFollowUpSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusDialogVisible" title="修改状态" width="400px">
      <el-form label-width="80px">
        <el-form-item label="新状态">
          <el-select v-model="newStatus">
            <el-option label="待联系" value="pending" />
            <el-option label="已联系" value="contacted" />
            <el-option label="已面试" value="interviewed" />
            <el-option label="已录取" value="admitted" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleStatusSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getRecruitmentPlans,
  createRecruitmentPlan,
  updateRecruitmentPlan,
  getApplicants,
  updateApplicantStatus,
  addFollowUp,
  getFollowUps,
  getRecruitmentStats
} from '@/api/recruitment'

const activeTab = ref('plans')

const planSearchForm = reactive({
  year: '',
  status: ''
})
const planTableData = ref([])
const planLoading = ref(false)
const planPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const planDialogVisible = ref(false)
const planDialogTitle = ref('')
const planFormRef = ref()
const planFormData = reactive({
  id: '',
  name: '',
  year: new Date().getFullYear(),
  quota: 0,
  start_date: '',
  end_date: '',
  description: ''
})
const planFormRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  year: [{ required: true, message: '请输入招生年份', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
}

const applicantSearchForm = reactive({
  status: ''
})
const applicantTableData = ref([])
const applicantLoading = ref(false)
const applicantPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const stats = reactive({ pending: 0, contacted: 0, interviewed: 0, admitted: 0 })

const followUpDialogVisible = ref(false)
const followUpFormRef = ref()
const currentApplicantId = ref('')
const followUpFormData = reactive({
  follow_type: 'phone',
  content: '',
  next_follow_date: ''
})
const followUpFormRules = {
  follow_type: [{ required: true, message: '请选择跟进类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入跟进内容', trigger: 'blur' }]
}

const statusDialogVisible = ref(false)
const newStatus = ref('')
const currentStatusApplicantId = ref('')

const formatDate = (date: string) => {
  if (!date) return '-'
  return date.substring(0, 10)
}

const fetchPlans = async () => {
  planLoading.value = true
  try {
    const res = await getRecruitmentPlans({
      year: planSearchForm.year ? Number(planSearchForm.year) : undefined,
      status: planSearchForm.status || undefined,
      page: planPagination.page,
      page_size: planPagination.pageSize
    })
    planTableData.value = res.data.items
    planPagination.total = res.data.total
  } catch (e) {
    ElMessage.error('获取招生计划失败')
  } finally {
    planLoading.value = false
  }
}

const handlePlanSearch = () => {
  planPagination.page = 1
  fetchPlans()
}

const handlePlanReset = () => {
  planSearchForm.year = ''
  planSearchForm.status = ''
  handlePlanSearch()
}

const handleAddPlan = () => {
  planDialogTitle.value = '新增招生计划'
  planFormData.id = ''
  planFormData.name = ''
  planFormData.year = new Date().getFullYear()
  planFormData.quota = 0
  planFormData.start_date = ''
  planFormData.end_date = ''
  planFormData.description = ''
  planDialogVisible.value = true
}

const handleEditPlan = (row: any) => {
  planDialogTitle.value = '编辑招生��划'
  planFormData.id = row.id
  planFormData.name = row.name
  planFormData.year = row.year
  planFormData.quota = row.quota
  planFormData.start_date = row.start_date?.substring(0, 10)
  planFormData.end_date = row.end_date?.substring(0, 10)
  planFormData.description = row.description
  planDialogVisible.value = true
}

const handlePlanSubmit = async () => {
  if (!planFormRef.value) return
  await planFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        if (planFormData.id) {
          await updateRecruitmentPlan(planFormData.id, planFormData)
          ElMessage.success('更新成功')
        } else {
          await createRecruitmentPlan(planFormData)
          ElMessage.success('创建成功')
        }
        planDialogVisible.value = false
        fetchPlans()
      } catch (e) {
        ElMessage.error('操作失败')
      }
    }
  })
}

const handleDeletePlan = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定删除该招生计划?', '提示', { type: 'warning' })
    ElMessage.success('删除成功')
    fetchPlans()
  } catch {}
}

const handleTabChange = (tab: string) => {
  if (tab === 'plans') {
    fetchPlans()
  } else if (tab === 'applicants') {
    fetchApplicants()
    fetchStats()
  }
}

const fetchApplicants = async () => {
  applicantLoading.value = true
  try {
    const res = await getApplicants({
      status: applicantSearchForm.status || undefined,
      page: applicantPagination.page,
      page_size: applicantPagination.pageSize
    })
    applicantTableData.value = res.data.items
    applicantPagination.total = res.data.total
  } catch (e) {
    ElMessage.error('获取报名信息失败')
  } finally {
    applicantLoading.value = false
  }
}

const handleApplicantSearch = () => {
  applicantPagination.page = 1
  fetchApplicants()
}

const handleApplicantReset = () => {
  applicantSearchForm.status = ''
  handleApplicantSearch()
}

const fetchStats = async () => {
  try {
    const res = await getRecruitmentStats()
    Object.assign(stats, res.data)
  } catch (e) {
    ElMessage.error('获取统计数据失败')
  }
}

const handleViewApplicant = (row: any) => {
  ElMessage.info('查看详情: ' + row.student_name)
}

const handleAddFollowUp = (row: any) => {
  currentApplicantId.value = row.id
  followUpFormData.follow_type = 'phone'
  followUpFormData.content = ''
  followUpFormData.next_follow_date = ''
  followUpDialogVisible.value = true
}

const handleFollowUpSubmit = async () => {
  if (!followUpFormRef.value) return
  await followUpFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        await addFollowUp(currentApplicantId.value, followUpFormData)
        ElMessage.success('添加成功')
        followUpDialogVisible.value = false
      } catch (e) {
        ElMessage.error('添加失败')
      }
    }
  })
}

const handleChangeStatus = (row: any) => {
  currentStatusApplicantId.value = row.id
  newStatus.value = row.status
  statusDialogVisible.value = true
}

const handleStatusSubmit = async () => {
  try {
    await updateApplicantStatus(currentStatusApplicantId.value, newStatus.value)
    ElMessage.success('状态更新成功')
    statusDialogVisible.value = false
    fetchApplicants()
    fetchStats()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

onMounted(() => {
  fetchPlans()
})
</script>

<style scoped>
.recruitment-management {
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