<template>
  <div class="graduation-management">
    <a-card :bordered="false">
      <template #title>
        <div class="card-title">
          <span>毕业管理</span>
          <a-space>
            <a-button type="primary" @click="showAuditModal = true">
              <template #icon><PlusOutlined /></template>
              新建审核
            </a-button>
            <a-button @click="loadData">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <a-form layout="inline" :model="searchForm">
          <a-form-item label="学年">
            <a-select
              v-model:value="searchForm.academic_year"
              placeholder="请选择学年"
              style="width: 150px"
              allowClear
            >
              <a-select-option value="2025-2026">2025-2026</a-select-option>
              <a-select-option value="2024-2025">2024-2025</a-select-option>
              <a-select-option value="2023-2024">2023-2024</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="状态">
            <a-select
              v-model:value="searchForm.status"
              placeholder="请选择状态"
              style="width: 120px"
              allowClear
            >
              <a-select-option value="pending">待审核</a-select-option>
              <a-select-option value="approved">已通过</a-select-option>
              <a-select-option value="rejected">已拒绝</a-select-option>
              <a-select-option value="graduated">已毕业</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="学号">
            <a-input
              v-model:value="searchForm.student_id"
              placeholder="请输入学号"
              style="width: 150px"
              allowClear
            />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              搜索
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 统计卡片 -->
      <a-row :gutter="16" class="statistics-row">
        <a-col :span="6">
          <a-statistic
            title="总人数"
            :value="statistics.total_students"
            :value-style="{ color: '#1890ff' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="待审核"
            :value="statistics.pending_count"
            :value-style="{ color: '#faad14' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="已毕业"
            :value="statistics.graduated_count"
            :value-style="{ color: '#52c41a' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="毕业率"
            :value="statistics.graduation_rate * 100"
            suffix="%"
            :precision="1"
            :value-style="{ color: '#722ed1' }"
          />
        </a-col>
      </a-row>

      <!-- 数据表格 -->
      <a-table
        :columns="columns"
        :data-source="dataList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="GraduationStatusMap[record.status]?.color">
              {{ GraduationStatusMap[record.status]?.text }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'completion_rate'">
            <a-progress
              :percent="record.completion_rate * 100"
              :status="record.is_eligible ? 'success' : 'normal'"
              size="small"
            />
          </template>
          <template v-else-if="column.key === 'gpa'">
            <a-tag :color="getGpaColor(record.gpa)">
              {{ record.gpa.toFixed(2) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewDetail(record)">
                详情
              </a-button>
              <a-button
                v-if="record.status === 'pending'"
                type="link"
                size="small"
                @click="handleAudit(record)"
              >
                审核
              </a-button>
              <a-button
                v-if="record.status === 'approved'"
                type="link"
                size="small"
                @click="handleIssueCertificate(record)"
              >
                发证
              </a-button>
              <a-button
                v-if="record.status === 'approved'"
                type="link"
                size="small"
                @click="handleLeaveSchool(record)"
              >
                离校
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 新建审核弹窗 -->
    <a-modal
      v-model:open="showAuditModal"
      title="新建毕业审核"
      @ok="handleCreateAudit"
      @cancel="showAuditModal = false"
    >
      <a-form
        ref="auditFormRef"
        :model="auditForm"
        :label-col="{ span: 6 }"
      >
        <a-form-item label="学号" name="student_id" required>
          <a-input v-model:value="auditForm.student_id" placeholder="请输入学号" />
        </a-form-item>
        <a-form-item label="学年" name="academic_year" required>
          <a-select v-model:value="auditForm.academic_year" placeholder="请选择学年">
            <a-select-option value="2025-2026">2025-2026</a-select-option>
            <a-select-option value="2024-2025">2024-2025</a-select-option>
            <a-select-option value="2023-2024">2023-2024</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="学期" name="semester">
          <a-select v-model:value="auditForm.semester">
            <a-select-option :value="1">第一学期</a-select-option>
            <a-select-option :value="2">第二学期</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="审核类型" name="audit_type">
          <a-select v-model:value="auditForm.audit_type">
            <a-select-option value="preliminary">资格预审</a-select-option>
            <a-select-option value="formal">正式审核</a-select-option>
            <a-select-option value="appeal">申诉审核</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 审核弹窗 -->
    <a-modal
      v-model:open="showAuditDialog"
      title="毕业审核"
      width="700px"
      @ok="handleSubmitAudit"
      @cancel="showAuditDialog = false"
    >
      <a-descriptions bordered :column="2" v-if="currentRecord">
        <a-descriptions-item label="学号">{{ currentRecord.student_id }}</a-descriptions-item>
        <a-descriptions-item label="学年">{{ currentRecord.academic_year }}</a-descriptions-item>
        <a-descriptions-item label="总学分">{{ currentRecord.total_credits }}</a-descriptions-item>
        <a-descriptions-item label="专业学分">{{ currentRecord.major_credits }}</a-descriptions-item>
        <a-descriptions-item label="GPA">{{ currentRecord.gpa.toFixed(2) }}</a-descriptions-item>
        <a-descriptions-item label="完成度">
          <a-progress :percent="currentRecord.completion_rate * 100" size="small" />
        </a-descriptions-item>
        <a-descriptions-item label="是否符合条件">
          <a-tag :color="currentRecord.is_eligible ? 'green' : 'red'">
            {{ currentRecord.is_eligible ? '符合' : '不符合' }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>

      <a-form :model="auditResult" :label-col="{ span: 4 }" style="margin-top: 20px">
        <a-form-item label="审核意见">
          <a-textarea
            v-model:value="auditResult.comment"
            placeholder="请输入审核意见"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="showDetailModal"
      title="毕业审核详情"
      width="800px"
      :footer="null"
    >
      <a-descriptions bordered :column="2" v-if="currentRecord">
        <a-descriptions-item label="学号" :span="2">{{ currentRecord.student_id }}</a-descriptions-item>
        <a-descriptions-item label="学年">{{ currentRecord.academic_year }}</a-descriptions-item>
        <a-descriptions-item label="学期">{{ currentRecord.semester }}</a-descriptions-item>
        <a-descriptions-item label="审核类型">{{ currentRecord.audit_type }}</a-descriptions-item>
        <a-descriptions-item label="审核状态">
          <a-tag :color="GraduationStatusMap[currentRecord.status]?.color">
            {{ GraduationStatusMap[currentRecord.status]?.text }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="总学分">{{ currentRecord.total_credits }}</a-descriptions-item>
        <a-descriptions-item label="专业学分">{{ currentRecord.major_credits }}</a-descriptions-item>
        <a-descriptions-item label="选修学分">{{ currentRecord.elective_credits }}</a-descriptions-item>
        <a-descriptions-item label="实践学分">{{ currentRecord.practice_credits }}</a-descriptions-item>
        <a-descriptions-item label="已完成课程">{{ currentRecord.completed_courses }}</a-descriptions-item>
        <a-descriptions-item label="GPA">{{ currentRecord.gpa.toFixed(2) }}</a-descriptions-item>
        <a-descriptions-item label="是否符合条件" :span="2">
          <a-tag :color="currentRecord.is_eligible ? 'green' : 'red'">
            {{ currentRecord.is_eligible ? '符合' : '不符合' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="完成度" :span="2">
          <a-progress :percent="currentRecord.completion_rate * 100" />
        </a-descriptions-item>
        <a-descriptions-item label="审核意见" :span="2">
          {{ currentRecord.audit_comment || '-' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { TableProps, FormInstance } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import {
  getAuditList,
  createAudit,
  submitAudit,
  getGraduationStatistics,
  GraduationStatusMap,
  type GraduationAudit,
  type GraduationStatistics
} from '@/api/student/graduation'

// 数据
const loading = ref(false)
const dataList = ref<GraduationAudit[]>([])
const statistics = reactive<GraduationStatistics>({
  academic_year: '',
  semester: 2,
  total_students: 0,
  graduated_count: 0,
  pending_count: 0,
  deferred_count: 0,
  average_gpa: 0,
  highest_gpa: 0,
  lowest_gpa: 0,
  graduation_rate: 0
})

// 搜索
const searchForm = reactive({
  academic_year: '',
  status: '',
  student_id: ''
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 审核表单
const showAuditModal = ref(false)
const auditFormRef = ref<FormInstance>()
const auditForm = reactive({
  student_id: '',
  academic_year: '2025-2026',
  semester: 2,
  audit_type: 'preliminary'
})

// 审核对话框
const showAuditDialog = ref(false)
const currentRecord = ref<GraduationAudit | null>(null)
const auditResult = reactive({
  comment: ''
})

// 详情弹窗
const showDetailModal = ref(false)

// 表格列定义
const columns = [
  {
    title: '学号',
    dataIndex: 'student_id',
    key: 'student_id',
    width: 120
  },
  {
    title: '学年',
    dataIndex: 'academic_year',
    key: 'academic_year',
    width: 120
  },
  {
    title: '总学分',
    dataIndex: 'total_credits',
    key: 'total_credits',
    width: 100
  },
  {
    title: 'GPA',
    dataIndex: 'gpa',
    key: 'gpa',
    width: 80
  },
  {
    title: '完成度',
    dataIndex: 'completion_rate',
    key: 'completion_rate',
    width: 150
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 220
  }
]

// 获取GPA颜色
const getGpaColor = (gpa: number): string => {
  if (gpa >= 3.5) return 'green'
  if (gpa >= 3.0) return 'cyan'
  if (gpa >= 2.0) return 'blue'
  return 'orange'
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      academic_year: searchForm.academic_year || undefined,
      status: searchForm.status || undefined,
      student_id: searchForm.student_id ? parseInt(searchForm.student_id) : undefined,
      page: pagination.current,
      page_size: pagination.pageSize
    }

    const res = await getAuditList(params)
    if (res.code === 0) {
      dataList.value = res.data.items
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载统计
const loadStatistics = async () => {
  try {
    const year = searchForm.academic_year || '2025-2026'
    const res = await getGraduationStatistics(year)
    if (res.code === 0) {
      Object.assign(statistics, res.data)
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadData()
  loadStatistics()
}

// 表格变化
const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  loadData()
}

// 创建审核
const handleCreateAudit = async () => {
  try {
    const res = await createAudit({
      student_id: parseInt(auditForm.student_id),
      academic_year: auditForm.academic_year,
      semester: auditForm.semester,
      audit_type: auditForm.audit_type
    })

    if (res.code === 0) {
      message.success('创建成功')
      showAuditModal.value = false
      auditFormRef.value?.resetFields()
      loadData()
    }
  } catch (error) {
    console.error('创建失败:', error)
  }
}

// 审核
const handleAudit = (record: GraduationAudit) => {
  currentRecord.value = record
  auditResult.comment = ''
  showAuditDialog.value = true
}

// 提交审核
const handleSubmitAudit = async () => {
  if (!currentRecord.value) return

  try {
    const res = await submitAudit(
      currentRecord.value.id,
      1, // TODO: 实际使用当前用户ID
      auditResult.comment
    )

    if (res.code === 0) {
      message.success('审核提交成功')
      showAuditDialog.value = false
      loadData()
      loadStatistics()
    }
  } catch (error) {
    console.error('审核失败:', error)
  }
}

// 查看详情
const viewDetail = (record: GraduationAudit) => {
  currentRecord.value = record
  showDetailModal.value = true
}

// 发证
const handleIssueCertificate = (record: GraduationAudit) => {
  message.info(`为学生 ${record.student_id} 发放毕业证书`)
  // TODO: 跳转到证书管理
}

// 离校
const handleLeaveSchool = (record: GraduationAudit) => {
  message.info(`办理学生 ${record.student_id} 离校手续`)
  // TODO: 跳转到离校管理
}

// 初始化
onMounted(() => {
  loadData()
  loadStatistics()
})
</script>

<style scoped>
.graduation-management {
  padding: 0;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 16px;
}

.statistics-row {
  margin-bottom: 24px;
}
</style>
