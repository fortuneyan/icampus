<template>
  <div class="course-selection-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>选课管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData">
          <i class="el-icon-refresh"></i> 刷新
        </el-button>
      </div>
    </div>

    <!-- 选课规则信息 -->
    <el-card class="rule-info-card" v-if="currentRule">
      <div slot="header">
        <span>当前选课规则</span>
      </div>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="规则名称">{{ currentRule.name }}</el-descriptions-item>
        <el-descriptions-item label="学年学期">
          {{ currentRule.academic_year }} 第{{ currentRule.semester }}学期
        </el-descriptions-item>
        <el-descriptions-item label="选课模式">
          {{ getModeText(currentRule.selection_mode) }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(currentRule.start_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ formatDateTime(currentRule.end_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="学分范围">
          {{ currentRule.min_credits }} - {{ currentRule.max_credits }} 学分
        </el-descriptions-item>
        <el-descriptions-item label="课程数量">
          {{ currentRule.min_courses || 0 }} - {{ currentRule.max_courses || 0 }} 门
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentRule.is_active ? 'success' : 'info'">
            {{ currentRule.is_active ? '选课进行中' : '未开始' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 学生选课汇总 -->
    <el-card class="summary-card" v-if="studentSummary">
      <div slot="header">
        <span>我的选课情况</span>
      </div>
      <el-row :gutter="20">
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">{{ studentSummary.total_courses }}</div>
            <div class="stat-label">总选课数</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item success">
            <div class="stat-value">{{ studentSummary.approved_courses }}</div>
            <div class="stat-label">已通过</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item warning">
            <div class="stat-value">{{ studentSummary.pending_courses }}</div>
            <div class="stat-label">待审核</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item info">
            <div class="stat-value">{{ studentSummary.waitlisted_courses }}</div>
            <div class="stat-label">候补中</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-value">{{ studentSummary.total_credits }}</div>
            <div class="stat-label">总学分</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item success">
            <div class="stat-value">{{ studentSummary.approved_credits }}</div>
            <div class="stat-label">已获学分</div>
          </div>
        </el-col>
      </el-row>

      <!-- 警告信息 -->
      <el-alert
        v-if="studentSummary.warnings.length > 0"
        :title="studentSummary.warnings.join(', ')"
        type="warning"
        show-icon
        class="mt-20"
      ></el-alert>
    </el-card>

    <!-- 标签页 -->
    <el-card class="main-card">
      <el-tabs v-model="activeTab">
        <!-- 我的选课 -->
        <el-tab-pane label="我的选课" name="my-selection">
          <el-table :data="myRecords" stripe>
            <el-table-column prop="course_name" label="课程名称" min-width="150"></el-table-column>
            <el-table-column prop="course_id" label="课程代码" width="120"></el-table-column>
            <el-table-column prop="credits" label="学分" width="80"></el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template slot-scope="{ row }">
                <el-tag :type="getStatusColor(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="selected_at" label="选课时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.selected_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="waitlist_position" label="候补位置" width="100">
              <template slot-scope="{ row }">
                {{ row.waitlist_position || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template slot-scope="{ row }">
                <el-button
                  v-if="canWithdraw(row.status)"
                  type="text"
                  size="small"
                  @click="handleWithdraw(row)"
                >
                  撤选
                </el-button>
                <el-button
                  v-if="canDrop(row.status)"
                  type="text"
                  size="small"
                  @click="handleDrop(row)"
                >
                  退选
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 选课规则 -->
        <el-tab-pane label="选课规则" name="rules">
          <el-table :data="rules" stripe>
            <el-table-column prop="name" label="规则名称" min-width="150"></el-table-column>
            <el-table-column prop="academic_year" label="学年" width="120"></el-table-column>
            <el-table-column prop="semester" label="学期" width="80">
              <template slot-scope="{ row }">
                第{{ row.semester }}学期
              </template>
            </el-table-column>
            <el-table-column prop="period_type" label="时段" width="100">
              <template slot-scope="{ row }">
                {{ getPeriodText(row.period_type) }}
              </template>
            </el-table-column>
            <el-table-column label="选课时间" width="180">
              <template slot-scope="{ row }">
                {{ formatDate(row.start_time) }} - {{ formatDate(row.end_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template slot-scope="{ row }">
                <el-tag :type="getRuleStatusColor(row.status)" size="small">
                  {{ getRuleStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template slot-scope="{ row }">
                <el-button type="text" size="small" @click="viewRuleDetail(row)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 报表统计 -->
        <el-tab-pane label="报表统计" name="report">
          <el-form :inline="true" class="report-form">
            <el-form-item label="学年">
              <el-input v-model="reportYear" placeholder="如: 2025-2026" style="width: 150px;"></el-input>
            </el-form-item>
            <el-form-item label="学期">
              <el-select v-model="reportSemester" style="width: 100px;">
                <el-option label="第一学期" :value="1"></el-option>
                <el-option label="第二学期" :value="2"></el-option>
                <el-option label="第三学期" :value="3"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadReport">查询报表</el-button>
            </el-form-item>
          </el-form>

          <!-- 报表数据 -->
          <div v-if="reportData" class="report-content">
            <el-row :gutter="20" class="report-stats">
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-value">{{ reportData.total_courses }}</div>
                  <div class="stat-label">开设课程</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-value">{{ reportData.total_students }}</div>
                  <div class="stat-label">选课学生</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-value">{{ reportData.total_selections }}</div>
                  <div class="stat-label">选课人次</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-value">{{ reportData.total_approved }}</div>
                  <div class="stat-label">通过人次</div>
                </div>
              </el-col>
            </el-row>

            <!-- 热门课程 -->
            <h4 class="section-title">热门课程 TOP10</h4>
            <el-table :data="reportData.popular_courses" stripe size="small">
              <el-table-column type="index" width="60"></el-table-column>
              <el-table-column prop="course_name" label="课程名称" min-width="150"></el-table-column>
              <el-table-column prop="total" label="报名人数" width="100"></el-table-column>
              <el-table-column prop="approved" label="通过人数" width="100"></el-table-column>
            </el-table>

            <!-- 低需求课程 -->
            <h4 class="section-title mt-20">低需求课程</h4>
            <el-table :data="reportData.low_demand_courses" stripe size="small">
              <el-table-column type="index" width="60"></el-table-column>
              <el-table-column prop="course_name" label="课程名称" min-width="150"></el-table-column>
              <el-table-column prop="total" label="报名人数" width="100"></el-table-column>
              <el-table-column prop="approved" label="通过人数" width="100"></el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 规则详情弹窗 -->
    <el-dialog title="选课规则详情" :visible.sync="ruleDetailVisible" width="700px">
      <el-descriptions v-if="selectedRule" :column="2" border>
        <el-descriptions-item label="规则名称">{{ selectedRule.name }}</el-descriptions-item>
        <el-descriptions-item label="选课模式">
          {{ getModeText(selectedRule.selection_mode) }}
        </el-descriptions-item>
        <el-descriptions-item label="学年">{{ selectedRule.academic_year }}</el-descriptions-item>
        <el-descriptions-item label="学期">第{{ selectedRule.semester }}学期</el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(selectedRule.start_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ formatDateTime(selectedRule.end_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="学分要求">
          {{ selectedRule.min_credits }} - {{ selectedRule.max_credits }} 学分
        </el-descriptions-item>
        <el-descriptions-item label="课程数量">
          {{ selectedRule.min_courses || 0 }} - {{ selectedRule.max_courses || 0 }} 门
        </el-descriptions-item>
        <el-descriptions-item label="选课策略" :span="2">
          {{ getStrategyText(selectedRule.strategy) }}
        </el-descriptions-item>
      </el-descriptions>
      <div slot="footer">
        <el-button @click="ruleDetailVisible = false">关闭</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator'
import * as api from '@/api/edu/course_selection'
import { getStatusText, getStatusColor, statusTextMap, statusColorMap } from '@/api/edu/course_selection'

@Component({
  name: 'CourseSelection'
})
export default class extends Vue {
  // 状态
  private activeTab = 'my-selection'
  private loading = false
  private currentRule: api.SelectionRule | null = null
  private studentSummary: api.StudentSummary | null = null
  private myRecords: api.SelectionRecord[] = []
  private rules: api.SelectionRule[] = []
  private reportData: api.SelectionReport | null = null
  private ruleDetailVisible = false
  private selectedRule: api.SelectionRule | null = null

  // 报表参数
  private reportYear = '2025-2026'
  private reportSemester = 1

  // 当前用户信息（模拟）
  private currentStudentId = 1001

  // 生命周期
  created() {
    this.initData()
  }

  // 初始化数据
  async initData() {
    await this.loadCurrentRule()
    await this.loadStudentSummary()
    await this.loadMyRecords()
    await this.loadRules()
  }

  // 刷新数据
  async refreshData() {
    await this.initData()
    this.$message.success('数据已刷新')
  }

  // 加载当前生效规则
  async loadCurrentRule() {
    try {
      const res = await api.getActiveRule('2025-2026', 1)
      this.currentRule = res
    } catch (e) {
      console.error('获取选课规则失败:', e)
    }
  }

  // 加载学生选课汇总
  async loadStudentSummary() {
    try {
      const res = await api.getStudentSummary(this.currentStudentId, '2025-2026', 1)
      this.studentSummary = res
    } catch (e) {
      console.error('获取选课汇总失败:', e)
    }
  }

  // 加载我的选课记录
  async loadMyRecords() {
    try {
      const res = await api.getStudentRecords(this.currentStudentId, '2025-2026', 1)
      this.myRecords = res
    } catch (e) {
      console.error('获取选课记录失败:', e)
    }
  }

  // 加载选课规则列表
  async loadRules() {
    try {
      const res = await api.listRules()
      this.rules = res
    } catch (e) {
      console.error('获取规则列表失败:', e)
    }
  }

  // 加载报表
  async loadReport() {
    try {
      const res = await api.getSelectionReport(this.reportYear, this.reportSemester)
      this.reportData = res
    } catch (e) {
      console.error('获取报表失败:', e)
    }
  }

  // 查看规则详情
  viewRuleDetail(rule: api.SelectionRule) {
    this.selectedRule = rule
    this.ruleDetailVisible = true
  }

  // 撤选
  async handleWithdraw(record: api.SelectionRecord) {
    try {
      await this.$confirm('确定要撤选该课程吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })

      await api.withdrawCourse({
        record_id: record.id,
        student_id: record.student_id
      })

      this.$message.success('撤选成功')
      await this.refreshData()
    } catch (e) {
      if (e !== 'cancel') {
        this.$message.error('撤选失败')
      }
    }
  }

  // 退选
  async handleDrop(record: api.SelectionRecord) {
    try {
      await this.$confirm('确定要退选该课程吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })

      await api.dropCourse({
        record_id: record.id,
        student_id: record.student_id
      })

      this.$message.success('退选成功')
      await this.refreshData()
    } catch (e) {
      if (e !== 'cancel') {
        this.$message.error('退选失败')
      }
    }
  }

  // 判断是否可以撤选
  canWithdraw(status: string): boolean {
    return ['pending', 'waitlisted', 'lottery_pending'].includes(status)
  }

  // 判断是否可以退选
  canDrop(status: string): boolean {
    return status === 'approved'
  }

  // 格式化日期时间
  formatDateTime(dateStr?: string): string {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  }

  // 格式化日期
  formatDate(dateStr?: string): string {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN')
  }

  // 获取状态文本
  getStatusText(status: string): string {
    return statusTextMap[status as keyof typeof statusTextMap] || status
  }

  // 获取状态颜色
  getStatusColor(status: string): string {
    return statusColorMap[status as keyof typeof statusColorMap] || 'info'
  }

  // 获取选课模式文本
  getModeText(mode: string): string {
    const modeMap: Record<string, string> = {
      'credit': '学分制',
      'course': '课程制',
      'lottery': '抽签制'
    }
    return modeMap[mode] || mode
  }

  // 获取选课策略文本
  getStrategyText(strategy: string): string {
    const strategyMap: Record<string, string> = {
      'fcfs': '先到先得',
      'priority': '优先级选课',
      'random': '随机抽签',
      'weighted': '加权随机'
    }
    return strategyMap[strategy] || strategy
  }

  // 获取时段文本
  getPeriodText(period: string): string {
    const periodMap: Record<string, string> = {
      'first': '第一轮',
      'second': '第二轮',
      'add': '补选',
      'drop': '退选'
    }
    return periodMap[period] || period
  }

  // 获取规则状态文本
  getRuleStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      'draft': '草稿',
      'active': '生效中',
      'suspended': '已暂停',
      'expired': '已过期'
    }
    return statusMap[status] || status
  }

  // 获取规则状态颜色
  getRuleStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'draft': 'info',
      'active': 'success',
      'suspended': 'warning',
      'expired': 'info'
    }
    return colorMap[status] || 'info'
  }
}
</script>

<style lang="scss" scoped>
.course-selection-container {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 500;
    }
  }

  .rule-info-card,
  .summary-card,
  .main-card {
    margin-bottom: 20px;
  }

  .stat-item {
    text-align: center;
    padding: 15px;

    .stat-value {
      font-size: 28px;
      font-weight: bold;
      color: #409eff;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-top: 5px;
    }

    &.success .stat-value {
      color: #67c23a;
    }

    &.warning .stat-value {
      color: #e6a23c;
    }

    &.info .stat-value {
      color: #909399;
    }
  }

  .report-form {
    margin-bottom: 20px;
  }

  .report-stats {
    margin-bottom: 30px;
  }

  .stat-card {
    background: #f5f7fa;
    border-radius: 8px;
    padding: 20px;
    text-align: center;

    .stat-value {
      font-size: 32px;
      font-weight: bold;
      color: #409eff;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-top: 8px;
    }
  }

  .section-title {
    font-size: 16px;
    font-weight: 500;
    margin: 20px 0 15px;
    color: #303133;
  }

  .mt-20 {
    margin-top: 20px;
  }
}
</style>
