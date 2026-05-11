<template>
  <div class="team-logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>团队日志</span>
          <el-button @click="handleBack">返回列表</el-button>
        </div>
      </template>

      <!-- 统计面板 -->
      <div class="stats-panel">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-statistic title="本月提交数" :value="stats.total || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="已审核数" :value="stats.reviewed || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="待审核数" :value="stats.pending || 0" />
          </el-col>
        </el-row>
      </div>

      <!-- 筛选区域 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="queryForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item label="教师">
          <el-select
            v-model="queryForm.teacher_id"
            placeholder="全部教师"
            clearable
            style="width: 200px;"
          >
            <el-option
              v-for="teacher in teacherList"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 日志卡片列表 -->
      <div v-loading="loading" class="log-cards">
        <el-card
          v-for="item in logList"
          :key="item.id"
          class="log-card"
          shadow="hover"
          @click="handleCardClick(item)"
        >
          <div class="log-card-header">
            <div class="log-card-info">
              <span class="teacher-name">{{ item.author_name }}</span>
              <el-tag :type="getTypeTagType(item.log_type)" size="small">
                {{ getTypeLabel(item.log_type) }}
              </el-tag>
              <el-tag :type="getStatusTagType(item.status)" size="small" effect="plain">
                {{ getStatusLabel(item.status) }}
              </el-tag>
            </div>
            <span class="submit-time">{{ item.created_at }}</span>
          </div>
          <div class="log-card-period">
            {{ item.period_start }} 至 {{ item.period_end }}
          </div>
          <div class="log-card-summary" v-if="expandedId !== item.id">
            {{ (item.summary || '').substring(0, 100) }}{{ (item.summary || '').length > 100 ? '...' : '' }}
          </div>

          <!-- 展开详情 -->
          <div v-if="expandedId === item.id" class="log-card-detail">
            <div class="detail-section">
              <h4>本周期总结</h4>
              <div class="markdown-content" v-html="renderMarkdown(item.summary || '')"></div>
            </div>
            <div class="detail-section">
              <h4>下周期计划</h4>
              <div class="markdown-content" v-html="renderMarkdown(item.plan || '')"></div>
            </div>

            <!-- 审核操作区域 -->
            <div v-if="item.status === 'SUBMITTED' || item.status === 'PENDING'" class="review-section">
              <el-divider />
              <h4>审核意见</h4>
              <el-input
                v-model="reviewForm.comment"
                type="textarea"
                :rows="4"
                placeholder="请输入审核意见"
                class="review-textarea"
              />
              <div class="review-actions">
                <el-button type="primary" @click.stop="handleReview(item, 'REVIEWED')">
                  通过
                </el-button>
                <el-button type="warning" @click.stop="handleReview(item, 'REVISION_REQUIRED')">
                  驳回修改
                </el-button>
              </div>
            </div>

            <!-- 已有审核意见展示 -->
            <div v-if="item.review_comment" class="existing-review">
              <el-divider />
              <h4>审核意见</h4>
              <div class="review-comment-content">{{ item.review_comment }}</div>
            </div>
          </div>
        </el-card>

        <el-empty v-if="!loading && logList.length === 0" description="暂无日志数据" />
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import { worklogApi } from '@/api/oa/worklogs'

const router = useRouter()

const loading = ref(false)
const logList = ref<any[]>([])
const teacherList = ref<any[]>([])
const expandedId = ref<string | null>(null)

const stats = reactive({
  total: 0,
  reviewed: 0,
  pending: 0
})

const queryForm = reactive({
  date_range: [] as string[],
  teacher_id: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const reviewForm = reactive({
  comment: ''
})

/** 渲染 Markdown */
function renderMarkdown(content: string): string {
  if (!content) return ''
  try {
    return marked.parse(content) as string
  } catch (e) {
    return content
  }
}

/** 获取日志类型标签 */
function getTypeLabel(type: string): string {
  const map: Record<string, string> = {
    daily: '日报',
    weekly: '周报',
    monthly: '月报'
  }
  return map[type] || type
}

function getTypeTagType(type: string): string {
  const map: Record<string, string> = {
    daily: '',
    weekly: 'success',
    monthly: 'warning'
  }
  return map[type] || ''
}

/** 获取状态标签 */
function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    DRAFT: '草稿',
    SUBMITTED: '待审核',
    PENDING: '待审核',
    REVIEWED: '已审核',
    REVISION_REQUIRED: '需修改'
  }
  return map[status] || status
}

