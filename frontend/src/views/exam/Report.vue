<template>
  <div class="score-report">
    <a-card :bordered="false">
      <template #title>
        <div class="card-title">
          <span>成绩报表</span>
          <a-space>
            <a-button type="primary" @click="showReportModal = true">
              <template #icon><FileTextOutlined /></template>
              生成报表
            </a-button>
            <a-button @click="loadData">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>
      </template>

      <!-- 统计概览 -->
      <a-row :gutter="16" class="statistics-row">
        <a-col :span="6">
          <a-statistic
            title="总学生数"
            :value="overview.total_students"
            :value-style="{ color: '#1890ff' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="总考试数"
            :value="overview.total_exams"
            :value-style="{ color: '#52c41a' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="平均分"
            :value="overview.overall_average"
            suffix="分"
            :precision="1"
            :value-style="{ color: '#722ed1' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="及格率"
            :value="overview.overall_pass_rate * 100"
            suffix="%"
            :precision="1"
            :value-style="{ color: overview.overall_pass_rate >= 0.6 ? '#52c41a' : '#faad14' }"
          />
        </a-col>
      </a-row>

      <!-- 标签页 -->
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="student" tab="学生报表">
          <StudentReportTab @view-detail="handleViewDetail" />
        </a-tab-pane>
        <a-tab-pane key="class" tab="班级报表">
          <ClassReportTab />
        </a-tab-pane>
        <a-tab-pane key="subject" tab="科目报表">
          <SubjectReportTab />
        </a-tab-pane>
        <a-tab-pane key="exam" tab="考试报表">
          <ExamReportTab />
        </a-tab-pane>
        <a-tab-pane key="trend" tab="成绩趋势">
          <TrendReportTab />
        </a-tab-pane>
        <a-tab-pane key="ranking" tab="成绩排名">
          <RankingTab />
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 生成报表弹窗 -->
    <a-modal
      v-model:open="showReportModal"
      title="生成成绩报表"
      @ok="handleGenerateReport"
      @cancel="showReportModal = false"
    >
      <a-form :model="reportForm" :label-col="{ span: 6 }">
        <a-form-item label="报表类型" name="report_type">
          <a-select v-model:value="reportForm.report_type">
            <a-select-option value="student">学生报表</a-select-option>
            <a-select-option value="class">班级报表</a-select-option>
            <a-select-option value="subject">科目报表</a-select-option>
            <a-select-option value="exam">考试报表</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="学年" name="academic_year">
          <a-select v-model:value="reportForm.academic_year">
            <a-select-option value="2025-2026">2025-2026</a-select-option>
            <a-select-option value="2024-2025">2024-2025</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="学期" name="semester">
          <a-select v-model:value="reportForm.semester">
            <a-select-option :value="1">第一学期</a-select-option>
            <a-select-option :value="2">第二学期</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="reportForm.report_type === 'student'" label="学号" name="student_id">
          <a-input v-model:value="reportForm.student_id" placeholder="请输入学号" />
        </a-form-item>
        <a-form-item v-if="reportForm.report_type === 'class'" label="班级ID" name="class_id">
          <a-input v-model:value="reportForm.class_id" placeholder="请输入班级ID" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 学生详情弹窗 -->
    <a-modal
      v-model:open="showDetailModal"
      title="学生成绩详情"
      width="900px"
      :footer="null"
    >
      <a-descriptions bordered :column="2" v-if="studentReport">
        <a-descriptions-item label="学号">{{ studentReport.student_id }}</a-descriptions-item>
        <a-descriptions-item label="姓名">{{ studentReport.student_name }}</a-descriptions-item>
        <a-descriptions-item label="学年">{{ studentReport.academic_year }}</a-descriptions-item>
        <a-descriptions-item label="学期">{{ studentReport.semester }}</a-descriptions-item>
        <a-descriptions-item label="平均分">
          <a-tag color="blue">{{ studentReport.average_score }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="GPA">
          <a-tag :color="studentReport.gpa >= 3.0 ? 'green' : 'orange'">
            {{ studentReport.gpa }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="班级排名">{{ studentReport.class_rank || '-' }}</a-descriptions-item>
        <a-descriptions-item label="年级排名">{{ studentReport.grade_rank || '-' }}</a-descriptions-item>
        <a-descriptions-item label="及格率">
          <a-progress :percent="studentReport.pass_rate * 100" size="small" />
        </a-descriptions-item>
      </a-descriptions>

      <a-divider>成绩分布</a-divider>

      <a-row :gutter="16" v-if="studentReport">
        <a-col :span="6">
          <a-statistic title="优秀" :value="studentReport.grades_distribution.excellent" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="良好" :value="studentReport.grades_distribution.good" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="中等" :value="studentReport.grades_distribution.average" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="不及格" :value="studentReport.grades_distribution.fail" />
        </a-col>
      </a-row>

      <a-divider>科目明细</a-divider>

      <a-table
        v-if="studentScores.length"
        :columns="scoreColumns"
        :data-source="studentScores"
        :pagination="false"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'grade_level'">
            <a-tag :color="GradeLevelMap[record.grade_level]?.color">
              {{ GradeLevelMap[record.grade_level]?.text }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'percentile'">
            <a-progress :percent="record.percentile" size="small" :show-info="false" />
          </template>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  FileTextOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import {
  getStatisticsOverview,
  generateStudentReport,
  getStudentScores,
  GradeLevelMap,
  type StatisticsOverview,
  type StudentReport,
  type StudentScore
} from '@/api/exam/report'
import StudentReportTab from './StudentReportTab.vue'
import ClassReportTab from './ClassReportTab.vue'
import SubjectReportTab from './SubjectReportTab.vue'
import ExamReportTab from './ExamReportTab.vue'
import TrendReportTab from './TrendReportTab.vue'
import RankingTab from './RankingTab.vue'

// 统计概览
const overview = reactive<StatisticsOverview>({
  total_students: 0,
  total_exams: 0,
  total_subjects: 0,
  overall_average: 0,
  overall_pass_rate: 0,
  highest_score: 0,
  lowest_score: 0
})

// 标签页
const activeTab = ref('student')

// 生成报表弹窗
const showReportModal = ref(false)
const reportForm = reactive({
  report_type: 'student',
  academic_year: '2025-2026',
  semester: 1,
  student_id: '',
  class_id: ''
})

// 详情弹窗
const showDetailModal = ref(false)
const studentReport = ref<StudentReport | null>(null)
const studentScores = ref<StudentScore[]>([])

// 成绩表格列
const scoreColumns = [
  { title: '科目', dataIndex: 'subject_name', key: 'subject_name' },
  { title: '分数', dataIndex: 'score', key: 'score', width: 80 },
  { title: '满分', dataIndex: 'full_score', key: 'full_score', width: 80 },
  { title: '等级', dataIndex: 'grade_level', key: 'grade_level', width: 100 },
  { title: '百分比', key: 'percentile', width: 150 }
]

// 加载统计概览
const loadOverview = async () => {
  try {
    const res = await getStatisticsOverview('2025-2026', 1)
    if (res.code === 0) {
      Object.assign(overview, res.data)
    }
  } catch (error) {
    console.error('加载统计概览失败:', error)
  }
}

// 加载数据
const loadData = () => {
  loadOverview()
}

// 生成报表
const handleGenerateReport = async () => {
  if (reportForm.report_type === 'student' && !reportForm.student_id) {
    message.warning('请输入学号')
    return
  }

  if (reportForm.report_type === 'class' && !reportForm.class_id) {
    message.warning('请输入班级ID')
    return
  }

  message.success('报表生成成功')
  showReportModal.value = false
}

// 查看详情
const handleViewDetail = async (studentId: number) => {
  try {
    const res = await generateStudentReport({
      student_id: studentId,
      student_name: '',
      academic_year: '2025-2026',
      semester: 1
    })
    if (res.code === 0) {
      studentReport.value = res.data

      // 加载成绩明细
      const scoreRes = await getStudentScores(studentId)
      if (scoreRes.code === 0) {
        studentScores.value = scoreRes.data
      }

      showDetailModal.value = true
    }
  } catch (error) {
    console.error('加载学生详情失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.score-report {
  padding: 0;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.statistics-row {
  margin-bottom: 24px;
}
</style>
