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
                <el-button type="success" @click="handleAddApplicant">人工录入</el-button>
              </el-form-item>
              <el-form-item>
                <el-button type="warning" @click="handleImport">导入CSV</el-button>
                <el-button type="info" @click="handleDownloadTemplate">下载模板</el-button>
                <el-button type="danger" :disabled="!selectedApplicants.length" @click="handleBatchUpdate">批量更新</el-button>
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

          <el-table :data="applicantTableData" v-loading="applicantLoading" stripe @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="55" />
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

    <el-dialog v-model="importDialogVisible" title="导入报名信息" width="500px">
      <el-form label-width="100px">
        <el-form-item label="选择招生计划">
          <el-select v-model="importPlanId" placeholder="可选" clearable>
            <el-option v-for="p in planTableData" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传CSV文件">
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".csv" :on-change="handleFileChange">
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">仅支持CSV格式文件</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-alert v-if="importResult" :title="`导入完成: 成功${importResult.success_count}条, 失败${importResult.fail_count}条`" :type="importResult.fail_count > 0 ? 'warning' : 'success'" />
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImportSubmit">导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="applicantDialogVisible" :title="applicantDialogTitle" width="600px">
      <el-form ref="applicantFormRef" :model="applicantFormData" :rules="applicantFormRules" label-width="100px">
        <el-form-item label="学生姓名" prop="student_name">
          <el-input v-model="applicantFormData.student_name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="applicantFormData.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="applicantFormData.birth_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="applicantFormData.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="监护人">
          <el-input v-model="applicantFormData.guardian_name" placeholder="请输入监护人姓名" />
        </el-form-item>
        <el-form-item label="监护人电话">
          <el-input v-model="applicantFormData.guardian_phone" placeholder="请输入监护人电话" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="applicantFormData.id_card" placeholder="请输入身份证号" />
        </el-form-item>
        <el-form-item label="家庭地址">
          <el-input v-model="applicantFormData.address" placeholder="请输入家庭住址" />
        </el-form-item>
        <el-form-item label="就读学校">
          <el-input v-model="applicantFormData.current_school" placeholder="请输入当前就读学校" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="applicantFormData.source" placeholder="请选择来源">
            <el-option label="线上报名" value="online" />
            <el-option label="线下报名" value="offline" />
            <el-option label="转介绍" value="referral" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="applicantFormData.remarks" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applicantDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleApplicantSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialogVisible" title="批量更新" width="400px">
      <el-form label-width="80px">
        <el-form-item label="更新状态">
          <el-select v-model="batchUpdateData.status" placeholder="不更新" clearable>
            <el-option label="待联系" value="pending" />
            <el-option label="已联系" value="contacted" />
            <el-option label="已面试" value="interviewed" />
            <el-option label="已录取" value="admitted" />
          </el-select>
        </el-form-item>
        <el-form-item label="录取批次">
          <el-input v-model="batchUpdateData.enrollment_batch" placeholder="不更新" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchSubmit">确定更新{{ selectedApplicants.length }}条</el-button>
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
  batchUpdateApplicants,
  importApplicants,
  downloadTemplate,
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

const selectedApplicants = ref<any[]>([])
const importDialogVisible = ref(false)
const importPlanId = ref('')
const importFile = ref<File | null>(null)
const importResult = ref<any>(null)
const importing = ref(false)
const batchDialogVisible = ref(false)
const batchUpdateData = reactive({
  status: '',
  enrollment_batch: ''
})

const applicantDialogVisible = ref(false)
const applicantDialogTitle = ref('')
const applicantFormRef = ref()
const applicantFormData = reactive({
  id: '',
  student_name: '',
  gender: '',
  birth_date: '',
  phone: '',
  guardian_name: '',
  guardian_phone: '',
  id_card: '',
  address: '',
  current_school: '',
  source: 'offline',
  remarks: ''
})
const applicantFormRules = {
  student_name: [{ required: true, message: '请输入学生姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }]
}

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

const handleSelectionChange = (selection: any[]) => {
  selectedApplicants.value = selection
}

const handleImport = () => {
  importFile.value = null
  importResult.value = null
  importDialogVisible.value = true
}

const handleFileChange = (file: any) => {
  importFile.value = file.raw
}

const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择CSV文件')
    return
  }
  importing.value = true
  try {
    const res = await importApplicants(importFile.value, importPlanId.value || undefined)
    importResult.value = res.data
    ElMessage.success(`导入完成: 成功${res.data.success_count}条, 失败${res.data.fail_count}条`)
    fetchApplicants()
    fetchStats()
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

const handleDownloadTemplate = async () => {
  try {
    const res = await downloadTemplate()
    const url = window.URL.createObjectURL(new Blob([res as any]))
    const link = document.createElement('a')
    link.href = url
    link.download = '报名信息导入模板.csv'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载模板失败')
  }
}

const handleBatchUpdate = () => {
  if (!selectedApplicants.value.length) {
    ElMessage.warning('请先选择要更新的记录')
    return
  }
  batchUpdateData.status = ''
  batchUpdateData.enrollment_batch = ''
  batchDialogVisible.value = true
}

const handleBatchSubmit = async () => {
  try {
    await batchUpdateApplicants({
      ids: selectedApplicants.value.map((a: any) => a.id),
      status: batchUpdateData.status || undefined,
      enrollment_batch: batchUpdateData.enrollment_batch || undefined
    })
    ElMessage.success(`成功更新${selectedApplicants.value.length}条记录`)
    batchDialogVisible.value = false
    fetchApplicants()
    fetchStats()
  } catch (e) {
    ElMessage.error('批量更新失败')
  }
}

const handleAddApplicant = () => {
  applicantDialogTitle.value = '人工录入报名信息'
  applicantFormData.id = ''
  applicantFormData.student_name = ''
  applicantFormData.gender = ''
  applicantFormData.birth_date = ''
  applicantFormData.phone = ''
  applicantFormData.guardian_name = ''
  applicantFormData.guardian_phone = ''
  applicantFormData.id_card = ''
  applicantFormData.address = ''
  applicantFormData.current_school = ''
  applicantFormData.source = 'offline'
  applicantFormData.remarks = ''
  applicantDialogVisible.value = true
}

const handleApplicantSubmit = async () => {
  if (!applicantFormRef.value) return
  await applicantFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (applicantFormData.id) {
          ElMessage.success('更新成功')
        } else {
          await createApplicant(applicantFormData as any)
          ElMessage.success('录入成功')
        }
        applicantDialogVisible.value = false
        fetchApplicants()
        fetchStats()
      } catch (e: any) {
        ElMessage.error(e.message || '操作失败')
      }
    }
  })
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