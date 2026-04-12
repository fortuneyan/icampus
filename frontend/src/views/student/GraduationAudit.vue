<template>
  <div class="graduation-audit">
    <a-card :bordered="false">
      <template #title>
        <div class="card-title">
          <span>毕业审核</span>
          <a-space>
            <a-button type="primary" @click="showBatchAuditModal = true">
              <template #icon><CheckOutlined /></template>
              批量审核
            </a-button>
            <a-button @click="loadData">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <a-form layout="inline" :model="filterForm">
          <a-form-item label="学年">
            <a-select
              v-model:value="filterForm.academic_year"
              placeholder="请选择学年"
              style="width: 150px"
              @change="handleFilterChange"
            >
              <a-select-option value="2025-2026">2025-2026</a-select-option>
              <a-select-option value="2024-2025">2024-2025</a-select-option>
              <a-select-option value="2023-2024">2023-2024</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="审核类型">
            <a-select
              v-model:value="filterForm.audit_type"
              placeholder="请选择类型"
              style="width: 120px"
              allowClear
              @change="handleFilterChange"
            >
              <a-select-option value="preliminary">资格预审</a-select-option>
              <a-select-option value="formal">正式审核</a-select-option>
              <a-select-option value="appeal">申诉审核</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="资格条件">
            <a-select
              v-model:value="filterForm.is_eligible"
              placeholder="请选择"
              style="width: 120px"
              allowClear
              @change="handleFilterChange"
            >
              <a-select-option value="true">符合</a-select-option>
              <a-select-option value="false">不符合</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>

      <!-- 数据表格 -->
      <a-table
        :columns="columns"
        :data-source="dataList"
        :loading="loading"
        :pagination="pagination"
        :row-selection="rowSelection"
        @change="handleTableChange"
        row-key="id"
        :scroll="{ x: 1200 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'student_id'">
            <a @click="viewDetail(record)">{{ record.student_id }}</a>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="GraduationStatusMap[record.status]?.color">
              {{ GraduationStatusMap[record.status]?.text }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_eligible'">
            <a-tag :color="record.is_eligible ? 'green' : 'red'">
              {{ record.is_eligible ? '符合' : '不符合' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'completion_rate'">
            <a-progress
              :percent="record.completion_rate * 100"
              size="small"
              :status="record.is_eligible ? 'success' : 'normal'"
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
                @click="generateReport(record)"
              >
                报告
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 批量审核弹窗 -->
    <a-modal
      v-model:open="showBatchAuditModal"
      title="批量审核毕业资格"
      @ok="handleBatchAudit"
      @cancel="showBatchAuditModal = false"
    >
      <a-result
        v-if="selectedRowKeys.length === 0"
        status="warning"
        title="请先选择要审核的记录"
      />
      <template v-else>
        <p>已选择 <strong>{{ selectedRowKeys.length }}</strong> 条记录</p>
        <a-form :model="batchAuditForm" :label-col="{ span: 6 }">
          <a-form-item label="审核结果">
            <a-radio-group v-model:value="batchAuditForm.approved">
              <a-radio :value="true">全部通过</a-radio>
              <a-radio :value="false">全部拒绝</a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item label="审核意见">
            <a-textarea
              v-model:value="batchAuditForm.comment"
              placeholder="请输入审核意见"
              :rows="3"
            />
          </a-form-item>
        </a-form>
      </template>
    </a-modal>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="showDetailModal"
      title="毕业审核详情"
      width="900px"
      :footer="null"
    >
      <a-descriptions bordered :column="2" v-if="currentRecord">
        <a-descriptions-item label="审核ID" :span="2">
          {{ currentRecord.id }}
        </a-descriptions-item>
        <a-descriptions-item label="学号">{{ currentRecord.student_id }}</a-descriptions-item>
        <a-descriptions-item label="学年">{{ currentRecord.academic_year }}</a-descriptions-item>
        <a-descriptions-item label="学期">
          {{ currentRecord.semester === 1 ? '第一学期' : '第二学期' }}
        </a-descriptions-item>
        <a-descriptions-item label="审核类型">
          <a-tag>{{ currentRecord.audit_type }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="审核状态">
          <a-tag :color="GraduationStatusMap[currentRecord.status]?.color">
            {{ GraduationStatusMap[currentRecord.status]?.text }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="是否符合条件">
          <a-tag :color="currentRecord.is_eligible ? 'green' : 'red'">
            {{ currentRecord.is_eligible ? '符合' : '不符合' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="完成度" :span="2">
          <a-progress :percent="currentRecord.completion_rate * 100" />
        </a-descriptions-item>

        <a-divider>学业情况</a-divider>

        <a-descriptions-item label="总学分">
          {{ currentRecord.total_credits }} / 160
        </a-descriptions-item>
        <a-descriptions-item label="专业学分">
          {{ currentRecord.major_credits }} / 80
        </a-descriptions-item>
        <a-descriptions-item label="选修学分">
          {{ currentRecord.elective_credits }} / 20
        </a-descriptions-item>
        <a-descriptions-item label="实践学分">
          {{ currentRecord.practice_credits }} / 15
        </a-descriptions-item>
        <a-descriptions-item label="已完成课程">
          {{ currentRecord.completed_courses }} 门
        </a-descriptions-item>
        <a-descriptions-item label="GPA">
          <a-tag :color="getGpaColor(currentRecord.gpa)">
            {{ currentRecord.gpa.toFixed(2) }}
          </a-tag>
        </a-descriptions-item>

        <a-divider>必修课情况</a-divider>

        <a-descriptions-item label="已通过必修课" :span="2">
          {{ currentRecord.passed_required?.length || 0 }} 门
        </a-descriptions-item>
        <a-descriptions-item label="未通过必修课" :span="2">
          {{ currentRecord.failed_required?.length || 0 }} 门
        </a-descriptions-item>

        <a-divider>审核结果</a-divider>

        <a-descriptions-item label="审核意见" :span="2">
          {{ currentRecord.audit_comment || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="审核人">
          {{ currentRecord.auditor_id || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="审核时间">
          {{ currentRecord.audit_time || '-' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <!-- 报告弹窗 -->
    <a-modal
      v-model:open="showReportModal"
      title="毕业报告"
      width="800px"
      :footer="null"
    >
      <a-result
        v-if="!reportData"
        status="info"
        title="正在生成报告..."
      />
      <a-descriptions v-else bordered :column="2" title="学业概况">
        <a-descriptions-item label="学号">{{ reportData.student_id }}</a-descriptions-item>
        <a-descriptions-item label="姓名">{{ reportData.student_name }}</a-descriptions-item>
        <a-descriptions-item label="总学分">{{ reportData.total_credits }}</a-descriptions-item>
        <a-descriptions-item label="GPA">{{ reportData.gpa.toFixed(2) }}</a-descriptions-item>
        <a-descriptions-item label="是否符合条件" :span="2">
          <a-tag :color="reportData.is_eligible ? 'green' : 'red'">
            {{ reportData.is_eligible ? '符合' : '不符合' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="完成度" :span="2">
          <a-progress :percent="reportData.completion_rate * 100" />
        </a-descriptions-item>
      </a-descriptions>

      <a-divider />

      <a-descriptions v-if="reportData?.missing_requirements?.length" bordered :column="1" title="未满足条件">
        <a-descriptions-item v-for="(item, index) in reportData.missing_requirements" :key="index">
          <a-tag color="orange">{{ item }}</a-tag>
        </a-descriptions-item>
      </a-descriptions>

      <a-divider />

      <a-descriptions v-if="reportData?.suggestions?.length" bordered :column="1" title="建议">
        <a-descriptions-item v-for="(item, index) in reportData.suggestions" :key="index">
          <li>{{ item }}</li>
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { TableProps } from 'ant-design-vue'
import {
  CheckOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import {
  getAuditList,
  batchAudit,
  generateGraduationReport,
  GraduationStatusMap,
  type GraduationAudit,
  type GraduationReport
} from '@/api/student/graduation'

// 数据
const loading = ref(false)
const dataList = ref<GraduationAudit[]>([])
const selectedRowKeys = ref<number[]>([])

// 筛选
const filterForm = reactive({
  academic_year: '2025-2026',
  audit_type: '',
  is_eligible: ''
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 行选择
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys
  }
}))

// 批量审核
const showBatchAuditModal = ref(false)
const batchAuditForm = reactive({
  approved: true,
  comment: ''
})

// 详情弹窗
const showDetailModal = ref(false)
const currentRecord = ref<GraduationAudit | null>(null)

// 报告弹窗
const showReportModal = ref(false)
const reportData = ref<GraduationReport | null>(null)

// 表格列
const columns = [
  {
    title: '学号',
    dataIndex: 'student_id',
    key: 'student_id',
    width: 120,
    fixed: 'left'
  },
  {
    title: '学年',
    dataIndex: 'academic_year',
    key: 'academic_year',
    width: 120
  },
  {
    title: '审核类型',
    dataIndex: 'audit_type',
    key: 'audit_type',
    width: 100
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
    title: '是否合格',
    dataIndex: 'is_eligible',
    key: 'is_eligible',
    width: 100
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
    width: 150
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
      academic_year: filterForm.academic_year,
      page: pagination.current,
      page_size: pagination.pageSize
    }

    if (filterForm.audit_type) {
      (params as any).audit_type = filterForm.audit_type
    }
    if (filterForm.is_eligible) {
      (params as any).status = 'pending'
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

// 筛选变化
const handleFilterChange = () => {
  pagination.current = 1
  selectedRowKeys.value = []
  loadData()
}

// 表格变化
const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  loadData()
}

// 查看详情
const viewDetail = (record: GraduationAudit) => {
  currentRecord.value = record
  showDetailModal.value = true
}

// 审核
const handleAudit = (record: GraduationAudit) => {
  viewDetail(record)
  // TODO: 打开审核对话框
}

// 批量审核
const handleBatchAudit = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要审核的记录')
    return
  }

  try {
    const res = await batchAudit(
      {
        audit_ids: selectedRowKeys.value,
        approved: batchAuditForm.approved,
        comment: batchAuditForm.comment
      },
      1 // TODO: 实际使用当前用户ID
    )

    if (res.code === 0) {
      message.success(`批量审核完成: 通过 ${res.data.approved}, 拒绝 ${res.data.rejected}`)
      showBatchAuditModal.value = false
      selectedRowKeys.value = []
      loadData()
    }
  } catch (error) {
    console.error('批量审核失败:', error)
  }
}

// 生成报告
const generateReport = async (record: GraduationAudit) => {
  try {
    const res = await generateGraduationReport(record.id)
    if (res.code === 0) {
      reportData.value = res.data
      showReportModal.value = true
    }
  } catch (error) {
    console.error('生成报告失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.graduation-audit {
  padding: 0;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 16px;
}
</style>