function getStatusTagType(status: string): string {
  const map: Record<string, string> = {
    DRAFT: 'info',
    SUBMITTED: 'warning',
    PENDING: 'warning',
    REVIEWED: 'success',
    REVISION_REQUIRED: 'danger'
  }
  return map[status] || 'info'
}

/** 加载团队日志列表 */
async function loadTeamLogs() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize
    }
    if (queryForm.date_range && queryForm.date_range.length === 2) {
      params.period_start = queryForm.date_range[0]
      params.period_end = queryForm.date_range[1]
    }
    if (queryForm.teacher_id) {
      params.teacher_id = queryForm.teacher_id
    }
    const res = await worklogApi.getTeamLogs(params)
    logList.value = res.data?.list || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载团队日志失败')
  } finally {
    loading.value = false
  }
}

/** 加载统计数据 */
async function loadStats() {
  try {
    const res = await worklogApi.getStats()
    const data = res.data || {}
    stats.total = data.total || 0
    stats.reviewed = data.reviewed || 0
    stats.pending = data.pending || 0
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

/** 加载教师列表 */
async function loadTeacherList() {
  try {
    const res = await worklogApi.getSubordinateList({ page: 1, pageSize: 100 })
    // 从下属列表中提取教师信息
    const list = res.data?.list || []
    const teacherMap = new Map<string, string>()
    list.forEach((item: any) => {
      if (item.author_id && item.author_name && !teacherMap.has(item.author_id)) {
        teacherMap.set(item.author_id, item.author_name)
      }
    })
    teacherList.value = Array.from(teacherMap, ([id, name]) => ({ id, name }))
  } catch (error) {
    console.error('加载教师列表失败', error)
  }
}

/** 点击卡片展开/收起 */
function handleCardClick(item: any) {
  if (expandedId.value === item.id) {
    expandedId.value = null
    reviewForm.comment = ''
  } else {
    expandedId.value = item.id
    reviewForm.comment = ''
  }
}

/** 审核操作 */
async function handleReview(item: any, status: string) {
  const statusLabel = status === 'REVIEWED' ? '通过' : '驳回修改'
  try {
    await ElMessageBox.confirm(`确定要${statusLabel}该日志吗？`, '审核确认', {
      type: 'warning'
    })
    await worklogApi.review(item.id, {
      status,
      comment: reviewForm.comment
    })
    ElMessage.success(`${statusLabel}成功`)
    expandedId.value = null
    reviewForm.comment = ''
    loadTeamLogs()
    loadStats()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('审核操作失败')
    }
  }
}

/** 查询 */
function handleQuery() {
  pagination.page = 1
  loadTeamLogs()
}

/** 重置 */
function handleReset() {
  queryForm.date_range = []
  queryForm.teacher_id = ''
  handleQuery()
}

/** 分页 */
function handleSizeChange() {
  pagination.page = 1
  loadTeamLogs()
}

function handlePageChange() {
  loadTeamLogs()
}

/** 返回 */
function handleBack() {
  router.push('/oa/worklogs')
}

onMounted(() => {
  loadTeamLogs()
  loadStats()
  loadTeacherList()
})
</script>

<style scoped>
.team-logs {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-panel {
  padding: 24px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.query-form {
  margin-bottom: 16px;
}

.log-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-card {
  cursor: pointer;
  transition: all 0.2s;
}

.log-card:hover {
  border-color: #409eff;
}

.log-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-card-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.teacher-name {
  font-weight: bold;
  font-size: 15px;
}

.submit-time {
  color: #909399;
  font-size: 13px;
}

.log-card-period {
  color: #606266;
  font-size: 13px;
  margin-bottom: 8px;
}

.log-card-summary {
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}

.log-card-detail {
  margin-top: 16px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.markdown-content {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
  font-size: 14px;
  color: #606266;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin: 8px 0;
  color: #303133;
}

.markdown-content :deep(p) {
  margin: 4px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 20px;
}

.review-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.review-textarea {
  margin-bottom: 12px;
}

.review-actions {
  display: flex;
  gap: 12px;
}

.existing-review h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.review-comment-content {
  padding: 12px;
  background: #fdf6ec;
  border-radius: 4px;
  border-left: 4px solid #e6a23c;
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
