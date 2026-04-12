<template>
  <div class="exam-report-tab">
    <a-table
      :columns="columns"
      :data-source="dataList"
      :loading="loading"
      row-key="exam_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'overall_average'">
          <a-tag :color="getScoreColor(record.overall_average)">
            {{ record.overall_average }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'pass_rate'">
          <a-progress
            :percent="record.pass_rate * 100"
            size="small"
            :status="record.pass_rate >= 0.6 ? 'success' : 'normal'"
          />
        </template>
        <template v-else-if="column.key === 'difficulty_index'">
          <a-tag :color="getDifficultyColor(record.difficulty_index)">
            {{ record.difficulty_index }}
          </a-tag>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const loading = ref(false)
const dataList = ref<any[]>([])

const columns = [
  { title: '考试ID', dataIndex: 'exam_id', key: 'exam_id', width: 100 },
  { title: '考试名称', dataIndex: 'exam_name', key: 'exam_name', width: 200 },
  { title: '考试日期', dataIndex: 'exam_date', key: 'exam_date', width: 120 },
  { title: '考生数', dataIndex: 'total_students', key: 'total_students', width: 100 },
  { title: '平均分', dataIndex: 'overall_average', key: 'overall_average', width: 100 },
  { title: '及格率', dataIndex: 'pass_rate', key: 'pass_rate', width: 150 },
  { title: '难度指数', dataIndex: 'difficulty_index', key: 'difficulty_index', width: 100 }
]

const getScoreColor = (score: number): string => {
  if (score >= 85) return 'green'
  if (score >= 75) return 'cyan'
  if (score >= 65) return 'blue'
  return 'orange'
}

const getDifficultyColor = (index: number): string => {
  if (index >= 0.8) return 'green'      // 容易
  if (index >= 0.6) return 'blue'      // 适中
  if (index >= 0.4) return 'orange'   // 较难
  return 'red'                          // 困难
}

const loadData = async () => {
  loading.value = true
  // 模拟数据
  dataList.value = [
    { exam_id: 1, exam_name: '期中考试', exam_date: '2025-11-15', total_students: 120, overall_average: 78.5, pass_rate: 0.85, difficulty_index: 0.78 },
    { exam_id: 2, exam_name: '期末考试', exam_date: '2026-01-20', total_students: 118, overall_average: 72.3, pass_rate: 0.76, difficulty_index: 0.72 }
  ]
  loading.value = false
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.exam-report-tab {
  padding: 16px 0;
}
</style>
