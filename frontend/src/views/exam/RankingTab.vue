<template>
  <div class="ranking-tab">
    <a-row :gutter="16" class="filter-row">
      <a-col :span="8">
        <a-select v-model:value="academicYear" placeholder="选择学年" style="width: 100%">
          <a-select-option value="2025-2026">2025-2026</a-select-option>
          <a-select-option value="2024-2025">2024-2025</a-select-option>
        </a-select>
      </a-col>
      <a-col :span="8">
        <a-button type="primary" @click="loadRanking">
          查询排名
        </a-button>
      </a-col>
    </a-row>

    <a-table
      :columns="columns"
      :data-source="dataList"
      :loading="loading"
      row-key="rank"
      :pagination="{ pageSize: 20 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'rank'">
          <a-badge
            :number-style="getRankBadgeStyle(record.rank)"
            :text="record.rank"
          />
        </template>
        <template v-else-if="column.key === 'average_score'">
          <a-tag :color="getScoreColor(record.average_score)">
            {{ record.average_score }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'pass_rate'">
          <a-progress
            :percent="record.pass_rate * 100"
            size="small"
            :status="record.pass_rate >= 0.6 ? 'success' : 'normal'"
          />
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const loading = ref(false)
const academicYear = ref('2025-2026')
const dataList = ref<any[]>([])

const columns = [
  { title: '排名', dataIndex: 'rank', key: 'rank', width: 80 },
  { title: '学号', dataIndex: 'student_id', key: 'student_id', width: 120 },
  { title: '姓名', dataIndex: 'student_name', key: 'student_name', width: 100 },
  { title: '平均分', dataIndex: 'average_score', key: 'average_score', width: 100 },
  { title: '考试次数', dataIndex: 'total_exams', key: 'total_exams', width: 100 },
  { title: '及格率', dataIndex: 'pass_rate', key: 'pass_rate', width: 150 }
]

const getRankBadgeStyle = (rank: number) => {
  if (rank === 1) return { backgroundColor: '#FFD700' }
  if (rank === 2) return { backgroundColor: '#C0C0C0' }
  if (rank === 3) return { backgroundColor: '#CD7F32' }
  return { backgroundColor: '#1890ff' }
}

const getScoreColor = (score: number): string => {
  if (score >= 90) return 'green'
  if (score >= 80) return 'cyan'
  if (score >= 70) return 'blue'
  if (score >= 60) return 'orange'
  return 'red'
}

const loadRanking = async () => {
  loading.value = true
  // 模拟数据
  dataList.value = [
    { rank: 1, student_id: 1005, student_name: '李四', average_score: 92.5, total_exams: 8, pass_rate: 1.0 },
    { rank: 2, student_id: 1001, student_name: '张三', average_score: 88.3, total_exams: 8, pass_rate: 0.95 },
    { rank: 3, student_id: 1008, student_name: '王五', average_score: 85.7, total_exams: 8, pass_rate: 0.9 },
    { rank: 4, student_id: 1003, student_name: '赵六', average_score: 82.1, total_exams: 8, pass_rate: 0.88 },
    { rank: 5, student_id: 1002, student_name: '钱七', average_score: 78.9, total_exams: 8, pass_rate: 0.85 }
  ]
  loading.value = false
}

onMounted(() => {
  loadRanking()
})
</script>

<style scoped>
.ranking-tab {
  padding: 16px 0;
}

.filter-row {
  margin-bottom: 16px;
}
</style>
