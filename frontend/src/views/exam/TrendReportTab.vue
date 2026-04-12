<template>
  <div class="trend-report-tab">
    <a-row :gutter="16" class="search-row">
      <a-col :span="8">
        <a-input v-model:value="studentId" placeholder="请输入学号" />
      </a-col>
      <a-col :span="8">
        <a-button type="primary" @click="loadTrend">
          查询趋势
        </a-button>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="stats-row" v-if="trendData">
      <a-col :span="6">
        <a-statistic
          title="整体趋势"
          :value="TrendMap[trendData.overall_trend]?.text || trendData.overall_trend"
          :value-style="{ color: getTrendColor(trendData.overall_trend) }"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          title="进步率"
          :value="trendData.improvement_rate"
          suffix="%"
          :precision="1"
          :value-style="{ color: trendData.improvement_rate >= 0 ? '#52c41a' : '#faad14' }"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          title="预测下次成绩"
          :value="trendData.predicted_next"
          :precision="1"
          suffix="分"
        />
      </a-col>
    </a-row>

    <a-card title="成绩趋势图" class="chart-card" v-if="trendData">
      <div class="chart-placeholder">
        <a-result
          title="成绩趋势"
          :sub-title="`学期趋势数据已加载，共${trendData.semester_scores?.length || 0}个学期`"
        >
          <template #icon>
            <LineChartOutlined style="font-size: 64px; color: #1890ff;" />
          </template>
        </a-result>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { LineChartOutlined } from '@ant-design/icons-vue'
import { TrendMap } from '@/api/exam/report'

const studentId = ref('')
const trendData = ref<any>(null)

const getTrendColor = (trend: string): string => {
  if (trend === '上升' || trend === 'up') return '#52c41a'
  if (trend === '下降' || trend === 'down') return '#faad14'
  return '#1890ff'
}

const loadTrend = async () => {
  if (!studentId.value) return

  // 模拟数据
  trendData.value = {
    student_id: parseInt(studentId.value),
    student_name: '学生',
    academic_year: '2025-2026',
    semester_scores: [
      { semester: 1, average: 75 },
      { semester: 2, average: 78 },
      { semester: 3, average: 82 },
      { semester: 4, average: 85 }
    ],
    overall_trend: '上升',
    improvement_rate: 13.3,
    predicted_next: 88
  }
}
</script>

<style scoped>
.trend-report-tab {
  padding: 16px 0;
}

.search-row {
  margin-bottom: 24px;
}

.stats-row {
  margin-bottom: 24px;
}

.chart-card {
  margin-top: 16px;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
