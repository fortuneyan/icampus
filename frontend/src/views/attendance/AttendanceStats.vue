<template>
  <div class="attendance-stats-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>考勤统计报表</h2>
      <div class="header-actions">
        <a-button @click="refreshData">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="showReportModal = true">
          <template #icon><FileTextOutlined /></template>
          生成报表
        </a-button>
      </div>
    </div>

    <!-- 统计概览卡片 -->
    <a-row :gutter="16" class="stats-cards">
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="应到人数"
            :value="summaryData.total_students"
            :prefix="h(UserOutlined)"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="出勤率"
            :value="summaryData.overall_attendance_rate"
            suffix="%"
            :value-style="{ color: getTrendColor(summaryTrend) }"
            :prefix="h(CheckCircleOutlined)"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="正常率"
            :value="summaryData.overall_normal_rate"
            suffix="%"
            :prefix="h(SmileOutlined)"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="异常记录"
            :value="abnormalStats.total"
            :prefix="h(WarningOutlined)"
          >
            <template #suffix>
              <span class="abnormal-badge">
                <a-tag :color="abnormalStats.high > 0 ? 'red' : 'orange'">
                  {{ abnormalStats.high }} 严重
                </a-tag>
              </span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 快捷筛选 -->
    <a-card class="filter-card">
      <a-form layout="inline" :model="filterForm">
        <a-form-item label="统计类型">
          <a-select
            v-model:value="filterForm.stat_type"
            :options="STAT_TYPE_OPTIONS"
            style="width: 120px"
            @change="handleFilterChange"
          />
        </a-form-item>
        <a-form-item label="统计维度">
          <a-select
            v-model:value="filterForm.dimension"
            :options="DIMENSION_OPTIONS"
            style="width: 120px"
            @change="handleFilterChange"
          />
        </a-form-item>
        <a-form-item label="开始日期">
          <a-date-picker
            v-model:value="filterForm.start_date"
            format="YYYY-MM-DD"
            @change="handleFilterChange"
          />
        </a-form-item>
        <a-form-item label="结束日期">
          <a-date-picker
            v-model:value="filterForm.end_date"
            format="YYYY-MM-DD"
            @change="handleFilterChange"
          />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="loadStats">查询</a-button>
            <a-button @click="resetFilter">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 统计图表 -->
    <a-row :gutter="16" class="chart-row">
      <a-col :span="16">
        <a-card title="考勤趋势">
          <div ref="trendChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="考勤分布">
          <div ref="pieChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 考勤排名 -->
    <a-card title="考勤排名" class="ranking-card">
      <a-tabs v-model:activeKey="rankingTab">
        <a-tab-pane key="attendance" tab="出勤率排名">
          <a-table
            :columns="rankingColumns"
            :data-source="attendanceRanking"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'rank'">
                <a-badge
                  :count="record.rank"
                  :number-style="{
                    backgroundColor: record.rank <= 3 ? '#faad14' : '#e8e8e8',
                    color: record.rank <= 3 ? '#fff' : '#666',
                  }"
                />
              </template>
              <template v-else-if="column.key === 'attendance_rate'">
                <a-progress
                  :percent="record.attendance_rate"
                  size="small"
                  :stroke-color="record.attendance_rate >= 95 ? '#52c41a' : record.attendance_rate >= 85 ? '#faad14' : '#ff4d4f'"
                />
              </template>
              <template v-else-if="column.key === 'trend'">
                <a-tag :color="getTrendColor(record.trend)">
                  {{ getTrendLabel(record.trend) }}
                </a-tag>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="abnormal" tab="异常排名">
          <a-table
            :columns="abnormalRankingColumns"
            :data-source="abnormalRanking"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'rank'">
                <a-badge
                  :count="record.rank"
                  :number-style="{
                    backgroundColor: record.rank <= 3 ? '#ff4d4f' : '#e8e8e8',
                    color: record.rank <= 3 ? '#fff' : '#666',
                  }"
                />
              </template>
              <template v-else-if="column.key === 'late_count'">
                <a-tag color="orange">{{ record.late_count }} 次</a-tag>
              </template>
              <template v-else-if="column.key === 'absent_count'">
                <a-tag color="red">{{ record.absent_count }} 次</a-tag>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 异常记录列表 -->
    <a-card title="异常记录" class="abnormal-card">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="abnormalFilter.abnormal_type"
            placeholder="异常类型"
            allow-clear
            style="width: 100px"
            :options="ABNORMAL_TYPE_OPTIONS"
            @change="loadAbnormalRecords"
          />
          <a-select
            v-model:value="abnormalFilter.severity"
            placeholder="严重程度"
            allow-clear
            style="width: 100px"
            :options="SEVERITY_OPTIONS"
            @change="loadAbnormalRecords"
          />
          <a-select
            v-model:value="abnormalFilter.status"
            placeholder="处理状态"
            allow-clear
            style="width: 100px"
            :options="STATUS_OPTIONS"
            @change="loadAbnormalRecords"
          />
        </a-space>
      </template>
      <a-table
        :columns="abnormalColumns"
        :data-source="abnormalRecords"
        :loading="abnormalLoading"
        :pagination="abnormalPagination"
        @change="handleAbnormalTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'abnormal_type'">
            <a-tag :color="getAbnormalTypeColor(record.abnormal_type)">
              {{ getAbnormalTypeLabel(record.abnormal_type) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'severity'">
            <a-tag :color="getSeverityColor(record.severity)">
              {{ getSeverityLabel(record.severity) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status === 'handled' ? 'green' : 'orange'">
              {{ record.status === 'handled' ? '已处理' : '待处理' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a @click="showAbnormalDetail(record)">详情</a>
              <a-divider type="vertical" />
              <a @click="handleAbnormal(record)" v-if="record.status === 'pending'">
                处理
              </a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 生成报表弹窗 -->
    <a-modal
      v-model:open="showReportModal"
      title="生成考勤报表"
      width="600px"
      @ok="handleGenerateReport"
      @cancel="showReportModal = false"
    >
      <a-form
        ref="reportFormRef"
        layout="vertical"
        :model="reportForm"
      >
        <a-form-item label="报表类型" name="report_type">
          <a-select
            v-model:value="reportForm.report_type"
            :options="REPORT_TYPE_OPTIONS"
            placeholder="请选择报表类型"
          />
        </a-form-item>
        <a-form-item label="统计维度" name="dimension">
          <a-select
            v-model:value="reportForm.dimension"
            :options="DIMENSION_OPTIONS"
            placeholder="请选择统计维度"
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开始日期" name="start_date">
              <a-date-picker
                v-model:value="reportForm.start_date"
                format="YYYY-MM-DD"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" name="end_date">
              <a-date-picker
                v-model:value="reportForm.end_date"
                format="YYYY-MM-DD"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="班级" name="class_id">
          <a-select
            v-model:value="reportForm.class_id"
            placeholder="请选择班级（可选）"
            allow-clear
          >
            <a-select-option value="1">初一(1)班</a-select-option>
            <a-select-option value="2">初一(2)班</a-select-option>
            <a-select-option value="3">初二(1)班</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="include_abnormal">
          <a-checkbox v-model:checked="reportForm.include_abnormal">
            包含异常记录
          </a-checkbox>
        </a-form-item>
        <a-form-item name="compare_with_previous">
          <a-checkbox v-model:checked="reportForm.compare_with_previous">
            与上期对比
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 异常详情弹窗 -->
    <a-modal
      v-model:open="showAbnormalModal"
      title="异常详情"
      width="500px"
      :footer="null"
    >
      <a-descriptions bordered v-if="currentAbnormal">
        <a-descriptions-item label="学生姓名">
          {{ currentAbnormal.student_name }}
        </a-descriptions-item>
        <a-descriptions-item label="班级">
          {{ currentAbnormal.class_name }}
        </a-descriptions-item>
        <a-descriptions-item label="异常类型">
          <a-tag :color="getAbnormalTypeColor(currentAbnormal.abnormal_type)">
            {{ getAbnormalTypeLabel(currentAbnormal.abnormal_type) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="严重程度">
          <a-tag :color="getSeverityColor(currentAbnormal.severity)">
            {{ getSeverityLabel(currentAbnormal.severity) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="发生日期">
          {{ currentAbnormal.record_date }}
        </a-descriptions-item>
        <a-descriptions-item label="处理状态">
          <a-tag :color="currentAbnormal.status === 'handled' ? 'green' : 'orange'">
            {{ currentAbnormal.status === 'handled' ? '已处理' : '待处理' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="迟到时长" v-if="currentAbnormal.late_minutes > 0">
          {{ currentAbnormal.late_minutes }} 分钟
        </a-descriptions-item>
        <a-descriptions-item label="早退时长" v-if="currentAbnormal.early_minutes > 0">
          {{ currentAbnormal.early_minutes }} 分钟
        </a-descriptions-item>
        <a-descriptions-item label="课程" v-if="currentAbnormal.course_name">
          {{ currentAbnormal.course_name }}
        </a-descriptions-item>
        <a-descriptions-item label="教师" v-if="currentAbnormal.teacher_name">
          {{ currentAbnormal.teacher_name }}
        </a-descriptions-item>
        <a-descriptions-item label="处理结果" v-if="currentAbnormal.handle_result" :span="2">
          {{ currentAbnormal.handle_result }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <!-- 处理异常弹窗 -->
    <a-modal
      v-model:open="showHandleModal"
      title="处理异常记录"
      @ok="submitHandle"
      @cancel="showHandleModal = false"
    >
      <a-form layout="vertical">
        <a-form-item label="处理结果">
          <a-textarea
            v-model:value="handleForm.result"
            placeholder="请输入处理结果"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue';
import type { TableProps } from 'ant-design-vue';
import {
  ReloadOutlined,
  FileTextOutlined,
  UserOutlined,
  CheckCircleOutlined,
  SmileOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import * as echarts from 'echarts';
import {
  getAttendanceStats,
  getAttendanceSummary,
  getAbnormalRecords,
  getAttendanceRanking,
  generateReport,
  STAT_TYPE_OPTIONS,
  DIMENSION_OPTIONS,
  REPORT_TYPE_OPTIONS,
  RANKING_TYPE_OPTIONS,
  ABNORMAL_TYPE_OPTIONS,
  SEVERITY_OPTIONS,
  STATUS_OPTIONS,
  getTrendLabel,
  getTrendColor,
  getAbnormalTypeLabel,
  getAbnormalTypeColor,
  getSeverityLabel,
  getSeverityColor,
} from '@/api/attendance/attendance_stats';
import type { AttendanceStatRecord, AbnormalRecord, RankingItem } from '@/api/attendance/attendance_stats';

// ============== Refs ==============
const trendChartRef = ref<HTMLDivElement>();
const pieChartRef = ref<HTMLDivElement>();

// ============== State ==============
const filterForm = reactive({
  stat_type: 'daily',
  dimension: 'class',
  start_date: null as Dayjs | null,
  end_date: null as Dayjs | null,
});

const summaryData = reactive({
  total_students: 0,
  total_normal: 0,
  total_late: 0,
  total_early_leave: 0,
  total_absent: 0,
  total_leave: 0,
  overall_normal_rate: 0,
  overall_attendance_rate: 0,
});

const abnormalStats = reactive({
  total: 0,
  high: 0,
  medium: 0,
  low: 0,
});

const summaryTrend = ref<string>('normal');

const statsData = ref<AttendanceStatRecord[]>([]);
const statsLoading = ref(false);

const abnormalRecords = ref<AbnormalRecord[]>([]);
const abnormalLoading = ref(false);
const abnormalPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
});

const abnormalFilter = reactive({
  abnormal_type: undefined,
  severity: undefined,
  status: undefined,
});

const rankingTab = ref('attendance');
const attendanceRanking = ref<RankingItem[]>([]);
const abnormalRanking = ref<RankingItem[]>([]);

const showReportModal = ref(false);
const reportForm = reactive({
  report_type: 'summary',
  dimension: 'class',
  start_date: null as Dayjs | null,
  end_date: null as Dayjs | null,
  class_id: undefined,
  include_abnormal: true,
  compare_with_previous: false,
});

const showAbnormalModal = ref(false);
const currentAbnormal = ref<AbnormalRecord | null>(null);

const showHandleModal = ref(false);
const handleForm = reactive({
  id: 0,
  result: '',
});

// ============== Columns ==============
const rankingColumns = [
  { title: '排名', key: 'rank', width: 80 },
  { title: '名称', dataIndex: 'dimension_name', key: 'dimension_name' },
  { title: '出勤率', key: 'attendance_rate', width: 200 },
  { title: '趋势', key: 'trend', width: 100 },
];

const abnormalRankingColumns = [
  { title: '排名', key: 'rank', width: 80 },
  { title: '名称', dataIndex: 'dimension_name', key: 'dimension_name' },
  { title: '迟到次数', key: 'late_count', width: 120 },
  { title: '缺勤次数', key: 'absent_count', width: 120 },
];

const abnormalColumns = [
  { title: '学生', dataIndex: 'student_name', key: 'student_name', width: 100 },
  { title: '班级', dataIndex: 'class_name', key: 'class_name', width: 120 },
  { title: '类型', key: 'abnormal_type', width: 100 },
  { title: '严重程度', key: 'severity', width: 100 },
  { title: '日期', dataIndex: 'record_date', key: 'record_date', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
];

// ============== Methods ==============
const loadSummary = async () => {
  try {
    const startDate = filterForm.start_date?.format('YYYY-MM-DD') || dayjs().subtract(7, 'day').format('YYYY-MM-DD');
    const endDate = filterForm.end_date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD');

    const response = await getAttendanceSummary({
      start_date: startDate,
      end_date: endDate,
      dimension: filterForm.dimension as any,
    });

    if (response.success && response.data) {
      Object.assign(summaryData, response.data.summary);
      summaryTrend.value = response.data.summary.overall_attendance_rate >= 95 ? 'normal' :
        response.data.summary.overall_attendance_rate >= 85 ? 'improving' : 'deteriorating';
    }
  } catch (error) {
    console.error('加载汇总失败:', error);
  }
};

const loadStats = async () => {
  statsLoading.value = true;
  try {
    const startDate = filterForm.start_date?.format('YYYY-MM-DD') || dayjs().subtract(7, 'day').format('YYYY-MM-DD');
    const endDate = filterForm.end_date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD');

    const response = await getAttendanceStats({
      stat_type: filterForm.stat_type as any,
      dimension: filterForm.dimension as any,
      start_date: startDate,
      end_date: endDate,
      page: 1,
      page_size: 100,
    });

    if (response.success && response.data) {
      statsData.value = response.data.records;
      updateCharts();
    }
  } catch (error) {
    console.error('加载统计失败:', error);
  } finally {
    statsLoading.value = false;
  }
};

const loadAbnormalRecords = async () => {
  abnormalLoading.value = true;
  try {
    const startDate = filterForm.start_date?.format('YYYY-MM-DD') || dayjs().subtract(7, 'day').format('YYYY-MM-DD');
    const endDate = filterForm.end_date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD');

    const response = await getAbnormalRecords({
      start_date: startDate,
      end_date: endDate,
      abnormal_type: abnormalFilter.abnormal_type as any,
      severity: abnormalFilter.severity as any,
      status: abnormalFilter.status as any,
      page: abnormalPagination.current,
      page_size: abnormalPagination.pageSize,
    });

    if (response.success && response.data) {
      abnormalRecords.value = response.data.records;
      abnormalPagination.total = response.data.pagination.total;

      // 统计
      abnormalStats.total = response.data.statistics.total;
      abnormalStats.high = response.data.statistics.by_severity.high;
      abnormalStats.medium = response.data.statistics.by_severity.medium;
      abnormalStats.low = response.data.statistics.by_severity.low;
    }
  } catch (error) {
    console.error('加载异常记录失败:', error);
  } finally {
    abnormalLoading.value = false;
  }
};

const loadRanking = async () => {
  try {
    const startDate = filterForm.start_date?.format('YYYY-MM-DD') || dayjs().subtract(7, 'day').format('YYYY-MM-DD');
    const endDate = filterForm.end_date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD');

    const [attendanceRes, abnormalRes] = await Promise.all([
      getAttendanceRanking({
        dimension: filterForm.dimension as any,
        start_date: startDate,
        end_date: endDate,
        ranking_type: 'attendance',
        limit: 10,
      }),
      getAttendanceRanking({
        dimension: filterForm.dimension as any,
        start_date: startDate,
        end_date: endDate,
        ranking_type: 'absent',
        limit: 10,
      }),
    ]);

    if (attendanceRes.success && attendanceRes.data) {
      attendanceRanking.value = attendanceRes.data.ranking;
    }
    if (abnormalRes.success && abnormalRes.data) {
      abnormalRanking.value = abnormalRes.data.ranking;
    }
  } catch (error) {
    console.error('加载排名失败:', error);
  }
};

const updateCharts = () => {
  if (trendChartRef.value && statsData.value.length > 0) {
    const trendChart = echarts.init(trendChartRef.value);

    // 按日期聚合数据
    const dateMap = new Map<string, any>();
    statsData.value.forEach(record => {
      const existing = dateMap.get(record.stat_date);
      if (existing) {
        existing.total += record.total_count;
        existing.normal += record.normal_count;
        existing.late += record.late_count;
        existing.absent += record.absent_count;
      } else {
        dateMap.set(record.stat_date, {
          date: record.stat_date,
          total: record.total_count,
          normal: record.normal_count,
          late: record.late_count,
          absent: record.absent_count,
        });
      }
    });

    const dates = Array.from(dateMap.keys()).sort();
    const attendanceRates = dates.map(d => {
      const data = dateMap.get(d)!;
      return Math.round((data.total - data.absent) / data.total * 100 * 100) / 100;
    });

    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['出勤率(%)'] },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', min: 80, max: 100, axisLabel: { formatter: '{value}%' } },
      series: [{
        name: '出勤率(%)',
        type: 'line',
        data: attendanceRates,
        smooth: true,
        areaStyle: { opacity: 0.3 },
        lineStyle: { width: 3 },
        itemStyle: { color: '#1890ff' },
      }],
    });
  }

  if (pieChartRef.value) {
    const pieChart = echarts.init(pieChartRef.value);

    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}: {c}' },
        data: [
          { value: summaryData.total_normal, name: '正常', itemStyle: { color: '#52c41a' } },
          { value: summaryData.total_late, name: '迟到', itemStyle: { color: '#faad14' } },
          { value: summaryData.total_early_leave, name: '早退', itemStyle: { color: '#fa8c16' } },
          { value: summaryData.total_absent, name: '缺勤', itemStyle: { color: '#ff4d4f' } },
          { value: summaryData.total_leave, name: '请假', itemStyle: { color: '#1890ff' } },
        ],
      }],
    });
  }
};

const handleFilterChange = () => {
  // 筛选变化时的处理
};

const resetFilter = () => {
  filterForm.stat_type = 'daily';
  filterForm.dimension = 'class';
  filterForm.start_date = dayjs().subtract(7, 'day');
  filterForm.end_date = dayjs();
  loadStats();
  loadSummary();
  loadRanking();
  loadAbnormalRecords();
};

const refreshData = () => {
  loadStats();
  loadSummary();
  loadRanking();
  loadAbnormalRecords();
};

const handleGenerateReport = async () => {
  try {
    const startDate = reportForm.start_date?.format('YYYY-MM-DD');
    const endDate = reportForm.end_date?.format('YYYY-MM-DD');

    if (!startDate || !endDate) {
      return;
    }

    const response = await generateReport({
      report_type: reportForm.report_type as any,
      dimension: reportForm.dimension as any,
      start_date: startDate,
      end_date: endDate,
      class_id: reportForm.class_id,
      include_abnormal: reportForm.include_abnormal,
      compare_with_previous: reportForm.compare_with_previous,
    });

    if (response.success) {
      // 导出报表
      await exportReport({
        report_id: response.data!.id,
        export_format: 'excel',
      });
    }

    showReportModal.value = false;
  } catch (error) {
    console.error('生成报表失败:', error);
  }
};

const showAbnormalDetail = (record: AbnormalRecord) => {
  currentAbnormal.value = record;
  showAbnormalModal.value = true;
};

const handleAbnormal = (record: AbnormalRecord) => {
  handleForm.id = record.id;
  handleForm.result = '';
  showHandleModal.value = true;
};

const submitHandle = () => {
  // 提交处理结果
  console.log('提交处理:', handleForm);
  showHandleModal.value = false;
  loadAbnormalRecords();
};

const handleAbnormalTableChange: TableProps['onChange'] = (pag) => {
  abnormalPagination.current = pag.current || 1;
  abnormalPagination.pageSize = pag.pageSize || 10;
  loadAbnormalRecords();
};

// ============== Lifecycle ==============
onMounted(() => {
  // 初始化日期
  filterForm.start_date = dayjs().subtract(7, 'day');
  filterForm.end_date = dayjs();
  reportForm.start_date = dayjs().subtract(7, 'day');
  reportForm.end_date = dayjs();

  // 加载数据
  loadSummary();
  loadStats();
  loadRanking();
  loadAbnormalRecords();
});
</script>

<style scoped>
.attendance-stats-container {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  margin-bottom: 16px;
}

.stats-cards :deep(.ant-card) {
  text-align: center;
}

.abnormal-badge {
  margin-left: 8px;
}

.filter-card {
  margin-bottom: 16px;
}

.chart-row {
  margin-bottom: 16px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.ranking-card {
  margin-bottom: 16px;
}

.abnormal-card {
  margin-bottom: 16px;
}
</style>
