<template>
  <div class="subject-report-tab">
    <a-table
      :columns="columns"
      :data-source="dataList"
      :loading="loading"
      row-key="subject_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'subject_average'">
          <a-tag :color="getScoreColor(record.subject_average)">
            {{ record.subject_average }}
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
const dataList = ref<any[]>([])

const columns = [
  { title: '科目ID', dataIndex: 'subject_id', key: 'subject_id', width: 100 },
  { title: '科目名称', dataIndex: 'subject_name', key: 'subject_name', width: 150 },
  { title: '考生数', dataIndex: 'total_students', key: 'total_students', width: 100 },
  { title: '平均分', dataIndex: 'subject_average', key: 'subject_average', width: 100 },
  { title: '最高分', dataIndex: 'highest_score', key: 'highest_score', width: 100 },
  { title: '最低分', dataIndex: 'lowest_score', key: 'lowest_score', width: 100 },
  { title: '及格率', dataIndex: 'pass_rate', key: 'pass_rate', width: 150 }
]

const getScoreColor = (score: number): string => {
  if (score >= 85) return 'green'
  if (score >= 75) return 'cyan'
  if (score >= 65) return 'blue'
  return 'orange'
}

const loadData = async () => {
  loading.value = true
  // 模拟数据
  dataList.value = [
    { subject_id: 1, subject_name: '语文', total_students: 120, subject_average: 82.5, highest_score: 98, lowest_score: 45, pass_rate: 0.92 },
    { subject_id: 2, subject_name: '数学', total_students: 120, subject_average: 75.3, highest_score: 100, lowest_score: 32, pass_rate: 0.78 },
    { subject_id: 3, subject_name: '英语', total_students: 120, subject_average: 80.1, highest_score: 95, lowest_score: 50, pass_rate: 0.88 }
  ]
  loading.value = false
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.subject-report-tab {
  padding: 16px 0;
}
</style>
